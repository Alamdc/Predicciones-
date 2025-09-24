import pandas as pd
from .config import RANGOS

def calcular_ultimo_saldo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mapeo: es_captadora==0 → 'pagadora'; es_captadora==1 → 'captadora'.
    """
    ultimo = (
        df.sort_values("fecha")
        .groupby("id_sucursal")
        .tail(1)[["id_sucursal", "saldo_final", "es_captadora"]]
        .copy()
    )
    ultimo["id_sucursal"] = ultimo["id_sucursal"].astype(str)
    ultimo["tipo"] = ultimo["es_captadora"].apply(
        lambda x: "pagadora" if x == 0 else "captadora"
    )
    return ultimo

def promedios_ultimos_n(df: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """
    Promedios usando los últimos N registros por sucursal.
    """
    df = df.copy()
    df["id_sucursal"] = df["id_sucursal"].astype(str)
    df = df.sort_values(["id_sucursal", "fecha"])
    ultimos = df.groupby("id_sucursal").tail(n)

    prom = (
        ultimos.groupby("id_sucursal")
        .agg({
            "entradas": "mean",
            "salidas": "mean",
            "flujo_efectivo": "mean",
        })
        .reset_index()
    ).rename(columns={
        "entradas": "entrada_prom",
        "salidas": "salida_prom",
        "flujo_efectivo": "flujo_efectivo_prom",
    })

    prom["id_sucursal"] = prom["id_sucursal"].astype(str)
    prom["tamaño_flujo"] = prom["entrada_prom"] + prom["salida_prom"]
    prom["indice_actividad"] = abs(
        (prom["entrada_prom"] + prom["salida_prom"]) / (prom["flujo_efectivo_prom"] + 1e-6)
    )
    return prom

def asignar_rango(row) -> str:
    tipo = row["tipo"]
    tam_flujo = row["tamaño_flujo"]
    indice = row["indice_actividad"]

    rangos_tipo = RANGOS.get(tipo, {})
    asignado = None
    for rango, (lo, hi) in rangos_tipo.items():
        if lo <= tam_flujo <= hi:
            asignado = rango
            break

    if asignado is None:
        if "E" in rangos_tipo and tam_flujo > rangos_tipo["E"][1]:
            return "E"
        return "Fuera de Rango"

    keys = list(rangos_tipo.keys())
    idx = keys.index(asignado)
    if indice > 5 and idx + 1 < len(keys):
        return keys[idx + 1]
    return asignado

def encontrar_dia_transferencia_y_monto(
    id_sucursal: str,
    tipo: str,
    rango: str,
    saldo_actual: float,
    tabla_futuro: pd.DataFrame
):
    """
    Fecha: primer día que el saldo acumulado sale del rango, recorriendo flujos futuros.
    Monto: punto_medio - (saldo_actual + suma_total_futuro)
    """
    if tipo not in RANGOS or rango not in RANGOS[tipo]:
        return None, None

    min_val, max_val = RANGOS[tipo][rango]
    punto_medio = (min_val + max_val) / 2

    datos = (
        tabla_futuro[tabla_futuro["id_sucursal"].astype(str) == str(id_sucursal)]
        .sort_values("fecha")
        .copy()
    )
    if datos.empty:
        return None, None

    saldo = saldo_actual
    fecha_salida = None
    for _, fila in datos.iterrows():
        saldo += fila["flujo_efectivo"]
        if saldo < min_val or saldo > max_val:
            fecha_salida = fila["fecha"].date()
            break

    if fecha_salida is None:
        return datos["fecha"].max().date(), 0.0

    suma_total_futuro = float(datos["flujo_efectivo"].sum())
    saldo_final_proyectado = saldo_actual + suma_total_futuro
    transferencia = round(punto_medio - saldo_final_proyectado, 2)

    return fecha_salida, transferencia

def _suma_total_futuro_y_nombre(tabla_futuro: pd.DataFrame) -> pd.DataFrame:
    fut = tabla_futuro.copy()
    fut["id_sucursal"] = fut["id_sucursal"].astype(str)
    suma = fut.groupby("id_sucursal")["flujo_efectivo"].sum().reset_index()
    suma = suma.rename(columns={"flujo_efectivo": "suma_total_futuro"})
    fut = fut.sort_values(["id_sucursal", "fecha"])
    last_state = fut.groupby("id_sucursal").tail(1)[["id_sucursal", "nombre_estado"]]
    aux = suma.merge(last_state, on="id_sucursal", how="left")
    return aux

def calcular_resultado(df_recientes: pd.DataFrame, df_futuro: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    ult = calcular_ultimo_saldo(df_recientes)
    prom = promedios_ultimos_n(df_recientes, n=n)

    df = pd.merge(ult, prom, on="id_sucursal", how="left")
    df["rango"] = df.apply(asignar_rango, axis=1)

    df["dia_transferencia"], df["transferencia_requerida"] = zip(*df.apply(
        lambda r: encontrar_dia_transferencia_y_monto(
            r["id_sucursal"], r["tipo"], r["rango"], r["saldo_final"], df_futuro
        ),
        axis=1
    ))

    extras = _suma_total_futuro_y_nombre(df_futuro)
    df = df.merge(extras, on="id_sucursal", how="left")

    cols = [
        "id_sucursal", "nombre_estado", "tipo", "rango",
        "saldo_final", "suma_total_futuro",
        "entrada_prom", "salida_prom", "tamaño_flujo",
        "flujo_efectivo_prom", "indice_actividad",
        "transferencia_requerida", "dia_transferencia",
    ]
    return df[cols]
