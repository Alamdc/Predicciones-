import streamlit as st
from config import USUARIOS

def login():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if st.session_state.autenticado:
        return True

    st.title("Inicio de Sesión")
    usuario = st.text_input("Usuario")
    contraseña = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión"):
        if usuario in USUARIOS and USUARIOS[usuario] == contraseña:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()
    return False
