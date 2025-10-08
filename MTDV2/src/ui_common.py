import os
import streamlit as st

# Funciones comunes de UI
def load_css(style_path: str = "src/assets/style.css"): # función para cargar CSS
    if os.path.exists(style_path):
        with open(style_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True) # Carga el CSS en la app

# función para renderizar la barra de navegación
def render_navbar(active: str = "inicio"):
    col1, col2, col3, col4, _ = st.columns([1,1,1,1,6])

    with col1:
        st.page_link("app.py", label="Inicio", disabled=(active=="inicio"))
    with col2:
        st.page_link("pages/1_XGBoost.py", label="XGBoost", disabled=(active=="xgb"))
    with col3:
        st.page_link("pages/2_Rangos.py", label="Rangos", disabled=(active=="rangos"))
    with col4:
        st.page_link("pages/3_Limpieza.py", label="Limpieza", disabled=(active=="limpieza"))

    st.markdown("<hr class='nav-divider'/>", unsafe_allow_html=True)

