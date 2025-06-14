import re
import time
import polars as pl
import duckdb
import uuid
from datetime import datetime, timezone
from pathlib import Path
from itzamna_pipeline.itzamna_core.utils.config import Paths

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
    2) Parsear fechas según tipo de tabla
    3) Agregar ingestion_id, source_file, ingestion_timestamp, pozo
    4) Escribir Parquet en data/lake/bronze/{table_name}/
    5) Crear tabla externa bronze.{table_name} con union_by_name
    """
    pozo = extract_pozo(csv_path, table_name)

    df = pl.read_csv(csv_path)
    
    # Parseo de fechas según la tabla
    if table_name == "equipos":
        df = df.with_columns([
            # fecha_entrada_operacion
            pl.when(pl.col("fecha_entrada_operacion").str.contains("T"))
            .then(pl.col("fecha_entrada_operacion").str.strptime(
                pl.Datetime(time_unit="us", time_zone="UTC"), "%Y-%m-%dT%H:%M:%S%z", strict=False
            ))
            .otherwise(pl.col("fecha_entrada_operacion").str.strptime(
                pl.Datetime(time_unit="us", time_zone="UTC"), "%Y-%m-%d %H:%M:%S%z", strict=False
            )).alias("fecha_entrada_operacion"),

            # fecha_salida_operacion
            pl.when(pl.col("fecha_salida_operacion").str.contains("T"))
            .then(pl.col("fecha_salida_operacion").str.strptime(
                pl.Datetime(time_unit="us", time_zone="UTC"), "%Y-%m-%dT%H:%M:%S%z", strict=False
            ))
            .otherwise(pl.col("fecha_salida_operacion").str.strptime(
                pl.Datetime(time_unit="us", time_zone="UTC"), "%Y-%m-%d %H:%M:%S%z", strict=False
            )).alias("fecha_salida_operacion")
        ])

    elif table_name == "eventos":
        df = df.rename({
            "fecha_paro": "fecha_inicio",
            "fecha_reinicio": "fecha_fin"
        }).with_columns([
            pl.when(pl.col("fecha_inicio").str.contains("T"))
            .then(pl.col("fecha_inicio").str.strptime(
                pl.Datetime(time_unit="us", time_zone="UTC"), "%Y-%m-%dT%H:%M:%S%z", strict=False))
            .otherwise(pl.col("fecha_inicio").str.strptime(
                pl.Datetime(time_unit="us", time_zone="UTC"), "%Y-%m-%d %H:%M:%S%z", strict=False))
            .alias("fecha_inicio"),

            pl.when(pl.col("fecha_fin").str.contains("T"))
            .then(pl.col("fecha_fin").str.strptime(
                pl.Datetime(time_unit="us", time_zone="UTC"), "%Y-%m-%dT%H:%M:%S%z", strict=False))
            .otherwise(pl.col("fecha_fin").str.strptime(
                pl.Datetime(time_unit="us", time_zone="UTC"), "%Y-%m-%d %H:%M:%S%z", strict=False))
            .alias("fecha_fin")
        ])
        
    elif table_name == "sensor_data":
        # Parsear la columna timestamp
        df = df.with_columns([
            pl.col("timestamp").str.strptime(
                pl.Datetime(time_unit="us", time_zone="UTC"),
                "%Y-%m-%d %H:%M:%S%z",
                strict=False
            )
        ])

        # Detectar y convertir columnas numéricas (excepto 'timestamp')
        columnas_num = [
            col for col in df.columns
            if col != "timestamp" and df[col].dtype == pl.Utf8
        ]
        df = df.with_columns([
            pl.col(col).cast(pl.Float64) for col in columnas_num
        ])

    # Agregar columnas comunes
    df = df.with_columns([
        pl.lit(pozo).alias("pozo"),
        pl.lit(str(uuid.uuid4())).alias("id_ingestion"),
        pl.lit(csv_path.name).alias("source_file"),
        pl.lit(datetime.now(timezone.utc)).alias("ingestion_timestamp")
    ])

    # Guardar Parquet
    out_dir = Paths.BRONZE_DIR / table_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{csv_path.stem}.parquet"
    df.write_parquet(out_file, compression="zstd")
    
    time.sleep(0.2)
    
    with duckdb.connect(str(Paths.LAKE_FILE)) as con:
        name = csv_path.name
        exists = con.execute(
            "SELECT 1 FROM bronze.ingested_files WHERE file_name = ?",
            [name]
        ).fetchone()
        if exists:
            return

        con.execute(f"""
        CREATE OR REPLACE TABLE bronze.{table_name} AS
        SELECT *
        FROM read_parquet('{out_dir}/*.parquet', union_by_name=true);
        """)

        con.execute(
        "INSERT INTO bronze.ingested_files VALUES (?, ?)",
        [name, datetime.now(timezone.utc)]
        )