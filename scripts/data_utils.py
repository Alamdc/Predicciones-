import pandas as pd
import streamlit as st

def cargar_csv(archivo, nombre, parse_cols=("fecha",)):
    try:
        return pd.read_csv(archivo, parse_dates=list(parse_cols))
    except Exception as e:
        st.error(f"No se pudo leer **{nombre}**. Detalle: {e}")
        return None

def validar_columnas(df: pd.DataFrame, requeridas: set, nombre: str) -> bool:
    faltantes = requeridas - set(df.columns)
    if faltantes:
        st.error(f"El archivo **{nombre}** no contiene columnas: {sorted(faltantes)}")
        return False
    return True

def normalizar_ids(df: pd.DataFrame) -> pd.DataFrame:
    if "id_sucursal" not in df.columns and "d_sucursal" in df.columns:
        df = df.rename(columns={"d_sucursal": "id_sucursal"})
    if "id_sucursal" in df.columns:
        df["id_sucursal"] = df["id_sucursal"].astype(str)
    return df
