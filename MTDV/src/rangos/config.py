# Configuración global y constantes

RANGOS = {
    "captadora": {
        "A": (10000, 35000),
        "B": (15000, 50000),
        "C": (25000, 80000),
        "D": (40000, 140000),
        "E": (60000, 300000),
    },
    "pagadora": {
        "A": (15000, 40000),
        "B": (30000, 80000),
        "C": (60000, 160000),
        "D": (120000, 300000),
        "E": (240000, 600000),
    },
}

COLUMNAS_RECIENTES_REQUERIDAS = {
    "fecha", "id_sucursal", "saldo_final", "es_captadora",
    "entradas", "salidas", "flujo_efectivo"
}
COLUMNAS_FUTURO_REQUERIDAS = {"fecha", "id_sucursal", "flujo_efectivo"}
