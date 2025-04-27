import polars as pl
import duckdb
import uuid
from datetime import datetime, timezone
from pathlib import Path
from src.utils.config import Paths

con = duckdb.connect(Paths.LAKE_FILE)

def ingest_csv_to_bronze(csv_path: Path, table_name: str):
    """
    1) Read CSV with Polars
    2) Add ingestion_id, source_file, and ingestion_timestamp
    3) Write Parquet to data/lake/bronze/{table_name}/
    4) Create or replace external table bronze.{table_name}
    """
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
      SELECT * FROM read_parquet('{out_dir}/*.parquet');
    """)