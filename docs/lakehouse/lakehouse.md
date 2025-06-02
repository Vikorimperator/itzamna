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

# 🟡 Estructura de las Tablas Gold (`itzamna_dbt`)

Las tablas en la capa **Gold** representan vistas transformadas y listas para análisis avanzado, especialmente orientadas a tareas de NLP como recuperación aumentada por generación (RAG). A continuación se describe la estructura de cada tabla:

---

## 📘 `main_gold.sensor_cobertura_real`

### 🧱 Descripción
Tabla que indica la cobertura de cada sensor (porcentaje de datos válidos) por combinación de `pozo` y `numero_equipo`.

### 📐 Esquema

| Columna             | Tipo       | Descripción                                                                 |
|---------------------|------------|-----------------------------------------------------------------------------|
| `pozo`              | `VARCHAR`  | Identificador del pozo.                                                    |
| `numero_equipo`     | `INTEGER`  | Número del equipo dentro del pozo.                                         |
| `sensor`            | `VARCHAR`  | Nombre del sensor registrado en `lecturas_silver`.                         |
| `total_registros`   | `INTEGER`  | Total de registros para ese sensor en esa combinación pozo-equipo.         |
| `registros_validos` | `INTEGER`  | Registros que no son `NULL` para el sensor.                                |
| `porcentaje_valido` | `FLOAT`    | Proporción `registros_validos / total_registros`.                          |

### 🔎 Consideraciones
- Sólo se incluyen sensores cuyo `porcentaje_valido >= 0.9`.
- Útil para filtrar sensores no operativos o irrelevantes por baja cobertura.

---

## 📘 `main_gold.document_chunks`

### 🧱 Descripción
Tabla que agrupa y convierte las lecturas de sensores válidos en documentos diarios por equipo y pozo. Cada documento es un chunk textual con formato legible para tareas de NLP.

### 📐 Esquema

| Columna         | Tipo        | Descripción                                                                 |
|------------------|-------------|-----------------------------------------------------------------------------|
| `id`             | `VARCHAR`   | ID único: `pozo-numero_equipo-fecha (YYYYMMDD)`.                           |
| `content`        | `TEXT`      | Texto plano con las lecturas del día agrupadas por sensor y timestamp.     |
| `pozo`           | `VARCHAR`   | Identificador del pozo.                                                    |
| `numero_equipo`  | `INTEGER`   | Número del equipo dentro del pozo.                                         |
| `fecha`          | `DATE`      | Fecha (a nivel día) de los datos agregados.                                |

### 🔎 Formato del campo `content`
```text
2023-08-24 00:00 | Corriente de entrada: 8.4
2023-08-24 00:10 | Corriente de entrada: 8.7
2023-08-24 00:20 | Corriente de entrada: 8.9
```

## 🧠 Aplicaciones
- Entrada directa para generación de embeddings (OpenAI, HuggingFace, Vertex AI).
- Ideal para búsqueda semántica o recuperación de contexto para LLMs.

## 🔄 Relación entre tablas
- document_chunks depende de los sensores válidos definidos en sensor_cobertura_real.
- Ambas se derivan de la tabla silver.lecturas_silver, pero document_chunks filtra y estructura los datos de forma legible.

## 🧪 Siguiente paso sugerido
Indexar document_chunks con una base de datos vectorial y usarlo como fuente en un pipeline de Retrieval-Augmented Generation (RAG).