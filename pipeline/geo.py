"""Asignación de provincia por intersección espacial."""
from __future__ import annotations

import pandas as pd

from shared import config as cfg


def asignar_provincia(df: pd.DataFrame) -> pd.DataFrame:
    """Asigna provincia a cada punto por intersección espacial.

    Con la grilla nativa de 4 km los bordes provinciales quedan bien resueltos,
    así que ya no se usan correcciones manuales por punto.
    """
    import geopandas as gpd
    from shapely.geometry import Point

    prov = gpd.read_file(cfg.NOMBRES_GEOJSON)
    pts = gpd.GeoDataFrame(df.copy(),
                           geometry=[Point(xy) for xy in zip(df.lon, df.lat)],
                           crs=prov.crs)
    pts = gpd.sjoin(pts, prov[["nombre", "geometry"]], how="left", predicate="within")
    pts = pts.rename(columns={"nombre": "Provincia"}).drop(columns=["index_right"], errors="ignore")
    return pd.DataFrame(pts.drop(columns="geometry")).dropna(subset=["Provincia"])
