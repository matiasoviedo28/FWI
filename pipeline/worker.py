"""Worker del pipeline: consume la cola de jobs y mantiene el día actual.

- Toma jobs de backfill (encolados desde la web), los procesa día a día y va
  actualizando el progreso y la cobertura.
- Cuando está ocioso, una vez por día asegura el día de hoy + el pronóstico.
"""
from __future__ import annotations

import time
from datetime import date, timedelta

from pipeline import db, ingest, run, storage

IDLE_SLEEP = 5         # segundos entre chequeos cuando no hay jobs (reband ágil)
DAILY_FILL_MAX = 10    # huecos de hasta N días se rellenan solos; más grandes, backfill manual


def _cubierto(d: date) -> bool:
    return d.strftime("%Y-%m-%d") in storage.fechas_met()


def procesar_job(job) -> None:
    job_id, desde, hasta, total = job
    print(f"[job {job_id}] {desde}..{hasta} ({total} días)")
    dias = [desde + timedelta(days=i) for i in range((hasta - desde).days + 1)]
    done = 0
    try:
        for d in dias:
            ya = _cubierto(d)                       # ya estaba (no cuenta como descarga)
            run.ingest_observado(d)
            if _cubierto(d):
                db.marcar_cubierto(d)
                if not ya:
                    done += 1
                    db.progreso(job_id, done, f"descargado {d:%Y-%m-%d}")
            else:
                db.progreso(job_id, done, f"{d:%Y-%m-%d} no disponible en el SMN")
        # fase 2: procesamiento (recalcular índices + generar las bandas por día).
        # En períodos largos este render de N días también lleva tiempo, así que
        # se muestra con su propia barra.
        db.cambiar_fase(job_id, "procesando", len(dias))
        run.regenerar(dias, base_pronostico=None, cortes=db.get_cortes(),
                      on_progress=lambda i, n: db.progreso(job_id, i, f"procesando {i}/{n}", total=n))
        db.finalizar(job_id, "done", f"{done} días descargados, {len(dias)} procesados")
        print(f"[job {job_id}] done")
    except Exception as e:  # noqa: BLE001 — el worker no debe morir por un job
        db.finalizar(job_id, "failed", str(e)[:300])
        print(f"[job {job_id}] FAILED: {e}")
    finally:
        ingest.limpiar_cache_nc()


def asegurar_hoy(hoy: date) -> None:
    """Rellena de forma contigua desde el último día cubierto hasta hoy + pronóstico.

    Así, si el sistema estuvo apagado unos días, no quedan huecos (que romperían
    el encadenamiento). Huecos mayores a DAILY_FILL_MAX se dejan para backfill manual.
    """
    _, max_c = db.rango_cobertura()
    inicio = (max_c + timedelta(days=1)) if max_c else hoy
    inicio = max(inicio, hoy - timedelta(days=DAILY_FILL_MAX))
    inicio = min(inicio, hoy)
    dias = [inicio + timedelta(days=i) for i in range((hoy - inicio).days + 1)]
    print(f"[daily] asegurando {inicio:%Y-%m-%d}..{hoy:%Y-%m-%d} + pronóstico")

    nuevos = []
    for d in dias:
        run.ingest_observado(d)
        if _cubierto(d):
            db.marcar_cubierto(d)
            nuevos.append(d)
    try:
        run.regenerar(nuevos or [hoy], base_pronostico=hoy, cortes=db.get_cortes())
    except Exception as e:  # noqa: BLE001
        print(f"[daily] aviso: {e}")
    finally:
        ingest.limpiar_cache_nc()


def main() -> None:
    print("[worker] init DB ...")
    db.init()
    ultimo_daily = None
    print("[worker] listo, escuchando la cola ...")
    while True:
        job = db.reclamar()
        if job:
            procesar_job(job)
            continue
        hoy = date.today()
        if ultimo_daily != hoy:
            asegurar_hoy(hoy)
            ultimo_daily = hoy
        time.sleep(IDLE_SLEEP)


if __name__ == "__main__":
    main()
