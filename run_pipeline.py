from src.utils.init_db import init_bronze_schema, init_silver_schema
from src.data_ingestion.load_csv import auto_discover_and_ingest
from src.utils.logging_config import setup_logging
from src.data_transformation.transform_to_silver import process_all_bronze_data
from src.data_loading.load_to_silver import load_lecturas_silver, load_sensor_catalog, load_equipos_silver, load_eventos_silver
import logging

setup_logging()

if __name__ == "__main__":
    logging.info("Starting pipeline...")

    try:
        init_bronze_schema()        # Crea tablas bronce si no existen
        init_silver_schema()        # Crea tablas silver si no existen
        logging.info("Schemas initialized.")

        auto_discover_and_ingest()  # Ingresa los CSV automáticamente
        logging.info("Ingestion to bronze completed successfully.")

        # Transformación y carga a Silver
        lecturas_df, catalog_df, equipos_df, eventos_df = process_all_bronze_data()
        load_lecturas_silver(lecturas_df)
        load_sensor_catalog(catalog_df)
        load_equipos_silver(equipos_df)
        load_eventos_silver(eventos_df)
        logging.info("Transformation and loading to silver completed successfully.")

    except Exception as e:
        logging.exception(f"Error in pipeline execution: {e}")