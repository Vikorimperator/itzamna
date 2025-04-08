-- Tabla sensor_data_bronce
CREATE TABLE IF NOT EXISTS sensor_data_bronce (
    id_ingestion TEXT PRIMARY KEY,
    pozo TEXT,
    ingestion_timestamp TIMESTAMP,
    source_file TEXT,
    raw_data JSON
);

-- Tabla equipos_bronce
CREATE TABLE IF NOT EXISTS equipos_bronce (
    id_ingestion TEXT PRIMARY KEY,
    pozo TEXT,
    modelo_bomba TEXT,
    marca_bomba TEXT,
    modelo_motor TEXT,
    numero_equipo TEXT,
    fecha_entrada_operacion DATE,
    fecha_salida_operacion DATE,
    ingestion_timestamp TIMESTAMP,
    source_file TEXT
);

-- Tabla eventos_bronce
CREATE TABLE IF NOT EXISTS eventos_bronce (
    id_ingestion TEXT PRIMARY KEY,
    pozo TEXT,
    categoria_principal TEXT,
    categoria_secundaria TEXT,
    fecha_paro TIMESTAMP,
    fecha_reinicio TIMESTAMP,
    comentario TEXT,
    ingestion_timestamp TIMESTAMP,
    source_file TEXT
);

-- Tabla control duplicados
CREATE TABLE IF NOT EXISTS ingested_files (
    file_name TEXT PRIMARY KEY,
    ingestion_timestamp TIMESTAMP
);