from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List
from datetime import datetime

from .constants import (
    COLUMNS_TO_DROP, RENAME_MAP,
    INCOME_COLS, EXPENSE_COLS,
    DEFAULT_LAGS, DEFAULT_MAS
)

def _coerce_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df

def _parse_fecha_dia(df: pd.DataFrame) -> pd.DataFrame:
    """
    La tabla trae 'fecha' como texto 'YYYY-MM' y 'dia' como SMALLINT.
    Construimos 'fecha_dia'=YYYY-MM-<dia>.
    Si no es válido, se coerce a NaT.
    """
    df = df.copy()
    df["fecha"] = df["fecha"].astype(str).str.strip()
    df["dia"] = pd.to_numeric(df["dia"], errors="coerce").astype("Int64")

    def make_date(row):
        f = row["fecha"]
        d = row["dia"]
        try:
            if pd.isna(d): return pd.NaT
            return pd.to_datetime(f"{f}-{int(d):02d}", format="%Y-%m-%d", errors="coerce")
        except Exception:
            return pd.NaT

    df["fecha_dia"] = df.apply(make_date, axis=1)
    return df

def _add_calendar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["dia_semana"] = df["fecha_dia"].dt.weekday
    df["semana_año"] = df["fecha_dia"].dt.isocalendar().week.astype("Int64")
    df["mes"] = df["fecha_dia"].dt.month.astype("Int64")
    df["año"] = df["fecha_dia"].dt.year.astype("Int64")
    df["trimestre"] = df["fecha_dia"].dt.quarter.astype("Int64")
    return df

def _compute_cashflow_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula:
      - ingresos_total (suma INCOME_COLS)
      - egresos_total (suma EXPENSE_COLS)
      - flujo_efectivo = ingresos_total - egresos_total
    """
    df = df.copy()
    df = _coerce_numeric(df, INCOME_COLS + EXPENSE_COLS)

    df["ingresos_total"] = df[INCOME_COLS].sum(axis=1)
    df["egresos_total"]  = df[EXPENSE_COLS].sum(axis=1)
    df["flujo_efectivo"] = df["ingresos_total"] - df["egresos_total"]
    return df

def _add_lags_ma(df: pd.DataFrame,
                 group_cols = ["edo", "adm"],
                 lags: List[int] = None,
                 mas: List[int] = None) -> pd.DataFrame:
    """
    Lags y medias móviles de flujo_efectivo, agrupando por edo/adm.
    """
    if lags is None: lags = DEFAULT_LAGS
    if mas  is None: mas  = DEFAULT_MAS

    df = df.sort_values(group_cols + ["fecha_dia"]).copy()
    g = df.groupby(group_cols, observed=False)

    # Lags
    for L in sorted(set(lags)):
        df[f"flujo_lag_{L}"] = g["flujo_efectivo"].shift(L)

    # Medias móviles 
    for W in sorted(set(mas)):
        df[f"flujo_ma_{W}"] = g["flujo_efectivo"].shift(1).rolling(W, min_periods=max(2, W//2)).mean()

    return df

def clean_base_data(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Pipeline de limpieza:
      1) Renombrar extent→ext_dep, extsal→ext_ret
      2) Eliminar columnas pedidas
      3) Ajustar tipos/fechas, ordenar
      4) Computar ingresos/egresos y flujo_efectivo
      5) Calendar + lags + medias móviles
    """
    df = raw.copy()

    # Renombrados
    for old, new in RENAME_MAP.items():
        if old in df.columns:
            df = df.rename(columns={old: new})

    # Dropear columnas pedidas
    to_drop = [c for c in COLUMNS_TO_DROP if c in df.columns]
    df = df.drop(columns=to_drop, errors="ignore")

    # Tipos base
    for numcol in ["edo","adm"]:
        if numcol in df.columns:
            df[numcol] = pd.to_numeric(df[numcol], errors="coerce").astype("Int64")
    if "sucursal" in df.columns:
        df["sucursal"] = df["sucursal"].astype(str).str.strip()

    # Fecha a día
    df = _parse_fecha_dia(df)

    # Orden por edo y adm (y fecha_dia)
    sort_cols = [c for c in ["edo","adm","fecha_dia"] if c in df.columns]
    df = df.sort_values(sort_cols).reset_index(drop=True)

    # Cálculo de flujo
    df = _compute_cashflow_columns(df)

    # Calendario + features
    df = _add_calendar(df)
    df = _add_lags_ma(df)

    return df


def select_columns_for_output(df: pd.DataFrame) -> pd.DataFrame:
    """
    Selección final de columnas para guardar/mostrar.
    """
    keep = [
        "edo","adm","sucursal","fecha","dia","fecha_dia",
        # totales base:
        "deposito","retiro","corresponsaliadep","corresponsaliaret",
        "internain","internaleg","gne","gnp","terceros","terceropago","granusuario","tele",
        # renombradas:
        "ext_dep","ext_ret",
        # features:
        "ingresos_total","egresos_total","flujo_efectivo",
        "dia_semana","semana_año","mes","año","trimestre",
        "flujo_lag_1","flujo_lag_2","flujo_lag_3","flujo_lag_5",
        "flujo_ma_3","flujo_ma_5","flujo_ma_10","flujo_ma_14",
    ]
    exist = [c for c in keep if c in df.columns]
    return df[exist].copy()
