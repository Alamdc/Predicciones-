import streamlit as st
import pandas as pd

from src.ui_common import load_css, render_navbar
from src.clean.io import fetch_base_data, write_cleaned_to_db
from src.clean.cleaner import clean_base_data, select_columns_for_output

st.set_page_config(page_title="Limpieza — Sistema de Traslado de Valores", layout="wide")

load_css()
render_navbar(active="limpieza")

st.title("Limpieza de datos: data.data_base")

with st.form("filtros"):
    col1, col2 = st.columns(2)
    with col1:
        edo_min = st.number_input("edo desde", min_value=0, value=1, step=1)
        edo_max = st.number_input("edo hasta", min_value=0, value=10, step=1)
    with col2:
        adm_min = st.number_input("adm desde", min_value=0, value=1, step=1)
        adm_max = st.number_input("adm hasta", min_value=0, value=10, step=1)

    submitted = st.form_submit_button("Cargar y limpiar")

if submitted:
    with st.spinner("Leyendo de Postgres y limpiando..."):
        raw = fetch_base_data(edo_min, edo_max, adm_min, adm_max)
        if raw.empty:
            st.warning("No se obtuvieron filas con esos filtros.")
            st.stop()

        clean = clean_base_data(raw)
        out = select_columns_for_output(clean)

    st.success(f"Filas limpias: {len(out):,}")
    st.dataframe(out, use_container_width=True, height=520)

    if st.button("Subir a Postgres (tabla: data.base_filtrada)"):
        ok, err = write_cleaned_to_db(out)
        if ok:
            st.success("Datos subidos correctamente a data.base_filtrada (append).")
        else:
            st.error(f"Error escribiendo en Postgres: {err}")
