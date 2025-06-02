from src.utils.logging_config import setup_logging
from src.data_ingestion.ingest_bronze import ingest_csv_to_bronze
from src.data_transformation.transform_to_silver import transform_bronze_to_silver
from pathlib import Path
import logging

setup_logging()

if __name__ == "__main__":
    logging.info("=== Ingestión Bronce en DuckDB ===")

    raw = Path("data/raw")
    # Sensores
    for csv in raw.glob("AYATSIL-*_all.csv"):
        ingest_csv_to_bronze(csv, table_name="sensor_data")

    # Equipos
    for csv in raw.glob("BEC_AYATSIL-*_all.csv"):
        ingest_csv_to_bronze(csv, table_name="equipos")

    # Eventos
    for csv in raw.glob("Eventos_AYATSIL-*_all.csv"):
        ingest_csv_to_bronze(csv, table_name="eventos")

    logging.info("=== Ingestión Bronce completada ===")
    
    logging.info("=== Transformación a Silver en DuckDB ===")
    
    # Transformación de datos de bronce a silver
    transform_bronze_to_silver()
    
    logging.info("=== Capa Silver completada ===")