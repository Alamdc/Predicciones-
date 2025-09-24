import os
from PIL import Image
import streamlit as st

st.set_page_config(page_title="Sistema de Traslado de Valores", layout="wide")

LOGO_PATH = "src/assets/logo.png"
STYLE_PATH = "src/assets/style.css"

# Cargar CSS
if os.path.exists(STYLE_PATH):
    with open(STYLE_PATH) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Header
try:
    img = Image.open(LOGO_PATH)
    st.markdown('<div class="header-logo">', unsafe_allow_html=True)
    st.image(img, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
except Exception:
    st.info("No se encontró el logo. Verifica assets/logo.png")

st.markdown('<div class="titulo-bienvenida">Bienvenido al Sistema de Traslado de Valores</div>', unsafe_allow_html=True)

# NAVBAR 
col1, col2, _ = st.columns([1,1,6])
with col1:
    st.page_link("app.py", label="Inicio", icon="🏠")
with col2:
    st.page_link("pages/1_XGBoost.py", label="XGBoost", icon="⚙️")

st.markdown("<hr class='nav-divider'/>", unsafe_allow_html=True)

# Contenido de bienvenida (solo en esta página)
st.markdown(
    """
    ### ¿Qué puedes hacer aquí?
    - **Cargar CSV** consolidado por sucursal  
    - **Entrenar modelos** globales o por sucursal  
    - **Predecir** los próximos días  
    - **Descargar** el pronóstico en CSV  
    """
)

