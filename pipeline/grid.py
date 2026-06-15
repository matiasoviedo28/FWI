"""Grilla de muestreo y mapeo punto -> celda del WRF.

El mapeo se calcula UNA sola vez con un KDTree (la grilla del WRF es fija) y se
cachea: el día a día solo lee el cache. Reemplaza el argmin-sobre-toda-la-grilla
por punto que hacía el código viejo (~232 s/día -> ~0.1 s/día).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import xarray as xr
from scipy.spatial import cKDTree

from shared import config as cfg


def generar_grilla() -> pd.DataFrame:
    """Genera los puntos centrales de cada cuadrante de ~GRID_KM km sobre Argentina."""
    km_to_deg_lat = 1 / 111.0
    paso_lat = cfg.GRID_KM * km_to_deg_lat
    lat_med = (cfg.LAT_MIN + cfg.LAT_MAX) / 2
    paso_lon = cfg.GRID_KM * (1 / (111.0 * math.cos(math.radians(lat_med))))

    filas, pid = [], 1
    lat = cfg.LAT_MIN
    while lat <= cfg.LAT_MAX:
        lon = cfg.LON_MIN
        while lon <= cfg.LON_MAX:
            filas.append({"PUNTO": f"PUNTO_{pid}",
                          "lat": lat + paso_lat / 2,
                          "lon": lon + paso_lon / 2})
            pid += 1
            lon += paso_lon
        lat += paso_lat
    return pd.DataFrame(filas)


def _haversine_km(la1, lo1, la2, lo2):
    R = 6371.0
    la1, lo1, la2, lo2 = map(np.radians, [la1, lo1, la2, lo2])
    d = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(d))


def construir_indice_celdas(nc_grilla: str, puntos: pd.DataFrame) -> pd.DataFrame:
    """KDTree punto -> (y, x) sobre la grilla 2D del WRF. Una sola vez."""
    ds = xr.open_dataset(nc_grilla)
    lat = np.asarray(ds["lat"].values)
    lon = np.asarray(ds["lon"].values)
    ds.close()

    tree = cKDTree(np.column_stack([lat.ravel(), lon.ravel()]))
    _, flat = tree.query(np.column_stack([puntos.lat.values, puntos.lon.values]))
    ys, xs = np.unravel_index(flat, lat.shape)

    out = puntos.copy()
    out["y"], out["x"] = ys, xs
    out["cell_lat"], out["cell_lon"] = lat[ys, xs], lon[ys, xs]
    out["dist_km"] = _haversine_km(puntos.lat.values, puntos.lon.values,
                                   out.cell_lat.values, out.cell_lon.values)
    return out


def cargar_indice_celdas(nc_grilla: str) -> pd.DataFrame:
    """Devuelve el mapeo punto->celda desde cache; si no existe, lo construye."""
    if cfg.CELL_INDEX.exists():
        return pd.read_parquet(cfg.CELL_INDEX)
    idx = construir_indice_celdas(nc_grilla, generar_grilla())
    idx.to_parquet(cfg.CELL_INDEX)
    return idx
