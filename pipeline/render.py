"""Render del campo de FWI como bandas vectoriales rellenas (isobandas por nivel).

En vez de servir ~167k puntos (que dejan huecos al hacer zoom y pesan ~50 MB), se
agrupan las celdas contiguas del mismo nivel de riesgo en polígonos. El resultado:
llena el mapa, es vector (nítido a cualquier zoom) y pesa ~1 MB.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
from affine import Affine
from rasterio import features
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

from shared import config as cfg

_NODATA = 255


def _grilla_2d(dia: pd.DataFrame):
    """Reconstruye la grilla regular 2D de FWI y su transform pixel->lon/lat."""
    paso_lat = cfg.GRID_KM / 111.0
    paso_lon = cfg.GRID_KM / (111.0 * math.cos(math.radians((cfg.LAT_MIN + cfg.LAT_MAX) / 2)))
    lat0 = cfg.LAT_MIN + paso_lat / 2
    lon0 = cfg.LON_MIN + paso_lon / 2
    rows = np.round((dia.lat.values - lat0) / paso_lat).astype(int)
    cols = np.round((dia.lon.values - lon0) / paso_lon).astype(int)
    fwi = np.full((rows.max() + 1, cols.max() + 1), np.nan, dtype="float32")
    fwi[rows, cols] = dia.FWI.values
    transform = Affine(paso_lon, 0, cfg.LON_MIN, 0, paso_lat, cfg.LAT_MIN)
    return fwi, transform


def _arg_polygon():
    import geopandas as gpd
    return unary_union(gpd.read_file(cfg.LIMITES_GEOJSON).geometry.values)


def generar_bandas(dia: pd.DataFrame, destino_full, destino_simple,
                   cortes=None, simplify_tol: float = 0.03) -> None:
    """Genera el GeoJSON de bandas (full y simplificado) del día."""
    cortes = cortes or cfg.CORTES_FWI
    fwi, transform = _grilla_2d(dia)
    clase = np.digitize(fwi, cortes).astype("int32")                # 0..4
    clase = np.where(np.isnan(fwi), _NODATA, clase).astype("int32")

    geoms = {k: [] for k in range(5)}
    for geom, val in features.shapes(clase, mask=(clase != _NODATA), transform=transform):
        v = int(val)
        if v < 5:
            geoms[v].append(shape(geom))

    arg = _arg_polygon()

    def feature_collection(tol: float):
        feats = []
        for k in range(5):
            if not geoms[k]:
                continue
            g = unary_union(geoms[k]).intersection(arg)
            if g.is_empty:
                continue
            if tol:
                g = g.simplify(tol, preserve_topology=True)
            feats.append({
                "type": "Feature",
                "geometry": mapping(g),
                "properties": {"nivel": cfg.NIVELES[k], "color": cfg.COLORES_CLASE[k], "clase": k},
            })
        return {"type": "FeatureCollection", "features": feats}

    with open(destino_full, "w") as f:
        json.dump(feature_collection(0.0), f)
    with open(destino_simple, "w") as f:
        json.dump(feature_collection(simplify_tol), f)


def guardar_puntos(dia: pd.DataFrame, destino) -> None:
    """Guarda los datos por celda para las consultas on-click del popup."""
    cols = ["PUNTO", "lat", "lon", "Fecha", "Temperatura", "Humedad", "Viento",
            "Precipitacion", "FWI"]
    if "Provincia" in dia.columns:
        cols.append("Provincia")
    dia[cols].to_parquet(destino, index=False)
