from dagster import Definitions
from itzamna_pipeline.jobs import ingest_all_bronze_op_based
from itzamna_pipeline.schedules import daily_ingestion_schedule

defs = Definitions(
    jobs=[ingest_all_bronze_op_based],
    schedules=[daily_ingestion_schedule]
)