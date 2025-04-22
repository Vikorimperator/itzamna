
# 📄 Documentación de Scripts - Proyecto Itzamna

Este documento describe la funcionalidad de los scripts clave que componen el pipeline de datos para el proyecto Itzamna.

---

## `run_pipeline.py`

- **Ubicación**: `/run_pipeline.py`
- **Propósito**: Orquestar la ejecución del pipeline para:
  1. Inicializar el esquema de la base de datos bronce.
  2. Ingresar automáticamente los archivos `.csv` detectados.
- **Entradas**: 
  - Archivos `.csv` ubicados en la carpeta `data/raw/`.
  - Script SQL `schema_bronze.sql` para la creación de tablas.
- **Salidas**:
  - Tablas creadas en PostgreSQL bajo el esquema `bronce`.
  - Datos cargados a las tablas correspondientes.
  - Logs registrados en `pipeline.log`.
- **Funciones involucradas**:
  - `init_bronze_schema()` de `src.utils.init_db`: ejecuta `schema_bronze.sql`.
  - `auto_discover_and_ingest()` de `src.data_ingestion.load_csv`: automatiza la carga de archivos.
  - `setup_logging()` de `src.utils.logging_config`: configura el logging.
- **Dependencias**:
  - `logging`, `src.utils`, `src.data_ingestion`
- **Ejecución recomendada**:
  ```bash
  python run_pipeline.py
  ```
- **Notas**:
  - El sistema captura errores y los registra con `logging.exception`.
  - Requiere que el archivo `.env` esté presente y correctamente configurado para la conexión a la base de datos.


---

## `src/utils/config.py`

- **Ubicación**: `src/utils/config.py`
- **Propósito**: Definir rutas del proyecto y proporcionar la URL de conexión a la base de datos de Bronce desde variables de entorno.
- **Clases**:
  - `Paths`: Clase que centraliza las rutas importantes del proyecto.
    - `PROJECT_ROOT`: Directorio raíz del proyecto (2 niveles arriba del archivo actual).
    - `RAW_DATA`: Ruta donde se encuentran los archivos crudos (`/data/raw`).
    - `PROCESSED_DATA`: Ruta prevista para almacenar datos transformados (`/data/processed`).
    - `BRONZE_DB_URL`: Cadena de conexión a la base de datos PostgreSQL, obtenida desde `.env`.
- **Dependencias**:
  - `pathlib`, `os`, `dotenv`
- **Notas**:
  - Este archivo permite mantener centralizadas las rutas y configuraciones clave, facilitando su reutilización en otros módulos.


---

## `src/utils/logging_config.py`

- **Ubicación**: `src/utils/logging_config.py`
- **Propósito**: Configurar el sistema de logging del proyecto para registrar en consola y en archivo.
- **Funciones**:
  - `setup_logging(level=logging.INFO)`: Configura el nivel de logging, el formato y los handlers:
    - Archivo `pipeline.log` en el directorio raíz del proyecto.
    - Salida estándar (consola).
- **Notas**:
  - Es recomendable llamar a esta función al inicio del script principal para asegurar el registro de toda la ejecución.

---

## `src/utils/init_db.py`

- **Ubicación**: `src/utils/init_db.py`
- **Propósito**: Inicializa el esquema de la base de datos Bronce ejecutando el script SQL correspondiente.
- **Funciones**:
  - `init_bronze_schema()`: Ejecuta el archivo `schema_bronze.sql` para crear o verificar tablas en la base de datos PostgreSQL.
- **Entradas**:
  - `schema_bronze.sql` en la ruta `database/`.
- **Dependencias**:
  - `sqlalchemy`, `logging`, `pathlib`
- **Notas**:
  - Usa SQLAlchemy para crear una conexión segura con la base de datos.
  - Registra cualquier error que ocurra al ejecutar el SQL.

---

## `src/data_ingestion/load_csv.py`

- **Ubicación**: `src/data_ingestion/load_csv.py`
- **Propósito**: Automatizar la ingestión de archivos `.csv` crudos a las tablas de Bronce correspondientes según su patrón de nombre.
- **Funciones principales**:
  - `ingest_sensor_data(csv_path, well_id)`
  - `ingest_equipos_data(csv_path, well_id)`
  - `ingest_eventos_data(csv_path, well_id)`
  - `is_file_already_ingested(file_name)`
  - `register_ingested_file(file_name)`
  - `auto_discover_and_ingest()`: función orquestadora que detecta los archivos y llama a la función de ingestión adecuada.
- **Lógica de ingestión**:
  - Detecta tipo de archivo usando expresiones regulares (sensor, equipos, eventos).
  - Genera columnas necesarias (`id_ingestion`, `ingestion_timestamp`, `source_file`, etc.).
  - Inserta los datos en la base de datos con `to_sql` (con chunking y sin índices).
  - Evita duplicados verificando si el archivo ya fue registrado.
- **Dependencias**:
  - `pandas`, `sqlalchemy`, `uuid`, `datetime`, `logging`, `os`, `re`, `pathlib`
- **Notas**:
  - Solo se aceptan archivos con extensión `.csv` y nombres válidos según los patrones definidos.
  - La función `auto_discover_and_ingest()` es llamada desde el script principal.