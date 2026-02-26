"""
Configuración de SQLAlchemy y conexión a base de datos
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings
from pathlib import Path

# Crear directorio de datos si no existe
Path(settings.DATABASE_DIR).mkdir(parents=True, exist_ok=True)

# Engine de SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Necesario para SQLite
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para modelos ORM
Base = declarative_base()

# Dependency para FastAPI
def get_db():
    """Dependency injection para obtener sesión de BD"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
