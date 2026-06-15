"""Plano de control en Postgres: cobertura de datos y cola de jobs de descarga.

Las grillas pesadas viven en Parquet/GeoJSON; acá solo va el *estado*: qué días
tenemos (cobertura) y los trabajos de backfill disparados desde la web.
"""
from __future__ import annotations

import time
from datetime import date

import psycopg

from shared import config as cfg

SCHEMA = """
CREATE TABLE IF NOT EXISTS coverage (
    fecha        DATE PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS jobs (
    id         SERIAL PRIMARY KEY,
    desde      DATE NOT NULL,
    hasta      DATE NOT NULL,
    status     TEXT NOT NULL DEFAULT 'pending',   -- pending/running/done/failed
    fase       TEXT NOT NULL DEFAULT 'descarga',  -- descarga/procesando
    total      INT  NOT NULL,
    done       INT  NOT NULL DEFAULT 0,
    message    TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
-- migraciones idempotentes para DBs previas
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS fase TEXT NOT NULL DEFAULT 'descarga';
"""


def connect(retries: int = 30, delay: float = 2.0):
    last = None
    for _ in range(retries):
        try:
            return psycopg.connect(cfg.DATABASE_URL, autocommit=True)
        except psycopg.OperationalError as e:  # la DB puede tardar en levantar
            last = e
            time.sleep(delay)
    raise last


def init(sync_fs: bool = True) -> None:
    with connect() as c:
        c.execute(SCHEMA)
        if sync_fs:
            # reconciliar cobertura con lo que ya exista en disco (observado)
            for f in cfg.fechas_disponibles("observed"):
                c.execute("INSERT INTO coverage (fecha) VALUES (%s) ON CONFLICT DO NOTHING", (f,))


# --- cobertura ---

def marcar_cubierto(d: date) -> None:
    with connect() as c:
        c.execute("INSERT INTO coverage (fecha) VALUES (%s) ON CONFLICT DO NOTHING", (d,))


def cobertura() -> list[date]:
    with connect() as c:
        return [r[0] for r in c.execute("SELECT fecha FROM coverage ORDER BY fecha").fetchall()]


def rango_cobertura() -> tuple[date | None, date | None]:
    with connect() as c:
        r = c.execute("SELECT min(fecha), max(fecha) FROM coverage").fetchone()
        return (r[0], r[1]) if r else (None, None)


# --- cola de jobs ---

def encolar(desde: date, hasta: date) -> int:
    total = (hasta - desde).days + 1
    with connect() as c:
        return c.execute(
            "INSERT INTO jobs (desde, hasta, total) VALUES (%s, %s, %s) RETURNING id",
            (desde, hasta, total)).fetchone()[0]


def reclamar():
    """Toma atómicamente el próximo job pendiente (FOR UPDATE SKIP LOCKED)."""
    with connect() as c:
        return c.execute("""
            UPDATE jobs SET status='running', started_at=now(), updated_at=now()
            WHERE id = (SELECT id FROM jobs WHERE status='pending'
                        ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1)
            RETURNING id, desde, hasta, total
        """).fetchone()


def progreso(job_id: int, done: int, message: str | None = None, total: int | None = None) -> None:
    with connect() as c:
        if total is None:
            c.execute("UPDATE jobs SET done=%s, message=%s, updated_at=now() WHERE id=%s",
                      (done, message, job_id))
        else:
            c.execute("UPDATE jobs SET done=%s, total=%s, message=%s, updated_at=now() WHERE id=%s",
                      (done, total, message, job_id))


def cambiar_fase(job_id: int, fase: str, total: int) -> None:
    """Pasa a una nueva fase: reinicia el contador y el cronómetro (para la ETA)."""
    with connect() as c:
        c.execute("UPDATE jobs SET fase=%s, total=%s, done=0, started_at=now(), updated_at=now() WHERE id=%s",
                  (fase, total, job_id))


def finalizar(job_id: int, status: str, message: str | None = None) -> None:
    with connect() as c:
        c.execute("UPDATE jobs SET status=%s, message=%s, updated_at=now() WHERE id=%s",
                  (status, message, job_id))


_JOB_COLS = ["id", "desde", "hasta", "status", "fase", "total", "done", "message",
             "created_at", "started_at", "updated_at"]
_JOB_SELECT = "SELECT " + ",".join(_JOB_COLS) + " FROM jobs"


def _job_dict(row) -> dict:
    import datetime as _dt

    d = dict(zip(_JOB_COLS, row))
    # ETA estimada a partir del ritmo de descarga (días/seg) desde que arrancó
    eta = None
    if d["status"] == "running" and d["started_at"] and d["done"] > 0:
        elapsed = (_dt.datetime.now(_dt.timezone.utc) - d["started_at"]).total_seconds()
        eta = round(elapsed / d["done"] * (d["total"] - d["done"]))
    d["eta_seg"] = eta
    for k in ("desde", "hasta", "created_at", "started_at", "updated_at"):
        d[k] = d[k].isoformat() if d[k] else None
    return d


def listar_jobs(limit: int = 20) -> list[dict]:
    with connect() as c:
        rows = c.execute(f"{_JOB_SELECT} ORDER BY id DESC LIMIT %s", (limit,)).fetchall()
        return [_job_dict(r) for r in rows]


def obtener_job(job_id: int) -> dict | None:
    with connect() as c:
        r = c.execute(f"{_JOB_SELECT} WHERE id=%s", (job_id,)).fetchone()
        return _job_dict(r) if r else None


# --- escala de riesgo (cortes de FWI configurables, persistidos) ---

def get_cortes() -> list[float]:
    """Cortes activos: los guardados por el usuario, o los de por defecto."""
    import json
    with connect() as c:
        r = c.execute("SELECT value FROM settings WHERE key='cortes_fwi'").fetchone()
    return json.loads(r[0]) if r else list(cfg.CORTES_FWI)


def set_cortes(cortes: list[float]) -> None:
    import json
    with connect() as c:
        c.execute("""INSERT INTO settings (key, value) VALUES ('cortes_fwi', %s)
                     ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value""",
                  (json.dumps(cortes),))


def reset_cortes() -> None:
    with connect() as c:
        c.execute("DELETE FROM settings WHERE key='cortes_fwi'")


def cortes_modificados() -> bool:
    with connect() as c:
        return c.execute("SELECT 1 FROM settings WHERE key='cortes_fwi'").fetchone() is not None
