"""Cálculo de los índices del CFFWIS (FFMC, DMC, DC, ISI, BUI, FWI).

Adaptador sobre `xclim.indices.fire`, que implementa las ecuaciones oficiales de
Van Wagner validadas contra el paquete `cffdrs` de R. Sustituye los calculators
artesanales del proyecto viejo (5 de 6 fórmulas tenían errores; ver auditoría F2).

`xclim.indices.fire.cffwis_indices` recibe series temporales (time x punto) y se
encarga del **encadenamiento temporal** (el DC/DMC acumulan día a día — el bug
principal del código viejo, que recalculaba desde cero cada día), de las **bandas
de latitud / hemisferio** (Argentina usa la tabla del Hemisferio Sur) y,
opcionalmente, del *overwintering* del DC.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

INDICES = ["FFMC", "DMC", "DC", "ISI", "BUI", "FWI"]


def _da(values, dims, coords, units):
    da = xr.DataArray(values, dims=dims, coords=coords)
    da.attrs["units"] = units
    return da


def calcular_indices_serie(history: pd.DataFrame, *, overwintering: bool = False,
                           season_method: str | None = None) -> pd.DataFrame:
    """Calcula los 6 índices para un histórico largo (una fila por punto y fecha).

    history debe traer: PUNTO, Fecha, lat, Temperatura, Humedad, Viento, Precipitacion.
    Devuelve el mismo DataFrame con las columnas FFMC, DMC, DC, ISI, BUI, FWI.
    """
    from xclim.indices import fire

    h = history.sort_values(["Fecha", "PUNTO"]).copy()
    fechas = np.sort(h["Fecha"].unique())
    puntos = h["PUNTO"].drop_duplicates().to_numpy()

    # pivotear long -> (time, punto)
    def pivot(col):
        return (h.pivot(index="Fecha", columns="PUNTO", values=col)
                 .reindex(index=fechas, columns=puntos).to_numpy())

    coords = {"time": pd.to_datetime(fechas), "point": puntos}
    dims = ("time", "point")
    tas = _da(pivot("Temperatura"), dims, coords, "degC")
    pr = _da(pivot("Precipitacion"), dims, coords, "mm/d")
    sfcWind = _da(pivot("Viento"), dims, coords, "km/h")
    hurs = _da(pivot("Humedad"), dims, coords, "%")
    lat = _da(h.drop_duplicates("PUNTO").set_index("PUNTO").loc[puntos, "lat"].to_numpy(),
              ("point",), {"point": puntos}, "degrees_north")

    dc, dmc, ffmc, isi, bui, fwi = fire.cffwis_indices(
        tas=tas, pr=pr, sfcWind=sfcWind, hurs=hurs, lat=lat,
        overwintering=overwintering, season_method=season_method,
    )

    out = xr.Dataset({"FFMC": ffmc, "DMC": dmc, "DC": dc,
                      "ISI": isi, "BUI": bui, "FWI": fwi})
    long = (out.to_dataframe().reset_index()
            .rename(columns={"time": "Fecha", "point": "PUNTO"}))
    long["Fecha"] = pd.to_datetime(long["Fecha"])
    return h.merge(long[["Fecha", "PUNTO", *INDICES]], on=["Fecha", "PUNTO"], how="left")


# --- wrappers escalares para la API (un cálculo puntual, modo simple/complejo) ---

_STARTUP = {"FFMC": 85.0, "DMC": 6.0, "DC": 15.0}


def calcular_indice_puntual(indice: str, datos: dict, *, mes: int = 1, lat: float = -34.0,
                            previo: float | None = None) -> float:
    """Calcula un índice para un único registro (lo usa la API).

    `previo` es el valor del día anterior (modo complejo); si es None se usa el
    valor de arranque estándar (modo simple).
    """
    from xclim.indices.fire import _cffwis as c

    A = lambda v: np.array([float(v)], dtype=float)
    indice = indice.upper()

    if indice == "FFMC":
        prev = _STARTUP["FFMC"] if previo is None else previo
        return float(c._fine_fuel_moisture_code(
            A(datos["temperatura_celsius"]), A(datos.get("precipitacion_mm", 0.0)),
            A(datos.get("velocidad_viento_kmh", 0.0)), A(datos["humedad_relativa"]), prev)[0])
    if indice == "DMC":
        prev = _STARTUP["DMC"] if previo is None else previo
        return float(c._duff_moisture_code(
            A(datos["temperatura_celsius"]), A(datos.get("precipitacion_mm", 0.0)),
            A(datos["humedad_relativa"]), int(mes), float(lat), prev)[0])
    if indice == "DC":
        prev = _STARTUP["DC"] if previo is None else previo
        return float(c._drought_code(
            A(datos["temperatura_celsius"]), A(datos.get("precipitacion_mm", 0.0)),
            np.array([int(mes)], dtype=np.int64), float(lat), prev)[0])
    if indice == "ISI":
        return float(c.initial_spread_index(
            A(datos["velocidad_viento_kmh"]), A(datos["ffmc"]))[0])
    if indice == "BUI":
        return float(c.build_up_index(A(datos["dmc"]), A(datos["dc"]))[0])
    if indice == "FWI":
        isi = c.initial_spread_index(A(datos["velocidad_viento_kmh"]), A(datos["ffmc"]))
        bui = c.build_up_index(A(datos["dmc"]), A(datos["dc"]))
        return float(c.fire_weather_index(isi, bui)[0])
    raise ValueError(f"Índice desconocido: {indice}")
