# ✨ Modelos Gold en dbt (`itzamna_dbt`)

Este documento describe los modelos de la capa **Gold** construidos mediante `dbt`. Estos modelos están diseñados para aplicaciones avanzadas como generación aumentada por recuperación (**RAG**) usando modelos LLM.

---

## 📘 Tabla: `main_gold.sensor_cobertura_real`

### 🎯 Objetivo
Identificar los sensores con suficiente cobertura de datos por equipo y pozo, filtrando aquellos cuya tasa de datos válidos sea menor al 90%.

### 📥 Fuente
- `silver.lecturas_silver` (definida como source en dbt)

### ⚙️ Lógica
1. Se hace un **unpivot** de la tabla `lecturas_silver`.
2. Se agrupa por `pozo`, `numero_equipo` y `sensor`.
3. Se calcula:
   - `total_registros`: Total de filas para ese sensor.
   - `registros_validos`: Filas donde el valor no es NULL.
   - `porcentaje_valido`: Proporción de datos válidos.
4. Se filtran aquellos sensores con al menos 90% de cobertura.

### 🧪 Fórmula:
```sql
COUNT(valor) / COUNT(*) >= 0.9
🧾 Ejemplo de salida:
pozo	numero_equipo	sensor	total_registros	registros_validos	porcentaje_valido
139	5	Corriente de entrada	65311	65242	0.999
```

## 📘 Tabla: main_gold.document_chunks
### 🎯 Objetivo
Generar un texto estructurado diario para cada combinación de pozo y equipo, incluyendo sensores válidos y sus lecturas. Este texto puede usarse como entrada para tareas de NLP (RAG, embeddings, búsqueda semántica, etc.).

### 📥 Fuentes
- `silver.lecturas_silver`
- `main_gold.sensor_cobertura_real` (referenciado con {{ ref() }})

### ⚙️ Lógica
1. Se realiza un unpivot de lecturas_silver.
2. Se filtran los sensores según sensor_cobertura_real.
3. Se agrupa por día (DATE_TRUNC('day', timestamp)), pozo y número de equipo.
4. Se construye un campo content concatenando cada lectura con formato legible:

``` yaml
2023-08-24 00:10 | Corriente de entrada: 8.6
2023-08-24 00:20 | Corriente de entrada: 8.8
```

### 🔑 Campo clave
```sql
id = pozo || '-' || numero_equipo || '-' || STRFTIME(fecha, '%Y%m%d')
🧾 Ejemplo de salida
id	content	pozo	numero_equipo	fecha
139-5-20230824	...documento generado...	139	5	2023-08-24
``` 

## 🧠 Aplicaciones futuras
- Indexar document_chunks con FAISS, Weaviate o Chroma.
- Crear embeddings con OpenAI, HuggingFace, Vertex AI Embeddings.
- Construir un sistema de recuperación para asistente tipo RAG.