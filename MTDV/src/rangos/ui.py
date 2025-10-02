import streamlit as st
from .data_utils import cargar_csv, validar_columnas, normalizar_ids # Importa utilidades de datos
from .config import COLUMNAS_RECIENTES_REQUERIDAS, COLUMNAS_FUTURO_REQUERIDAS # Importa configuración y constantes
from .logic import calcular_resultado # Importa lógica central

# Función principal para renderizar la página de Rangos
def render_rangos_page():
    col1, col2 = st.columns(2)
    with col1:
        tabla1_file = st.file_uploader("Carga archivo de datos recientes", type="csv", key="rangos_recent")
    with col2:
        tabla2_file = st.file_uploader("Carga archivo de flujo futuro", type="csv", key="rangos_future")

    n = st.slider("Número de registros recientes por sucursal (N)",
                  min_value=10, max_value=120, value=30, step=5,
                  help="Promedios calculados con los últimos N registros por sucursal.")

    if tabla1_file and tabla2_file:
        tabla1 = cargar_csv(tabla1_file, "datos recientes")
        tabla2 = cargar_csv(tabla2_file, "flujo futuro")

        if tabla1 is not None and tabla2 is not None:   
            tabla1 = normalizar_ids(tabla1)
            tabla2 = normalizar_ids(tabla2)

            if validar_columnas(tabla1, COLUMNAS_RECIENTES_REQUERIDAS, "datos recientes") \
               and validar_columnas(tabla2, COLUMNAS_FUTURO_REQUERIDAS, "flujo futuro"):

                resultado = calcular_resultado(tabla1, tabla2, n=n)

                st.subheader("Resultado por sucursal")
                st.dataframe(resultado, use_container_width=True)

                st.download_button(
                    label="Descargar resultados en CSV",
                    data=resultado.to_csv(index=False).encode("utf-8"),
                    file_name="Transferencias_sucursales.csv",
                    mime="text/csv",
                )
