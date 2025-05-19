# 🦆 Arquitectura Bronce y Silver con DuckDB

Este documento describe cómo se implementó el sistema de ingesta y transformación de datos desde archivos CSV hacia un **Lakehouse local usando DuckDB**, estructurado por capas: **Bronce** y **Silver**.

---

## 📁 Estructura del Lakehouse

data/
└── lake/
├── bronze/
│ ├── sensor_data/
│ ├── equipos/
│ └── eventos/
└── silver/
├── lecturas_filtradas/
├── eventos_procesados/
├── equipos_enriquecidos/
└── pozos_catalogo/
warehouse.duckdb

---

## 🧊 Capa Bronce (Raw + Metadata)

Los archivos CSV se ingestan a Bronce utilizando `Polars` y `DuckDB`. En esta capa:

- Se agregan las columnas:
  - `pozo`: extraída del nombre del archivo
  - `id_ingestion`: UUID único
  - `source_file`: nombre del archivo de origen
  - `ingestion_timestamp`: fecha y hora de ingesta
- Las fechas se tipan a `datetime[μs, America/Mexico_City]`
- Las columnas numéricas se convierten a `Float64`

### ✅ Tablas Bronce

| Tabla           | Descripción                                |
|-----------------|--------------------------------------------|
| `bronze.sensor_data` | Lecturas crudas por sensor               |
| `bronze.equipos`     | Datos de configuración de equipos        |
| `bronze.eventos`     | Paros programados/no programados         |
| `bronze.ingested_files` | Control de archivos ya ingestados      |

---

## ⚙️ Capa Silver (Validación y Transformación)

En Silver se aplican transformaciones de negocio con `Polars`:

### Funciones Clave

- `prepare_equipos`: asigna estado `"activo"` o `"inactivo"` según la fecha de salida del equipo
- `filtrar_sensores_validos`: conserva solo las lecturas dentro del período de operación del equipo
- `preparar_eventos`: renombra y estructura los eventos
- `enriquecer_eventos_con_equipo`: asigna `numero_equipo` a cada evento
- `generar_tabla_pozos`: resume el estado y cantidad de equipos por pozo

### 🕐 Zonas Horarias

- Toda la lógica trabaja en `datetime[μs, America/Mexico_City]`
- Se evita el uso de UTC para mantener coherencia y facilidad de debugging local

---

## ✅ Buenas prácticas aplicadas

- Ingesta incremental basada en `ingested_files`
- Enriquecimiento desde nombre del archivo (sin modificar los crudos)
- Separación clara entre Bronce (raw) y Silver (validado)
- Uso de `Polars` por su rendimiento y compatibilidad con `DuckDB` vía `Arrow`

---

## 🧪 Verificaciones recomendadas

```python
con = duckdb.connect(\"warehouse.duckdb\")
df = con.execute(\"SELECT * FROM bronze.sensor_data LIMIT 5\").arrow()
pl.from_arrow(df).schema
```

🚧 Próximos pasos sugeridos
* Incorporar capa Gold para KPIs agregados
* Automatizar con Dagster o Prefect
* Agregar dbt para modelado declarativo