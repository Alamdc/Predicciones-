import streamlit as st
import pandas as pd
from src.ui_common import load_css, render_navbar
from src.clean.scheduler import (
    schedule_weekly_cleanup, list_jobs, remove_job, run_job_now, run_ad_hoc_once
)

st.set_page_config(page_title="Programación — Sistema de Traslado de Valores", layout="wide")

load_css()
render_navbar(active="programacion")

st.title("Programación de limpiezas")

with st.expander("Programar limpieza semanal", expanded=True):
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        day = st.selectbox("Día de la semana", ["sun","mon","tue","wed","thu","fri","sat"], index=0)
        hour = st.number_input("Hora (24h)", min_value=0, max_value=23, value=3, step=1)
        minute = st.number_input("Minuto", min_value=0, max_value=59, value=0, step=1)
    with col2:
        edo_min = st.number_input("edo desde", min_value=0, value=1, step=1)
        edo_max = st.number_input("edo hasta", min_value=0, value=5, step=1)
        adm_min = st.number_input("adm desde", min_value=0, value=1, step=1)
        adm_max = st.number_input("adm hasta", min_value=0, value=10, step=1)
    with col3:
        job_id_override = st.text_input("Job ID (opcional, para reemplazar)")

    if st.button("Programar/Actualizar limpieza semanal"):
        jid = schedule_weekly_cleanup(
            job_id=job_id_override or None,
            day_of_week=day, hour=int(hour), minute=int(minute),
            edo_min=int(edo_min), edo_max=int(edo_max),
            adm_min=int(adm_min), adm_max=int(adm_max)
        )
        st.success(f"Limpieza programada con job_id: {jid}")

st.subheader("Ejecución ad-hoc (una sola vez)")
col1, col2, col3, col4 = st.columns(4)
with col1:
    a_edo_min = st.number_input("edo desde (ad-hoc)", min_value=0, value=1, step=1, key="a_edo_min")
with col2:
    a_edo_max = st.number_input("edo hasta (ad-hoc)", min_value=0, value=5, step=1, key="a_edo_max")
with col3:
    a_adm_min = st.number_input("adm desde (ad-hoc)", min_value=0, value=1, step=1, key="a_adm_min")
with col4:
    a_adm_max = st.number_input("adm hasta (ad-hoc)", min_value=0, value=10, step=1, key="a_adm_max")

if st.button("Ejecutar limpieza ahora"):
    with st.spinner("Ejecutando limpieza..."):
        result = run_ad_hoc_once(int(a_edo_min), int(a_edo_max), int(a_adm_min), int(a_adm_max))
    st.write(result if result else {"status":"no-op"})

st.subheader("Tareas programadas")
jobs = list_jobs()
if jobs:
    df_jobs = pd.DataFrame(jobs)
    st.dataframe(df_jobs, use_container_width=True)

    colA, colB = st.columns(2)
    with colA:
        job_to_run = st.text_input("job_id para ejecutar ahora")
        if st.button("Ejecutar job ahora"):
            if run_job_now(job_to_run):
                st.success("Job marcado para ejecución inmediata.")
            else:
                st.error("No se pudo ejecutar el job (verifica job_id).")
    with colB:
        job_to_remove = st.text_input("job_id para eliminar")
        if st.button("Eliminar job"):
            if remove_job(job_to_remove):
                st.success("Job eliminado.")
            else:
                st.error("No se pudo eliminar el job (verifica job_id).")
else:
    st.info("No hay tareas programadas aún.")
