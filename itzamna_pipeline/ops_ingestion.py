from dagster import op, In, Nothing
from itzamna_pipeline.itzamna_core.data_ingestion.ingest_bronze import ingest_csv_to_bronze
from itzamna_pipeline.itzamna_core.utils.config import Paths

@op
def ingest_sensor_data() -> Nothing:
    for csv in Paths.RAW_DATA.glob("AYATSIL-*_all.csv"):
        ingest_csv_to_bronze(csv, table_name="sensor_data")
    return None

@op(ins={"start": In(Nothing)})
def ingest_equipos_data() -> Nothing:
    for csv in Paths.RAW_DATA.glob("BEC_AYATSIL-*_all.csv"):
        ingest_csv_to_bronze(csv, table_name="equipos")
    return None

@op(ins={"start": In(Nothing)})
def ingest_eventos_data() -> Nothing:
    for csv in Paths.RAW_DATA.glob("Eventos_AYATSIL-*_all.csv"):
        ingest_csv_to_bronze(csv, table_name="eventos")
    return None