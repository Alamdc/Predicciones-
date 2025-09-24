import os
import streamlit as st
from src.xgb.ui import render_xgb_page  # importa tu UI ya hecha

st.set_page_config(page_title="XGBoost — Sistema de Traslado de Valores", layout="wide")

# Navbar también aquí para que sea consistente entre páginas
col1, col2, _ = st.columns([1,1,6])
with col1:
    st.page_link("app.py", label="Inicio", icon="🏠")
with col2:
    st.page_link("pages/1_XGBoost.py", label="XGBoost", icon="⚙️")

st.markdown("<hr class='nav-divider'/>", unsafe_allow_html=True)

# Título de la página XGBoost
st.title("XGBoost — Pronóstico de Entradas/Salidas/Flujo")
st.caption("Sube tu CSV histórico. Entrenamos XGBoost y descargas el pronóstico.")

# Renderiza SOLO la UI de XGBoost aquí (no hay texto de bienvenida)
render_xgb_page()
