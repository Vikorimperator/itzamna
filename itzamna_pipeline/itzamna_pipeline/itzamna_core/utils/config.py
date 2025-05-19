from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class Paths:
    # Directorio raíz del proyecto
    PROJECT_ROOT = Path(__file__).parents[2].resolve()
    # Directorio de raw data
    RAW_DATA        = PROJECT_ROOT / "data" / "raw"
    # Archivo de catálogo de DuckDB
    LAKE_FILE       = PROJECT_ROOT / "warehouse.duckdb"
    # Directorio de datos de parquet de bronce
    BRONZE_DIR      = PROJECT_ROOT / "data" / "lake" / "bronze"
    # Directorio de datos de parquet de silver
    SILVER_DIR      = PROJECT_ROOT / "data" / "lake" / "silver"