"""
Servicio RAG (Retrieval-Augmented Generation) Mejorado
- Chunking inteligente (sin cortar palabras)
- Búsqueda híbrida: BM25 (palabras clave) + embeddings (semántica)
- Procesamiento de PDFs
- Ranking de relevancia
"""
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from services.groq_service import embed_text
from database.database import SessionLocal
from database.models import Document
import numpy as np

class RAGService:
    """Servicio RAG con búsqueda híbrida"""
    
    CHUNK_SIZE = 600  # Caracteres por chunk
    CHUNK_OVERLAP = 150  # Overlap entre chunks
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """
        Extrae texto de PDF usando PyPDF2 o fallback simple
        """
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            text = ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Página {i+1} ---\n{page_text}\n"
            return text.strip()
        except ImportError:
            raise Exception("PyPDF2 no instalado. Instala: pip install PyPDF2")
        except Exception as e:
            raise Exception(f"Error leyendo PDF: {e}")
    
    @staticmethod
    def chunk_text_intelligent(text: str, chunk_size: int = 600, overlap: int = 150) -> List[str]:
        """
        Divide texto en chunks SIN CORTAR PALABRAS
        - Divide por párrafos primero
        - Luego agrupa párrafos para alcanzar chunk_size
        - Mantiene overlap de párrafos
        """
        # Dividir por párrafos (doble salto de línea)
        paragraphs = re.split(r'\n\s*\n', text.strip())
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            # Si añadir este párrafo excede el límite y ya tenemos contenido
            if current_size + para_size > chunk_size and current_chunk:
                # Guardar chunk actual
                chunk_text = '\n\n'.join(current_chunk)
                if len(chunk_text) > 100:  # Filtrar muy pequeños
                    chunks.append(chunk_text)
                
                # Mantener overlap: últimos párrafos del chunk anterior
                overlap_paras = current_chunk[-1:] if len(current_chunk) > 1 else []
                current_chunk = overlap_paras + [para]
                current_size = sum(len(p) for p in current_chunk)
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Agregar último chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            if len(chunk_text) > 100:
                chunks.append(chunk_text)
        
        return chunks
    
    @staticmethod
    def bm25_score(query_terms: set, doc_text: str) -> float:
        """
        Calcula score BM25 simplificado
        Mide qué tan bien coinciden los términos de la query en el documento
        """
        doc_terms = set(re.findall(r'\w+', doc_text.lower()))
        matches = len(query_terms & doc_terms)
        
        if not query_terms:
            return 0.0
        
        # Score: cantidad de coincidencias normalizadas
        return matches / len(query_terms)
    
    @staticmethod
    def process_pdf(pdf_path: str, source_name: str = None) -> Dict:
        """
        Procesa PDF completo: extrae → chunking → embeddings → BD
        """
        db = None
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")
            
            source_name = source_name or Path(pdf_path).name
            print(f"📖 Procesando PDF: {source_name}")
            
            # Extractar
            print(f"   • Extrayendo texto...")
            text = RAGService.extract_text_from_pdf(pdf_path)
            print(f"   • {len(text)} caracteres extraídos")
            
            # Chunking inteligente
            print(f"   • Dividiendo en chunks...")
            chunks = RAGService.chunk_text_intelligent(text)
            print(f"   • {len(chunks)} chunks creados")
            
            # Guardar en BD con embeddings
            print(f"   • Generando embeddings...")
            db = SessionLocal()
            saved = 0
            
            for i, chunk in enumerate(chunks):
                try:
                    emb = embed_text(chunk)
                    doc = Document(
                        title=f"{source_name} - Parte {i+1}/{len(chunks)}",
                        content=chunk,
                        source=source_name,
                        chunk_index=i,
                        embedding=json.dumps(emb)
                    )
                    db.add(doc)
                    saved += 1
                    if (i + 1) % 5 == 0:
                        print(f"      {i+1}/{len(chunks)} procesados...")
                except Exception as chunk_err:
                    print(f"      ⚠️  Error en chunk {i+1}: {str(chunk_err)}")
                    continue
            
            db.commit()
            
            return {
                'success': True,
                'chunks_count': len(chunks),
                'documents_saved': saved,
                'message': f"✅ {saved} documentos guardados"
            }
        
        except Exception as e:
            if db:
                try:
                    db.rollback()
                except:
                    pass
            return {
                'success': False,
                'chunks_count': 0,
                'documents_saved': 0,
                'message': f"❌ Error: {str(e)}"
            }
        finally:
            if db:
                try:
                    db.close()
                except:
                    pass
    
    @staticmethod
    def search_hybrid(query: str, top_k: int = 5, use_graph: bool = True) -> List[Dict]:
        """
        Búsqueda HÍBRIDA: 70% embeddings semánticos + 30% BM25 (palabras clave)
        Opcionalmente usa RERANKING CON GRAFO para mejorar resultados
        
        Esto combina:
        - Embeddings: captura SIGNIFICADO (relevancia semántica)
        - BM25: captura PALABRAS EXACTAS (precisión léxica)
        - Grafo: mejora CONTEXTO y RELACIONES entre conceptos (opcional)
        """
        try:
            db = SessionLocal()
            documents = db.query(Document).all()
            db.close()
            
            if not documents:
                return []
            
            # Preparar query
            query_terms = set(re.findall(r'\w+', query.lower()))
            query_emb = embed_text(query)
            query_array = np.array(query_emb)
            
            scores = []
            
            for doc in documents:
                try:
                    if not doc.embedding:
                        continue
                    
                    # 1. Score embeddings (70%)
                    doc_emb = np.array(json.loads(doc.embedding))
                    emb_score = np.dot(query_array, doc_emb)
                    
                    # 2. Score BM25 (30%)
                    bm25_score = RAGService.bm25_score(query_terms, doc.content)
                    
                    # 3. Score combinado
                    combined = (0.7 * emb_score) + (0.3 * bm25_score)
                    
                    scores.append({
                        'doc': doc,
                        'score': combined,
                        'emb_score': emb_score,
                        'bm25_score': bm25_score
                    })
                except:
                    pass
            
            # Ordenar y retornar top-k
            scores.sort(key=lambda x: x['score'], reverse=True)
            
            results = []
            for item in scores[:top_k]:
                results.append({
                    'text': item['doc'].content,
                    'article': item['doc'].article_number,
                    'source': item['doc'].source,
                    'score': float(item['score']),
                    'emb_score': float(item['emb_score']),
                    'bm25_score': float(item['bm25_score'])
                })
            
            # RERANKING CON GRAFO (si está disponible)
            if use_graph:
                try:
                    from services.graph_service import graph_service
                    if graph_service.is_loaded:
                        results = graph_service.rerank_documents_with_graph(query, results, boost_factor=0.2)
                except:
                    pass
            
            return results
        
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return []

# Instancia global para usar en el CLI
rag_service = RAGService()
