from __future__ import annotations
import numpy as np
import pandas as pd
from collections import deque
from typing import Iterable
import xgboost as xgb

from .features import FEATURES, TARGET, build_future_frame_per_branch

def _best_pred_booster(bst: xgb.Booster, d: xgb.DMatrix) -> float:
    """Predice usando la mejor iteración si existe."""
    try:
        bi = bst.best_iteration
        if bi is not None:
            return float(bst.predict(d, iteration_range=(0, bi + 1))[0])
    except Exception:
        pass
    return float(bst.predict(d)[0])

def _predict_any(model, X_row_df: pd.DataFrame) -> float:
    if isinstance(model, xgb.Booster):
        dX = xgb.DMatrix(X_row_df, enable_categorical=True)
        return _best_pred_booster(model, dX)
    # sklearn-like
    return float(model.predict(X_row_df.values)[0])

def _rolling_update(deq: deque, new_val: float, window: int) -> float:
    """Actualiza media móvil con ventana fija usando deque."""
    deq.append(new_val)
    if len(deq) > window:
        deq.popleft()
    return float(np.mean(deq)) if len(deq) == window else float("nan")

def forecast_7d(model,
                hist_df: pd.DataFrame,
                horizon: int = 7,
                non_working_days: Iterable[int] = (6,),  # 6=domingo
                residual_std: float | None = None) -> pd.DataFrame:
    results = []

    for sid, g in hist_df.groupby("id_sucursal", sort=False, observed=False):
        g = g.sort_values("fecha")
        last = g.iloc[-1].copy()

        # Inicializar buffers con historia reciente de TARGET
        last_vals = list(g[TARGET].tail(5).values)
        lag_buf = deque(last_vals, maxlen=5)

        mm3  = deque(g[TARGET].tail(3).values,  maxlen=3)
        mm5  = deque(g[TARGET].tail(5).values,  maxlen=5)
        mm10 = deque(g[TARGET].tail(10).values, maxlen=10)
        mm14 = deque(g[TARGET].tail(14).values, maxlen=14)

        # Arma frame futuro (solo días laborales según non_working_days)
        future = build_future_frame_per_branch(last, horizon, non_working_days)

        preds = []
        for i in range(len(future)):  # ya viene con longitud == horizon
            # Lags desde buffer (lag_1 = último valor)
            l1 = lag_buf[-1] if len(lag_buf) >= 1 else np.nan
            l2 = lag_buf[-2] if len(lag_buf) >= 2 else np.nan
            l3 = lag_buf[-3] if len(lag_buf) >= 3 else np.nan
            l5 = lag_buf[-5] if len(lag_buf) >= 5 else np.nan

            future.at[i, "lag_1"] = l1
            future.at[i, "lag_2"] = l2
            future.at[i, "lag_3"] = l3
            future.at[i, "lag_5"] = l5

            # Medias móviles con buffers actuales
            future.at[i, "media_movil_3"]  = float(np.mean(mm3))  if len(mm3)==3  else np.nan
            future.at[i, "media_movil_5"]  = float(np.mean(mm5))  if len(mm5)==5  else np.nan
            future.at[i, "media_movil_10"] = float(np.mean(mm10)) if len(mm10)==10 else np.nan
            future.at[i, "media_movil_14"] = float(np.mean(mm14)) if len(mm14)==14 else np.nan

            # Arma fila de features y predice
            X_row_df = future.loc[[i], FEATURES].copy().fillna(0.0)
            yhat = _predict_any(model, X_row_df)
            preds.append(yhat)

            # Actualiza buffers con la nueva predicción
            lag_buf.append(yhat)
            _ = _rolling_update(mm3,  yhat, 3)
            _ = _rolling_update(mm5,  yhat, 5)
            _ = _rolling_update(mm10, yhat, 10)
            _ = _rolling_update(mm14, yhat, 14)

        out = future.copy()
        out[f"pred_{TARGET}"] = preds
        out["nombre_estado"] = g["nombre_estado"].iloc[-1] if "nombre_estado" in g.columns else ""

        # Intervalos simples si se proporcionó desviación residual global
        if residual_std is not None and residual_std > 0:
            out["pi80_lo"] = out[f"pred_{TARGET}"] - 1.28 * residual_std
            out["pi80_hi"] = out[f"pred_{TARGET}"] + 1.28 * residual_std
            out["pi95_lo"] = out[f"pred_{TARGET}"] - 1.96 * residual_std
            out["pi95_hi"] = out[f"pred_{TARGET}"] + 1.96 * residual_std

        results.append(out)

    pred_df = pd.concat(results, axis=0).sort_values(["id_sucursal","fecha"]).reset_index(drop=True)
    return pred_df
