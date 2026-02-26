"""
Modelos ORM (Object-Relational Mapping)
Definen las tablas en la base de datos
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base
from datetime import datetime

class User(Base):
    """Modelo para usuarios"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    chat_histories = relationship("ChatHistory", back_populates="user")

class Document(Base):
    """Modelo para documentos (artículos del Código del Trabajo)"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255))  # Ej: "Codigo_del_Trabajo.pdf"
    article_number = Column(String(50), index=True)
    embedding = Column(Text)  # JSON serializado del vector (384 dims)
    chunk_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    chat_histories = relationship("ChatHistory", back_populates="document")

class ChatHistory(Base):
    """Modelo para historial de chat"""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    relevance_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="chat_histories")
    document = relationship("Document", back_populates="chat_histories")
