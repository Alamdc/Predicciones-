import streamlit as st
from auth import login
from data_utils import cargar_csv, validar_columnas, normalizar_ids
from config import COLUMNAS_RECIENTES_REQUERIDAS, COLUMNAS_FUTURO_REQUERIDAS
from logic import calcular_resultado
from ui import mostrar_resultados

st.set_page_config(page_title="Análisis y Transferencias", layout="wide")

if login():
    st.title("Análisis y Transferencias por Sucursal")

    col1, col2 = st.columns(2)
    with col1:
        tabla1_file = st.file_uploader("Carga archivo de **datos recientes**", type="csv")
    with col2:
        tabla2_file = st.file_uploader("Carga archivo de **flujo futuro**", type="csv")

    # NUEVO: selector de N
    n = st.slider("Número de registros recientes por sucursal (N)", min_value=10, max_value=120, value=30, step=5,
                  help="Se calculan promedios usando los últimos N registros de cada sucursal.")

    if tabla1_file and tabla2_file:
        tabla1 = cargar_csv(tabla1_file, "datos recientes")
        tabla2 = cargar_csv(tabla2_file, "flujo futuro")

        if tabla1 is not None and tabla2 is not None:
            tabla1 = normalizar_ids(tabla1)
            tabla2 = normalizar_ids(tabla2)

            if validar_columnas(tabla1, COLUMNAS_RECIENTES_REQUERIDAS, "datos recientes") \
               and validar_columnas(tabla2, COLUMNAS_FUTURO_REQUERIDAS, "flujo futuro"):
                # NUEVO: pasar N a la lógica
                resultado = calcular_resultado(tabla1, tabla2, n=n)
                mostrar_resultados(resultado)
