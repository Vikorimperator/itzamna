import pandas as pd
from sqlalchemy import create_engine
from src.utils.config import Paths
from datetime import datetime
from collections import defaultdict
import logging

engine = create_engine(Paths.BRONZE_DB_URL)

def load_data_from_bronze():
    """Carga los datos desde las tablas bronce necesarias."""
    sensores = pd.read_sql("SELECT * FROM sensor_data_bronce", con=engine)
    equipos = pd.read_sql("SELECT * FROM equipos_bronce", con=engine)
    eventos = pd.read_sql("SELECT * FROM eventos_bronce", con=engine)
    return sensores, equipos, eventos

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

    # Eliminar columnas completamente vacías desde el inicio
    columnas_sensor = [col for col in columnas_sensor if df_filtrado[col].notna().sum() > 0]

    columnas_vacias = [col for col in df_filtrado.columns if df_filtrado[col].isna().all()]
    if columnas_vacias:
        logging.warning(f"Columnas completamente vacías detectadas en sensor_data_bronce: {columnas_vacias}")

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

    if interpolados:
        df_lecturas = pd.concat(interpolados, ignore_index=True)
    else:
        df_lecturas = pd.DataFrame()

    if catalogo:
        df_catalogo = pd.DataFrame([{'pozo': p, 'numero_equipo': e, 'sensor': s}
                                    for (p, e), sensores in catalogo.items()
                                    for s in sensores])
    else:
        df_catalogo = pd.DataFrame()

    return df_lecturas, df_catalogo

def calculate_equipment_status(fecha_salida):
    """Devuelve 'activo' si el equipo sigue operando, 'inactivo' si ya salió de operación."""
    if pd.isna(fecha_salida) or fecha_salida > pd.Timestamp.now(tz='UTC'):
        return 'activo'
    else:
        return 'inactivo'
    
def assign_equipo_to_eventos(eventos_df, equipos_df):
    """Asigna el numero_equipo a cada evento según fechas de operación."""
    eventos_df = eventos_df.copy()
    eventos_df['numero_equipo'] = None

    for i, evento in eventos_df.iterrows():
        pozo = evento['pozo']
        fecha_paro = evento['fecha_paro']

        posibles_equipos = equipos_df[
            (equipos_df['pozo'] == pozo) &
            (equipos_df['fecha_entrada_operacion'] <= fecha_paro) &
            ((equipos_df['fecha_salida_operacion'].isna()) | (equipos_df['fecha_salida_operacion'] >= fecha_paro))
        ]

        if not posibles_equipos.empty:
            eventos_df.at[i, 'numero_equipo'] = posibles_equipos.iloc[0]['numero_equipo']

    return eventos_df
    
def transform_eventos_to_silver(df_eventos):
    """Transforma los datos de eventos de Bronce hacia Silver."""
    df_eventos = df_eventos.copy()
    df_eventos = df_eventos.rename(columns={
        'fecha_paro': 'fecha_inicio',
        'fecha_reinicio': 'fecha_fin',
        'categoria_principal': 'tipo_evento',
        'categoria_secundaria': 'descripcion'
    })
    return df_eventos[[
        'pozo', 'numero_equipo', 'tipo_evento', 'descripcion',
        'fecha_inicio', 'fecha_fin', 'comentario'
    ]]

def process_all_bronze_data():
    """Proceso principal para transformar datos desde Bronce hacia Silver."""
    sensores, equipos, eventos = load_data_from_bronze()
    
    equipos['fecha_salida_operacion'] = pd.to_datetime(
        equipos['fecha_salida_operacion'], utc=True, errors='coerce'
        )
    equipos['estado_equipo'] = equipos['fecha_salida_operacion'].apply(calculate_equipment_status)
    
    eventos = assign_equipo_to_eventos(eventos, equipos)
    
    df_filtrado = prepare_and_filter_data(sensores, equipos)
    df_lecturas, df_catalogo = extract_valid_signals_by_equipment(df_filtrado)
    df_eventos_silver = transform_eventos_to_silver(eventos)
    
    return df_lecturas, df_catalogo, equipos, df_eventos_silver

