"""Persistencia en Parquet (reemplaza el append a CSV del proyecto viejo).

Se guarda la extracción meteorológica cruda, un archivo por fecha (idempotente).
Los índices se recalculan sobre la serie completa en cada corrida, porque el
CFFWIS es acumulativo (encadenado) y necesita la serie para ser correcto.
"""
from __future__ import annotations

import pandas as pd

from shared import config as cfg

_MET_DIR = cfg.PARQUET / "met"
_MET_DIR.mkdir(parents=True, exist_ok=True)


def _ruta_met(fecha) -> "pathlib.Path":
    return _MET_DIR / f"met_{pd.Timestamp(fecha):%Y-%m-%d}.parquet"


def guardar_met(df_dia: pd.DataFrame) -> None:
    fecha = pd.Timestamp(df_dia["Fecha"].iloc[0])
    df_dia.to_parquet(_ruta_met(fecha), index=False)


def fechas_met() -> set:
    return {p.stem.replace("met_", "") for p in _MET_DIR.glob("met_*.parquet")}


def leer_met(desde=None, hasta=None) -> pd.DataFrame:
    archivos = sorted(_MET_DIR.glob("met_*.parquet"))
    if not archivos:
        return pd.DataFrame()
    df = pd.concat((pd.read_parquet(a) for a in archivos), ignore_index=True)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    if desde is not None:
        df = df[df["Fecha"] >= pd.Timestamp(desde)]
    if hasta is not None:
        df = df[df["Fecha"] <= pd.Timestamp(hasta)]
    return df
