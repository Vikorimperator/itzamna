import pandas as pd
from sqlalchemy import create_engine
from src.utils.config import Paths
import logging

engine = create_engine(Paths.BRONZE_DB_URL)


def load_lecturas_silver(df_lecturas: pd.DataFrame):
    """
    Carga el DataFrame de lecturas interpoladas a la tabla lecturas_silver.
    Asume que las columnas ya están alineadas con el esquema de la tabla.
    """
    try:
        df_lecturas.to_sql(
            'lecturas_silver',
            con=engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=500
        )
        logging.info(f"Lecturas cargadas a lecturas_silver: {len(df_lecturas)} registros")
    except Exception as e:
        logging.exception("Error al cargar lecturas_silver")
        raise


def load_sensor_catalog(df_catalogo: pd.DataFrame):
    """
    Carga el catálogo de sensores detectados por equipo a sensor_coverage_silver.
    """
    try:
        df_catalogo.to_sql(
            'sensor_coverage_silver',
            con=engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=500
        )
        logging.info(f"Catálogo de sensores cargado: {len(df_catalogo)} registros")
    except Exception as e:
        logging.exception("Error al cargar sensor_coverage_silver")
        raise
