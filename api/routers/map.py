"""Endpoints de datos del mapa: cobertura, bandas por fecha/tipo y detalle por celda."""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from shared import config as cfg

router = APIRouter(prefix="/fwi", tags=["Mapa"])

Kind = str  # "observed" | "forecast"


@router.get("/coverage", summary="Cobertura de datos: desde/hasta y horizonte de pronóstico")
def coverage():
    from pipeline import db
    obs = [d.isoformat() for d in db.cobertura()]          # autoritativo: la DB
    fct = cfg.fechas_disponibles("forecast")
    # tope de pronóstico: el día observado más reciente + FORECAST_MAX_OFFSET
    tope = None
    if obs:
        tope = (date.fromisoformat(obs[-1]) + timedelta(days=cfg.FORECAST_MAX_OFFSET)).isoformat()
    return {
        "observed": {"desde": obs[0] if obs else None, "hasta": obs[-1] if obs else None, "dias": obs},
        "forecast": {"dias": fct},
        "forecast_max": tope,          # el front no debe permitir elegir más allá de esto
        "forecast_max_offset": cfg.FORECAST_MAX_OFFSET,
    }


def _resolver_kind(fecha: str, kind: str | None) -> str:
    if kind in cfg.KINDS:
        return kind
    if fecha in cfg.fechas_disponibles("observed"):
        return "observed"
    if fecha in cfg.fechas_disponibles("forecast"):
        return "forecast"
    raise HTTPException(404, f"No hay datos para {fecha}.")


@router.get("/limites.geojson", summary="Límites interprovinciales (para dibujar encima)")
def limites():
    if not cfg.LIMITES_GEOJSON.exists():
        raise HTTPException(404, "Sin geojson de límites.")
    return FileResponse(cfg.LIMITES_GEOJSON, media_type="application/geo+json")


@router.get("/bands.geojson", summary="Bandas de FWI de una fecha")
def bands(fecha: str = Query(..., description="YYYY-MM-DD"),
          kind: str | None = None, simple: bool = True):
    k = _resolver_kind(fecha, kind)
    path = cfg.bands_path(k, fecha, simple=simple)
    if not path.exists():
        raise HTTPException(404, f"Sin bandas para {fecha} ({k}).")
    return FileResponse(path, media_type="application/geo+json")


@router.get("/at", summary="Datos de la celda más cercana (para el popup)")
def at(lat: float, lon: float, fecha: str, kind: str | None = None):
    k = _resolver_kind(fecha, kind)
    path = cfg.points_path(k, fecha)
    if not path.exists():
        raise HTTPException(404, f"Sin datos por celda para {fecha} ({k}).")
    df = pd.read_parquet(path)
    i = int(np.argmin((df["lat"].values - lat) ** 2 + (df["lon"].values - lon) ** 2))
    r = df.iloc[i]
    from pipeline import db
    clase = cfg.clase_fwi(float(r["FWI"]), db.get_cortes())   # cortes en vivo
    return {
        "punto": r["PUNTO"], "provincia": r.get("Provincia"),
        "lat": round(float(r["lat"]), 3), "lon": round(float(r["lon"]), 3),
        "fwi": round(float(r["FWI"]), 2), "clase": clase, "nivel": cfg.NIVELES[clase],
        "temperatura": round(float(r["Temperatura"]), 1),
        "humedad": round(float(r["Humedad"]), 1),
        "viento": round(float(r["Viento"]), 1),
        "precipitacion": round(float(r["Precipitacion"]), 1),
        "fecha": fecha, "tipo": k,
    }
