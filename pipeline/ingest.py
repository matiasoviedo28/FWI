"""Descarga de los NetCDF del SMN desde el bucket público (acceso anónimo).

Cada corrida del modelo (run 00Z de una fecha de inicialización) pronostica hasta
+72h. Según el `offset` de pronóstico se bajan los dos archivos del día objetivo:
  - instantáneas de mediodía (lead +15h/+39h/+63h)
  - precipitación acumulada 24h (lead +24h/+48h/+72h)
Es idempotente: si el archivo ya está en cache, no lo vuelve a bajar.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from shared import config as cfg


def _key_y_destino(init: date, lead: str) -> tuple[str, Path]:
    key = cfg.S3_KEY_TMPL.format(y=f"{init:%Y}", m=f"{init:%m}", d=f"{init:%d}", lead=lead)
    return key, cfg.CACHE / Path(key).name


def descargar(init: date, offset: int) -> dict[str, Path]:
    """Descarga (si falta) los archivos del run `init` para el `offset` pedido.

    `init` = fecha de inicialización del run. El día objetivo es init + offset.
    """
    import s3fs

    fs = s3fs.S3FileSystem(anon=True)
    lead_inst, lead_pp = cfg.leads_para(offset)
    rutas: dict[str, Path] = {}
    for nombre, lead in (("instant", lead_inst), ("precip", lead_pp)):
        key, destino = _key_y_destino(init, lead)
        if not destino.exists():
            fs.get(f"{cfg.S3_BUCKET}/{key}", str(destino))
        rutas[nombre] = destino
    return rutas


def limpiar_cache_nc() -> int:
    """Borra los .nc del cache una vez procesados. Devuelve cuántos borró."""
    n = 0
    for f in cfg.CACHE.glob("*.nc"):
        f.unlink()
        n += 1
    return n
