# 🔨 Constructor de Grafo RAG

**Script standalone para extraer grafos de conocimiento desde PDFs**

## 📋 Descripción

Este script procesa cualquier PDF y extrae:
- **Entidades**: Conceptos, actores, derechos, obligaciones
- **Relaciones**: Conexiones entre entidades (regula, otorga, require, etc)
- **Grafo JSON**: Estructura nodes/edges lista para usar en RAG

## ⏱️ Estimación de Tiempo

El script ahora incluye **estimación automática de tiempo**:

```
📊 Procesando 5 chunks
⏱️  Tiempo estimado: ≈ 0m 13s
--------------------------------------------------

  [1/5] 0% - Procesando...
  [2/5] 40% - Tiempo restante: ≈ 0m 8s
  [3/5] 60% - Tiempo restante: ≈ 0m 5s
  [4/5] 80% - Tiempo restante: ≈ 0m 2s
  [5/5] 100% - Tiempo restante: ≈ 0m 0s
```

**Cálculo**:
- Tiempo por chunk: 2.5s (promedio Groq API)
- Tiempo total = (# chunks) × 2.5s
- Se actualiza en tiempo real conforme procesa

## 🚀 Uso

### Opción 1: Procesar un PDF (sin stats)
```bash
python build_knowledge_graph.py documento.pdf
```

**Output**:
```
✅ Grafo RAG CREADO EXITOSAMENTE

📁 Archivo: documento_graph.json
📊 Nodos: 34
🔗 Relaciones: 156
⏱️  Tiempo total: 0m 13s
```

### Opción 2: Procesar con estadísticas detalladas
```bash
python build_knowledge_graph.py documento.pdf --stats
```

**Output adicional**:
```
📊 ESTADÍSTICAS DEL GRAFO
📈 Tamaño:
  • Nodos: 34
  • Relaciones: 156
  • Densidad: 4.59 edges por nodo

🏷️  Tipos de entidades:
  • concepto: 18
  • articulo: 10
  • derecho: 4
  • obligacion: 2

🔗 Tipos de relaciones:
  • regula: 78
  • otorga: 45
  • require: 33
```

### Opción 3: Limitar chunks (para PDFs grandes)
```bash
python build_knowledge_graph.py documento.pdf --max-chunks 10
```

**Esto procesa solo los primeros 10 chunks**:
- Más rápido (≈ 25 segundos)
- Útil para testing
- Genera grafo proporcional

### Opción 4: Guardar con nombre personalizado
```bash
python build_knowledge_graph.py documento.pdf --output mi_grafo.json
```

### Opción 5: Combinar todo
```bash
python build_knowledge_graph.py documento.pdf \
  --max-chunks 15 \
  --output custom_graph.json \
  --stats
```

## 📊 Parámetros

| Parámetro | Corto | Tipo | Default | Descripción |
|-----------|-------|------|---------|-------------|
| `pdf` | - | string | - | Ruta al PDF (obligatorio) |
| `--output` | `-o` | string | `{pdf_name}_graph.json` | Archivo de salida JSON |
| `--max-chunks` | `-m` | int | 10 | Máximo chunks a procesar |
| `--stats` | `-s` | flag | False | Mostrar estadísticas |

## ⏲️ Tiempo Estimado por Chunks

```
Chunks  | Tiempo Est.  | Procesamiento
--------|--------------|----------------
1       | 0m 03s      | Rápido
5       | 0m 13s      | Rápido
10      | 0m 25s      | Moderado
20      | 0m 50s      | Moderado
50      | 2m 05s      | Lento
100     | 4m 10s      | Muy lento
```

**Recomendación**: Usar `--max-chunks 10-15` para testing

## 📁 Estructura del Output JSON

```json
{
  "metadata": {
    "source": "documento.pdf",
    "total_text_chars": 125000,
    "chunks_processed": 5,
    "nodes_count": 34,
    "edges_count": 156
  },
  "nodes": [
    {
      "id": "art_65",
      "label": "Artículo 65 - Descanso",
      "type": "articulo",
      "description": "El trabajador tiene derecho a un día de descanso...",
      "chunk_index": 0
    }
  ],
  "edges": [
    {
      "source": "art_65",
      "target": "descanso",
      "relation": "regula",
      "weight": 0.95
    }
  ]
}
```

## 🔍 Tipos de Entidades Reconocidas

- **articulo**: Artículos de ley
- **concepto**: Conceptos legales (ej: descanso, salario)
- **actor**: Actores (ej: trabajador, empleador)
- **derecho**: Derechos laborales
- **obligacion**: Obligaciones

## 🔗 Tipos de Relaciones

- **regula**: A regula B (una ley regula un derecho)
- **otorga**: A otorga B (proporciona un derecho)
- **require**: A requiere B (precondición)
- **related_to**: Relación genérica

## 💡 Ejemplo Real

```bash
$ python build_knowledge_graph.py /home/raziel/Proyectos/AI_Codigo_trabajo/articles-117137_galeria_02.pdf \
  --max-chunks 20 \
  --output leyes_graph.json \
  --stats

======================================================================
🔨 CONSTRUCTOR DE GRAFO RAG
======================================================================

📖 Extrayendo texto del PDF...
✅ 1395129 caracteres extraídos

✂️  Diviendo en chunks...
✅ 320 chunks creados

🤖 Extrayendo entidades y relaciones con Groq LLM...

📊 Procesando 20 chunks
⏱️  Tiempo estimado: ≈ 0m 50s
--------------------------------------------------

  [1/20] 5% - Procesando...
  [2/20] 10% - Tiempo restante: ≈ 0m 48s
  ...
  [20/20] 100% - Tiempo restante: ≈ 0m 0s

  ✅ 20 chunks procesados en 0m 48s
✅ Extraídas 128 entidades, 456 relaciones

======================================================================
✅ GRAFO RAG CREADO EXITOSAMENTE
======================================================================

📁 Archivo: leyes_graph.json
📊 Nodos: 115
🔗 Relaciones: 456
⏱️  Tiempo total: 0m 48s
```

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'groq'"
```bash
pip install groq sqlalchemy pydantic numpy python-dotenv PyPDF2
```

### "PDF no encontrado"
Verifica que la ruta sea correcta:
```bash
# Ruta absoluta (recomendado)
python build_knowledge_graph.py /full/path/to/document.pdf

# O ruta relativa
python build_knowledge_graph.py ../documents/law.pdf
```

### "invalid_api_key"
- Verifica `.env` con `GROQ_API_KEY`
- Regenera key en https://console.groq.com
- Formato: `GROQ_API_KEY=gsk_xxxxx`

### Procesamiento muy lento
Usa `--max-chunks` para procesar menos:
```bash
# Solo 5 chunks (≈13 segundos)
python build_knowledge_graph.py documento.pdf --max-chunks 5
```

## 📚 Próximo Paso

Una vez tengas el JSON del grafo, puedes:

1. **Integrarlo en el RAG actual** (próxima fase)
2. **Inspeccionarlo**: Ver conexiones principales
3. **Mejorarlo**: Ajustar extracciones editar el JSON
4. **Usarlo para reranking**: Mejorar búsquedas en RAG

## 📄 Licencia

Mismo que el proyecto principal

---

**¿Preguntas?** Ver README principal del proyecto
