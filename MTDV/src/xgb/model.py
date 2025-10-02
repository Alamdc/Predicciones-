from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass
from sklearn.metrics import mean_squared_error
import xgboost as xgb


@dataclass # Resultado del entrenamiento de modelos
class TrainResult:
    model_entradas: xgb.Booster
    model_salidas: xgb.Booster
    rmse_entradas: float
    rmse_salidas: float
    features: List[str]


def _time_split(df: pd.DataFrame, valid_days: int = 28) -> Tuple[pd.DataFrame, pd.DataFrame]: # División temporal de validación
    max_date = df["fecha"].max()
    split_day = max_date - pd.Timedelta(days=valid_days)
    train = df[df["fecha"] <= split_day].copy()
    valid = df[df["fecha"] >  split_day].copy()
    return train, valid


def _winsorize_per_branch(df: pd.DataFrame, cols: List[str], low_q=0.005, high_q=0.995) -> pd.DataFrame:    # Winsorización por sucursal
    df = df.copy()
    for col in cols:
        q = df.groupby("id_sucursal", observed=False)[col].quantile([low_q, high_q]).unstack()
        q = q.rename(columns={low_q: "low", high_q: "high"})
        df = df.merge(q, left_on="id_sucursal", right_index=True, how="left", suffixes=("",""))
        df[col] = df[[col,"low","high"]].apply(lambda r: np.clip(r[col], r["low"], r["high"]), axis=1)
        df = df.drop(columns=["low","high"])
    return df


def _to_dmatrix(X: pd.DataFrame, y: pd.Series | None = None) -> xgb.DMatrix:    # Convierte DataFrame a DMatrix de XGBoost
    return xgb.DMatrix(
        data=X,
        label=None if y is None else y.values,
        enable_categorical=True
    )


def _best_pred(bst: xgb.Booster, d: xgb.DMatrix) -> np.ndarray:     # Predicciones con la mejor iteración (si aplica)
    try:
        bi = bst.best_iteration
        if bi is not None:
            return bst.predict(d, iteration_range=(0, bi + 1))
    except Exception:
        pass
    return bst.predict(d)


def _fit_one_booster(           # Entrena un modelo XGBoost para una variable objetivo
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    y_col: str,
    feature_cols: List[str],
    seed: int,
    params_override: dict | None,
    num_boost_round: int,
    es_rounds: int
) -> Tuple[xgb.Booster, float]:
    params = {  # Parámetros por defecto de XGBoost
        "objective": "reg:squarederror",
        "learning_rate": 0.05,
        "max_depth": 6,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_lambda": 2.0,
        "reg_alpha": 0.0,
        "tree_method": "hist",
        "seed": seed,
        "eval_metric": "rmse",
        "enable_categorical": True,
    }
    if params_override:
        params.update(params_override)

    Xtr, ytr = train_df[feature_cols], train_df[y_col]
    Xva, yva = valid_df[feature_cols], valid_df[y_col]

    dtr = _to_dmatrix(Xtr, ytr) 
    dva = _to_dmatrix(Xva, yva)

    bst = xgb.train(    # Entrenamiento del modelo XGBoost
        params=params,
        dtrain=dtr,
        num_boost_round=int(num_boost_round),
        evals=[(dva, "valid")],
        early_stopping_rounds=int(es_rounds),
        verbose_eval=False,
    )

    preds = _best_pred(bst, dva)    # Predicciones en validación
    mse = mean_squared_error(yva, preds) # Error cuadrático medio
    rmse = np.sqrt(mse)
    return bst, rmse    # Retorna el modelo y el RMSE


def train_models(       # Entrena modelos XGBoost para entradas y salidas
    df_feat: pd.DataFrame,
    feature_cols: List[str],
    valid_days: int = 28,
    seed: int = 2025,
    winsorize: bool = True,
    xgb_params_override: dict | None = None,
    num_boost_round: int = 5000,
    early_stopping_rounds: int = 200
) -> TrainResult:   
    work = df_feat.copy()   
    if winsorize:
        work = _winsorize_per_branch(work, ["entradas","salidas"])

    train, valid = _time_split(work, valid_days=valid_days)
    if len(train) == 0 or len(valid) == 0:
        raise ValueError("No hay suficientes datos para la división temporal de validación.")

    m_ent, rmse_ent = _fit_one_booster(
        train, valid, "entradas", feature_cols, seed,
        xgb_params_override, num_boost_round, early_stopping_rounds
    )
    m_sal, rmse_sal = _fit_one_booster(
        train, valid, "salidas", feature_cols, seed,
        xgb_params_override, num_boost_round, early_stopping_rounds
    )

    return TrainResult(
        model_entradas=m_ent,
        model_salidas=m_sal,
        rmse_entradas=rmse_ent,
        rmse_salidas=rmse_sal,
        features=feature_cols,
    )


def _advance_day_features(  # Avanza un día en las features para predicción autoregresiva
    last_rows: pd.DataFrame,
    new_date: pd.Timestamp,
    lags: List[int],
    mas: List[int]
) -> pd.DataFrame:
    df = last_rows.copy()
    df["fecha"] = pd.to_datetime(new_date)
    df["dia_semana"] = df["fecha"].dt.weekday
    df["semana_año"] = df["fecha"].dt.isocalendar().week.astype(int)
    df["mes"] = df["fecha"].dt.month
    df["año"] = df["fecha"].dt.year
    df["trimestre"] = df["fecha"].dt.quarter

    try:
        import holidays as _hol
        mxh = _hol.country_holidays("MX")
        df["festivo_mx"] = df["fecha"].dt.date.astype(object).apply(lambda d: 1 if d in mxh else 0)
    except Exception:
        df["festivo_mx"] = 0

    def shift_lags(prefix: str):    # Actualiza lags y medias móviles
        sorted_lags = sorted(set(lags))
        for i in reversed(sorted_lags):
            if i == 1:
                continue
            df[f"{prefix}_lag_{i}"] = df.get(f"{prefix}_lag_{i-1}", df.get(f"{prefix}_lag_{i}", np.nan))
        for W in sorted(set(mas)):
            vals = []
            for k in range(1, W+1):
                colk = f"{prefix}_lag_{k}"
                if colk in df.columns:
                    vals.append(df[colk])
            if vals:
                arr = sum(vals) / len(vals)
                df[f"{prefix}_ma_{W}"] = arr

    shift_lags("entradas")
    shift_lags("salidas")

    return df   # Retorna el DataFrame con las features actualizadas


def forecast_horizon(   # Genera pronóstico para un horizonte dado usando modelos entrenados
    hist_feat: pd.DataFrame,
    train_result: TrainResult,
    lags: List[int],
    mas: List[int],
    horizon: int = 7,
) -> pd.DataFrame:
    features = train_result.features
    ent_model = train_result.model_entradas
    sal_model = train_result.model_salidas

    last_by_branch = (      # Última fila por sucursal para iniciar predicciones
        hist_feat.sort_values(["id_sucursal","fecha"])
                 .groupby("id_sucursal", observed=False)
                 .tail(1)
                 .copy()
    )

    preds_all = []

    current_state = last_by_branch.copy()
    current_state["entradas_lag_1"] = current_state["entradas"]
    current_state["salidas_lag_1"]  = current_state["salidas"]

    start_date = hist_feat["fecha"].max()

    for h in range(1, horizon+1):   # iteración por cada día del horizonte
        day = start_date + pd.Timedelta(days=h)
        step_df = _advance_day_features(current_state, day, lags, mas)

        X = step_df[features]
        dX = _to_dmatrix(X)

        ent_pred = _best_pred(ent_model, dX)
        sal_pred = _best_pred(sal_model, dX)

        out = step_df[["id_sucursal","nombre_estado","fecha"]].copy()
        out["entradas_pred"] = ent_pred
        out["salidas_pred"]  = sal_pred
        out["flujo_pred"]    = out["entradas_pred"] - out["salidas_pred"]
        preds_all.append(out)

        current_state["entradas_lag_1"] = ent_pred
        current_state["salidas_lag_1"]  = sal_pred
        current_state["entradas"] = ent_pred
        current_state["salidas"]  = sal_pred

    forecast = pd.concat(preds_all, ignore_index=True)
    return forecast
