"""
Modelos Pydantic para validación de requests/responses
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ===== CHAT =====
class ChatRequest(BaseModel):
    """Request para el endpoint de chat"""
    query: str = Field(..., min_length=1, max_length=1000, description="Pregunta del usuario")
    context: Optional[str] = Field(None, description="Contexto opcional (para testing)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "¿Cuál es mi derecho a descanso?",
                "context": "Artículo 65: El trabajador tendrá derecho a un día de descanso..."
            }
        }

class ChatResponse(BaseModel):
    """Response del endpoint de chat"""
    query: str
    response: str
    relevant_articles: Optional[list[str]] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "¿Cuál es mi derecho a descanso?",
                "response": "Según el Artículo 65...",
                "relevant_articles": ["Art. 65", "Art. 66"],
                "confidence": 0.92,
                "timestamp": "2026-02-25T12:30:00"
            }
        }

# ===== AUTENTICACION =====
class UserLogin(BaseModel):
    """Request para login"""
    email: str = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=6)

class UserRegister(BaseModel):
    """Request para registro"""
    email: str = Field(..., description="Email único")
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    """Response con datos del usuario"""
    id: int
    email: str
    full_name: Optional[str]
    created_at: datetime

class TokenResponse(BaseModel):
    """Response con token JWT"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
