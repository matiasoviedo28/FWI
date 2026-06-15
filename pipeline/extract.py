"""Extracción vectorizada de las variables meteorológicas para todos los puntos.

Aplica las correcciones verificadas en F1:
  - variables instantáneas del archivo _015 (mediodía local)
  - precipitación 24h del archivo _024 (acumulada 0->24h; resuelve el bug de la
    ventana del código viejo que siempre daba 0 en la parte del día anterior)
  - HR clampeada a [0, 100] (el modelo puede dar >100%)
  - viento m/s -> km/h
Abre cada NetCDF UNA sola vez e indexa los ~28k puntos de golpe.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from shared import config as cfg


def extraer_dia(indice_celdas: pd.DataFrame, nc_instant: Path, nc_precip: Path) -> pd.DataFrame:
    ys = indice_celdas.y.values
    xs = indice_celdas.x.values

    d15 = xr.open_dataset(nc_instant)
    temp = np.asarray(d15[cfg.VAR_TEMP].values)[0, ys, xs]
    hum = np.asarray(d15[cfg.VAR_HUM].values)[0, ys, xs]
    viento = np.asarray(d15[cfg.VAR_WIND].values)[0, ys, xs] * 3.6  # m/s -> km/h
    fecha = pd.to_datetime(d15["time"].values)[0]
    d15.close()

    d24 = xr.open_dataset(nc_precip)
    precip = np.asarray(d24[cfg.VAR_PRECIP].values)[0, ys, xs]      # acumulada 0->24h
    d24.close()

    hum = np.clip(hum, 0.0, 100.0)

    return pd.DataFrame({
        "PUNTO": indice_celdas.PUNTO.values,
        "lat": indice_celdas.lat.values,
        "lon": indice_celdas.lon.values,
        "Fecha": fecha.normalize(),
        "Temperatura": temp.astype("float32"),
        "Humedad": hum.astype("float32"),
        "Viento": viento.astype("float32"),
        "Precipitacion": precip.astype("float32"),
    })
