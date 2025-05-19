from dagster import job
from itzamna_pipeline.ops_ingestion import (
    ingest_sensor_data,
    ingest_equipos_data,
    ingest_eventos_data
)

@job
def ingest_all_bronze_op_based():
    ingest_sensor_data()
    ingest_equipos_data()
    ingest_eventos_data()