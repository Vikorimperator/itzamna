import re
import os
import pandas as pd
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from pathlib import Path
from src.utils.config import Paths

# Expresiones regulares para detectar archivo y extraer pozo
REGEX_SENSOR = r"^AYATSIL-(\d+)_all\.csv$"
REGEX_EQUIPOS = r"^BEC_AYATSIL-(\d+)_all\.csv$"
REGEX_EVENTOS = r"^Eventos_AYATSIL-(\d+)_all\.csv$"

engine = create_engine(Paths.BRONZE_DB_URL)

def ingest_sensor_data(file: Path, pozo: str):
    df = pd.read_csv(file)
    df_bronce = pd.DataFrame({
        "id_ingestion": [str(uuid.uuid4()) for _ in range(len(df))],
        "pozo": pozo,
        "ingestion_timestamp": datetime.now(timezone.utc),
        "source_file": file.name,
        "raw_data": df.to_json(orient="records", lines=True).splitlines()
    })
    df_bronce.to_sql(
        "sensor_data_bronce",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
        )

def ingest_equipos_data(file: Path, pozo: str):
    df = pd.read_csv(file, parse_dates=["fecha_entrada_operacion", "fecha_salida_operacion"])
    df["id_ingestion"] = [str(uuid.uuid4()) for _ in range(len(df))]
    df["pozo"] = pozo
    df["ingestion_timestamp"] = datetime.now(timezone.utc)
    df["source_file"] = file.name
    df.to_sql(
        "equipos_bronce",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
        )

def ingest_eventos_data(file: Path, pozo: str):
    df = pd.read_csv(file, parse_dates=["fecha_paro", "fecha_reinicio"])
    df["id_ingestion"] = [str(uuid.uuid4()) for _ in range(len(df))]
    df["pozo"] = pozo
    df["ingestion_timestamp"] = datetime.now(timezone.utc)
    df["source_file"] = file.name
    df.to_sql(
        "eventos_bronce",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
        )

# Función  para ingestar todos los archivos CSV en la carpeta 'data/raw'
# y cargarlos a la tabla Bronce adecuada según su patrón de nombre
def auto_discover_and_ingest():
    """
    Detecta automáticamente todos los .csv en 'data/raw' y
    los ingesta a la tabla Bronce adecuada según su patrón de nombre.
    """
    raw_dir = Paths.RAW_DATA
    for file_name in os.listdir(raw_dir):
        if not file_name.endswith(".csv"):
            continue  # ignorar archivos que no son CSV

        csv_path = raw_dir / file_name
        
        # SENSOR
        match_sensor = re.match(REGEX_SENSOR, file_name)
        if match_sensor:
            pozo_id = match_sensor.group(1)  # extrae XXX
            ingest_sensor_data(csv_path, pozo_id)
            continue

        # EQUIPOS
        match_equipos = re.match(REGEX_EQUIPOS, file_name)
        if match_equipos:
            pozo_id = match_equipos.group(1)
            ingest_equipos_data(csv_path, pozo_id)
            continue

        # EVENTOS
        match_eventos = re.match(REGEX_EVENTOS, file_name)
        if match_eventos:
            pozo_id = match_eventos.group(1)
            ingest_eventos_data(csv_path, pozo_id)
            continue

        # Si no coincide con ninguno de los patrones, ignoramos o logueamos
        print(f"Archivo {file_name} no coincide con patrones esperados, se ignora.")