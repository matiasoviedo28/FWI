"""Configuración central del proyecto FWI Argentina.

Reúne en un solo lugar lo que antes estaba disperso y hardcodeado en app.py:
rutas, parámetros de la grilla, fuente de datos del SMN y escala de riesgo.
Las rutas se resuelven relativas a la raíz del repo (sin paths absolutos del server).
"""
from __future__ import annotations

import os
from pathlib import Path

# --- base de datos (plano de control: cobertura + cola de jobs) ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fwi:fwi@localhost:5432/fwi")

# --- rutas ---
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = DATA / "cache"          # .nc descargados (efímero)
PARQUET = DATA / "parquet"      # histórico de índices (particionado por fecha)
OUTPUTS = DATA / "outputs"      # salidas servidas (GeoJSON); volumen compartido api<->pipeline
CSV = DATA / "CSV"
JSON = DATA / "JSON"

HISTORY = PARQUET                            # dataset parquet del histórico
# Salidas del mapa, organizadas por tipo (observado/pronóstico) y fecha.
# Cada día queda como bandas vectoriales (full + simple) + puntos para el popup.
OUTPUTS_OBS = OUTPUTS / "observed"
OUTPUTS_FCT = OUTPUTS / "forecast"

for _p in (CACHE, PARQUET, OUTPUTS, OUTPUTS_OBS, OUTPUTS_FCT):
    _p.mkdir(parents=True, exist_ok=True)

KINDS = ("observed", "forecast")


def _salida_dir(kind: str, fecha: str):
    d = (OUTPUTS_OBS if kind == "observed" else OUTPUTS_FCT) / fecha
    d.mkdir(parents=True, exist_ok=True)
    return d


def bands_path(kind: str, fecha: str, simple: bool = False):
    return _salida_dir(kind, fecha) / ("bands_simple.geojson" if simple else "bands.geojson")


def points_path(kind: str, fecha: str):
    return _salida_dir(kind, fecha) / "points.parquet"


def fechas_disponibles(kind: str) -> list[str]:
    base = OUTPUTS_OBS if kind == "observed" else OUTPUTS_FCT
    return sorted(p.name for p in base.iterdir() if p.is_dir() and (p / "bands.geojson").exists())

# --- grilla de muestreo sobre Argentina (bounding box) ---
LAT_MIN, LAT_MAX = -55.049798, -21.942106
LON_MIN, LON_MAX = -73.533832, -53.615167
# Resolución nativa del modelo WRF-DET = 4 km. No tiene sentido bajar de ahí
# (sería sobremuestrear las mismas celdas). Configurable vía FWI_GRID_KM.
GRID_KM = float(os.getenv("FWI_GRID_KM", "4"))   # tamaño de cuadrante (km)

# El cache del mapeo punto->celda depende del tamaño de grilla: si cambia,
# se regenera solo (no reutiliza el de otra resolución).
CELL_INDEX = CACHE / f"cell_index_{GRID_KM:g}km.parquet"

# --- fuente de datos: SMN WRF-DET (bucket público, acceso anónimo) ---
S3_BUCKET = "smn-ar-wrf"
S3_KEY_TMPL = "DATA/WRF/DET/{y}/{m}/{d}/00/WRFDETAR_01H_{y}{m}{d}_00_{lead}.nc"

# El run de las 00Z pronostica hasta +72h. Desde un mismo run obtenemos varios
# días según el "offset" de pronóstico (días desde la fecha de inicialización):
#   offset 0 = ese día (observado)       -> mediodía=+15h, lluvia24h=+24h
#   offset 1 = día siguiente (pronóstico)-> +39h / +48h
#   offset 2 = +2 días (pronóstico)      -> +63h / +72h  (tope: +72h es el máximo)
LEAD_INSTANT_H0 = 15   # mediodía local del día de inicialización
LEAD_PRECIP_H0 = 24    # acumulación 24h del día de inicialización
FORECAST_MAX_OFFSET = 2   # tope automático: más allá de +2 días no hay datos (>72h)


def leads_para(offset: int) -> tuple[str, str]:
    """Devuelve (lead_instantáneas, lead_precip) para un offset de pronóstico."""
    if not 0 <= offset <= FORECAST_MAX_OFFSET:
        raise ValueError(f"offset fuera de rango 0..{FORECAST_MAX_OFFSET}: {offset}")
    return f"{LEAD_INSTANT_H0 + 24 * offset:03d}", f"{LEAD_PRECIP_H0 + 24 * offset:03d}"

# variables del NetCDF que consumimos
VAR_TEMP = "T2"            # °C (calibrada)
VAR_HUM = "HR2"           # %  (puede superar 100 -> clamp)
VAR_WIND = "magViento10"  # m/s -> km/h (*3.6)
VAR_PRECIP = "PP"         # mm acumulados

# --- escala de riesgo FWI (5 niveles) ---
NIVELES = ["bajo", "moderado", "alto", "muy alto", "extremo"]
COLORES_CLASE = ["green", "blue", "yellow", "orange", "red"]   # por clase 0..4
# Cortes de la escala por defecto (uniforme por ahora). clase = nº de cortes < FWI.
CORTES_FWI = [5.65, 13.95, 26.56, 42.07]
ESCALAS_CSV = CSV / "escalas_provincias.csv"


def clase_fwi(valor: float, cortes: list[float] | None = None) -> int:
    """Devuelve la clase de riesgo 0..4 para un valor de FWI (cortes opcionales)."""
    c = 0
    for corte in (cortes or CORTES_FWI):
        if valor > corte:
            c += 1
    return c
LIMITES_GEOJSON = JSON / "limites_provincias.geojson"
NOMBRES_GEOJSON = JSON / "nombres_provincias.geojson"
