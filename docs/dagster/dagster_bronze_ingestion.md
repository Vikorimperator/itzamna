# 🧾 Documentación del pipeline de ingestión de datos bronce con Dagster

Este documento describe la arquitectura, configuración y flujo de trabajo actual del pipeline de ingestión de datos bronce utilizando **Dagster**, **DuckDB**, **Polars** y ejecución controlada por `@op` y `@job`.

---

## 🏗️ Estructura general del proyecto

itzamna_pipeline/
├── ops_ingestion.py # Contiene los ops: sensor, equipos, eventos
├── jobs.py # Define el job secuencial de ingestión
├── schedules.py # Agenda el job diario a las 6am
├── itzamna_core/
│ ├── data_ingestion/
│ │ └── ingest_bronze.py # Lógica de carga CSV + Parquet + DuckDB
│ └── utils/
│ └── config.py # Configuración de rutas
├── definitions.py # Punto de entrada registrado en Dagster

---

## 🔁 Flujo de ejecución

Se orquesta la carga de datos a la base **bronce (DuckDB)** desde archivos `.csv` en `data/raw/`. El flujo es:

sensor_data → equipos → eventos

Esto garantiza que no haya conflictos de acceso concurrente al archivo `warehouse.duckdb`.

---

## ⚙️ Componentes clave

### `@op`: ingest_sensor_data

- Carga archivos `AYATSIL-*_all.csv`
- Guarda en `data/lake/bronze/sensor_data/*.parquet`
- Crea o actualiza `bronze.sensor_data` en DuckDB

### `@op`: ingest_equipos_data

- Carga archivos `BEC_AYATSIL-*_all.csv`
- Preprocesa fechas de operación
- Guarda en `bronze.equipos`

### `@op`: ingest_eventos_data

- Carga archivos `Eventos_AYATSIL-*_all.csv`
- Renombra y transforma fechas
- Guarda en `bronze.eventos`

---

## 🧠 Encadenamiento con Nothing

Para evitar paralelismo y errores de conexión en DuckDB, se usó el patrón:

```python
@op(ins={"start": In(Nothing)})
def siguiente_op() -> Nothing:
    ...
```

Y el @job queda:

```python
@job
def ingest_all_bronze_op_based():
    sensor = ingest_sensor_data()
    equipos = ingest_equipos_data(start=sensor)
    ingest_eventos_data(start=equipos)
```

## 📅 Schedule: ejecución diaria

En schedules.py se definió:

```python
daily_ingestion_schedule = ScheduleDefinition(
    job=ingest_all_bronze_op_based,
    cron_schedule="0 6 * * *",
    execution_timezone="America/Mexico_City",
    name="daily_ingestion_schedule"
)
```

Esto permite ejecutar el flujo diariamente (manual o automático si se habilita el daemon).

## 🔎 Beneficios logrados
* ✅ Ejecución secuencial segura
* ✅ Uso de Polars + Parquet + DuckDB en modo local
* ✅ Monitoreo visual y control de errores en Dagit
* ✅ Modularización para escalar a capa Silver

## 📌 Pendientes posibles
* Agregar @sensor si se desea ejecución por aparición de nuevos archivos.
* Agregar capa Silver con nuevos @op.
* Agregar pruebas unitarias a cada @op.
* Agregar una funcion para registrar automáticamente todos los assets de un módulo.