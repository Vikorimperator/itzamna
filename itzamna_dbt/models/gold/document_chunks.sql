{{ config(materialized='table') }}

-- Paso 1: Cargar lecturas y sensores válidos por equipo
WITH lecturas AS (

    SELECT *
    FROM {{ source('silver', 'lecturas_silver') }}

),

sensores_validos AS (

    SELECT pozo, numero_equipo, sensor
    FROM {{ source('sensor_cobertura_real') }}

),

-- Paso 2: Convertir lecturas a formato largo (una fila por sensor)
unpivoted AS (

    {{ unpivot_lecturas_sql('lecturas_silver', ['pozo', 'numero_equipo', 'timestamp']) }}

),

-- Paso 3: Filtrar solo sensores válidos según cobertura real
filtrado AS (

    SELECT u.*
    FROM unpivoted u
    JOIN sensores_validos s
    ON u.pozo = s.pozo AND u.numero_equipo = s.numero_equipo AND u.sensor = s.sensor

),

-- Paso 4: Agrupar por día y generar el contenido tipo documento
agrupado AS (

    SELECT
        pozo,
        numero_equipo,
        DATE_TRUNC('day', timestamp) AS fecha,,

        -- Agrupamos por timestamp: sensor: valor
        STRING_AGG(
            FORMAT('%s | %s: %s', 
                STRFTIME(timestamp, '%Y-%m-%d %H:%M'), 
                sensor, 
                COALESCE(CAST(valor AS TEXT), 'null')
            ),
            '\n' ORDER BY timestamp
        ) AS content

    FROM filtrado
    GROUP BY pozo, numero_equipo, DATE_TRUNC('day', timestamp)

)

-- Paso 5: Salida final con ID único por chunk
SELECT
    pozo || '-' || numero_equipo || '-' || STRFTIME(fecha, '%Y%m%d') AS id,
    content,
    pozo,
    numero_equipo,
    fecha
FROM agrupado
