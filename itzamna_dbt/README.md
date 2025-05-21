# 🧮 itzamna_dbt

Este proyecto `dbt` define la capa **Gold** del modelo de datos para el sistema `Itzamna`, utilizando **DuckDB** como motor SQL local.

La capa Gold está diseñada para:

- Estandarizar y transformar datos limpios desde la capa Silver.
- Preparar datasets optimizados para análisis, dashboards y **Retrieval-Augmented Generation (RAG)** con modelos LLM.
- Implementar transformaciones reproducibles, testeables y versionadas mediante SQL declarativo.

---

## 📂 Estructura recomendada de modelos
```plaintext
itzamna_dbt/
├── models/
│ ├── silver/ # Representación directa de las tablas validadas
│ ├── gold/ # Modelos optimizados para consumo
│ └── marts/ # Vistas de alto nivel listas para negocio o LLM
```

---

## ⚙️ Configuración

### DuckDB

Este proyecto apunta al archivo:
warehouse.duckdb

Puedes configurar la conexión en `~/.dbt/profiles.yml` así:

```yaml
itzamna_dbt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: F:/Proyectos/itzamna/warehouse.duckdb
      threads: 4
```

---

## 🚀 Comandos básicos
```bash
dbt debug         # Verifica configuración
dbt run           # Ejecuta modelos
dbt test          # Ejecuta tests definidos en YAML
dbt docs generate # Genera documentación HTML
```

---

## 🧠 Notas
* Este proyecto se integra con Dagster como orquestador.
* Se enfoca en la preparación de contenido para tareas de generación aumentada por recuperación (RAG).
* La arquitectura de medallas (Bronce → Silver → Gold) es respetada y modularizada.