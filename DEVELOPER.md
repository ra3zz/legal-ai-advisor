# 👨‍💻 Guía para Desarrolladores Externos

Este documento guía a desarrolladores nuevos a entender y trabajar con el proyecto Legal AI Advisor.

---

## 📚 Estructura de Documentación

### Para Empezar Rápido

1. **[QUICKSTART.md](QUICKSTART.md)** ← **COMIENZA AQUÍ**
   - Instalación en 30 segundos
   - Comandos básicos
   - Troubleshooting rápido

2. **[README.md](README.md)** ← Documentación Principal
   - Descripción general del sistema
   - Instalación paso a paso
   - Cómo funciona el sistema
   - Performance y configuración

### Documentación Técnica

3. **[GRAPH_RAG_INTEGRATION_README.md](GRAPH_RAG_INTEGRATION_README.md)** ← Arquitectura del Grafo
   - Cómo funciona el reranking
   - Algoritmos de búsqueda híbrida
   - Integración grafo + RAG
   - Parámetros configurables

4. **[backend/KNOWLEDGE_GRAPH_README.md](backend/KNOWLEDGE_GRAPH_README.md)** ← Extracción de Grafos
   - Cómo generar grafos desde PDFs
   - Estructura JSON del grafo
   - Extracción de entidades
   - Ejemplos de uso

---

## 🗂️ Estructura del Proyecto

```
AI_Codigo_trabajo/
│
├── 📄 QUICKSTART.md                      # Inicio rápido (30s)
├── 📘 README.md                          # Documentación completa
├── 🔗 GRAPH_RAG_INTEGRATION_README.md    # Arquitectura técnica
│
├── 🚀 run.sh                             # Script de ejecución principal
│
├── 📦 articles-117137_galeria_02.pdf     # PDF origen
├── 📊 articles-117137_galeria_02_graph.json   # Grafo procesado
│
└── backend/
    ├── 🟢 cli_chat.py                    # PUNTO DE ENTRADA - CLI interactivo
    │   └── Funciones principales:
    │       • CLIChat.__init__()      - Inicializa BD + grafo
    │       • chat()                  - Procesa preguntas
    │       • run()                   - Loop principal
    │
    ├── 🔵 build_knowledge_graph.py       # Generador de grafos desde PDFs
    │   └── Funciones principales:
    │       • KnowledgeGraphBuilder.extract_pdf()
    │       • extract_entities_and_relations()
    │
    ├── services/                         # Lógica de negocio
    │   ├── rag_service.py                # Búsqueda híbrida
    │   │   • search_hybrid()             - Busca embeddings + BM25
    │   │   • bm25_score()                - Ranking por keywords
    │   │
    │   ├── graph_service.py              # Grafo de conocimiento
    │   │   • load_graph()                - Carga JSON
    │   │   • rerank_documents_with_graph() - Mejora ranking con grafo
    │   │   • enrich_context()            - Añade contexto
    │   │
    │   └── groq_service.py               # Integración Groq LLM
    │       • embed_text()                - Genera embeddings
    │       • chat_with_doc()             - Llamadas LLM
    │
    ├── database/                         # Persistencia
    │   ├── database.py                   # Conexión SQLAlchemy
    │   └── models.py                     # ORM Document, User
    │
    ├── config/settings.py                # Configuración centralizada
    │
    ├── requirements.txt                  # Dependencias Python
    ├── .env                              # Variables de entorno (NO comitear)
    │
    ├── 🧪 test_suite.py                  # Tests unitarios
    ├── 🧪 test_rag.py                    # Tests RAG manuales
    ├── 🔧 reset_db.py                    # Script limpiar BD
    │
    ├── scripts/init_db.py                # Inicializar BD
    ├── data/app.db                       # Base de datos SQLite
    └── venv/                             # Virtual environment
        └── [paquetes Python instalados]
```

---

## 🔄 Flujo de Ejecución

### Secuencia Completa (De Usuario a Respuesta)

```
Usuario: "¿Qué derechos tiene un trabajador?"
                    ↓
         cli_chat.py → chat()
                    ↓
    1. RAGService.search_hybrid(query)
       • Genera embedding de query
       • Busca por similitud (70% embeddings)
       • Busca por keywords BM25 (30%)
       • Retorna top-3 documentos
                    ↓
    2. GraphService.rerank_documents_with_graph()
       • Extrae entidades de query
       • Busca en grafo conexiones
       • Calcula boost por conectividad
       • Reordena documentos
                    ↓
    3. GraphService.enrich_context()
       • Extrae entidades relevantes
       • Obtiene relaciones del grafo
       • Formatea como contexto
                    ↓
    4. GroqService.chat_with_doc()
       • Llama Groq LLM con contexto
       • llama-3.3-70b-versatile
       • Retorna respuesta
                    ↓
    5. Formatear y mostrar
       • Respuesta en terminal
       • Mostrar fuentes
       • Guardar en historial
```

---

## 🔧 Componentes Clave

### 1. RAGService (rag_service.py)

**Responsabilidad**: Búsqueda híbrida de documentos

```python
# Usar:
results = RAGService.search_hybrid(query, top_k=3, use_graph=True)

# Retorna:
[
    {
        'text': 'contenido del documento...',
        'score': 0.412,
        'emb_score': 0.55,
        'bm25_score': 0.20,
        'graph_boost': 0.067
    },
    ...
]
```

**Parámetros**:
- `query`: Texto a buscar
- `top_k`: Documentos a retornar (default: 5)
- `use_graph`: Aplicar reranking (default: True)

### 2. GraphService (graph_service.py)

**Responsabilidad**: Gestionar grafo de conocimiento

```python
# Usar:
from services.graph_service import graph_service

graph_service.load_graph("ruta/grafo.json")
entities = graph_service.extract_entities_from_text(texto)
related = graph_service.get_related_nodes(node_id, max_depth=2)
context = graph_service.enrich_context(query, results)
```

**Métodos principales**:
- `load_graph()`: Carga JSON del grafo
- `find_nodes_by_text()`: Busca entidades
- `rerank_documents_with_graph()`: Mejora ranking
- `enrich_context()`: Añade información del grafo

### 3. GroqService (groq_service.py)

**Responsabilidad**: Integración con Groq LLM

```python
# Usar:
embedding = embed_text(texto)  # Vector 384-dims
response = chat_with_doc(query, contexto)  # Respuesta LLM
```

---

## 📝 Workflow: Agregar Función Nueva

### Ejemplo: Buscar por tipo de entidad

```python
# 1. Agregar método en GraphService (graph_service.py)
def find_entities_by_type(self, entity_type: str) -> List[Dict]:
    """Encuentra todas las entidades de un tipo"""
    results = []
    for node_id, node in self.nodes.items():
        if node.get('type') == entity_type:
            results.append({'id': node_id, **node})
    return results

# 2. Usar en cli_chat.py
elif query.lower().startswith("tipo:"):
    tipo = query[5:].strip()
    entities = graph_service.find_entities_by_type(tipo)
    print(f"Entidades de tipo '{tipo}':")
    for e in entities:
        print(f"  • {e['label']}: {e['description']}")

# 3. Testear
# 💬 Tu pregunta: tipo:actor
# Entidades de tipo 'actor':
#   • Dirección del Trabajo: Organismo gubernamental
#   • ...
```

---

## 🧪 Testing

### Ejecutar Tests

```bash
cd backend
python test_suite.py

# Output:
# ✅ Test 1: RAG Search - PASSED
# ✅ Test 2: Embeddings - PASSED
# ✅ Test 3: Graph Loading - PASSED
```

### Agregar Test Nuevo

```python
# En test_suite.py
def test_custom_feature():
    """Test para nueva funcionalidad"""
    from services.rag_service import RAGService
    
    results = RAGService.search_hybrid("test query", top_k=1)
    assert len(results) > 0, "Debería retornar al menos 1 resultado"
    assert 'score' in results[0], "Resultado debería tener 'score'"
    
    print("✅ Test Custom Feature - PASSED")
```

---

## 🔍 Debugging

### Logs y Debug

```python
# Habilitar debug en rag_service.py
print(f"[DEBUG] Query: {query}")
print(f"[DEBUG] Top-3 results: {len(results)} encontrados")
print(f"[DEBUG] Score promedio: {sum(r['score'] for r in results)/len(results):.2f}")
```

### Ver Estado del Grafo

```bash
💬 Tu pregunta: grafo

# Muestra:
# - Nodos: 54
# - Relaciones: 80
# - Densidad: 1.48
# - Top connected: ...
```

### Inspeccionar BD

```bash
cd backend
sqlite3 data/app.db

sqlite> SELECT COUNT(*) FROM document;
320

sqlite> SELECT title FROM document LIMIT 3;
articles-117137_galeria_02 - Parte 1/320
articles-117137_galeria_02 - Parte 2/320
```

---

## 📊 Datos Actuales

### Base de Datos (SQLite)

| Tabla | Columnas | Registros |
|-------|----------|-----------|
| Document | id, title, content, source, embedding, article_number | 320 |
| User | (si aplica) | - |

### Grafo JSON

| Métrica | Valor |
|---------|-------|
| Nodos | 54 |
| Relaciones | 80 |
| Densidad | 1.48 edges/nodo |
| Archivo | 28 KB |

---

## 🚀 Deployment / Próximas Fases

### Fase 1: Mejoras Actuales (Recomendado)
- [ ] Mejorar prompt de extracción de entidades
- [ ] Agregar soporte para múltiples PDFs
- [ ] Interfaz web (FastAPI + React)

### Fase 2: Escalabilidad
- [ ] Dockerizar aplicación
- [ ] Deploy a Railway/Render
- [ ] Agregar auth básica

### Fase 3: Funcionalidades Avanzadas
- [ ] Graph embeddings (GNN)
- [ ] Multi-hop reasoning
- [ ] Query reformulation

---

## 📞 Preguntas Frecuentes para Devs

**P: ¿Cómo agregar un nuevo servicio?**  
R: Crear archivo `services/mi_servicio.py` y importar en `cli_chat.py`

**P: ¿Cómo cambiar el LLM de Groq a otro?**  
R: Reemplazar lógica en `groq_service.py` con nueva API

**P: ¿Cómo procesar otro PDF?**  
R: `python build_knowledge_graph.py /ruta/pdf.pdf --stats`

**P: ¿Por qué el scoring es 0.7 embeddings + 0.3 BM25?**  
R: Balance empírico entre semántica y exactitud. Ajustable en `rag_service.py`

**P: ¿Cómo agregar más contexto del grafo?**  
R: Aumentar `max_entities` en `graph_service.enrich_context()`

---

## 🔐 Consideraciones de Seguridad

### En Desarrollo
- `.env` no se comitea (en `.gitignore`)
- API keys en variables de entorno
- BD local, sin exposición externa

### En Producción
- Usar AWS Secrets Manager o similar
- Rate limiting en API
- Encriptación de datos sensibles
- Auditoría de accesos

---

## 📖 Lectura Recomendada

1. **Empezar**:
   - [QUICKSTART.md](QUICKSTART.md) - 5 minutos
   - [README.md](README.md) - 15 minutos

2. **Entender Arquitectura**:
   - [GRAPH_RAG_INTEGRATION_README.md](GRAPH_RAG_INTEGRATION_README.md) - 20 minutos
   - [backend/KNOWLEDGE_GRAPH_README.md](backend/KNOWLEDGE_GRAPH_README.md) - 15 minutos

3. **Código Fuente**:
   - `backend/cli_chat.py` - Punto de entrada
   - `backend/services/rag_service.py` - Búsqueda
   - `backend/services/graph_service.py` - Grafo

---

## 💡 Tips para Contribuir

1. **Testing First**: Escribe tests antes de código
2. **Documentación**: Comenta código complejo
3. **Commits Atómicos**: Un cambio por commit
4. **PR Reviews**: Pedir review antes de merge

---

**¿Listo para contribuir?** Comienza por [QUICKSTART.md](QUICKSTART.md) 🚀

