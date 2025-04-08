from sqlalchemy import create_engine, text
from utils.config import Paths
from pathlib import Path
import logging

def init_broze_schema():
    engine =  create_engine(Paths.BRONZE_DB_URL)
    schema_path = Path(Paths.PROJECT_ROOT) / 'database' / 'schema_bronze.sql'
    
    logging.info("🔧 Executing schema_bronze.sql...")
    
    try:
        with engine.begin() as connection:
            with open(schema_path, 'r') as file:
                sql_statements = file.read()
                # Execute the SQL commands to create the schema
                connection.execute(text(sql_statements))
        logging.info("✅ Tables created or verified.")
    except Exception as e:
        logging.exception(f"❌ Error creating tables: {e}")
        raise