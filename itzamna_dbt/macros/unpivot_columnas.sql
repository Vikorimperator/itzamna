{% macro generate_unpivot_sql(model, id_columns, min_porcentaje_valido=0.9) %}
    {#
        model: nombre de la tabla fuente (ej. 'lecturas_silver')
        id_columns: columnas que no deben unpivotarse (ej. ['pozo', 'numero_equipo'])
        min_porcentaje_valido: umbral mínimo requerido de datos válidos por sensor
    #}

    {% set relation = source('silver', model) %}
    {% set columns = adapter.get_columns_in_relation(relation) %}
    {% set sensor_columns = [] %}

    {% for col in columns %}
        {% if col.name not in id_columns %}
            {% do sensor_columns.append(col.name) %}
        {% endif %}
    {% endfor %}

    {% set selects = [] %}
    {% for sensor in sensor_columns %}
        {% set sql %}
            SELECT
                pozo,
                numero_equipo,
                '{{ sensor }}' AS sensor,
                COUNT(*) AS total_registros,
                COUNT({{ sensor }}) AS registros_validos,
                ROUND(COUNT({{ sensor }}) * 1.0 / COUNT(*), 3) AS porcentaje_valido
            FROM {{ relation }}
            GROUP BY pozo, numero_equipo
            HAVING ROUND(COUNT({{ sensor }}) * 1.0 / COUNT(*), 3) >= {{ min_porcentaje_valido }}
        {% endset %}
        {% do selects.append(sql) %}
    {% endfor %}

    {% if selects | length == 0 %}
        SELECT * FROM (
            SELECT
                CAST(NULL AS VARCHAR) AS pozo,
                CAST(NULL AS INT) AS numero_equipo,
                CAST(NULL AS VARCHAR) AS sensor,
                CAST(NULL AS INTEGER) AS total_registros,
                CAST(NULL AS INTEGER) AS registros_validos,
                CAST(NULL AS DOUBLE) AS porcentaje_valido
        ) WHERE false
    {% else %}
        {{ selects | join(" UNION ALL\n") }}
    {% endif %}
{% endmacro %}
