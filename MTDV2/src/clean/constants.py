# Columnas a eliminar totalmente del dataset limpio
COLUMNS_TO_DROP = [
    "sumingresos", "sumegresos", "importe_meta", "sedesol",
]

# Renombrados (tu indicación “cambiarás extent, extsal” la interpreto como renombrar)
RENAME_MAP = {
    "extent": "ext_dep",
    "extsal": "ext_ret"
}

# Columnas que trataremos como INGRESOS y EGRESOS para construir flujo_efectivo
INCOME_COLS = [
    "deposito", "corresponsaliadep", "internain",
    "gne", "gnp", "terceros", "granusuario", "tele",
    # Si quieres considerar "ext_dep" como ingreso, agrega "ext_dep" aquí.
]

EXPENSE_COLS = [
    "retiro", "corresponsaliaret", "internaleg", "terceropago",
    # Si quieres considerar "ext_ret" como egreso, agrega "ext_ret" aquí.
]

# Lags y ventanas de medias móviles para flujo_efectivo
DEFAULT_LAGS = [1, 2, 3, 5]
DEFAULT_MAS  = [3, 5, 10, 14]
