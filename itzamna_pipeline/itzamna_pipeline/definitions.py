from dagster import Definitions

from itzamna_pipeline.jobs import ingest_all_bronze_op_based

defs = Definitions(
    jobs=[ingest_all_bronze_op_based]
)