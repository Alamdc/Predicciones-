import numpy as np
import pandas as pd

REQUIRED_COLS = [           # columnas requeridas en el CSV de entrada
    "fecha","nombre_estado","id_sucursal",
    "entradas","salidas","flujo_efectivo",
]

#función para cargar y limpiar datos
def load_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]

    if "fecha" not in df.columns:       # Verifica columna 'fecha'
        raise ValueError("Falta la columna 'fecha'.")
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    if df["fecha"].isna().any():        # Verifica fechas inválidas
        raise ValueError("Fechas inválidas en el CSV.")

    if "id_sucursal" not in df.columns:  # Verifica columna 'id_sucursal'
        raise ValueError("Falta 'id_sucursal'.")
    df["id_sucursal"] = df["id_sucursal"].astype(str).str.strip()

    if "nombre_estado" not in df.columns:   # Verifica columna 'nombre_estado'
        df["nombre_estado"] = "desconocido"

    for c in ["entradas","salidas","flujo_efectivo"]:   
        if c not in df.columns:
            raise ValueError(f"Falta la columna '{c}'.")
        df[c] = pd.to_numeric(df[c], errors="coerce")

    for c in ["no_laborales","festivo_mx","es_captadora"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    df = df.sort_values(["id_sucursal","fecha"]).reset_index(drop=True) # Ordena por sucursal y fecha
    df = df.drop_duplicates(subset=["id_sucursal","fecha"]) # Elimina duplicados
    return df
