from dagster import Definitions

from itzamna_pipeline.assets_ingestion import (
    sensor_data_bronce,
    equipos_bronce,
    eventos_bronce
)

from itzamna_pipeline.jobs import ingest_all_bronze

defs = Definitions(
    assets=[
        sensor_data_bronce,
        equipos_bronce,
        eventos_bronce
    ],
    jobs=[ingest_all_bronze]
)