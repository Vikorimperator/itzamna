from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class Paths:
    # Root directory of the project
    PROJECT_ROOT = Path(__file__).parents[2]  # Dos niveles hacia arriba
    # Directory of the raw data
    RAW_DATA = PROJECT_ROOT / "data" / "raw"
    # Directory of the processed data
    PROCESSED_DATA = PROJECT_ROOT / "data" / "processed"
    # Directory of  bronze data base
    BRONZE_DB_URL = os.getenv("BRONZE_DB_URL", "postgresql://user:password@localhost:5432/tu_base")