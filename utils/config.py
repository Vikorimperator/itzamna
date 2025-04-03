from pathlib import Path

# Root directory of the project
ROOT_DIR = Path(__file__).resolve().parent.parent

# Directory of the raw data
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"

# Directory of data bases
BRONZE_DATA_DIR = ROOT_DIR / "data" / "bronze"