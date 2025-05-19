from dagster import job
from itzamna_pipeline.assets_ingestion import (
    sensor_data_bronce,
    equipos_bronce,
    eventos_bronce
)

@job
def ingest_all_bronze():
    sensor_data_bronce()
    equipos_bronce()
    eventos_bronce()