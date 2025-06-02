{{ config(materialized='table') }}

-- Este modelo identifica los sensores con cobertura real
-- (porcentaje de registros válidos >= 90%) para cada equipo y pozo.
-- La lógica de cálculo y filtro se realiza dinámicamente desde la macro.

SELECT *
FROM (
    {{ generate_unpivot_sql('lecturas_silver', ['pozo', 'numero_equipo'], 0.9) }}
) AS cobertura