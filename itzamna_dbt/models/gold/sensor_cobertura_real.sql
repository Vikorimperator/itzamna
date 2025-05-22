{{ config(materialized='table') }}

WITH base AS (
    SELECT * FROM {{ source('silver', 'lecturas_silver') }}
),

unpivoted AS (

    {{ generate_unpivot_sql('lecturas_silver', ['pozo', 'numero_equipo']) }}

),

cobertura AS (
    SELECT
        pozo,
        numero_equipo,
        sensor,
        COUNT(*) AS total_registros,
        COUNT(valor) AS registros_validos,
        ROUND(COUNT(valor) * 1.0 / COUNT(*), 3) AS porcentaje_valido
    FROM unpivoted
    GROUP BY pozo, numero_equipo, sensor
)

SELECT *
FROM cobertura
WHERE procentaje_valido >= 0.9