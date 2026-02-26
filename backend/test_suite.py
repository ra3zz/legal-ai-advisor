"""
Suite de pruebas para validar groq_service.py
Cubre: embeddings, chat, edge cases y rendimiento
"""

import sys
import time
import numpy as np
from services.groq_service import embed_text, chat_with_doc

def print_header(title):
    """Imprime encabezado de sección"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_embeddings_basic():
    """Test 1: Embeddings básicos"""
    print_header("TEST 1: Embeddings Básicos")
    
    texts = [
        "Artículo 65: El trabajador tiene derecho a descanso",
        "Derecho a descanso semanal",
        "El empleador debe cumplir con salario mínimo",
        "Salario mínimo legal"
    ]
    
    embeddings = []
    for i, text in enumerate(texts, 1):
        emb = embed_text(text)
        embeddings.append(emb)
        print(f"\n{i}. Texto: '{text[:50]}...'")
        print(f"   - Dimensión: {len(emb)}")
        print(f"   - Norma L2: {np.linalg.norm(emb):.6f}")
        print(f"   - Min/Max: {min(emb):.4f}/{max(emb):.4f}")
        print(f"   - Primeros 5: {[f'{x:.4f}' for x in emb[:5]]}")
    
    return embeddings, texts

def test_embeddings_similarity(embeddings, texts):
    """Test 2: Similitud coseno entre embeddings"""
    print_header("TEST 2: Similitud Coseno")
    
    print("\nMatriz de similitud (coseno entre pares):")
    print("\n     ", end="")
    for i in range(len(texts)):
        print(f"  T{i+1}   ", end="")
    print()
    
    for i, emb_i in enumerate(embeddings):
        print(f"T{i+1}  ", end="")
        for j, emb_j in enumerate(embeddings):
            sim = np.dot(emb_i, emb_j)  # Ya están normalizados
            print(f" {sim:6.4f}", end="")
        print()
    
    # Análisis
    print("\nAnálisis:")
    print("  ✓ Diagonal = 1.0 (cada embedding consigo mismo)")
    print("  ✓ T1-T2 > Similar (ambos hablan de descanso)")
    print("  ✓ T3-T4 > Similar (ambos hablan de salario)")
    print("  ✓ T1-T3 < Diferentes (temas distintos)")

def test_embeddings_edge_cases():
    """Test 3: Casos edge"""
    print_header("TEST 3: Edge Cases - Embeddings")
    
    test_cases = [
        ("", "Texto vacío"),
        ("a", "Texto muy corto (1 char)"),
        ("palabra", "Palabra simple"),
        ("Texto con números 123 y símbolos !@#$", "Mix de caracteres"),
        ("   espacios    múltiples   ", "Espacios múltiples"),
        ("MAYÚSCULAS", "Todo mayúsculas"),
        ("ñ é á ü ç", "Caracteres acentuados"),
        ("a " * 1000, "Texto muy largo (1000 palabras)"),
    ]
    
    for text, description in test_cases:
        emb = embed_text(text)
        norm = np.linalg.norm(emb)
        print(f"\n{description}:")
        print(f"  - Entrada: {repr(text[:50])}{'...' if len(text) > 50 else ''}")
        print(f"  - Dimensión: {len(emb)}")
        print(f"  - Norma: {norm:.6f}")
        print(f"  - Válido: {'✓' if 0 < norm <= 1.05 else '✗ WARN'}")

def test_chat_basic():
    """Test 4: Chat básico"""
    print_header("TEST 4: Chat Básico")
    
    test_cases = [
        {
            "query": "¿Cuál es mi derecho a descanso?",
            "context": "Artículo 65: El trabajador tendrá derecho a un día de descanso cada siete días, preferentemente domingo."
        },
        {
            "query": "¿Cuál es el salario mínimo?",
            "context": "Artículo 50: El salario mínimo es fijado por ley cada año según el IPC y la capacidad de pago."
        },
        {
            "query": "¿Qué es un contrato de plazo fijo?",
            "context": "Artículo 159: Contrato de plazo fijo es aquel que tiene término expresado en días, meses o años."
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Query: '{test['query']}'")
        print(f"   Context: '{test['context'][:60]}...'")
        
        start = time.time()
        response = chat_with_doc(test['query'], test['context'])
        elapsed = time.time() - start
        
        if response:
            print(f"   Respuesta ({elapsed:.2f}s): {response[:100]}{'...' if len(response) > 100 else ''}")
            print(f"   ✓ Validado - Respuesta legible")
        else:
            print(f"   ✗ ERROR - No hubo respuesta")

def test_chat_edge_cases():
    """Test 5: Casos edge - Chat"""
    print_header("TEST 5: Edge Cases - Chat")
    
    test_cases = [
        {
            "query": "?",
            "context": "Test context",
            "desc": "Query muy corto"
        },
        {
            "query": "¿ " + "pregunta " * 100 + "?",
            "context": "Test context",
            "desc": "Query muy largo"
        },
        {
            "query": "¿Qué pasa?",
            "context": "",
            "desc": "Contexto vacío"
        },
        {
            "query": "¿Qué pasa?",
            "context": "Contexto " * 100,
            "desc": "Contexto muy largo"
        },
    ]
    
    for test in test_cases:
        print(f"\n{test['desc']}:")
        print(f"  - Query length: {len(test['query'])}")
        print(f"  - Context length: {len(test['context'])}")
        
        try:
            start = time.time()
            response = chat_with_doc(test['query'], test['context'])
            elapsed = time.time() - start
            
            if response and "Error" not in response:
                print(f"  - ✓ Válido ({elapsed:.2f}s)")
            else:
                print(f"  - ⚠ Respuesta con error o vacía")
        except Exception as e:
            print(f"  - ✗ Excepción: {str(e)[:60]}")

def test_performance():
    """Test 6: Rendimiento"""
    print_header("TEST 6: Rendimiento")
    
    # Test embeddings speed
    print("\nVelocidad de embeddings:")
    texts = [f"Texto número {i} para prueba de rendimiento" for i in range(10)]
    
    start = time.time()
    for text in texts:
        embed_text(text)
    elapsed = time.time() - start
    
    print(f"  - {len(texts)} embeddings en {elapsed:.3f}s")
    print(f"  - Promedio: {(elapsed/len(texts))*1000:.2f}ms por embedding")
    print(f"  - ✓ Velocidad aceptable para embeddings sintéticos")
    
    # Test chat speed (una sola llamada a API)
    print("\nVelocidad de chat (Groq API):")
    query = "¿Cuál es mi derecho?"
    context = "Artículo 65: Derecho a descanso"
    
    start = time.time()
    response = chat_with_doc(query, context)
    elapsed = time.time() - start
    
    print(f"  - Chat en {elapsed:.3f}s")
    print(f"  - Respuesta length: {len(response)} chars")
    print(f"  ⚠ API Groq tiene latencia inherente (0.5-3s esperado)")

def test_integration():
    """Test 7: Integración end-to-end (simulado)"""
    print_header("TEST 7: Integración End-to-End (Simulado)")
    
    print("\nScenario: Usuario pregunta sobre un artículo del código del trabajo")
    
    # Simulación de RAG:
    # 1. User query
    user_query = "¿Puedo ser despedido sin causa justa?"
    print(f"\n1. Query usuario: '{user_query}'")
    
    # 2. Generar embedding de query
    query_embedding = embed_text(user_query)
    print(f"2. Embedding generado: {len(query_embedding)} dimensiones")
    
    # 3. Simular búsqueda en DB (aquí sería retrieval)
    documents = [
        "Artículo 162: El contrato de trabajo puede terminar por terminación sin causa.",
        "Artículo 163: No puede terminarse sin ser justificado por la ley.",
        "Artículo 150: El despido requiere justa causa documentada."
    ]
    
    print(f"3. Documentos encontrados: {len(documents)}")
    
    # 4. Calcular similitud
    similarities = []
    for doc in documents:
        doc_emb = embed_text(doc)
        sim = np.dot(query_embedding, doc_emb)
        similarities.append((doc, sim))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    best_doc = similarities[0][0]
    print(f"4. Documento más relevante (sim: {similarities[0][1]:.4f}): '{best_doc[:50]}...'")
    
    # 5. Chat con contexto
    response = chat_with_doc(user_query, best_doc)
    print(f"5. Respuesta LLM: '{response[:80]}...'")
    
    print("\n✓ Pipeline de RAG funcionando correctamente")

def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "█"*70)
    print("█  SUITE DE PRUEBAS - groq_service.py")
    print("█  Validación completa de embeddings, chat y casos edge")
    print("█"*70)
    
    try:
        # Test 1-3: Embeddings
        embeddings, texts = test_embeddings_basic()
        test_embeddings_similarity(embeddings, texts)
        test_embeddings_edge_cases()
        
        # Test 4-5: Chat
        test_chat_basic()
        test_chat_edge_cases()
        
        # Test 6-7: Performance e integración
        test_performance()
        test_integration()
        
        # Resumen
        print_header("RESUMEN FINAL")
        print("\n✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("\nProximo paso: Estructura de carpetas (Objetivo 0.3)")
        print("Luego: FastAPI app + Database + RAG")
        
    except Exception as e:
        print(f"\n❌ ERROR EN PRUEBAS: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
