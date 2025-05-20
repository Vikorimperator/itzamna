from dagster import job
from itzamna_pipeline.ops_ingestion import (
    ingest_sensor_data,
    ingest_equipos_data,
    ingest_eventos_data
)

@job
def ingest_all_bronze_op_based():
    sensor = ingest_sensor_data()
    equipos = ingest_equipos_data(start=sensor)
    ingest_eventos_data(start=equipos)
    
from itzamna_pipeline.ops_transform_silver import (
    load_bronze_data, prepare_equipos_silver, filter_valid_sensors,
    interpolate_sensors, generate_sensor_catalog, prepare_eventos_silver,
    enrich_eventos_with_equipo, generate_pozos_summary,
    save_all_silver_outputs, register_silver_tables
)

@job
def transform_all_silver_op_based():
    bronze = load_bronze_data()
    equipos = prepare_equipos_silver(bronze)
    sensores_filtrados = filter_valid_sensors(bronze, equipos)
    lecturas = interpolate_sensors(sensores_filtrados)
    catalogo = generate_sensor_catalog(lecturas)
    eventos = prepare_eventos_silver(bronze)
    eventos_enriquecidos = enrich_eventos_with_equipo(eventos, equipos)
    pozos = generate_pozos_summary(equipos)
    save_output  = save_all_silver_outputs(lecturas, catalogo, equipos, eventos_enriquecidos, pozos)
    register_silver_tables(save_output)