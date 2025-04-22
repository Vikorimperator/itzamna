import pandas as pd
from sqlalchemy import create_engine
from src.utils.config import Paths
from datetime import datetime
from collections import defaultdict

engine = create_engine(Paths.BRONZE_DB_URL)

def load_data_from_bronze():
    """Carga los datos desde las tablas bronce necesarias."""
    sensores = pd.read_sql("SELECT * FROM sensor_data_bronce", con=engine)
    equipos = pd.read_sql("SELECT * FROM equipos_bronce", con=engine)
    return sensores, equipos

def prepare_and_filter_data(sensores, equipos):
    """Une sensores con equipos por pozo y filtra por la ventana de operación del equipo."""
    sensores['timestamp'] = pd.to_datetime(sensores['ingestion_timestamp'], utc=True)

    equipos['fecha_entrada_operacion_alineada'] = pd.to_datetime(equipos['fecha_entrada_operacion'], utc=True).dt.floor('10min')
    equipos['fecha_salida_operacion_alineada'] = pd.to_datetime(equipos['fecha_salida_operacion'], utc=True, errors='coerce').dt.ceil('10min')
    equipos['fecha_salida_operacion_alineada'] = equipos['fecha_salida_operacion_alineada'].fillna(datetime.now().astimezone())

    merged = sensores.merge(equipos, on='pozo', how='left')
    filtrado = merged[(merged['timestamp'] >= merged['fecha_entrada_operacion_alineada']) &
                      (merged['timestamp'] <= merged['fecha_salida_operacion_alineada'])]
    return filtrado

def extract_valid_signals_by_equipment(df_filtrado):
    """Detecta columnas últiles y genera lecturas interpoladas + catálogo de sensores."""
    columnas_metadata = ['pozo', 'numero_equipo', 'timestamp']
    columnas_sensor = [col for col in df_filtrado.columns if col not in columnas_metadata and df_filtrado[col].dtype in ["float64", "int64"]]

    catalogo = defaultdict(list)
    interpolados = []

    for (pozo, equipo), grupo in df_filtrado.groupby(['pozo', 'numero_equipo']):
        grupo = grupo.set_index('timestamp').sort_index()
        grupo_resampleado = grupo[columnas_sensor].resample('10min').mean()

        columnas_utiles = [col for col in grupo_resampleado.columns
                           if grupo_resampleado[col].notna().sum() >= 2 and grupo_resampleado[col].nunique(dropna=True) > 1]

        if columnas_utiles:
            grupo_interp = grupo_resampleado[columnas_utiles].interpolate(method='linear')
            grupo_interp['pozo'] = pozo
            grupo_interp['numero_equipo'] = equipo
            grupo_interp = grupo_interp.reset_index()

            for sensor in columnas_utiles:
                catalogo[(pozo, equipo)].append(sensor)

            interpolados.append(grupo_interp)

    df_lecturas = pd.concat(interpolados, ignore_index=True)
    df_catalogo = pd.DataFrame([{'pozo': p, 'numero_equipo': e, 'sensor': s}
                                for (p, e), sensores in catalogo.items()
                                for s in sensores])
    return df_lecturas, df_catalogo

def calculate_equipment_status(fecha_salida):
    """Devuelve 'activo' si el equipo sigue operando, 'inactivo' si ya salió de operación."""
    if pd.isna(fecha_salida) or fecha_salida > pd.Timestamp.now(tz='UTC'):
        return 'activo'
    else:
        return 'inactivo'

def process_all_bronze_data():
    """Proceso principal para transformar datos desde Bronce hacia Silver."""
    sensores, equipos = load_data_from_bronze()
    equipos['estado_equipo'] = equipos['fecha_salida_operacion'].apply(calculate_equipment_status)

    df_filtrado = prepare_and_filter_data(sensores, equipos)
    df_lecturas, df_catalogo = extract_valid_signals_by_equipment(df_filtrado)
    
    return df_lecturas, df_catalogo, equipos