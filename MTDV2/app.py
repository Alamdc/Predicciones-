import os
from PIL import Image
import streamlit as st
from src.ui_common import load_css, render_navbar # Importa funciones comunes de UI

st.set_page_config(page_title="Sistema de Traslado de Valores", layout="wide") # asignamos el título y el layout

# CSS
load_css() # Carga el modulo CSS

# NAVBAR 
render_navbar(active="inicio") # Carga el modulo NAVBAR


st.markdown('<div class="titulo-bienvenida">Bienvenido al Sistema de Traslado de Valores</div>', unsafe_allow_html=True)  # Título de bienvenida


# Contenido de bienvenida 
st.markdown(
    """
    ### ¿Qué puedes hacer aquí?
    - Cargar CSV consolidado por sucursal.
    - Entrenar modelos globales o por sucursal.
    - Predecir los próximos días y descargar pronósticos.
    - Asignar rangos por sucursal y calcular fecha/monto de transferencia.
    """
)
