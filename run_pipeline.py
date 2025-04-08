from src.utils.init_db import init_bronze_schema
from src.data_ingestion.load_csv import auto_discover_and_ingest

if __name__ == "__main__":
    init_bronze_schema()             # Crea tablas si no existen
    auto_discover_and_ingest()       # Ingresa los CSV automáticamente
