from dagster import  In, op, Nothing
import polars as pl
import duckdb
from itzamna_pipeline.itzamna_core.utils.config import Paths
from itzamna_pipeline.itzamna_core.data_transformation.transform_to_silver import (
    read_bronze_tables,
    prepare_equipos,
    filtrar_sensores_validos,
    interpolar_por_equipo,
    generar_catalogo,
    preparar_eventos,
    enriquecer_eventos_con_equipo,
    generar_tabla_pozos,
    guardar_silver_parquet,
    registrar_tablas_silver
)

@op
def load_bronze_data():
    """Carga las tablas de sensores, equipos y eventos desde DuckDB (capa Bronce)."""
    con = duckdb.connect(str(Paths.LAKE_FILE))
    sensores, equipos, eventos = read_bronze_tables(con)
    con.close()
    return {
        "sensores": sensores,
        "equipos": equipos,
        "eventos": eventos
    }

@op
def prepare_equipos_silver(data):
    """Asigna estado 'activo' o 'inactivo' a cada equipo según su fecha de salida."""
    return prepare_equipos(data["equipos"])

@op
def filter_valid_sensors(data, equipos):
    """Filtra las lecturas de sensores para conservar solo aquellas dentro del período operativo del equipo."""
    return filtrar_sensores_validos(data["sensores"], equipos)

@op
def interpolate_sensors(df_filtrado):
    """Interpola lecturas de sensores cada 10 minutos para cada combinación pozo-equipo."""
    return interpolar_por_equipo(df_filtrado)

@op
def generate_sensor_catalog(df_lecturas):
    """Genera un catálogo de sensores disponibles por pozo y número de equipo."""
    return generar_catalogo(df_lecturas)

@op
def prepare_eventos_silver(data):
    """Estandariza columnas de eventos para el esquema Silver."""
    return preparar_eventos(data["eventos"])

@op
def enrich_eventos_with_equipo(eventos, equipos):
    """Asocia cada evento con el número de equipo correspondiente, basado en fechas de operación."""
    return enriquecer_eventos_con_equipo(eventos, equipos)

@op
def generate_pozos_summary(equipos):
    """Genera un resumen por pozo, incluyendo cantidad de equipos y estado del equipo más reciente."""
    return generar_tabla_pozos(equipos)

@op
def save_all_silver_outputs(lecturas, catalogo, equipos, eventos, pozos) -> Nothing:
    """Guarda las tablas procesadas en formato Parquet en la carpeta Silver del Lakehouse."""
    guardar_silver_parquet({
        "lecturas_silver": lecturas,
        "sensor_coverage_silver": catalogo,
        "equipos_silver": equipos.select([
            "pozo", "numero_equipo", "modelo_bomba", "marca_bomba",
            "modelo_motor", "fecha_entrada_operacion", "fecha_salida_operacion", "estado_equipo"
        ]),
        "eventos_silver": eventos,
        "pozos_silver": pozos
    })

@op(ins={"start": In(Nothing)})
def register_silver_tables() -> Nothing:
    """Registra las tablas Silver como vistas externas sobre archivos Parquet dentro de DuckDB."""
    con = duckdb.connect(str(Paths.LAKE_FILE))
    registrar_tablas_silver(con)
    con.close()
