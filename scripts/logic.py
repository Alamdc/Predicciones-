import pandas as pd
from config import RANGOS

def calcular_ultimo_saldo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Toma el último registro por sucursal para obtener saldo_final y el tipo (captadora/pagadora).
    Nota: Se respeta la lógica original: es_captadora == 1 -> 'pagadora', else -> 'captadora'.
    """
    ultimo = (
        df.sort_values("fecha")
        .groupby("id_sucursal")
        .tail(1)[["id_sucursal", "saldo_final", "es_captadora"]]
        .copy()
    )
    ultimo["tipo"] = ultimo["es_captadora"].apply(
        lambda x: "pagadora" if x == 1 else "captadora"
    )
    ultimo["id_sucursal"] = ultimo["id_sucursal"].astype(str)
    return ultimo


def promedios_ultimos_n(df: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """
    Calcula promedios usando los últimos N registros de cada sucursal.
    """
    df = df.copy()
    # Asegurar tipos correctos
    df["id_sucursal"] = df["id_sucursal"].astype(str)
    df = df.sort_values(["id_sucursal", "fecha"])

    # Tomar últimos n por sucursal
    ultimos = df.groupby("id_sucursal").tail(n)

    prom = (
        ultimos.groupby("id_sucursal")
        .agg({
            "entradas": "mean",
            "salidas": "mean",
            "flujo_efectivo": "mean",
        })
        .reset_index()
    )

    prom.rename(columns={
        "entradas": "entrada_prom",
        "salidas": "salida_prom",
        "flujo_efectivo": "flujo_efectivo_prom",
    }, inplace=True)

    prom["id_sucursal"] = prom["id_sucursal"].astype(str)
    prom["tamaño_flujo"] = prom["entrada_prom"] + prom["salida_prom"]
    prom["indice_actividad"] = (
        (prom["entrada_prom"] + prom["salida_prom"]) / (prom["flujo_efectivo_prom"] + 1e-6)
    )

    return prom


def asignar_rango(row) -> str:
    """
    Asigna rango A–E según tamaño_flujo y ajusta un nivel si indice_actividad > 5.
    Si excede el máximo del rango E, retorna 'E'. Si no entra en ningún rango, 'Fuera de Rango'.
    """
    tipo = row["tipo"]
    tam_flujo = row["tamaño_flujo"]
    indice = row["indice_actividad"]

    rangos_tipo = RANGOS.get(tipo, {})
    asignado = None

    for rango, (min_val, max_val) in rangos_tipo.items():
        if min_val <= tam_flujo <= max_val:
            asignado = rango
            break

    if asignado is None:
        if "E" in rangos_tipo and tam_flujo > rangos_tipo["E"][1]:
            return "E"
        return "Fuera de Rango"

    rango_keys = list(rangos_tipo.keys())
    idx = rango_keys.index(asignado)
    if indice > 5 and idx + 1 < len(rango_keys):
        return rango_keys[idx + 1]
    return asignado


def encontrar_dia_transferencia_y_monto(
    id_sucursal: str,
    tipo: str,
    rango: str,
    saldo_actual: float,
    tabla_futuro: pd.DataFrame
):
    """
    Recorre el flujo futuro por sucursal y calcula el primer día en que el saldo acumulado
    sale del rango; sugiere una transferencia hacia el punto medio.
    Si nunca sale, retorna la última fecha y transferencia 0.
    """
    if tipo not in RANGOS or rango not in RANGOS[tipo]:
        return None, None

    min_val, max_val = RANGOS[tipo][rango]
    punto_medio = (min_val + max_val) / 2

    datos = (
        tabla_futuro[tabla_futuro["id_sucursal"] == id_sucursal]
        .sort_values("fecha")
        .copy()
    )
    if datos.empty:
        return None, None

    saldo = saldo_actual
    for _, fila in datos.iterrows():
        saldo += fila["flujo_efectivo_futuro"]
        if saldo < min_val or saldo > max_val:
            return fila["fecha"].date(), round(punto_medio - saldo, 2)

    return datos["fecha"].max().date(), 0.0


def calcular_resultado(df_recientes: pd.DataFrame, df_futuro: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """
    Pipeline principal: último saldo + promedios de los ÚLTIMOS N REGISTROS + rango + día/importe de transferencia.
    """
    ultimo = calcular_ultimo_saldo(df_recientes)
    prom = promedios_ultimos_n(df_recientes, n=n)
    df = pd.merge(ultimo, prom, on="id_sucursal", how="left")

    df["rango"] = df.apply(asignar_rango, axis=1)
    df["dia_transferencia"], df["transferencia_requerida"] = zip(*df.apply(
        lambda r: encontrar_dia_transferencia_y_monto(
            r["id_sucursal"], r["tipo"], r["rango"], r["saldo_final"], df_futuro
        ),
        axis=1
    ))

    return df[[
        "id_sucursal", "tipo", "saldo_final",
        "entrada_prom", "salida_prom", "tamaño_flujo",
        "flujo_efectivo_prom", "indice_actividad", "rango",
        "transferencia_requerida", "dia_transferencia",
    ]]
