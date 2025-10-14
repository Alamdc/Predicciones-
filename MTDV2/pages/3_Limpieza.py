import streamlit as st
import pandas as pd

from src.ui_common import load_css, render_navbar
from src.clean.io import fetch_base_data, write_cleaned_to_db
from src.clean.cleaner import clean_base_data, select_columns_for_output, to_base_filtrada_schema

st.set_page_config(page_title="Limpieza", layout="wide")

load_css()
render_navbar(active="limpieza")

st.title("Limpieza de datos")

# inicializa session_state
if "clean_out_db" not in st.session_state:
    st.session_state["clean_out_db"] = None

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
            st.session_state["clean_out_db"] = None
            st.stop()

        clean = clean_base_data(raw)
        out_preview = select_columns_for_output(clean)

        # Mapea al esquema exacto de la tabla destino
        out_db = to_base_filtrada_schema(clean)
        st.session_state["clean_out_db"] = out_db  # guardar para el upload

    st.success(f"Filas limpias (previa): {len(out_preview):,}")
    st.dataframe(out_preview, use_container_width=True, height=520)

# Botón separado para subir (usa session_state)
if st.session_state.get("clean_out_db") is not None:
    if st.button("Subir a Postgres (tabla: data.base_filtrada)"):
        with st.spinner("Subiendo a Postgres..."):
            ok, err = write_cleaned_to_db(st.session_state["clean_out_db"])
        if ok:
            st.success("Datos subidos correctamente a data.base_filtrada (append).")
        else:
            st.error(f"Error escribiendo en Postgres: {err}")
else:
    st.info("Carga y limpia datos para habilitar el botón de subida.")
