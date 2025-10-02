#Modulo para manejar conexiones y consultas a la base de datos Postgres
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd
import streamlit as st

load_dotenv()  # Carga variables del archivo .env

def get_engine():   # Crea y devuelve un motor de SQLAlchemy para conectarse a la base de datos Postgres
    try:
        conn_str = (
            f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASS']}"
            f"@{os.environ['DB_HOST']}:{os.environ.get('DB_PORT','5432')}/{os.environ['DB_NAME']}"
        )
        return create_engine(conn_str)
    except KeyError as e:
        st.error(f"Variable de entorno faltante: {e}")
        return None


def run_query(query: str, params: dict = None) -> pd.DataFrame:
   # Ejecuta una consulta SQL y devuelve un DataFrame de Pandas.
    engine = get_engine()
    if engine is None:
        return pd.DataFrame()
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Error ejecutando la consulta: {e}")
        return pd.DataFrame()
