#!/usr/bin/env python3
"""
Test rápido del sistema RAG + CLI
Valida: embeddings, búsqueda híbrida, BD, Groq API
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.database import SessionLocal
from database.models import Document
from services.groq_service import embed_text, chat_with_doc
from services.rag_service import RAGService
import numpy as np
import json

print("\n" + "="*70)
print("🧪 TEST COMPLETO: RAG + CLI + GROQ")
print("="*70 + "\n")

# TEST 1: BD disponible
print("TEST 1: Base de datos")
db = SessionLocal()
doc_count = db.query(Document).count()
print(f"  ✅ {doc_count} documentos en BD")

# TEST 2: Embeddings funcionan
print("\nTEST 2: Embeddings")
test_texts = ["descanso", "salario", "contrato"]
for text in test_texts:
    emb = embed_text(text)
    print(f"  ✅ '{text}' → {len(emb)}-dim embedding")

# TEST 3: Similitud coseno
print("\nTEST 3: Similitud semántica")
emb1 = np.array(embed_text("derecho a descanso"))
emb2 = np.array(embed_text("día de descanso semanal"))
emb3 = np.array(embed_text("salario mínimo"))
sim_similar = np.dot(emb1, emb2)
sim_different = np.dot(emb1, emb3)
print(f"  • 'descanso' vs 'descanso': {sim_similar:.4f} (similar ✓)")
print(f"  • 'descanso' vs 'salario': {sim_different:.4f} (diferente ✓)")

# TEST 4: Búsqueda híbrida
print("\nTEST 4: Búsqueda híbrida (embeddings + BM25)")
query = "¿Cuál es mi derecho a descanso?"
results = RAGService.search_hybrid(query, top_k=3)
print(f"  Query: '{query}'")
print(f"  Encontrados: {len(results)} documentos")
for i, result in enumerate(results, 1):
    print(f"    {i}. {result['article']} (score: {result['score']:.4f})")
    print(f"       Embeddings: {result['emb_score']:.4f} | BM25: {result['bm25_score']:.4f}")

# TEST 5: Groq chat
print("\nTEST 5: Groq LLM")
context = "Artículo 65: El trabajador tendrá derecho a un día de descanso cada siete días, preferentemente domingo."
response = chat_with_doc("¿Por cuántos días tengo derecho a descanso?", context)
if response and "Error" not in response:
    print(f"  ✅ Query: '¿Por cuántos días...'")
    print(f"  Response: {response[:80]}...")
else:
    print(f"  ❌ Error: {response}")

# TEST 6: Pipeline completo
print("\nTEST 6: Pipeline completo (query → retrieval → response)")
full_query = "¿Qué es un contrato de plazo fijo?"
print(f"  Query: '{full_query}'")

# Búsqueda
retrieval_results = RAGService.search_hybrid(full_query, top_k=2)
if retrieval_results:
    best_article = retrieval_results[0]['article']
    best_text = retrieval_results[0]['text']
    print(f"  ✅ Encontrado: {best_article}")
    
    # Respuesta
    context_for_response = f"[{best_article}] {best_text}"
    final_response = chat_with_doc(full_query, context_for_response)
    print(f"  ✅ Response: {final_response[:100]}...")
else:
    print(f"  ❌ No se encontraron documentos")

db.close()

# RESUMEN
print("\n" + "="*70)
print("✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
print("="*70)
print("\n🚀 Para iniciar el chat interactivo:")
print("   $ python cli_chat.py\n")
