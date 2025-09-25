import os
import streamlit as st
from src.xgb.ui import render_xgb_page 
from src.ui_common import load_css, render_navbar

st.set_page_config(page_title="XGBoost — Sistema de Traslado de Valores", layout="wide")

load_css()

# Navbar 
render_navbar(active="xgb")
# Título de la página XGBoost
st.title("XGBoost — Pronóstico de Flujo de efectivo")
st.caption("Sube tu CSV histórico. Entrenamos XGBoost y descargas el pronóstico.")

# Renderiza SOLO la UI de XGBoost aquí 
render_xgb_page()
