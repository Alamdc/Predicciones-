import streamlit as st

def mostrar_resultados(df):
    st.subheader("Resultado por sucursal")
    st.dataframe(df, use_container_width=True)
    st.download_button(
        label="Descargar resultados en CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="Transferencias_sucursales.csv",
        mime="text/csv",
    )
