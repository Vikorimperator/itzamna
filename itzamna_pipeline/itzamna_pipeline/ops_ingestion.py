from dagster import op, In, Out, Nothing
from itzamna_pipeline.itzamna_core.data_ingestion.ingest_bronze import ingest_csv_to_bronze
from itzamna_pipeline.itzamna_core.utils.config import Paths

@op(out=Out)
def ingest_sensor_data():
    for csv in Paths.RAW_DATA.glob("AYATSIL-*_all.csv"):
        ingest_csv_to_bronze(csv, table_name="sensor_data")

@op(ins={"_start": In(Nothing)}, out=Out)
def ingest_equipos_data(_start):
    for csv in Paths.RAW_DATA.glob("BEC_AYATSIL-*_all.csv"):
        ingest_csv_to_bronze(csv, table_name="equipos")

@op(ins={"_start": In(Nothing)}, out=Out)
def ingest_eventos_data(_start):
    for csv in Paths.RAW_DATA.glob("Eventos_AYATSIL-*_all.csv"):
        ingest_csv_to_bronze(csv, table_name="eventos")