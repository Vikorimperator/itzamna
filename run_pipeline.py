from src.utils.init_db import init_bronze_schema
from src.data_ingestion.load_csv import auto_discover_and_ingest
from src.utils.logging_config import setup_logging
import logging

setup_logging()

if __name__ == "__main__":
    logging.info("🚀 Starting pipeline...")
    
    try:
        init_bronze_schema()        # Crea tablas si no existen
        logging.info("✅ Schema initialized.")

        auto_discover_and_ingest()  # Ingresa los CSV automáticamente
        logging.info("✅ Ingestion completed successfully.")

    except Exception as e:
        logging.exception(f"❌ Error in pipeline execution: {e}")