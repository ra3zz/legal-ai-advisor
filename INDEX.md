# 📖 Índice del Proyecto - Legal AI Advisor

Bienvenido a **Legal AI Advisor**, un sistema de inteligencia artificial para asesoramiento laboral.

Este archivo te ayuda a encontrar la documentación que necesitas.

---

## 🎯 ¿Qué Quieres Hacer?

### 🚀 "Quiero ejecutar el sistema AHORA"
→ Ve a **[QUICKSTART.md](QUICKSTART.md)** (30 segundos)

### 📚 "Quiero entender cómo funciona"
→ Lee **[README.md](README.md)** (15 minutos)

### 💻 "Soy programador, quiero contribuir"
→ Mira **[DEVELOPER.md](DEVELOPER.md)** (20 minutos)

### 🔬 "Quiero entender la arquitectura técnica"
→ Revisa **[GRAPH_RAG_INTEGRATION_README.md](GRAPH_RAG_INTEGRATION_README.md)** (técnico)

### 📊 "Quiero generar un grafo desde otro PDF"
→ Consulta **[backend/KNOWLEDGE_GRAPH_README.md](backend/KNOWLEDGE_GRAPH_README.md)**

---

## 📑 Documentación Completa

| Archivo | Para Quién | Tiempo | Contenido |
|---------|-----------|--------|-----------|
| [QUICKSTART.md](QUICKSTART.md) | Todos | 2 min | Ejecutar en 30 seg |
| [README.md](README.md) | Usuarios | 15 min | Guía general completa |
| [DEVELOPER.md](DEVELOPER.md) | Devs | 20 min | Cómo contribuir |
| [GRAPH_RAG_INTEGRATION_README.md](GRAPH_RAG_INTEGRATION_README.md) | Devs/Arch | 30 min | Arquitectura del grafo |
| [backend/KNOWLEDGE_GRAPH_README.md](backend/KNOWLEDGE_GRAPH_README.md) | ML Eng | 20 min | Extrayendo grafos |

---

## 📂 Estructura del Repositorio

```
AI_Codigo_trabajo/
├── run.sh                    🚀 EJECUTAR AQUI
├── README.md                 📘 Documentación principal
├── QUICKSTART.md             🏃 Inicio rápido
├── DEVELOPER.md              💻 Para desarrolladores
├── INDEX.md                  📖 Este archivo
│
├── articles-117137_galeria_02.pdf          # PDF original
├── articles-117137_galeria_02_graph.json   # Grafo procesado
│
└── backend/
    ├── cli_chat.py                   # 🟢 Interfaz CLI
    ├── build_knowledge_graph.py      # Generador de grafos
    ├── services/                      # Lógica (RAG, Grafo, Groq)
    ├── database/                      # Base de datos
    ├── scripts/                       # Utilidades
    ├── tests/                         # Tests
    └── data/app.db                    # 💾 BD SQLite
```

---

## 🎯 Roadmap Visual

```
USUARIO NUEVO
    ↓
1. Lee QUICKSTART.md (2 min)
    ↓
2. Ejecuta: ./run.sh
    ↓
3. Haz una pregunta
    ↓
4. Si quieres entender más:
    ├─→ README.md (entender proyecto)
    ├─→ DEVELOPER.md (contribuir)
    └─→ GRAPH_RAG_INTEGRATION_README.md (arquitectura)
```

---

## ⚡ Quick Commands

```bash
# Ejecutar
./run.sh

# Limpiar base de datos
cd backend && python reset_db.py

# Generar grafo desde PDF
python build_knowledge_graph.py /ruta/pdf.pdf --stats

# Ejecutar tests
python test_suite.py

# Ver grafo actual
# (Desde CLI: escribir "grafo")
```

---

## 🔑 Conceptos Clave

### Búsqueda Híbrida
- 70% embeddings (semántica)
- 30% BM25 (keywords exactos)
- Retorna documentos ordenados por relevancia

### Grafo de Conocimiento
- 54 entidades (actores, conceptos, derechos)
- 80 relaciones entre entidades
- Se usa para **reranking** y enriquecimiento de contexto

### Reranking con Grafo
- Detecta entidades en la pregunta
- Busca documentos con entidades conectadas
- Boostadt score si hay conexiones
- Mejora relevancia de resultados

### LLM Expert
- Groq llama-3.3-70b-versatile
- Genera respuestas basadas en contexto
- API gratis y rápida

---

## 📊 Estadísticas Actuales

- **Documentos**: 320 chunks del Código del Trabajo
- **Grafo**: 54 nodos, 80 relaciones
- **BD**: SQLite local, ~50 MB
- **LLM**: Groq (gratis, rápido)
- **Tiempo por pregunta**: ~2.2 segundos

---

## 🤔 FAQ Rápido

**P: ¿Necesito internet?**  
R: Solo para Groq API. La BD y grafo son locales.

**P: ¿Necesito una API key?**  
R: Sí, de Groq (gratis en console.groq.com)

**P: ¿Funciona offline?**  
R: Sí, excepto para generar respuestas LLM (necesita Groq)

**P: ¿Puedo usar otro PDF?**  
R: Sí, usa: `cargar /ruta/pdf.pdf` en el CLI

**P: ¿Cómo hago un grafo del nuevo PDF?**  
R: `python build_knowledge_graph.py /ruta/pdf.pdf`

**P: ¿Puedo cambiar el sistema?**  
R: Sí, ve a DEVELOPER.md para contribuir

---

## 🚀 Los Próximos Pasos

1. **Ejecuta**: `./run.sh`
2. **Espera** a que se configure
3. **Escribe** tu primera pregunta
4. **Disfruta** las respuestas inteligentes

---

## 📞 Ayuda

- **Errores técnicos**: Ver [QUICKSTART.md#Problemas](QUICKSTART.md)
- **Más info**: [README.md](README.md)
- **Arquitectura**: [GRAPH_RAG_INTEGRATION_README.md](GRAPH_RAG_INTEGRATION_README.md)
- **Desarrollo**: [DEVELOPER.md](DEVELOPER.md)

---

## 🎉 ¡Empecemos!

**El comando más importante:**

```bash
./run.sh
```

O si estás en Windows/WSL:

```bash
bash run.sh
```

¿Listo? 🚀
