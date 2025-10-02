import streamlit as st
from src.rangos.ui import render_rangos_page
from src.ui_common import load_css, render_navbar # Importa funciones comunes de UI

st.set_page_config(page_title="Rangos — Sistema de Traslado de Valores", layout="wide") # asignamos el título y el layout

load_css() #Carga el modulo CSS
render_navbar(active="rangos") # Carga el modulo NAVBAR

st.title("Asignación de Rangos y Transferencias por Sucursal")
st.caption("Sube tus archivos de datos recientes y flujo futuro. Calcula rango, fecha y monto de transferencia.")


render_rangos_page() # Renderiza SOLO la UI de Rangos aquí


