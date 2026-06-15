"""API FastAPI de FWI Argentina.

- /indices/*  : cálculo de índices del CFFWIS (respaldado por xclim)
- /fwi/*      : datos del mapa (GeoJSON del día) e historial por punto
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from api.routers import indices, manage, map as map_router

app = FastAPI(
    title="FWI Argentina API",
    version="3.0.1",
    description="Índices del Fire Weather Index (CFFWIS) y datos del mapa de peligro.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# El GeoJSON de 4 km pesa ~50 MB; gzip lo baja a ~10 MB en la transferencia.
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.include_router(indices.router)
app.include_router(map_router.router)
app.include_router(manage.router)


@app.on_event("startup")
def _init_db():
    # crea el esquema y reconcilia la cobertura con lo que ya exista en disco
    try:
        from pipeline import db
        db.init()
    except Exception as e:  # noqa: BLE001 — la API no debe morir si la DB tarda
        print(f"[api] aviso: no se pudo inicializar la DB al arranque: {e}")


@app.get("/salud", tags=["Operación"], summary="Estado de la API")
def salud():
    return {"estado": "ok", "version": app.version}
