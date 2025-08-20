# ---- Librarías ----------

import os
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ---- Funciones -> 1. Limpieza de Datos ---------

# [] --- Carga de los archivos .txt con la información

def cargar_txts_en_dataframe(carpeta):
    """
    Carga todos los archivos .txt de una carpeta en un único DataFrame,
    usando '|' como separador, sin encabezados, y asignando nombres de columna personalizados.

    Parámetros:
    - carpeta (str): Ruta a la carpeta que contiene los archivos .txt

    Retorna:
    - df_completo (pd.DataFrame): DataFrame con los datos combinados
    """
    columnas = [
        'estado', 'oficina', 'nombre', 'year_month', 'dia', 'saldo_inicial', 'saldo_final', 'limite_existencia', 'remesas_entrada', 'remesas_salida',
        'p_sociales', 'corresponsalia_entrada', 'corresponsalia_salida', 'trans_int_entrada',
        'trans_int_salida', 'giro_nac_expedicion', 'giro_nac_pago', 'terceros_entrada', 'terceros_salida',
        'grandes_usuarios', 'telegramas', 'suma ingresos', 'suma egresos', 'archivo_origen'
    ]

    archivos_txt = [f for f in os.listdir(carpeta) if f.endswith('.txt')]

    dataframes = []
    for archivo in archivos_txt:
        ruta_archivo = os.path.join(carpeta, archivo)
        df = pd.read_csv(ruta_archivo, sep='|', header=None, encoding='utf-8')

        if df.shape[1] != len(columnas):
            raise ValueError(f"El archivo {archivo} tiene {df.shape[1]} columnas, pero se esperaban {len(columnas)}.")

        df.columns = columnas
        df['archivo_origen'] = archivo  # Opcional, para rastrear el archivo original
        dataframes.append(df)

    df_completo = pd.concat(dataframes, ignore_index=True)
    return df_completo

# [] --- Transformación del DataFrame para la creación de id_sucursal y fecha

def transformar_dataframe(df):
    """
    Transforma el DataFrame de la siguiente manera:
    1. Reemplaza 'estado' y 'oficina' por una sola columna 'id_sucursal', con ceros a la izquierda.
    2. Reemplaza 'year_month' y 'dia' por una sola columna 'fecha' en formato datetime.
    3. Elimina las columnas innecesarias.
    
    Parámetros:
    - df (pd.DataFrame): DataFrame original
    
    Retorna:
    - df_mod (pd.DataFrame): DataFrame modificado
    """
    df_mod = df.copy()

    # 1. Crear columna 'id_sucursal' y eliminar 'estado' y 'oficina'
    df_mod['id_sucursal'] = df_mod['estado'].astype(str).str.zfill(2) + df_mod['oficina'].astype(str).str.zfill(3)
    df_mod.drop(columns=['estado', 'oficina'], inplace=True)

    # 2. Crear columna 'fecha' y eliminar 'year_month' y 'dia'
    df_mod['fecha'] = pd.to_datetime(
        df_mod['year_month'].astype(str) + '-' + df_mod['dia'].astype(str).str.zfill(2),
        format='%Y-%m-%d',
        errors='coerce'
    )
    df_mod.drop(columns=['year_month', 'dia'], inplace=True)

    # 3. Eliminar columnas innecesarias
    columnas_a_eliminar = ['limite_existencia', 'p_sociales', 'telegramas', 'suma ingresos', 'suma egresos', 'archivo_origen', 'nombre']
    df_mod.drop(columns=[col for col in columnas_a_eliminar if col in df_mod.columns], inplace=True)

    return df_mod

# ---- Funciones -> 2. Análisis Estadístico ---------

# [] --- Filtra la base de datos con los datos de un estado únicamente

def filtrar_estado(df_mod, estado):
    """
    Filtra la base de datos por un estado específico y retorna todas las columnas.

    Parámetros:
    df_mod (DataFrame): Base de datos con características temporales.
    estado (str): Nombre del estado a filtrar.

    Retorna:
    DataFrame filtrado con todas las columnas.
    """
    df_filtrado = df_mod[
        df_mod['nombre_estado'] == estado
    ].copy()
    
    return df_filtrado

# [] --- Muestra los id's de las sucucursales de la base de datos filtrada por el estado específico.

def obtener_ids_sucursales(df):
    """
    Extrae y muestra todos los id_sucursal únicos de un DataFrame.
    """
    ids_sucursales = {str(id_suc) for id_suc in df["id_sucursal"].dropna()}  # Evita NaN y convierte a str
    return sorted(ids_sucursales)

# [] --- De la base de datos filtrada por estado, filtra los datos de una sucursal en específico por su id

def obtener_datos_sucursal(flujo_caja_sucursales, id_sucursal):
    """
    Filtra la base de datos por un id_sucursal específico.

    Parámetros:
    flujo_caja_sucursales (DataFrame): Base de datos que contiene una columna 'id_sucursal'.
    id_sucursal (str o int): ID de la sucursal que se desea filtrar.

    Retorna:
    DataFrame con los datos de la sucursal seleccionada.
    """
    flujo_caja_sucursales = flujo_caja_sucursales.copy()
    flujo_caja_sucursales['id_sucursal'] = flujo_caja_sucursales['id_sucursal'].astype(str)

    id_sucursal = str(id_sucursal)
    df_filtrado = flujo_caja_sucursales[flujo_caja_sucursales['id_sucursal'] == id_sucursal]

    if df_filtrado.empty:
        print(f"No se encontraron datos para la sucursal con ID {id_sucursal}")
        return None

    return df_filtrado

# [] --- Con la base de datos del estado y el id de una sucursal, grafica el comportamiento del flujo de efectivo de la sucursal seleccionada

def graficar_sucursal(flujo_caja_sucursales, id_sucursal):
    """
    Filtra la base de datos por un id_sucursal específico y grafica sus valores de flujo_efectivo.

    Parámetros:
    flujo_caja_sucursales (DataFrame): Base de datos con columna 'fecha'.
    id_sucursal (str): ID de la sucursal a filtrar.

    Retorna:
    Muestra una gráfica de total_flujo a lo largo del tiempo.
    """
    flujo_caja_sucursales = flujo_caja_sucursales.copy()
    flujo_caja_sucursales['id_sucursal'] = flujo_caja_sucursales['id_sucursal'].astype(str)

    # Asegurar que 'Fecha' esté en formato datetime
    flujo_caja_sucursales['fecha'] = pd.to_datetime(flujo_caja_sucursales['fecha'])

    # Filtrar por sucursal
    df_sucursal = flujo_caja_sucursales[
        flujo_caja_sucursales['id_sucursal'] == str(id_sucursal)
    ]

    if df_sucursal.empty:
        print(f"No se encontraron datos para la sucursal con ID {id_sucursal}")
        return

    # Ordenar por fecha por si acaso
    df_sucursal = df_sucursal.sort_values('fecha')

    # Graficar
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df_sucursal['fecha'], df_sucursal['flujo_efectivo'], marker='o', linestyle='-')

    ax.set_xlabel('fecha')
    ax.set_ylabel('Flujo de Efectivo')
    ax.set_title(f'Total Flujo de la Sucursal {id_sucursal}')
    ax.grid(True)

    # Formatear eje X
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.show()