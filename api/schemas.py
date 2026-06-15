from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Modo = Literal["simple", "complejo"]


class DatosMeteo(BaseModel):
    temperatura_celsius: float = Field(..., description="Temperatura del aire en °C")
    humedad_relativa: float = Field(..., ge=0, le=100, description="Humedad relativa en %")
    velocidad_viento_kmh: Optional[float] = Field(0.0, description="Viento en km/h")
    precipitacion_mm: Optional[float] = Field(0.0, description="Precipitación 24h en mm")


class EntradaIndiceMeteo(BaseModel):
    modo: Modo = "simple"
    datos: DatosMeteo
    mes: int = Field(1, ge=1, le=12, description="Mes (afecta DMC/DC por duración del día)")
    lat: float = Field(-34.0, description="Latitud (hemisferio; Argentina < 0)")
    valor_dia_anterior: Optional[float] = Field(
        None, description="Valor del índice del día anterior (requerido en modo complejo)")


class EntradaISI(BaseModel):
    ffmc: float
    velocidad_viento_kmh: float


class EntradaBUI(BaseModel):
    dmc: float
    dc: float


class EntradaFWI(BaseModel):
    ffmc: float
    dmc: float
    dc: float
    velocidad_viento_kmh: float


class RespuestaIndice(BaseModel):
    indice: str
    valor: float
    unidad: str = "adimensional"
