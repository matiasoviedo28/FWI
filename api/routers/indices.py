"""Endpoints de cálculo de índices (respaldados por xclim / fórmulas validadas)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import (EntradaBUI, EntradaFWI, EntradaIndiceMeteo, EntradaISI,
                         RespuestaIndice)
from pipeline.indices import calcular_indice_puntual

router = APIRouter(prefix="/indices", tags=["Índices"])


@router.post("/{indice}", response_model=RespuestaIndice, summary="FFMC / DMC / DC (con clima)")
def calcular_meteo(indice: str, body: EntradaIndiceMeteo) -> RespuestaIndice:
    indice = indice.upper()
    if indice not in {"FFMC", "DMC", "DC"}:
        raise HTTPException(404, f"Usar este endpoint solo para FFMC/DMC/DC; '{indice}' no.")
    if body.modo == "complejo" and body.valor_dia_anterior is None:
        raise HTTPException(422, "modo 'complejo' requiere 'valor_dia_anterior'.")
    previo = body.valor_dia_anterior if body.modo == "complejo" else None
    valor = calcular_indice_puntual(indice, body.datos.model_dump(),
                                    mes=body.mes, lat=body.lat, previo=previo)
    return RespuestaIndice(indice=indice, valor=round(valor, 4))


@router.post("/ISI/calc", response_model=RespuestaIndice, summary="ISI")
def calcular_isi(body: EntradaISI) -> RespuestaIndice:
    valor = calcular_indice_puntual("ISI", body.model_dump())
    return RespuestaIndice(indice="ISI", valor=round(valor, 4))


@router.post("/BUI/calc", response_model=RespuestaIndice, summary="BUI")
def calcular_bui(body: EntradaBUI) -> RespuestaIndice:
    valor = calcular_indice_puntual("BUI", body.model_dump())
    return RespuestaIndice(indice="BUI", valor=round(valor, 4))


@router.post("/FWI/calc", response_model=RespuestaIndice, summary="FWI")
def calcular_fwi(body: EntradaFWI) -> RespuestaIndice:
    valor = calcular_indice_puntual("FWI", body.model_dump())
    return RespuestaIndice(indice="FWI", valor=round(valor, 4))
