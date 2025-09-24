import pandas as pd
from typing import List, Dict
from .data import load_and_clean
from .features import build_feature_table
from .model import train_models, forecast_horizon, TrainResult


def _per_branch_training(
    df_feat: pd.DataFrame,
    feature_cols: List[str],
    valid_days: int,
    winsorize: bool,
    seed: int,
    xgb_params_override: dict | None,
    num_boost_round: int,
    early_stopping_rounds: int,
) -> Dict[str, TrainResult]:
    models = {}
    for suc, g in df_feat.groupby("id_sucursal", observed=False):
        if g["fecha"].nunique() < 60:
            continue
        try:
            models[suc] = train_models(
                df_feat=g,
                feature_cols=feature_cols,
                valid_days=valid_days,
                seed=seed,
                winsorize=winsorize,
                xgb_params_override=xgb_params_override,
                num_boost_round=num_boost_round,
                early_stopping_rounds=early_stopping_rounds,
            )
        except Exception:
            continue
    return models


def train_and_forecast(
    df: pd.DataFrame,
    horizon: int = 7,
    per_branch: bool = False,
    valid_days: int = 28,
    lags: List[int] = [1,2,3,5],
    mas:  List[int] = [3,5,10,14],
    winsorize: bool = True,
    seed: int = 2025,
    xgb_params_override: dict | None = None,
    num_boost_round: int = 5000,
    early_stopping_rounds: int = 200,
) -> Dict[str, pd.DataFrame]:
    # 1) Cargar/limpiar
    base = load_and_clean(df)

    # 2) Features (calendario + lags/MAs SOLO con pasado)
    feat, feature_cols = build_feature_table(base, lags=lags, mas=mas)

    # 3) Entrena modelo global
    global_res = train_models(
        df_feat=feat,
        feature_cols=feature_cols,
        valid_days=valid_days,
        seed=seed,
        winsorize=winsorize,
        xgb_params_override=xgb_params_override,
        num_boost_round=num_boost_round,
        early_stopping_rounds=early_stopping_rounds,
    )

    metrics = [{
        "nivel": "global",
        "rmse_entradas": round(global_res.rmse_entradas, 4),
        "rmse_salidas":  round(global_res.rmse_salidas,  4),
        "sucursales_entrenadas": feat["id_sucursal"].nunique(),
        "filas_train_total": len(feat),
    }]

    # 4) (Opcional) entrenar modelos por sucursal
    per_branch_models = {}
    if per_branch:
        per_branch_models = _per_branch_training(
            df_feat=feat,
            feature_cols=feature_cols,
            valid_days=valid_days,
            winsorize=winsorize,
            seed=seed,
            xgb_params_override=xgb_params_override,
            num_boost_round=num_boost_round,
            early_stopping_rounds=early_stopping_rounds,
        )

    # 5) Pronóstico por sucursal (usa modelo por sucursal si existe; si no, global)
    forecasts = []
    for suc, hist in base.groupby("id_sucursal", observed=False):
        f_suc = feat[feat["id_sucursal"] == suc].copy()
        if f_suc.empty:
            continue

        use_model = per_branch_models.get(suc, global_res)
        fc = forecast_horizon(
            hist_feat=f_suc,
            train_result=use_model,
            lags=lags,
            mas=mas,
            horizon=horizon,
        )
        forecasts.append(fc)

        lvl = "por_sucursal" if (use_model is not global_res) else "global"
        metrics.append({
            "nivel": lvl,
            "id_sucursal": suc,
            "rmse_entradas": round(use_model.rmse_entradas, 4),
            "rmse_salidas":  round(use_model.rmse_salidas,  4),
        })

    final_fc = pd.concat(forecasts, ignore_index=True) if forecasts else pd.DataFrame()
    final_fc = final_fc[["fecha","nombre_estado","id_sucursal","entradas_pred","salidas_pred","flujo_pred"]] \
                       .sort_values(["id_sucursal","fecha"])

    return {"forecast": final_fc, "metrics": pd.DataFrame(metrics)}
