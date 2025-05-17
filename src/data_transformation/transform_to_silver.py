import polars as pl
import duckdb
import datetime
from pathlib import Path
from src.utils.config import Paths

def read_bronze_tables(con):
    """Carga las tablas de la capa Bronce desde DuckDB y las devuelve como DataFrames de Polars."""
    sensores = con.execute("SELECT * FROM bronze.sensor_data").pl()
    equipos = con.execute("SELECT* FROM bronze.equipos").pl()
    eventos = con.execute("SELECT * FROM bronze.eventos").pl()
    return sensores, equipos, eventos

def prepare_equipos(df_equipos):
    """
    Calcula la columna estado_equipo en función de la fecha de salida y la fecha actual (UTC).
    Asume que las fechas ya vienen correctamente parseadas como datetime desde Bronce.
    """
    df_equipos = df_equipos.with_columns([
        pl.when(
            pl.col("fecha_salida_operacion").is_null() |
            (pl.col("fecha_salida_operacion") > pl.lit(datetime.datetime.now(datetime.timezone.utc)))
        )
        .then(pl.lit("activo"))
        .otherwise(pl.lit("inactivo"))
        .alias("estado_equipo")
    ])
    return df_equipos

def filtrar_sensores_validos(df_sensores, df_equipos):
    """Une sensores con equipo y filtra aquellos que se encuentren dentro del periodo activo de operación."""
    df_sensores = df_sensores.with_columns([
        pl.col("timestamp").str.strptime(
            pl.Datetime(time_unit="us", time_zone="UTC"),
            "%Y-%m-%dT%H:%M:%S%.fZ",
            strict=False
            )
    ])
    merged = df_sensores.join(df_equipos, on="pozo", how="left")
    filtrado = merged.filter(
        (pl.col("timestamp") >= pl.col("fecha_entrada_operacion")) &
        (
            pl.col("fecha_salida_operacion").is_null() |
            (pl.col("timestamp") <= pl.col("fecha_salida_operacion"))
        )
    )
    return filtrado

def interpolar_por_equipo(df_filtrado):
    """Agrupa por pozo y equipo, realiza el resampleo cada 10 minutos e interporalcion lineal."""
    columnas_metadata = {"pozo", "numero_equipo", "timestamp", "source_file", "id_ingestion", "ingestion_timestamp"}
    columnas_sensores = [col for col in df_filtrado.columns if col not in columnas_metadata and df_filtrado[col].dtype in [pl.Float64, pl.Int64]]

    lecturas = []

    for (pozo, equipo), grupo in df_filtrado.group_by(["pozo", "numero_equipo"], maintain_order=True):
        g = grupo.sort("timestamp").select(["timestamp"] + columnas_sensores)
        if g.height < 2:
            continue
        g = g.set_sorted("timestamp")

        g_interp = g.upsample(time_column="timestamp", every="10m").interpolate()
        g_interp = g_interp.with_columns([
            pl.lit(pozo).alias("pozo"),
            pl.lit(equipo).alias("numero_equipo")
        ])
        lecturas.append(g_interp)

    return pl.concat(lecturas) if lecturas else pl.DataFrame()

def generar_catalogo(df_lecturas):
    """Genera un catálogo de sensores disponibles por pozo y equipo a partir de las lecturas interpoladas."""
    if df_lecturas.is_empty():
        return pl.DataFrame()

    columnas_excluidas = {"timestamp", "pozo", "numero_equipo"}
    sensores_cols = [col for col in df_lecturas.columns if col not in columnas_excluidas]
    catalogo = []
    for row in df_lecturas.select(["pozo", "numero_equipo"]).unique().iter_rows():
        for sensor in sensores_cols:
            catalogo.append({"pozo": row[0], "numero_equipo": row[1], "sensor": sensor})
    return pl.DataFrame(catalogo)

def preparar_eventos(df_eventos):
    """
    Renombra las columnas de eventos para el esquema Silver.
    Asume que las fechas ya vienen como datetime[μs, UTC] desde Bronce.
    """
    df_eventos = df_eventos.rename({
        "categoria_principal": "tipo_evento",
        "categoria_secundaria": "descripcion"
    })

    columnas_deseadas = [
        "pozo", "tipo_evento", "descripcion", "fecha_inicio", "fecha_fin", "comentario"
    ]
    columnas_finales = [col for col in columnas_deseadas if col in df_eventos.columns]

    return df_eventos.select(columnas_finales)
    
def enriquecer_eventos_con_equipo(df_eventos, df_equipos):
    """
    Une los eventos con los equipos por pozo,
    y asigna el numero_equipo si el evento ocurre dentro del rango de operación del equipo.
    """
    df = df_eventos.join(df_equipos, on="pozo", how="left")

    df = df.filter(
        (pl.col("fecha_inicio") >= pl.col("fecha_entrada_operacion")) &
        (
            pl.col("fecha_fin").is_null() |
            (pl.col("fecha_fin") <= pl.col("fecha_salida_operacion"))
        )
    )

    return df.select([
        "pozo", "numero_equipo", "tipo_evento", "descripcion", "fecha_inicio", "fecha_fin", "comentario"
    ])

def generar_tabla_pozos(df_equipos: pl.DataFrame) -> pl.DataFrame:
    """
    Genera una tabla por pozo con resumen operativo:
    fecha de entrada, última salida, estado actual, etc.
    """
    return (
        df_equipos
        .group_by("pozo")
        .agg([
            pl.col("fecha_entrada_operacion").min().alias("fecha_entrada"),
            pl.col("fecha_salida_operacion").max().alias("ultima_salida"),
            pl.col("numero_equipo").n_unique().alias("cantidad_equipos"),
            pl.col("estado_equipo").max().alias("estado_actual")
        ])
    )

def guardar_silver_parquet(dict_dfs):
    """Guarda cada DataFrame en formato Parquet dentro de su carpeta Silver correspondiente."""
    for name, df in dict_dfs.items():
        dir_path = Paths.SILVER_DIR / name
        dir_path.mkdir(parents=True, exist_ok=True)
        df.write_parquet(dir_path / f"{name}.parquet")

def registrar_tablas_silver(con):
    """Registra en DuckDB las tablas externas Silver leyendo los archivos Parquet."""
    for name in ["lecturas_silver", "sensor_coverage_silver", "equipos_silver", "eventos_silver"]:
        con.execute(f"""
            CREATE OR REPLACE TABLE silver.{name} AS
            SELECT * FROM read_parquet('{Paths.SILVER_DIR / name}/*.parquet');
        """)

def transform_bronze_to_silver():
    """Pipeline principal que transforma los datos desde Bronce a Silver utilizando Polars."""
    con = duckdb.connect(str(Paths.LAKE_FILE))

    sensores, equipos, eventos = read_bronze_tables(con)
    equipos = prepare_equipos(equipos)
    sensores_filtrados = filtrar_sensores_validos(sensores, equipos)
    lecturas = interpolar_por_equipo(sensores_filtrados)
    catalogo = generar_catalogo(lecturas)
    eventos_proc_raw = preparar_eventos(eventos)
    eventos_proc = enriquecer_eventos_con_equipo(eventos_proc_raw, equipos)
    pozos_silver = generar_tabla_pozos(equipos)

    guardar_silver_parquet({
        "lecturas_silver": lecturas,
        "sensor_coverage_silver": catalogo,
        "equipos_silver": equipos.select([
            "pozo", "numero_equipo", "modelo_bomba", "marca_bomba",
            "modelo_motor", "fecha_entrada_operacion", "fecha_salida_operacion", "estado_equipo"
        ]),
        "eventos_silver": eventos_proc,
        "pozos_silver": pozos_silver
    })

    registrar_tablas_silver(con)
    con.close()
