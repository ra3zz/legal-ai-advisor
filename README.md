# ⚖️ Legal AI Advisor - Asesor Laboral Inteligente

**Sistema de asesoramiento legal experto basado en RAG con Grafo de Conocimiento integrado**

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python) 
![Groq](https://img.shields.io/badge/Groq-LLM-orange) 
![SQLite](https://img.shields.io/badge/SQLite-DB-green) 
![CLI](https://img.shields.io/badge/CLI-Interactive-purple)

---

## 🎯 Descripción General

**Legal AI Advisor** es un sistema de inteligencia artificial especializado en asesoramiento sobre el **Código del Trabajo Chileno**. Combina:

- 🔍 **Búsqueda Híbrida**: Embeddings semánticos (70%) + Keywords BM25 (30%)
- 📊 **Grafo de Conocimiento**: Extrae entidades y relaciones automáticamente
- 🧠 **Reranking Inteligente**: Mejora resultados usando conexiones del grafo
- 💬 **LLM Experto**: Groq llama-3.3-70b para respuestas precisas
- 💾 **Base de Datos Local**: SQLite con 320+ documentos
- 🎨 **CLI Interactivo**: Interfaz terminal colorida

---

## 🚀 Quick Start (30 segundos)

```bash
cd /tu/ruta/AI_Codigo_trabajo
chmod +x run.sh
./run.sh
```

---

## 📋 Requisitos

- **OS**: Linux/macOS/Windows (con WSL)
- **Python**: 3.11+
- **RAM**: 2GB mínimo
- **Groq API Key**: Gratis en https://console.groq.com

---

## 📺 Instalación (5 minutos)

### Automático
```bash
chmod +x run.sh
./run.sh
```

### Manual
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "GROQ_API_KEY=tu_key" > .env
python scripts/init_db.py
python cli_chat.py
```

---

## 🎮 Cómo Usar

### Comandos Disponibles

```
?              - Mostrar ayuda
cargar <ruta>  - Cargar PDF nuevo
docs           - Listar documentos cargados
historial      - Ver últimas preguntas
grafo          - Ver estadísticas del grafo
reset-docs     - Limpiar base de datos
Tu pregunta    - Chatear
```

### Ejemplo de Uso

```
💬 Tu pregunta: ¿Qué derechos tiene un trabajador?

🔄 Buscando información relevante...
✅ 3 documento(s) encontrado(s):
   • Doc (relevancia: 41.2%) 📊+6.7%
   • Doc (relevancia: 40.9%) 📊+6.7%
   • Doc (relevancia: 38.2%) 📊+6.7%

⏳ Generando respuesta...

Respuesta:
Basándome en el Código del Trabajo Chileno, un trabajador 
tiene los siguientes derechos: remuneración, descanso, 
feriado, y respeto a sus garantías...

📝 Fuentes:
   • Artículo 5
   • Artículo 10
```

---

## 🏗️ Arquitectura

```
┌─────────────────────────────┐
│    CLI Interface (User)      │
│       cli_chat.py           │
└──────────────┬──────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼────┐ ┌──▼──────┐ ┌─▼────────┐
│   RAG  │ │ Grafo   │ │   Groq   │
│Search  │ │ Service │ │   LLM    │
└───┬────┘ └──┬──────┘ └─┬────────┘
    │         │         │
    │         │         │
 ┌──▼─────────▼────┬────▼──────┐
 │  SQLite (320)   │ JSON (54)  │
 │  Documentos     │ Nodos      │
 └─────────────────┴────────────┘
```

---

## 📁 Estructura del Proyecto

```
AI_Codigo_trabajo/
├── run.sh                           # 🚀 EJECUTAR AQUI
├── README.md                        # Este archivo
├── articles-117137_galeria_02.pdf   # PDF origen
├── articles-117137_galeria_02_graph.json  # Grafo
│
├── backend/
│   ├── cli_chat.py                  # Interface CLI principal
│   ├── build_knowledge_graph.py     # Generador de grafos
│   ├── requirements.txt              # Dependencias Python
│   │
│   ├── services/
│   │   ├── rag_service.py           # Búsqueda híbrida + reranking
│   │   ├── graph_service.py         # Grafo de conocimiento
│   │   └── groq_service.py          # Integración Groq API
│   │
│   ├── database/
│   │   ├── models.py                # ORM SQLAlchemy
│   │   └── database.py              # Config base de datos
│   │
│   ├── data/
│   │   └── app.db                   # Base de datos SQLite
│   │
│   ├── test_suite.py                # Tests unitarios
│   ├── reset_db.py                  # Script limpiar BD
│   └── .env                         # Variables de entorno
│
├── GRAPH_RAG_INTEGRATION_README.md  # Doc técnica: Integración Grafo
└── backend/KNOWLEDGE_GRAPH_README.md # Doc técnica: Generación de Grafos
```

---

## ⚙️ Configuración

### Variables de Entorno

**backend/.env:**
```bash
GROQ_API_KEY=gsk_...tu_api_key_aqui...
```

Obtén tu API key gratis en: https://console.groq.com

### Parámetros Ajustables

**En cli_chat.py - Línea 95:**
```python
results = RAGService.search_hybrid(query, top_k=3, use_graph=True)
# top_k: aumentar a 5+ para más contexto
# use_graph: True para reranking, False para búsqueda simple
```

**En graph_service.py - Línea 115:**
```python
graph_service.rerank_documents_with_graph(query, results, boost_factor=0.2)
# boost_factor: 0.2 (moderado) a 0.5 (agresivo)
```

---

## 📊 Base de Datos

### Contenido Actual

- **Documentos**: 320 chunks del PDF del Código del Trabajo
- **Embeddings**: 384 dimensiones (sintéticos)
- **Tamaño**: ~50 MB
- **Ubicación**: `backend/data/app.db`

### Reset/Limpiar

```bash
# Opción 1: Desde CLI
💬 Tu pregunta: reset-docs

# Opción 2: Script directo
cd backend && python reset_db.py

# Opción 3: Manual
rm backend/data/app.db
python scripts/init_db.py
```

---

## 🔗 Extracción de Grafos

Para generar un grafo desde otro PDF:

```bash
cd backend
python build_knowledge_graph.py /ruta/documento.pdf \
  --max-chunks 50 \
  --output mi_grafo.json \
  --stats

# Salida: mi_grafo.json con:
# - Entidades extraídas (actores, conceptos, derechos)
# - Relaciones entre entidades
# - Estadísticas del grafo
```

Ver documentación completa: [backend/KNOWLEDGE_GRAPH_README.md](backend/KNOWLEDGE_GRAPH_README.md)

---

## 🔗 Cómo Funciona el Sistema

### 1. Búsqueda Híbrida

```
Tu pregunta: "¿Qué derechos tiene un trabajador?"
                    ↓
         RAGService.search_hybrid()
                    ↓
    ┌───────────────┴──────────────┐
    │                              │
    ▼                              ▼
Embeddings (70%)             BM25 Keywords (30%)
Similitud semántica       Coincidencia exacta
                    ↓
            Combinado: 0.7*emb + 0.3*bm25
                    ↓
         Top-3 documentos ordenados
```

### 2. Reranking con Grafo

```
      Top-3 documentos
                    ↓
    GraphService.rerank()
                    ↓
    Extrae entidades en query:
    "derechos", "trabajador"
                    ↓
    Busca en grafo:
    ¿El doc menciona entidades conectadas?
                ↓
    Calcula connectivity_score
                ↓
    Aplica BOOST al score original
                ↓
    Reordena resultados con nuevo score
                ↓
    Top-3 rerankeados (+6.7% boost)
```

### 3. Generación de Respuesta

```
Documentos + Info del Grafo
                ↓
    Enriquecimiento de contexto
    (entidades + relaciones)
                ↓
    GroqService.chat_with_doc()
    (LLM: llama-3.3-70b)
                ↓
    Respuesta experta con fuentes
```

---

## 🧪 Testing

### Tests Unitarios

```bash
cd backend
python test_suite.py

# Output:
# ✅ Test 1: RAG Search - PASSED
# ✅ Test 2: Graph Loading - PASSED
# ✅ Test 3: LLM Response - PASSED
```

### Tests Manual

```python
# Probar búsqueda
from services.rag_service import RAGService
results = RAGService.search_hybrid("¿Qué es descanso?", top_k=3)
for r in results:
    print(f"Score: {r['score']:.2f} - {r['text'][:100]}")
```

---

## 📈 Performance

| Operación | Tiempo | Notas |
|-----------|--------|-------|
| Startup | ~2s | Carga BD + grafo |
| Búsqueda híbrida | ~150ms | Embeddings + BM25 |
| Reranking grafo | +30ms | Conexiones del grafo |
| Respuesta LLM | ~2s | Latencia Groq API |
| **Total/pregunta** | **~2.2s** | End-to-end |

**Hardware Recomendado:**
- CPU: 2+ cores
- RAM: 4GB (2GB mínimo)
- Disco: 500MB (venv + BD)

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'groq'"

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### "GROQ_API_KEY not found"

```bash
# Verificar que existe el archivo
cat backend/.env

# Si no, crear:
echo "GROQ_API_KEY=gsk_..." > backend/.env

# Obtén key en: https://console.groq.com
```

### "Database locked" o "app.db error"

```bash
# Opción 1: Esperar (se libera solo)
# Opción 2: Resetear
cd backend
rm data/app.db
python scripts/init_db.py
```

### Respuestas genéricas (sin contexto)

1. Verifica documentos: `💬 docs`
2. Intenta pregunta más específica
3. Aumenta `top_k=5` en `cli_chat.py`
4. Verifica grafo: `💬 grafo`

---

## 🔐 Seguridad

### API Key

⚠️ **IMPORTANTE**: La API key es sensible

```bash
# Nunca commitear .env
echo ".env" >> .gitignore

# En producción:
# 1. Usar secret manager (AWS Secrets, etc)
# 2. Usar variables de entorno del sistema
# 3. Rotar keys regularmente
```

### Privacidad

✅ **Todos los datos se almacenan localmente:**
- BD SQLite: `/backend/data/app.db`
- Grafo: Archivo JSON
- Sin conexión a servidores externos (excepto Groq API para LLM)

---

## 📚 Documentación Técnica Adicional

- **[GRAPH_RAG_INTEGRATION_README.md](GRAPH_RAG_INTEGRATION_README.md)** 
  - Cómo funciona el reranking con grafo
  - Arquitectura detallada
  - Parámetros configurables

- **[backend/KNOWLEDGE_GRAPH_README.md](backend/KNOWLEDGE_GRAPH_README.md)**
  - Cómo generar grafos desde PDFs
  - Estructura del JSON
  - Ejemplos de uso

- **[backend/services/rag_service.py](backend/services/rag_service.py)**
  - Código fuente búsqueda híbrida
  - Implementación BM25

- **[backend/services/graph_service.py](backend/services/graph_service.py)**
  - Código fuente servicios del grafo
  - Algoritmos de reranking

---

## 💡 Casos de Uso

✅ **Asesoramiento laboral**: "¿Puedo ser despedido sin causa?"  
✅ **Derechos del trabajador**: "¿Cuál es el sueldo mínimo?"  
✅ **Obligaciones empresariales**: "¿Cómo hago un contrato?"  
✅ **Resolución de conflictos**: "¿A dónde ir si hay un conflicto?"  
✅ **Información legal**: "¿Qué es un feriado compensatorio?"

---

## 🤝 Para Desarrolladores

### Agregar PDFs Nuevos

```bash
# 1. Generar grafo
cd backend
python build_knowledge_graph.py /ruta/documento.pdf --stats

# 2. Cargar en CLI
💬 Tu pregunta: cargar /ruta/documento.pdf

# 3. Probar
💬 Tu pregunta: docs
```

### Personalizar el Sistema

**Aumentar precisión:**
- Ajustar `boost_factor` en reranking (0.2 → 0.5)
- Aumentar `top_k` de 3 a 5-10

**Más contexto:**
- Aumentar `max_entities` en enriquecimiento

**Nuevas entidades:**
- Editar prompt en `build_knowledge_graph.py` línea 180

---

## 📈 Estadísticas Actuales

- **Total de documentos**: 320 chunks
- **Nodos del grafo**: 54 entidades
- **Relaciones**: 80 conexiones
- **Densidad**: 1.48 edges por nodo
- **Cobertura**: 100% del PDF original

### Entidades por Tipo

| Tipo | Cantidad | Ejemplos |
|------|----------|----------|
| Actores | 37 | Dirección del Trabajo, personas |
| Conceptos | 12 | Derechos, obligaciones, leyes |
| Derechos | 3 | Descanso, feriado, etc |
| Documentos | 1 | Código del Trabajo |
| Organismos | 1 | Instituciones |

---

## 📞 Soporte & Ayuda

| Problema | Solución |
|----------|----------|
| Script no arranca | `python --version` (debe ser 3.11+) |
| API key inválida | Regenera en https://console.groq.com |
| BD corrupta | `python scripts/init_db.py` |
| Grafo no carga | Verifica path: `ls -la articles-*.json` |
| Respuestas mal | Resetea: `reset-docs` en CLI |

**Recursos:**
- Groq Console: https://console.groq.com
- Python Docs: https://docs.python.org/3.11/
- SQLAlchemy: https://docs.sqlalchemy.org/

---

## 📝 Changelog

### v1.0 (25 Feb 2026) - Versión Final

✅ Sistema RAG completo con búsqueda híbrida  
✅ Grafo de conocimiento integrado (54 nodos, 80 relaciones)  
✅ Reranking automático basado en conexiones del grafo  
✅ CLI interactivo con historial y estadísticas  
✅ 320 documentos procesados y listos  
✅ Documentación técnica completa  
✅ Tests unitarios pasando  

---

## 🎉 ¡Listo para Empezar!

```bash
./run.sh
```

Luego escribe tu primera pregunta:

```
💬 Tu pregunta: ¿Cuáles son los derechos de un trabajador?
```

---

**Versión**: 1.0  
**Última actualización**: 25 de Febrero de 2026  
**Licencia**: Académica/Educativa  
**Contacto**: Rayzel (Proyecto de IA)
