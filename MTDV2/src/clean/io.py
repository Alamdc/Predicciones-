import pandas as pd
from sqlalchemy import text
from src.db.db import get_engine

def fetch_base_data(edo_min: int, edo_max: int, adm_min: int, adm_max: int) -> pd.DataFrame:
    """
    Lee desde Postgres data.data_base filtrando por rangos de edo y adm.
    """
    engine = get_engine()
    if engine is None:
        return pd.DataFrame()

    sql = text("""
        SELECT
            edo, adm, sucursal, fecha, dia,
            importe_meta, extent, extsal,
            deposito, retiro,
            sedesol,
            corresponsaliadep, corresponsaliaret,
            internain, internaleg,
            gne, gnp,
            terceros, terceropago,
            granusuario, tele,
            sumingresos, sumegresos
        FROM data.data_base
        WHERE edo BETWEEN :edo_min AND :edo_max
          AND adm BETWEEN :adm_min AND :adm_max
    """)

    with engine.connect() as conn:
        df = pd.read_sql_query(sql, conn, params={
            "edo_min": edo_min, "edo_max": edo_max,
            "adm_min": adm_min, "adm_max": adm_max
        })
    return df


def write_cleaned_to_db(df_clean: pd.DataFrame):
    """
    Escribe el dataframe limpio en Postgres:
      schema = data
      tabla  = base_filtrada
      modo   = append
    """
    engine = get_engine()
    if engine is None:
        return False, "No hay engine de base de datos"

    try:
        df_clean.to_sql(
            name="base_filtrada",
            schema="data",
            con=engine,
            if_exists="append",
            index=False
        )
        return True, None
    except Exception as e:
        return False, str(e)
