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

En Silver se aplican transformaciones de negocio con `Polars`. Los datos se interpolan, filtran y enriquecen para asegurar consistencia temporal y relacional.

### ✅ Tablas Silver

| Tabla                         | Descripción                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| `silver.lecturas_silver`      | Lecturas interpoladas cada 10 minutos por pozo y número de equipo           |
| `silver.sensor_coverage_silver` | Catálogo de sensores disponibles por equipo                                |
| `silver.equipos_silver`       | Datos técnicos de equipos + estado calculado (`activo` / `inactivo`)        |
| `silver.eventos_silver`       | Eventos enriquecidos con `numero_equipo`, según ventana de operación        |
| `silver.pozos_silver`         | Resumen por pozo: última fecha de operación, estado actual, número de equipos |

---

### Funciones Clave aplicadas

- `prepare_equipos`: asigna estado `"activo"` o `"inactivo"` según la fecha de salida del equipo.
- `filtrar_sensores_validos`: conserva solo las lecturas dentro del período de operación del equipo.
- `interpolar_por_equipo`: interpola lecturas cada 10 minutos.
- `generar_catalogo`: identifica los sensores válidos para cada equipo.
- `preparar_eventos`: estandariza eventos desde Bronce.
- `enriquecer_eventos_con_equipo`: asigna `numero_equipo` a eventos según fechas.
- `generar_tabla_pozos`: resume el estado y cantidad de equipos por pozo.

### 🕐 Zonas Horarias

- Toda la lógica trabaja en `datetime[μs, America/Mexico_City]`
- Se evita el uso de UTC para mantener coherencia y facilidad de debugging local

---

## ✅ Buenas prácticas aplicadas

- Ingesta incremental basada en `ingested_files`.
- Separación entre datos crudos (Bronce) y validados (Silver).
- Transformación eficiente y vectorizada con `Polars`.
- Interpolación controlada por equipo y por sensor.
- Registro automático de vistas externas en DuckDB.

---

## 🧪 Verificaciones recomendadas

```python
con = duckdb.connect(\"warehouse.duckdb\")
df = con.execute(\"SELECT * FROM bronze.sensor_data LIMIT 5\").arrow()
pl.from_arrow(df).schema
```

---

## 🚧 Próximos pasos sugeridos
* Incorporar capa Gold para KPIs agregados o dashboards.
* Agregar validaciones automáticas de calidad de datos.
* Integrar modelos predictivos (ML) sobre tablas Silver.
* Automatizar orquestación completa con sensores de archivos.
* Agregar dbt para modelado declarativo