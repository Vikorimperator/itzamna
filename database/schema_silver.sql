-- Tabla de lecturas interpoladas por bomba (formato ancho)
CREATE TABLE IF NOT EXISTS lecturas_silver (
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    pozo TEXT NOT NULL,
    numero_equipo TEXT NOT NULL,
    temperatura DOUBLE PRECISION,
    corriente DOUBLE PRECISION,
    presion DOUBLE PRECISION,
    -- otras columnas opcionales pueden añadirse
    PRIMARY KEY (timestamp, pozo, numero_equipo)
);

-- Tabla de cobertura de sensores por equipo
CREATE TABLE IF NOT EXISTS sensor_coverage_silver (
    pozo TEXT NOT NULL,
    numero_equipo TEXT NOT NULL,
    sensor TEXT NOT NULL,
    PRIMARY KEY (pozo, numero_equipo, sensor)
);

-- Tabla de información técnica de equipos con estado calculado (columna normal)
CREATE TABLE IF NOT EXISTS equipos_silver (
    pozo TEXT NOT NULL,
    numero_equipo TEXT NOT NULL,
    modelo_bomba TEXT,
    marca_bomba TEXT,
    modelo_motor TEXT,
    fecha_entrada_operacion TIMESTAMP WITH TIME ZONE,
    fecha_salida_operacion TIMESTAMP WITH TIME ZONE,
    estado_equipo TEXT,
    PRIMARY KEY (pozo, numero_equipo)
);

-- Tabla de eventos de operación por pozo y equipo
CREATE TABLE IF NOT EXISTS eventos_silver (
    id_evento SERIAL PRIMARY KEY,
    pozo TEXT NOT NULL,
    numero_equipo TEXT,
    tipo_evento TEXT,
    descripcion TEXT,
    fecha_inicio TIMESTAMP WITH TIME ZONE,
    fecha_fin TIMESTAMP WITH TIME ZONE,
    comentario TEXT
);

