#interfaz de usuario para XGBoost
import io
import pandas as pd
import streamlit as st
from .pipeline import train_and_forecast

# Función principal para renderizar la página de XGBoost
def render_xgb_page():
    uploaded = st.file_uploader("Arrastra tu CSV (histórico consolidado)", type=["csv"])
    horizon = st.number_input("Horizonte (días)", min_value=1, max_value=30, value=7, step=1)
    strategy = st.selectbox(
        "Estrategia de entrenamiento",
        ["Global (un modelo para todas las sucursales)", "Por sucursal (un modelo por cada sucursal)"],
        index=0,
    )
    per_branch = strategy.startswith("Por")
    # Parámetros de features
    with st.expander("Parámetros de features", expanded=False): 
        valid_days = st.number_input("Días para validación temporal", min_value=7, max_value=120, value=28, step=7)
        lags = st.text_input("Lags (coma)", value="1,2,3,5")
        mas = st.text_input("Medias móviles (coma)", value="3,5,10,14")
        winsor = st.checkbox("Winsorizar outliers por sucursal (0.5% - 99.5%)", value=True)
        seed = st.number_input("Seed", min_value=1, max_value=999999, value=2025, step=1)

    with st.expander("Hiperparámetros XGBoost", expanded=False): # Parámetros de XGBoost modificables
        learning_rate = st.number_input("learning_rate (eta)", min_value=0.005, max_value=0.5, value=0.05, step=0.005, format="%.3f")
        max_depth     = st.slider("max_depth", 2, 14, 6, 1)
        subsample     = st.slider("subsample", 0.5, 1.0, 0.8, 0.05)
        colsample_bt  = st.slider("colsample_bytree", 0.5, 1.0, 0.8, 0.05)
        reg_lambda    = st.number_input("reg_lambda (L2)", min_value=0.0, max_value=20.0, value=2.0, step=0.1)
        reg_alpha     = st.number_input("reg_alpha (L1)", min_value=0.0, max_value=20.0, value=0.0, step=0.1)
        tree_method   = st.selectbox("tree_method", ["hist", "approx", "gpu_hist"], index=0)
        n_boost_round = st.number_input("num_boost_round", min_value=100, max_value=20000, value=5000, step=100)
        es_rounds     = st.number_input("early_stopping_rounds", min_value=50, max_value=1000, value=200, step=50)

    if uploaded and st.button("Entrenar y generar pronóstico"):
        with st.spinner("Entrenando modelos y generando pronóstico…"):
            try:
                df = pd.read_csv(uploaded)  # Carga CSV
                # Procesa listas de lags y medias móviles
                lag_list = [int(x) for x in lags.split(",") if x.strip().isdigit()]
                ma_list  = [int(x) for x in mas.split(",") if x.strip().isdigit()]

                result = train_and_forecast(    # Llama a la función principal del pipeline
                    df=df,
                    horizon=horizon,
                    per_branch=per_branch,
                    valid_days=valid_days,
                    lags=lag_list,
                    mas=ma_list,
                    winsorize=winsor,
                    seed=seed,
                    xgb_params_override={       #hiperparámetros de XGBoost modificables
                        "learning_rate": learning_rate,
                        "max_depth": int(max_depth),
                        "subsample": subsample,
                        "colsample_bytree": colsample_bt,
                        "reg_lambda": reg_lambda,
                        "reg_alpha": reg_alpha,
                        "tree_method": tree_method,
                    },
                    num_boost_round=int(n_boost_round),
                    early_stopping_rounds=int(es_rounds),
                )

                st.success("Abajo puedes revisar métricas y descargar el CSV de pronóstico.")

                st.subheader("Métricas de validación (RMSE, última ventana)")
                st.dataframe(result["metrics"], use_container_width=True)

                st.subheader("Pronóstico completo")
                st.dataframe(result["forecast"], use_container_width=True, height=600)

                buf = io.StringIO()
                result["forecast"].to_csv(buf, index=False) # Prepara CSV en memoria
                st.download_button(     #botón de descarga de CSV
                    "Descargar pronóstico CSV",
                    data=buf.getvalue(),
                    file_name="pronostico_7d.csv",
                    mime="text/csv",
                )

            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()
