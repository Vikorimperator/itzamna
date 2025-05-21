from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class Paths:
    # Directorio de raw data
    RAW_DATA        = Path(os.getenv("RAW_DATA_PATH"))
    # Archivo de catálogo de DuckDB
    LAKE_FILE       = Path(os.getenv("LAKE_PATH"))
    # Directorio de datos de parquet de bronce
    BRONZE_DIR      = Path(os.getenv("BRONZE_DIR_PATH"))
    # Directorio de datos de parquet de silver
    SILVER_DIR      = Path(os.getenv("SILVER_DIR_PATH"))