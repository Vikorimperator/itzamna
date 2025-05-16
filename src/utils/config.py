from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class Paths:
    # Root directory of the project
    PROJECT_ROOT = Path(__file__).parents[2].resolve()
    # Directory of the raw data
    RAW_DATA        = PROJECT_ROOT / "data" / "raw"
    # DuckDB catalog file
    LAKE_FILE       = PROJECT_ROOT / "warehouse.duckdb"
    # Directory of parquet bronze data
    BRONZE_DIR      = PROJECT_ROOT / "data" / "lake" / "bronze"
    # Directory of parque silver data
    SILVER_DIR      = PROJECT_ROOT / "data" / "lake" / "silver"