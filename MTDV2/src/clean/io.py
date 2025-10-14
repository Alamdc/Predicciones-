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
    data.base_filtrada, y luego inserta df_clean (append).
    """
    engine = get_engine()
    if engine is None:
        return False, "No hay engine de base de datos"

    # Validaciones 
    for col in ("edo", "adm"):
        if col not in df_clean.columns:
            return False, f"Falta columna obligatoria en df_clean: {col}"
    if df_clean.empty:
        return False, "DataFrame vacío; no hay qué subir"

    try:
        edo_min, edo_max = int(df_clean["edo"].min()), int(df_clean["edo"].max())
        adm_min, adm_max = int(df_clean["adm"].min()), int(df_clean["adm"].max())

        with engine.begin() as conn:
            # 1) Eliminar registros previos del mismo rango
            conn.execute(
                text("""
                    DELETE FROM data.base_filtrada
                    WHERE edo BETWEEN :edo_min AND :edo_max
                      AND adm BETWEEN :adm_min AND :adm_max
                """),
                {"edo_min": edo_min, "edo_max": edo_max,
                 "adm_min": adm_min, "adm_max": adm_max}
            )

            # 2) Insertar nuevos registros
            df_clean.to_sql(
                name="base_filtrada",
                schema="data",
                con=conn,
                if_exists="append",
                index=False
            )

        return True, None

    except Exception as e:
        return False, str(e)