"""Gestión de datos desde la web: planificar/encolar descargas y ver jobs.

La cobertura debe quedar **contigua** (el CFFWIS encadena día a día; un hueco rompe
el cálculo). Por eso, al pedir un rango, se calcula qué días faltan para que la
cobertura siga siendo un intervalo continuo, y se muestra antes de descargar.
"""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pipeline import db
from shared import config as cfg

router = APIRouter(prefix="/fwi", tags=["Gestión"])

MB_POR_DIA = 72   # estimación de descarga por día (2 archivos NetCDF del SMN)
CORTE_MAX = 200.0   # cota razonable para un corte de FWI


class RangoReq(BaseModel):
    desde: date
    hasta: date


def _faltantes(desde: date, hasta: date) -> list[date]:
    """Días a descargar para cubrir [desde, hasta] manteniendo la cobertura contigua."""
    hoy = date.today()
    hasta = min(hasta, hoy)                 # no se puede observar el futuro
    if desde > hasta:
        return []
    min_c, max_c = db.rango_cobertura()
    if min_c is None:
        ini, fin = desde, hasta
    else:
        ini, fin = min(desde, min_c), min(max(hasta, max_c), hoy)
    cubierto = set(db.cobertura())
    dias, d = [], ini
    while d <= fin:
        if d not in cubierto:
            dias.append(d)
        d += timedelta(days=1)
    return dias


@router.post("/coverage/plan", summary="Previsualiza qué se descargaría (sin encolar)")
def plan(req: RangoReq):
    faltan = _faltantes(req.desde, req.hasta)
    if not faltan:
        return {"dias": 0, "mensaje": "Ese rango ya está cubierto."}
    return {"dias": len(faltan), "desde": faltan[0].isoformat(), "hasta": faltan[-1].isoformat(),
            "mb_aprox": len(faltan) * MB_POR_DIA}


@router.post("/coverage/extend", summary="Encola la descarga de un rango (contiguo)")
def extend(req: RangoReq):
    faltan = _faltantes(req.desde, req.hasta)
    if not faltan:
        raise HTTPException(422, "Ese rango ya está cubierto.")
    job_id = db.encolar(faltan[0], faltan[-1])
    # el total real son los días que faltan (los ya cubiertos en el medio se saltean)
    with db.connect() as c:
        c.execute("UPDATE jobs SET total=%s WHERE id=%s", (len(faltan), job_id))
    return {"job_id": job_id, "desde": faltan[0].isoformat(), "hasta": faltan[-1].isoformat(),
            "dias": len(faltan)}


# --- escala de riesgo configurable ---

class EscalaReq(BaseModel):
    cortes: list[float]


def _validar(cortes: list[float]) -> None:
    if len(cortes) != 4:
        raise HTTPException(422, "Se requieren exactamente 4 cortes (5 niveles).")
    if any(x < 0 or x > CORTE_MAX for x in cortes):
        raise HTTPException(422, f"Cada corte debe estar entre 0 y {CORTE_MAX:.0f}.")
    if not all(cortes[i] < cortes[i + 1] for i in range(3)):
        raise HTTPException(422, "Los cortes deben ser estrictamente crecientes.")


def _reband():
    """Encola la regeneración de las bandas para toda la cobertura (sin descargar)."""
    min_c, max_c = db.rango_cobertura()
    return db.encolar(min_c, max_c) if min_c else None


@router.get("/escala", summary="Cortes de FWI activos, por defecto y si fue modificada")
def escala():
    return {"cortes": db.get_cortes(), "default": list(cfg.CORTES_FWI),
            "modificado": db.cortes_modificados(),
            "niveles": cfg.NIVELES, "colores": cfg.COLORES_CLASE}


@router.put("/escala", summary="Guarda cortes nuevos (valida y regenera el mapa)")
def set_escala(req: EscalaReq):
    _validar(req.cortes)
    db.set_cortes([round(float(x), 2) for x in req.cortes])
    return {"ok": True, "job_id": _reband()}


@router.post("/escala/reset", summary="Vuelve a los cortes por defecto")
def reset_escala():
    db.reset_cortes()
    return {"ok": True, "job_id": _reband()}


@router.get("/jobs", summary="Últimos jobs de descarga")
def jobs():
    return db.listar_jobs()


@router.get("/jobs/{job_id}", summary="Estado/progreso de un job")
def job(job_id: int):
    j = db.obtener_job(job_id)
    if not j:
        raise HTTPException(404, "Job no encontrado.")
    return j
