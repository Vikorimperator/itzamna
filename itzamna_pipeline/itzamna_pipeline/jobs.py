from dagster import job
from itzamna_pipeline.ops_ingestion import (
    ingest_sensor_data,
    ingest_equipos_data,
    ingest_eventos_data
)

@job
def ingest_all_bronze_op_based():
    sensor = ingest_sensor_data()
    equipos = ingest_equipos_data()
    eventos = ingest_eventos_data()

    # Orden secuencial garantizado por el orden de llamadas
    equipos
    eventos