# ⚙️ Documentación del Pipeline de Transformación e Ingesta Silver

Este documento describe el flujo de transformación desde la capa **Bronce** a **Silver** utilizando Dagster, Polars y DuckDB. Incluye la lógica modular implementada con `@op`, su orquestación con `@job` y su ejecución automatizada con `@schedule`.

---

## 🎯 Objetivo

Transformar los datos crudos y no validados (capa Bronce) en datos **estructurados, limpios y listos para análisis o modelado** (capa Silver), manteniendo trazabilidad, consistencia de tipos y cobertura de sensores.

---

## 🧱 Estructura General del Pipeline

```plaintext
load_bronze_data
      ↓
prepare_equipos_silver
      ↓
filter_valid_sensors
      ↓
interpolate_sensors
      ↓
generate_sensor_catalog
      ↓
prepare_eventos_silver
      ↓
enrich_eventos_with_equipo
      ↓
generate_pozos_summary
      ↓
save_all_silver_outputs
      ↓
register_silver_tables
```
---

## ⚙️ Componentes Técnicos
### 🧩 Orquestador: Dagster
* Todos los pasos del flujo están implementados como @op.
* El @job transform_all_silver_op_based los encadena de manera secuencial.
* Se define un @schedule diario a las 6:30am en zona horaria America/Mexico_City.

### 📦 Base de datos: DuckDB
* Los archivos .parquet generados en Silver son registrados como tablas externas.
* Las tablas Silver viven en el esquema silver.* dentro del archivo warehouse.duckdb.

### 🧠 Librerías usadas
* polars para transformación rápida y eficiente.
* duckdb como motor analítico local.
* dagster para orquestación de pipelines.

---

## 🧾 Descripción de los pasos

| Etapa (`@op`)                | Descripción                                                                    |
|----------------------------------------------------------------------------                                   |
| `load_bronze_data`           | Carga sensores, equipos y eventos desde Bronce en DuckDB.                      |
| `prepare_equipos_silver`     | Asigna estado `'activo'` o `'inactivo'` a cada equipo según fecha de salida.   |
| `filter_valid_sensors`       | Conserva solo lecturas dentro del rango operativo del equipo.                  |
| `interpolate_sensors`        | Resamplea a cada 10 minutos e interpola valores numéricos por equipo.          |
| `generate_sensor_catalog`    | Crea una tabla de sensores disponibles por pozo-equipo.                        |
| `prepare_eventos_silver`     | Renombra columnas para alinearse con el esquema Silver.                        |
| `enrich_eventos_with_equipo` | Asocia eventos con el número de equipo correspondiente (basado en fechas).     |
| `generate_pozos_summary`     | Genera resumen por pozo: cantidad de equipos, estado, última entrada.          |
| `save_all_silver_outputs`    | Guarda archivos `.parquet` en la carpeta `data/lake/silver/`.                  |
| `register_silver_tables`     | Registra las tablas como vistas externas en DuckDB.                            |

---

## 🗂️ Ubicación de archivos generados
Los resultados de la transformación se guardan como .parquet en:

```plaintext
data/lake/silver/
├── lecturas_silver/
├── sensor_coverage_silver/
├── equipos_silver/
├── eventos_silver/
└── pozos_silver/
```

---

## 🔄 Automatización
El flujo transform_all_silver_op_based se ejecuta automáticamente gracias al siguiente schedule:

```python
ScheduleDefinition(
    job=transform_all_silver_op_based,
    cron_schedule="30 6 * * *",
    execution_timezone="America/Mexico_City",
    name="daily_transform_silver_schedule"
)
```

---

## 📌 Notas importantes
* Todas las fechas trabajan en datetime[μs, America/Mexico_City] para coherencia con sensores.
* Los .parquet son válidos como fuente directa para motores analíticos y ML.
* El @op register_silver_tables se ejecuta después de guardar los archivos, para evitar errores de sincronización con DuckDB.

---

## 📅 Próximos pasos sugeridos
* Agregar un @sensor para ejecutar solo si hay nuevos datos en Bronce.
* Implementar validaciones de calidad de datos (DQ checks).
* Crear documentación para la capa Gold o modelado de ML.