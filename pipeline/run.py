"""Orquestador del pipeline.

  - Observado: descarga el día (offset 0), lo guarda y entra en la cadena del CFFWIS.
  - Pronóstico: del mismo run lee los leads largos (+1, +2 días) y los calcula
    encadenados al final de la serie observada (sin contaminar el histórico).

Uso:
  python -m pipeline.run                      # hoy (observado) + pronóstico +1/+2
  python -m pipeline.run 2026-06-13           # ese día (observado) + pronóstico
  python -m pipeline.run 2026-06-01 2026-06-13   # backfill observado (sin pronóstico)
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta

import pandas as pd

from pipeline import extract, geo, grid, indices, ingest, render, storage
from shared import config as cfg


def _extraer(init: date, offset: int) -> pd.DataFrame:
    ncs = ingest.descargar(init, offset)
    idx = grid.cargar_indice_celdas(str(ncs["instant"]))
    return extract.extraer_dia(idx, ncs["instant"], ncs["precip"])  # Fecha = init + offset


def _ingest_observado(d: date) -> bool:
    if d.strftime("%Y-%m-%d") in storage.fechas_met():
        return False
    try:
        df = _extraer(d, 0)
    except FileNotFoundError:
        print(f"[aviso] {d:%Y-%m-%d}: aún no hay datos en el SMN, se saltea")
        return False
    storage.guardar_met(df)
    print(f"[obs] {d:%Y-%m-%d}: {len(df)} puntos")
    return True


def _salida(dia: pd.DataFrame, kind: str, cortes=None) -> str:
    fstr = pd.Timestamp(dia["Fecha"].iloc[0]).strftime("%Y-%m-%d")
    render.generar_bandas(dia, cfg.bands_path(kind, fstr), cfg.bands_path(kind, fstr, simple=True), cortes=cortes)
    render.guardar_puntos(geo.asignar_provincia(dia), cfg.points_path(kind, fstr))
    return fstr


# función pública para que el worker la use día a día (con progreso/cobertura)
def ingest_observado(d: date) -> bool:
    return _ingest_observado(d)


def regenerar(observados_emitir: list[date], base_pronostico: date | None,
              on_progress=None, cortes=None) -> None:
    """Recalcula los índices sobre toda la serie y (re)genera las salidas pedidas.

    El CFFWIS es acumulativo: se recomputa sobre todos los observados (más el
    pronóstico encadenado al final) para que las fechas emitidas sean correctas.
    `on_progress(hechos, total)` se llama al emitir cada día (fase de procesamiento).
    """
    obs = storage.leer_met()
    if obs.empty:
        print("Sin datos observados. Nada que calcular.")
        return

    fmet = []
    if base_pronostico is not None:
        for off in range(1, cfg.FORECAST_MAX_OFFSET + 1):
            try:
                fmet.append(_extraer(base_pronostico, off))
            except FileNotFoundError:
                print(f"[aviso] pronóstico +{off}d no disponible para el run {base_pronostico:%Y-%m-%d}")
    fdf = pd.concat(fmet, ignore_index=True) if fmet else None
    if fdf is not None:
        fdf = fdf[~fdf["Fecha"].isin(obs["Fecha"].unique())]

    combinado = pd.concat([obs] + ([fdf] if fdf is not None and len(fdf) else []), ignore_index=True)
    print(f"[indices] CFFWIS sobre {combinado['Fecha'].nunique()} días x {obs['PUNTO'].nunique()} puntos ...")
    res = indices.calcular_indices_serie(combinado)

    # armar la lista de salidas a emitir (observadas + pronóstico)
    emit = []
    for d in observados_emitir:
        sub = res[res["Fecha"] == pd.Timestamp(d)]
        if len(sub):
            emit.append((sub, "observed"))
    if fdf is not None and len(fdf):
        for fstr in sorted(pd.to_datetime(fdf["Fecha"]).dt.strftime("%Y-%m-%d").unique()):
            emit.append((res[res["Fecha"] == pd.Timestamp(fstr)], "forecast"))

    total = len(emit)
    for i, (sub, kind) in enumerate(emit, 1):
        f = _salida(sub, kind, cortes=cortes)
        print(f"[{kind}] {f} listo")
        if on_progress:
            on_progress(i, total)

    ingest.limpiar_cache_nc()


def procesar(observados: list[date], base_pronostico: date | None) -> None:
    for d in observados:
        ingest_observado(d)
    regenerar(observados, base_pronostico)


def _main(args: list[str]) -> None:
    if not args:
        hoy = date.today()
        procesar([hoy], base_pronostico=hoy)
    elif len(args) == 1:
        d = datetime.strptime(args[0], "%Y-%m-%d").date()
        procesar([d], base_pronostico=d)
    else:
        desde = datetime.strptime(args[0], "%Y-%m-%d").date()
        hasta = datetime.strptime(args[1], "%Y-%m-%d").date()
        dias, d = [], desde
        while d <= hasta:
            dias.append(d)
            d += timedelta(days=1)
        procesar(dias, base_pronostico=None)   # backfill observado sin pronóstico


if __name__ == "__main__":
    _main(sys.argv[1:])
