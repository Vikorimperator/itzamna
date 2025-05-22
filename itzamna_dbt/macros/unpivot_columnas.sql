{% macro generate_unpivot_sql(model, id_columns) %}
    {# 
        model: nombre del modelo (ej. 'lecturas_silver')
        id_columns: lista de columnas que NO se deben unpivotar
    #}

    {% set columns = adapter.get_columns_in_relation(ref(model)) %}
    {% set sensor_columns = [] %}
    
    {# Filtrar solo las columnas que no están en id_columns #}
    {% for col in columns %}
        {% if col.name not in id_columns %}
            {% do sensor_columns.append(col.name) %}
        {% endif %}
    {% endfor %}

    {% set selects = [] %}
    {% for sensor in sensor_columns %}
        {% set sql = "SELECT pozo, numero_equipo, '" ~ sensor ~ "' AS sensor, " ~ sensor ~ " AS valor FROM base" %}
        {% do selects.append(sql) %}
    {% endfor %}

    {{ selects | join(" UNION ALL\n") }}
{% endmacro %}
