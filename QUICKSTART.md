# 🚀 Quick Start - Legal AI Advisor

**Inicia en 30 segundos:**

```bash
chmod +x run.sh
./run.sh
```

El script:
- ✅ Verifica Python 3.11+
- ✅ Crea virtual environment
- ✅ Instala dependencias
- ✅ Configura API key
- ✅ Inicializa BD
- ✅ Inicia CLI

---

## 🔑 Antes de Empezar

1. **Obtén API Key Gratis:**
   - Ve a: https://console.groq.com
   - Crea una cuenta (5 minutos)
   - Genera una API key
   - Copia la key

2. **Durante ejecución:**
   - El script pedirá que edites `backend/.env`
   - Pega: `GROQ_API_KEY=gsk_...`
   - Guarda (Ctrl+X, Y, Enter)
   - Presiona ENTER

---

## 💬 Primer Uso

Una vez iniciado, prueba:

```
💬 Tu pregunta: ¿Qué derechos tiene un trabajador?

✅ 3 documento(s) encontrado(s)
   • Doc (relevancia: 41.2%) 📊+6.7%
   
Respuesta:
Un trabajador tiene derecho a: remuneración, descanso...
```

---

## 📋 Comandos

```
?              Ayuda
docs           Listar documentos
grafo          Stats del grafo
historial      Preguntas anteriores
cargar <ruta>  Cargar PDF nuevo
reset-docs     Limpiar BD
salir          Cerrar
```

---

## ❓ Problemas

**"Python 3.11 not found"**
```bash
apt install python3.11  # Linux
brew install python@3.11  # macOS
```

**"GROQ_API_KEY not found"**
- Verifica: `cat backend/.env`
- Debe tener: `GROQ_API_KEY=gsk_...`

**"Database locked"**
```bash
cd backend
rm data/app.db
python scripts/init_db.py
```

---

## 📚 Más Info

- **[README.md](README.md)** - Documentación completa
- **[GRAPH_RAG_INTEGRATION_README.md](GRAPH_RAG_INTEGRATION_README.md)** - Cómo funciona el grafo
- **[backend/KNOWLEDGE_GRAPH_README.md](backend/KNOWLEDGE_GRAPH_README.md)** - Generar grafo desde PDFs

---

**¡Listo!** Ejecuta: `./run.sh` 🎉
