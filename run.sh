#!/bin/bash
# ⚖️ Legal AI Advisor - Script de Ejecución Principal
# Este script configura todo automáticamente e inicia el sistema

set -e  # Exit on error

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'  # No Color

# Directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Header
echo -e "${BOLD}${BLUE}"
echo "════════════════════════════════════════════════════════════════"
echo "⚖️  LEGAL AI ADVISOR - Sistema de Asesoramiento Laboral"
echo "════════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo ""

# ===== PASO 1: Verificar Python =====
echo -e "${BLUE}[1/6]${NC} ${BOLD}Verificando Python 3.11+${NC}"
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python no encontrado. Instala Python 3.11+${NC}"
    exit 1
fi

# Obtener versión
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

PYTHON_VER=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VER | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VER | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
    echo -e "${RED}❌ Python $PYTHON_VER encontrado, se requiere 3.11+${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VER OK${NC}\n"

# ===== PASO 2: Verificar estructura =====
echo -e "${BLUE}[2/6]${NC} ${BOLD}Verificando estructura del proyecto${NC}"

if [ ! -d "backend" ]; then
    echo -e "${RED}❌ Carpeta backend no encontrada${NC}"
    exit 1
fi

if [ ! -f "backend/requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt no encontrado${NC}"
    exit 1
fi

if [ ! -f "backend/cli_chat.py" ]; then
    echo -e "${RED}❌ cli_chat.py no encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Estructura OK${NC}\n"

# ===== PASO 3: Crear/Activar venv =====
echo -e "${BLUE}[3/6]${NC} ${BOLD}Configurando ambiente virtual${NC}"

VENV_PATH="backend/venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "   Creando virtual environment..."
    $PYTHON_CMD -m venv "$VENV_PATH"
    echo -e "${GREEN}✅ Virtual env creado${NC}"
else
    echo -e "${GREEN}✅ Virtual env existe${NC}"
fi

# Activar venv
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
elif [ -f "$VENV_PATH/Scripts/activate" ]; then  # Windows
    source "$VENV_PATH/Scripts/activate"
else
    echo -e "${RED}❌ No se pudo activar venv${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Ambiente activado${NC}\n"

# ===== PASO 4: Instalar dependencias =====
echo -e "${BLUE}[4/6]${NC} ${BOLD}Instalando dependencias${NC}"

pip install -q --upgrade pip

# Instalar desde requirements.txt
if pip install -q -r backend/requirements.txt 2>/dev/null; then
    echo -e "${GREEN}✅ Dependencias instaladas${NC}"
else
    echo -e "${YELLOW}⚠️  Error instalando algunas dependencias, continuando...${NC}"
fi

echo ""

# ===== PASO 5: Configurar .env =====
echo -e "${BLUE}[5/6]${NC} ${BOLD}Configurando API Key${NC}"

if [ ! -f "backend/.env" ]; then
    echo "   Creando archivo .env..."
    echo "GROQ_API_KEY=" > backend/.env
    echo -e "${YELLOW}⚠️  Archivo .env creado SIN API KEY${NC}"
    echo -e "${YELLOW}   📝 IMPORTANTE: Edita backend/.env y agrega tu Groq API Key${NC}"
    echo -e "${YELLOW}   🔑 Obtén una key GRATIS en: https://console.groq.com${NC}"
    echo ""
else
    # Verificar que tiene API key
    if grep -q "GROQ_API_KEY=" backend/.env; then
        API_VALUE=$(grep "GROQ_API_KEY=" backend/.env | cut -d'=' -f2)
        if [ -z "$API_VALUE" ]; then
            echo -e "${YELLOW}⚠️  API Key en blanco${NC}"
            echo -e "${YELLOW}   📝 Edita backend/.env y agrega tu key${NC}"
            echo ""
        else
            echo -e "${GREEN}✅ API Key configurada${NC}\n"
        fi
    fi
fi

# ===== PASO 6: Inicializar Base de Datos =====
echo -e "${BLUE}[6/6]${NC} ${BOLD}Inicializando base de datos${NC}"

if [ ! -f "backend/data/app.db" ]; then
    echo "   Primera ejecución detectada, inicializando BD..."
    if $PYTHON_CMD backend/scripts/init_db.py 2>/dev/null; then
        echo -e "${GREEN}✅ Base de datos inicializada${NC}"
    else
        echo -e "${YELLOW}⚠️  Advertencia en inicialización, continuando...${NC}"
    fi
else
    DB_SIZE=$(stat -f%z "backend/data/app.db" 2>/dev/null || stat -c%s "backend/data/app.db" 2>/dev/null || echo "?")
    echo -e "${GREEN}✅ Base de datos existe ($DB_SIZE bytes)${NC}"
fi

echo ""

# ===== LISTO - INICIAR CLI =====
echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 Sistema listo para iniciar${NC}"
echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${BOLD}Información del Sistema:${NC}"
echo "  • Python: $PYTHON_VER"
echo "  • Venv: $VENV_PATH"
echo "  • DB: backend/data/app.db"
echo "  • Grafo: articles-117137_galeria_02_graph.json"
echo ""

echo -e "${BOLD}${YELLOW}Próximos pasos:${NC}"
echo "  1. Si es la PRIMERA VEZ:"
echo "     → Edita: backend/.env"
echo "     → Agrega: GROQ_API_KEY=tu_api_key"
echo "     → Obtén key: https://console.groq.com"
echo ""
echo "  2. Luego:"
echo "     → Presiona ENTER para iniciar el chat"
echo ""
echo -e "${YELLOW}Comandos disponibles en el chat:${NC}"
echo "  ? → Ayuda"
echo "  docs → Ver documentos"
echo "  grafo → Estadísticas del grafo"
echo "  historial → Ver preguntas anteriores"
echo "  cargar <ruta> → Cargar un PDF nuevo"
echo "  reset-docs → Borrar documentos"
echo "  salir → Cerrar"
echo ""

read -p "Presiona ENTER para iniciar..."

# Iniciar CLI
echo ""
echo -e "${BLUE}⏳ Iniciando CLI...${NC}\n"

$PYTHON_CMD backend/cli_chat.py

echo ""
echo -e "${GREEN}Gracias por usar Legal AI Advisor 👋${NC}"
echo ""
