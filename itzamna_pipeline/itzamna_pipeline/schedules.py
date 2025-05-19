from dagster import ScheduleDefinition
from itzamna_pipeline.jobs import ingest_all_bronze_op_based

# 🕒 Cron: todos los días a las 6:00 AM
daily_ingestion_schedule = ScheduleDefinition(
    job=ingest_all_bronze_op_based,
    cron_schedule="0 6 * * *",
    execution_timezone="America/Mexico_City", # formato cron: minuto hora día_mes mes día_semana
    name="daily_ingestion_schedule", # ajusta según tu zona horaria
)