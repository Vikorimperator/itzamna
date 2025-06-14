from sqlalchemy import create_engine, text
from itzamna_core.utils.config import Paths
from pathlib import Path
import logging

def init_bronze_schema():
    engine =  create_engine(Paths.BRONZE_DB_URL)
    schema_path = Path(Paths.PROJECT_ROOT) / 'database' / 'schema_bronze.sql'
    
    logging.info("Executing schema_bronze.sql...")
    
    try:
        with engine.begin() as connection:
            with open(schema_path, 'r') as file:
                sql_statements = file.read()
                # Execute the SQL commands to create the schema
                connection.execute(text(sql_statements))
        logging.info("Tables created or verified.")
    except Exception as e:
        logging.exception(f"Error creating tables: {e}")
        raise
    
def init_silver_schema():
    engine = create_engine(Paths.SILVER_DB_URL)
    schema_path = Path(Paths.PROJECT_ROOT) / 'database' / 'schema_silver.sql'

    logging.info("Executing schema_silver.sql...")
    try:
        with engine.begin() as connection:
            with open(schema_path, 'r') as file:
                sql_statements = file.read()
                connection.execute(text(sql_statements))
        logging.info("Silver tables created or verified.")
    except Exception as e:
        logging.exception(f"Error creating silver tables: {e}")
        raise