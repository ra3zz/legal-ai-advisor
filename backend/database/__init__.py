"""
Capa de acceso a datos
- database.py: Configuración SQLAlchemy
- models.py: Modelos ORM (Document, User, ChatHistory)
"""
from .database import engine, SessionLocal, Base

__all__ = ["engine", "SessionLocal", "Base"]
