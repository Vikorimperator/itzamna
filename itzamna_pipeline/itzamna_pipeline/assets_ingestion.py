from dagster import asset, Output, MetadataValue
from itzamna_core.data_ingestion.ingest_bronze import ingest_csv_to_bronze
from pathlib import Path

RAW_DIR  = Path("data/raw")

@asset
def sensor_data_bronce() -> Output[None]:
    count = 0
    for csv in RAW_DIR.glob("AYATSIL-*_all.csv"):
        ingest_csv_to_bronze(csv, table_name="sensor_data")
        count += 1
        
    return Output(
        value=None,
        metadata={
            "archivos_procesados": count,
            "tabla": "bronze.sensor_data"
        }
    )
    
@asset
def equipos_bronce() -> Output[None]:
    count = 0
    for csv in RAW_DIR.glob("BEC_AYATSIL-*_all.csv"):
        ingest_csv_to_bronze(csv, table_name="equipos")
        count += 1
        
    return Output(
        value=None,
        metadata={
            "archivos_procesados": count,
            "tabla": "bronze.equipos"
        }
    )
    
@asset
def eventos_bronce() -> Output[None]:
    count = 0
    for csv in RAW_DIR.glob("Eventos_AYATSIL-*_all.csv"):
        ingest_csv_to_bronze(csv, table_name="eventos")
        count += 1
        
    return Output(
        value=None,
        metadata={
            "archivos_procesados": count,
            "tabla": "bronze.eventos"
        }
    )