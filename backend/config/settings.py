"""
Configuración centralizada del backend
Variables de entorno, rutas, constantes
"""
import os
from pathlib import Path

class Settings:
    """Configuración de la aplicación"""
    
    # Directorios
    BASE_DIR = Path(__file__).parent.parent
    DATABASE_DIR = BASE_DIR / "data"
    DATABASE_URL = f"sqlite:///{DATABASE_DIR}/app.db"
    
    # API
    API_TITLE = "Legal AI Advisor - Código del Trabajo"
    API_VERSION = "0.1.0"
    API_DESCRIPTION = "RAG-based legal advisor for Chilean labor law"
    
    # Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_CHAT_MODEL = "llama-3.3-70b-versatile"
    
    # Seguridad
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # CORS
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
    ]
    
    # Chunking
    CHUNK_SIZE = 1000  # Caracteres
    CHUNK_OVERLAP = 200
    
    # Embeddings
    EMBEDDING_DIMENSION = 384

settings = Settings()
