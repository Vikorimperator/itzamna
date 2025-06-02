{% macro unpivot_lecturas_sql(model, id_columns) %}
    {#
        model: tabla de entrada (ej. 'lecturas_silver')
        id_columns: columnas que no se deben pivotar
    #}
    
    {% set relation = source('silver', model) %}
    {% set columns = adapter.get_columns_in_relation(relation) %}
    {% set sensores = [] %}

    {% for col in columns %}
        {% if col.name not in id_columns %}
            {% do sensores.append(col.name) %}
        {% endif %}
    {% endfor %}

    {% set selects = [] %}
    {% for sensor in sensores %}
        {% set sql %}
            SELECT 
                pozo, 
                numero_equipo, 
                timestamp, 
                '{{ sensor }}' AS sensor, 
                "{{ sensor }}" AS valor
            FROM {{ relation }}
        {% endset %}
        {% do selects.append(sql) %}
    {% endfor %}

    {% if selects | length == 0 %}
        SELECT NULL AS pozo, NULL AS numero_equipo, NULL AS timestamp, NULL AS sensor, NULL AS valor
    {% else %}
        {{ selects | join(" UNION ALL\n") }}
    {% endif %}
{% endmacro %}
