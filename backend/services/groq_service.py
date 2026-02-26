"""
Módulo para conectar con Groq API
Contiene funciones para:
- Embeddings (convertir texto a números)
- Chat (conversación con LLM)
"""

import os
from pathlib import Path
from groq import Groq

# Cargar API key desde .env (mismo método que test_models.py)
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Inicializar cliente Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Modelo actual disponible en tu cuenta de Groq
GROQ_CHAT_MODEL = "llama-3.3-70b-versatile"


def embed_text(text: str) -> list[float]:
    """
    Genera un embedding (vector semántico) del texto usando hashing eficiente.
    
    Opción B: Sin dependencias externas - usa técnicas de TF-IDF sintético.
    - Tokeniza el texto
    - Mapea tokens a índices del vector usando hashing
    - Normaliza para similitud de coseno
    
    Entrada: text (str): Texto a convertir
    Salida: list[float]: Vector de 384 dimensiones (estándar en embeddings)
    """
    import hashlib
    import numpy as np
    
    try:
        embedding_dim = 384
        embedding = np.zeros(embedding_dim)
        
        # Tokenizar: dividir por espacios y caracteres especiales
        tokens = text.lower().split()
        
        for token in tokens:
            # Limpiar puntuación
            token = ''.join(c for c in token if c.isalnum())
            if len(token) > 0:
                # Hash determinístico del token → índice del vector
                hash_value = int(hashlib.md5(token.encode()).hexdigest(), 16)
                index = hash_value % embedding_dim
                # TF-IDF simple: incrementar la dimensión correspondiente
                embedding[index] += 1.0
        
        # Normalizar a norma unitaria (para similitud de coseno)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        else:
            # Texto vacío: retornar vector pequeño
            embedding[0] = 1.0
        
        return embedding.tolist()
    
    except Exception as e:
        print(f"❌ Error en embed_text: {e}")
        return [0.0] * 384  # Retornar vector fallback


def chat_with_doc(query: str, context: str) -> str:
    """
    Llama a Groq para generar una respuesta
    
    Entrada:
        query (str): Pregunta del usuario
        context (str): Contexto del PDF
    
    Salida:
        str: Respuesta del LLM
    """
    try:
        # Usar modelo ACTUAL de Groq (llama-3.3-70b-versatile)
        response = client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un abogado experto en Derecho Laboral Chileno. Responde basándose SOLO en el contexto proporcionado."
                },
                {
                    "role": "user",
                    "content": f"Contexto:\n{context}\n\nPregunta: {query}"
                }
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        response_text = response.choices[0].message.content
        return response_text
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return f"Error: {e}"


def chat_simple(prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
    """
    Chat simple con el LLM (sin contexto específico)
    
    Entrada:
        prompt (str): Prompt para el LLM
        temperature (float): Creatividad (0.0-1.0)
        max_tokens (int): Máximo de tokens a generar
    
    Salida:
        str: Respuesta del LLM
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    print("🧪 TEST: Probando Groq API con modelo ACTUAL...\n")
    
    # Test 1: Embeddings (Opción B - sintético)
    print("📊 TEST EMBEDDINGS (Opción B - Sintético):")
    text1 = "Artículo 65: El trabajador tendrá derecho a un día de descanso cada siete días"
    text2 = "Derecho a descanso semanal"
    
    emb1 = embed_text(text1)
    emb2 = embed_text(text2)
    
    print(f"  Texto 1: '{text1[:50]}...'")
    print(f"  Embedding dim: {len(emb1)} (primeros 5: {[f'{x:.4f}' for x in emb1[:5]]})")
    print(f"  Texto 2: '{text2}'")
    print(f"  Embedding dim: {len(emb2)} (primeros 5: {[f'{x:.4f}' for x in emb2[:5]]})")
    
    # Calcular similitud de coseno
    import numpy as np
    sim = np.dot(emb1, emb2)  # Ya están normalizados
    print(f"  Similitud coseno: {sim:.4f}\n")
    
    # Test 2: Chat
    print("🤖 TEST CHAT:")
    test_query = "¿Cuál es mi derecho a descanso?"
    test_context = "Artículo 65: El trabajador tendrá derecho a un día de descanso cada siete días, preferentemente domingo."
    
    response = chat_with_doc(test_query, test_context)
    print(f"Pregunta: {test_query}")
    print(f"Respuesta: {response}\n")
    
    print("✅ Test completado")
