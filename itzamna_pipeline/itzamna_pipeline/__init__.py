from dagster import Definitions
from .assets_ingestion import sensor_data_bronce, equipos_bronce, eventos_bronce

defs = Definitions(
    assets=[
        sensor_data_bronce,
        equipos_bronce,
        eventos_bronce
    ]
)
