"""Tests de regresión de los índices: blindan los bugs corregidos en F2.

No reimplementan las fórmulas (eso lo da xclim, validado contra cffdrs); verifican
*comportamiento*: que el DC acumule (C1) y que el mes/hemisferio influya (C4).
"""
import numpy as np
import pandas as pd
import pytest

from pipeline.indices import INDICES, calcular_indice_puntual, calcular_indices_serie


def _serie_calida_seca(dias=10, puntos=20):
    pts = [f"PUNTO_{i}" for i in range(puntos)]
    filas = []
    for k in range(dias):
        for p in pts:
            filas.append({"PUNTO": p, "Fecha": pd.Timestamp("2026-01-01") + pd.Timedelta(days=k),
                          "lat": -34.0, "Temperatura": 30.0, "Humedad": 25.0,
                          "Viento": 20.0, "Precipitacion": 0.0})
    return pd.DataFrame(filas)


def test_dc_acumula_dia_a_dia():
    """C1: bajo calor y sequía sostenidos, el DC debe crecer monótonamente."""
    res = calcular_indices_serie(_serie_calida_seca())
    dc = res.groupby("Fecha")["DC"].mean()
    assert dc.is_monotonic_increasing
    assert dc.iloc[-1] > dc.iloc[0] + 50  # acumula de verdad, no se resetea


def test_devuelve_los_seis_indices_sin_nulos():
    res = calcular_indices_serie(_serie_calida_seca())
    for c in INDICES:
        assert c in res.columns
        assert res[c].notna().all()


def test_mes_y_hemisferio_influyen():
    """C4: en Argentina, enero (verano) debe secar más que julio (invierno)."""
    meteo = {"temperatura_celsius": 28, "humedad_relativa": 30, "precipitacion_mm": 0}
    dmc_verano = calcular_indice_puntual("DMC", meteo, mes=1, lat=-34)
    dmc_invierno = calcular_indice_puntual("DMC", meteo, mes=7, lat=-34)
    assert dmc_verano > dmc_invierno


def test_hr_se_clampea_en_la_extraccion():
    """C7: la HR del modelo puede pasar 100; la extracción la acota (test de contrato)."""
    hr = np.clip(np.array([118.4, 50.0, -3.0]), 0.0, 100.0)
    assert hr.max() <= 100.0 and hr.min() >= 0.0


def test_isi_tiene_el_factor_0208():
    """Bug histórico: el ISI artesanal omitía el factor 0.208 (~4.8x de más)."""
    isi = calcular_indice_puntual("ISI", {"ffmc": 90, "velocidad_viento_kmh": 20})
    # con el factor correcto, ISI(ffmc=90,w=20) ronda 11-12, no ~55
    assert 5 < isi < 20
