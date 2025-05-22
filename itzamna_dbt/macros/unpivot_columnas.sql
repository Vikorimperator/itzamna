{% macro generate_unpivot_sql(model, id_columns, min_porcentaje_valido=0.9) %}
    {#
        model: nombre de la tabla fuente (ej. 'lecturas_silver')
        id_columns: columnas que no deben unpivotarse (ej. ['pozo', 'numero_equipo'])
        min_porcentaje_valido: umbral mínimo requerido de datos válidos por sensor
    #}

    {% set columns = adapter.get_columns_in_relation(source('silver', model)) %}
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
            FROM {{ source('silver', model) }}
            GROUP BY pozo, numero_equipo
            HAVING ROUND(COUNT({{ sensor }}) * 1.0 / COUNT(*), 3) >= {{ min_porcentaje_valido }}
        {% endset %}
        {% do selects.append(sql) %}
    {% endfor %}

    {{ selects | join(" UNION ALL\n") }}
{% endmacro %}

