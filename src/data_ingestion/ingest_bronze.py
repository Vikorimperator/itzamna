import re
import polars as pl
import duckdb
import uuid
from datetime import datetime, timezone
from pathlib import Path
from src.utils.config import Paths

con = duckdb.connect(Paths.LAKE_FILE)

def extract_pozo(csv_path: Path, table_name: str) -> str:
    """
    Extrae el número de pozo desde el nombre del archivo según el tipo de tabla.
    """
    name = csv_path.name
    if table_name == "sensor_data":
        match = re.match(r"^AYATSIL-(\d+)_all\.csv$", name)
    elif table_name == "equipos":
        match = re.match(r"^BEC_AYATSIL-(\d+)_all\.csv$", name)
    elif table_name == "eventos":
        match = re.match(r"^Eventos_AYATSIL-(\d+)_all\.csv$", name)
    else:
        match = None

    if match:
        return match.group(1)
    else:
        raise ValueError(f"No se pudo extraer el número de pozo del archivo: {name}")

def ingest_csv_to_bronze(csv_path: Path, table_name: str):
    """
    1) Leer CSV con Polars
    2) Agregar ingestion_id, source_file, e ingestion_timestamp
    3) Escribir Parquet en data/lake/bronze/{table_name}/
    4) Crear o remplazar la tabla externa bronze.{table_name}
    """
    
    name = csv_path.name
    exists = con.execute(
        "SELECT 1 FROM bronze.ingested_files WHERE file_name = ?",
        [name]
    ).fetchone()
    if exists:
        return  
    
    df = (
        pl.read_csv(csv_path)
          .with_columns([
             pl.lit(str(uuid.uuid4())).alias("id_ingestion"),
             pl.lit(csv_path.name).alias("source_file"),
             pl.lit(datetime.now(timezone.utc)).alias("ingestion_timestamp")
          ])
    )

    out_dir = Paths.BRONZE_DIR / table_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{csv_path.stem}.parquet"
    df.write_parquet(out_file, compression="zstd")

    con.execute(f"""
      CREATE OR REPLACE TABLE bronze.{table_name} AS
      -- union_by_name: true une columnas por nombre y rellena con NULL
      SELECT *
      FROM read_parquet('{out_dir}/*.parquet', union_by_name=true);
    """)
    
    con.execute(
      "INSERT INTO bronze.ingested_files VALUES (?, ?)",
      [name, datetime.now(timezone.utc)]
    )