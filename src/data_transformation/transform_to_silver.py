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
    """Convierte las fechas de los equipos y calcula la columna estado_equipo."""
    df_equipos = df_equipos.with_columns([
        pl.col("fecha_entrada_operacion").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False),
        pl.col("fecha_salida_operacion").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False),
    ])
    df_equipos = df_equipos.with_columns([
        pl.when(
            pl.col("fecha_salida_operacion").is_null() | 
            (pl.col("fecha_salida_operacion") > datetime.datetime.now(datetime.timezone.utc))
        ).then("activo").otherwise("inactivo").alias("estado_equipo")
    ])
    return df_equipos

def filtrar_sensores_validos(df_sensores, df_equipos):
    """Une sensores con equipo y filtra aquellos que se encuentren dentro del periodo activo de operación."""
    df_sensores = df_sensores.with_columns([
        pl.col("timestamp").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False),
        pl.col("pozo").cast(pl.Utf8),
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
            pl.lit(equipo).alias("numero_equipo"),
        ])
        lecturas.append(g_interp)
    return pl.concat(lecturas) if lecturas else pl.DataFrame()

def generar_catalogo(df_lecturas):
    """Genera un catálogo de sensores disponibles por pozo y equipo a partir de las lecturas interpoladas."""
    columnas_excluidas = {"timestamp", "pozo", "numero_equipo"}
    sensores_cols = [col for col in df_lecturas.columns if col not in columnas_excluidas]
    catalogo = []
    for row in df_lecturas.select(["pozo", "numero_equipo"]).unique().iter_rows():
        for sensor in sensores_cols:
            catalogo.append({"pozo": row[0], "numero_equipo": row[1], "sensor": sensor})
    return pl.DataFrame(catalogo)

def preparar_eventos(df_eventos):
    """Renombra columnas de eventos para el esquema Silver."""
    return df_eventos.rename({
        "categoria_principal": "tipo_evento",
        "categoria_secundaria": "descripcion",
        "fecha_paro": "fecha_inicio",
        "fecha_reinicio": "fecha_fin"
    }).select([
        "pozo", "numero_equipo", "tipo_evento", "descripcion", "fecha_inicio", "fecha_fin", "comentario"
    ])

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
    eventos_proc = preparar_eventos(eventos)

    guardar_silver_parquet({
        "lecturas_silver": lecturas,
        "sensor_coverage_silver": catalogo,
        "equipos_silver": equipos.select([
            "pozo", "numero_equipo", "modelo_bomba", "marca_bomba",
            "modelo_motor", "fecha_entrada_operacion", "fecha_salida_operacion", "estado_equipo"
        ]),
        "eventos_silver": eventos_proc
    })

    registrar_tablas_silver(con)
    con.close()
