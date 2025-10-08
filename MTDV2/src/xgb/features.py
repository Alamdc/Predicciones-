import pandas as pd
import numpy as np
from typing import List, Tuple
from datetime import timedelta

try:        
    import holidays as _hol
    _MX_HOL = _hol.country_holidays("MX")
except Exception:
    _MX_HOL = None

def add_calendar(df: pd.DataFrame) -> pd.DataFrame: # Añade señales de calendario a df con columna 'fecha'
    df = df.copy()
    if "dia_semana" not in df.columns:
        df["dia_semana"] = df["fecha"].dt.weekday
    if "semana_año" not in df.columns:
        df["semana_año"] = df["fecha"].dt.isocalendar().week.astype(int)
    if "mes" not in df.columns:
        df["mes"] = df["fecha"].dt.month
    if "año" not in df.columns:
        df["año"] = df["fecha"].dt.year
    if "trimestre" not in df.columns:
        df["trimestre"] = df["fecha"].dt.quarter

    if "festivo_mx" not in df.columns:
        if _MX_HOL is not None:
            df["festivo_mx"] = df["fecha"].dt.date.astype(object).apply(lambda d: 1 if d in _MX_HOL else 0)
        else:
            df["festivo_mx"] = 0
    return df

def _group_rolling(df: pd.DataFrame, group_col: str, target: str, lags: List[int], mas: List[int]) -> pd.DataFrame: # Añade lags y medias móviles por grupo
    df = df.copy()
    for L in sorted(set(lags)):
        df[f"{target}_lag_{L}"] = df.groupby(group_col, observed=False)[target].shift(L)
    for W in sorted(set(mas)):
        df[f"{target}_ma_{W}"] = (
            df.groupby(group_col, observed=False)[target]
              .transform(lambda s: s.shift(1).rolling(W, min_periods=max(2, W//2)).mean())
        )
    return df

#  ENTRADAS/SALIDAS 
def build_feature_table(    # Crea tabla de entrenamiento para 'entradas' y 'salidas' con lags/MAs por sucursal
    df: pd.DataFrame,
    lags: List[int] = [1,2,3,5],
    mas:  List[int] = [3,5,10,14],
):
    df = add_calendar(df)   # Añade señales de calendario
    df["id_sucursal"] = df["id_sucursal"].astype("category")
    df["nombre_estado"] = df["nombre_estado"].astype("category")

    df = _group_rolling(df, "id_sucursal", "entradas", lags, mas)
    df = _group_rolling(df, "id_sucursal", "salidas",  lags, mas)

    base_feats = [  # arreglo de columnas base
        "id_sucursal","nombre_estado",
        "dia_semana","semana_año","mes","año","trimestre","festivo_mx",
    ]
    for bin_col in ["no_laborales","es_captadora"]:
        if bin_col in df.columns:
            base_feats.append(bin_col)

    lag_feats = [c for c in df.columns if c.startswith("entradas_lag_") or c.startswith("salidas_lag_")]
    ma_feats  = [c for c in df.columns if "_ma_" in c and (c.startswith("entradas") or c.startswith("salidas"))]
    feature_cols = base_feats + lag_feats + ma_feats

    usable = df.dropna(subset=[c for c in feature_cols if ("lag_" in c) or ("_ma_" in c)]).copy()
    return usable, feature_cols

#  FLUJO DIRECTO (para forecast.py)
TARGET = "flujo_efectivo"

# Features por defecto para el modelo de flujo directo
FEATURES = [
    "id_sucursal","nombre_estado",      # categóricas (soportadas por XGBoost con DMatrix)
    "dia_semana","semana_año","mes","año","trimestre","festivo_mx",
    "lag_1","lag_2","lag_3","lag_5",
    "media_movil_3","media_movil_5","media_movil_10","media_movil_14",
]

def build_flujo_feature_table(
    df: pd.DataFrame,
    lags: List[int] = [1,2,3,5],
    mas:  List[int] = [3,5,10,14],
) -> Tuple[pd.DataFrame, List[str]]:

   # Crea tabla de entrenamiento para 'flujo_efectivo' con lags/MAs por sucursal,
    #más señales de calendario. Devuelve (df_features, feature_cols).
    df = add_calendar(df)
    df["id_sucursal"] = df["id_sucursal"].astype("category")
    df["nombre_estado"] = df["nombre_estado"].astype("category")

    # construir lags/MAs del TARGET
    tmp = df.copy()
    for L in sorted(set(lags)):
        tmp[f"lag_{L}"] = tmp.groupby("id_sucursal", observed=False)[TARGET].shift(L)
    for W in sorted(set(mas)):
        tmp[f"media_movil_{W}"] = (
            tmp.groupby("id_sucursal", observed=False)[TARGET]
               .transform(lambda s: s.shift(1).rolling(W, min_periods=max(2, W//2)).mean())
        )

    # columnas base
    base_feats = [
        "id_sucursal","nombre_estado",
        "dia_semana","semana_año","mes","año","trimestre","festivo_mx",
    ]
    for bin_col in ["no_laborales","es_captadora"]:
        if bin_col in tmp.columns:
            base_feats.append(bin_col)

    feat_cols = base_feats + [f"lag_{L}" for L in lags] + [f"media_movil_{W}" for W in mas]

    usable = tmp.dropna(subset=[c for c in feat_cols if ("lag_" in c) or ("media_movil_" in c)]).copy()
    return usable, feat_cols

def build_future_frame_per_branch(      # Crea DataFrame futuro para predicción por sucursal, excluyendo no laborales
    last_row: pd.Series,
    horizon: int,
    non_working_days: tuple[int, ...] = (6,),  # 6=domingo
) -> pd.DataFrame:
    rows = []
    date = pd.to_datetime(last_row["fecha"])
    sid = last_row["id_sucursal"]
    estado = last_row.get("nombre_estado", "")

    i = 0
    while len(rows) < horizon and i < horizon * 14:  # límite de seguridad
        date += timedelta(days=1)
        wkday = int(date.weekday())
        if wkday in non_working_days:
            i += 1
            continue

        rows.append({
            "id_sucursal": sid,
            "nombre_estado": estado,
            "fecha": date,
        })
        i += 1

    future = pd.DataFrame(rows)
    future = add_calendar(future)

    # inicializa columnas de FEATURES que se rellenarán durante el forecast
    for col in ["lag_1","lag_2","lag_3","lag_5",
                "media_movil_3","media_movil_5","media_movil_10","media_movil_14"]:
        future[col] = np.nan

    # marca no_laborales opcional (0 en todos los futuros porque ya filtramos)
    if "no_laborales" in FEATURES and "no_laborales" not in future.columns:
        future["no_laborales"] = 0

    # categorías
    future["id_sucursal"] = future["id_sucursal"].astype("category")
    future["nombre_estado"] = future["nombre_estado"].astype("category")
    return future

def prepare_train_arrays(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Prepara X (DataFrame, útil para DMatrix) e y (numpy array) para entrenar un modelo
    de 'flujo_efectivo' usando FEATURES. Asume que df ya trae lags y MAs construidos
    (usa build_flujo_feature_table).
    """
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas para FEATURES: {missing}")

    X = df[FEATURES].copy()
    y = df[TARGET].to_numpy(dtype=float, copy=True)
    return X, y
