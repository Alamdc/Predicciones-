import os
import streamlit as st
from src.xgb.ui import render_xgb_page 
from src.ui_common import load_css, render_navbar # Importa funciones comunes de UI

st.set_page_config(page_title="XGBoost", layout="wide") # asignamos el título y el layout

load_css() # Carga el modulo CSS

# Navbar 
render_navbar(active="xgb")# Carga el modulo NAVBAR

# Título de la página XGBoost
st.title("XGBoost Pronóstico de Flujo de efectivo")
st.caption("Sube tu CSV histórico. Entrenamos XGBoost y descargas el pronóstico.")


render_xgb_page() # Renderiza SOLO la UI de XGBoost aquí
