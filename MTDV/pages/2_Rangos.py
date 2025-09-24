import streamlit as st
from src.rangos.ui import render_rangos_page

st.set_page_config(page_title="Rangos — Sistema de Traslado de Valores", layout="wide")

# Navbar consistente
col1, col2, col3, _ = st.columns([1,1,1,6])
with col1:
    st.page_link("app.py", label="Inicio")
with col2:
    st.page_link("pages/1_XGBoost.py", label="XGBoost")
with col3:
    st.page_link("pages/2_Rangos.py", label="Rangos")

st.markdown("<hr class='nav-divider'/>", unsafe_allow_html=True)

st.title("Asignación de Rangos y Transferencias por Sucursal")
st.caption("Sube tus archivos de datos recientes y flujo futuro. Calcula rango, fecha y monto de transferencia.")

render_rangos_page()
