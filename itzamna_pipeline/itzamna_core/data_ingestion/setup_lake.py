import duckdb
from itzamna_pipeline.itzamna_core.utils.config import Paths

def init_lakehouse():
    # Conecta al archivo; lo crea si no existe
    con = duckdb.connect(Paths.LAKE_FILE)
    
    # Crea los 2 esquemas lógicos
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")
    con.execute("CREATE SCHEMA IF NOT EXISTS silver;")
    
    # Crea la tabla de archivos ingestados
    con.execute("""CREATE TABLE IF NOT EXISTS bronze.ingested_files (
        file_name TEXT PRIMARY KEY,
        ingestion_timestamp TIMESTAMP
        );"""
        )
    
    con.close()

if __name__ == "__main__":
    init_lakehouse()
    print("→ Warehouse preparado en", Paths.LAKE_FILE)