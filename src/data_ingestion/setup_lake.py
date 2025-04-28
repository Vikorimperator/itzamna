import duckdb
from src.utils.config import Paths

def init_lakehouse():
    # Conecta al archivo; lo crea si no existe
    con = duckdb.connect(Paths.LAKE_FILE)
    
    # Crea los 3 esquemas lógicos
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")
    con.execute("CREATE SCHEMA IF NOT EXISTS silver;")
    con.close()

if __name__ == "__main__":
    init_lakehouse()
    print("→ Warehouse preparado en", Paths.LAKE_FILE)