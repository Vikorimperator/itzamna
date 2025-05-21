from dagster import ScheduleDefinition
from itzamna_pipeline.jobs import ingest_all_bronze_op_based, transform_all_silver_op_based

# 🟫 Ingesta Bronce diaria a las 6:00 AM
daily_ingestion_schedule = ScheduleDefinition(
    job=ingest_all_bronze_op_based,
    cron_schedule="0 6 * * *", # formato cron: minuto hora día_mes mes día_semana
    execution_timezone="America/Mexico_City", # ajusta según tu zona horaria
    name="daily_ingestion_schedule", 
)

# ⚙️ Transformación Silver diaria a las 6:30 AM
daily_transform_silver_schedule = ScheduleDefinition(
    job=transform_all_silver_op_based,
    cron_schedule="30 6 * * *",  # 6:30 AM todos los días
    execution_timezone="America/Mexico_City",
    name="daily_transform_silver_schedule"
)