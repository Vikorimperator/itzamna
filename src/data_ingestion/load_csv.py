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

# --- Ingestión por tipo ---
def ingest_sensor_data(csv_path: Path, well_id: str):
    df = pd.read_csv(csv_path)
    df_bronze = pd.DataFrame({
        "id_ingestion": [str(uuid.uuid4()) for _ in range(len(df))],
        "pozo": well_id,
        "ingestion_timestamp": datetime.now(timezone.utc),
        "source_file": csv_path.name,
        "raw_data": df.to_json(orient="records", lines=True).splitlines()
    })
    df_bronze.to_sql(
        "sensor_data_bronce",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500
        )

def ingest_equipos_data(csv_path: Path, well_id: str):
    df = pd.read_csv(csv_path, parse_dates=["fecha_entrada_operacion", "fecha_salida_operacion"])
    df["id_ingestion"] = [str(uuid.uuid4()) for _ in range(len(df))]
    df["pozo"] = well_id
    df["ingestion_timestamp"] = datetime.now(timezone.utc)
    df["source_file"] = csv_path.name
    df.to_sql(
        "equipos_bronce",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500
        )

def ingest_eventos_data(csv_path: Path, well_id: str):
    df = pd.read_csv(csv_path, parse_dates=["fecha_paro", "fecha_reinicio"])
    df["id_ingestion"] = [str(uuid.uuid4()) for _ in range(len(df))]
    df["pozo"] = well_id
    df["ingestion_timestamp"] = datetime.now(timezone.utc)
    df["source_file"] = csv_path.name
    df.to_sql(
        "eventos_bronce",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500
        )

# --- Control de duplicados ---
def is_file_already_ingested(file_name: str) -> bool:
    query = f"SELECT 1 FROM ingested_files WHERE file_name = :file"
    result = pd.read_sql(query, engine, params={"file": file_name})
    return not result.empty

def register_ingested_file(file_name: str):
    pd.DataFrame({
        "file_name": [file_name],
        "ingestion_timestamp": [datetime.utcnow()]
    }).to_sql("ingested_files", con=engine, if_exists="append", index=False)

# --- Lógica principal ---
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
            continue

        file_path = raw_dir / file_name

        if is_file_already_ingested(file_name):
            print(f"⚠️  File already ingested, skipping: {file_name}")
            continue

        # SENSOR
        if match := re.match(REGEX_SENSOR, file_name):
            ingest_sensor_data(file_path, match.group(1))
        # EQUIPOS
        elif match := re.match(REGEX_EQUIPOS, file_name):
            ingest_equipos_data(file_path, match.group(1))
        # EVENTOS
        elif match := re.match(REGEX_EVENTOS, file_name):
            ingest_eventos_data(file_path, match.group(1))
        else:
            print(f"❌ Unknown file pattern, skipping: {file_name}")
            continue

        register_ingested_file(file_name)
        print(f"✅ File ingested and registered: {file_name}")