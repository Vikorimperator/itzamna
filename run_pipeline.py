from src.utils.init_db import init_bronze_schema

if __name__ == "__main__":
    init_bronze_schema()  # 1. Crea las tablas si no existen
    # run_bronze_ingestion()  # 2. Corre ingestión de datos
