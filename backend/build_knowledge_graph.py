#!/usr/bin/env python3
"""
Script para construir Grafo RAG desde un PDF
Input: PDF cualquiera
Output: JSON con estructura de grafo (nodes + edges)

Uso:
    python build_knowledge_graph.py documento.pdf
    python build_knowledge_graph.py documento.pdf --output grafo_custom.json
    python build_knowledge_graph.py documento.pdf --max-chunks 10 --stats
"""
import sys
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import timedelta

# Agregar backend a path
sys.path.insert(0, str(Path(__file__).parent))

from services.rag_service import RAGService
from services import groq_service
import argparse


class KnowledgeGraphBuilder:
    """Construye grafo de conocimiento desde PDF"""
    
    # Tiempo promedio por chunk (en segundos) basado en API Groq
    ESTIMATED_TIME_PER_CHUNK = 2.5  # Promedio de latencia Groq + procesamiento
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.chunks = []
        self.nodes = {}  # {id: {label, type, description}}
        self.edges = []  # [{source, target, relation, weight}]
        self.start_time = None
        self.chunk_times = []  # Para calcular promedio real
    
    def extract_pdf(self) -> bool:
        """Extrae texto del PDF"""
        print("\n📖 Extrayendo texto del PDF...")
        try:
            self.text = RAGService.extract_text_from_pdf(self.pdf_path)
            print(f"✅ {len(self.text)} caracteres extraídos")
            return True
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def estimate_time(self) -> Dict:
        """
        Estima el tiempo total del proceso
        
        Retorna:
            dict con tiempos estimados
        """
        if not self.chunks:
            return {"total_seconds": 0, "total_readable": "0 minutos"}
        
        # Estimar tiempo por fase
        extraction_time = 5  # segundos
        chunking_time = 2    # segundos
        processing_time = len(self.chunks) * self.ESTIMATED_TIME_PER_CHUNK
        cleanup_time = 3     # segundos
        save_time = 1        # segundos
        
        total_seconds = extraction_time + chunking_time + processing_time + cleanup_time + save_time
        
        # Convertir a formato legible
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        if hours > 0:
            readable = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            readable = f"{minutes}m {seconds}s"
        else:
            readable = f"{seconds}s"
        
        return {
            "total_seconds": total_seconds,
            "total_readable": readable,
            "chunks": len(self.chunks),
            "time_per_chunk": self.ESTIMATED_TIME_PER_CHUNK,
            "breakdown": {
                "extraction": extraction_time,
                "chunking": chunking_time,
                "processing": processing_time,
                "cleanup": cleanup_time,
                "save": save_time
            }
        }
    
    def print_time_estimate(self):
        """Imprime la estimación de tiempo"""
        est = self.estimate_time()
        
        separator = "="*50
        print(f"\n⏱️  ESTIMACIÓN DE TIEMPO")
        print(separator)
        print(f"  Chunks a procesar: {est['chunks']}")
        print(f"  Tiempo por chunk: ~{est['time_per_chunk']}s")
        print(f"  ⏳ TIEMPO TOTAL ESTIMADO: {est['total_readable']}")
        print(separator)
        print(f"\n  Desglose por fase:")
        for phase, time_val in est['breakdown'].items():
            print(f"    • {phase:15s}: ~{time_val:6.1f}s")
        print()
    
    def chunk_text(self) -> bool:
        """Divide el texto en chunks"""
        print("\n✂️  Diviendo en chunks...")
        try:
            self.chunks = RAGService.chunk_text_intelligent(
                self.text, 
                chunk_size=1000,  # Chunk más grande para mejor contexto
                overlap=200
            )
            print(f"✅ {len(self.chunks)} chunks creados")
            return True
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def extract_entities_and_relations(self, max_chunks: int = None) -> bool:
        """
        Usa Groq LLM para extraer entidades y relaciones
        
        Args:
            max_chunks: Máximo número de chunks a procesar (None = todos)
        """
        print("\n🤖 Extrayendo entidades y relaciones con Groq LLM...")
        
        if not self.chunks:
            print("❌ No hay chunks para procesar")
            return False
        
        # Limitar chunks si es necesario
        chunks_to_process = self.chunks[:max_chunks] if max_chunks else self.chunks
        
        # Mostrar estimación de tiempo
        chunks_count = len(chunks_to_process)
        est_time = chunks_count * self.ESTIMATED_TIME_PER_CHUNK
        est_td = timedelta(seconds=int(est_time))
        print(f"\n📊 Procesando {chunks_count} chunks")
        print(f"⏱️  Tiempo estimado: ≈ {est_td}")
        print(f"{'-'*50}\n")
        
        self.start_time = time.time()
        
        try:
            processed = 0
            
            for i, chunk in enumerate(chunks_to_process):
                chunk_start = time.time()
                
                # Calcular tiempo restante
                if self.chunk_times:
                    avg_time = sum(self.chunk_times) / len(self.chunk_times)
                    remaining_chunks = chunks_count - i - 1
                    remaining_time = remaining_chunks * avg_time
                    remaining_td = timedelta(seconds=int(remaining_time))
                    pct = int((i / chunks_count) * 100)
                    print(f"  [{i+1}/{chunks_count}] {pct}% - Tiempo restante: ≈ {remaining_td}", end="\r")
                else:
                    pct = int((i / chunks_count) * 100)
                    print(f"  [{i+1}/{chunks_count}] {pct}% - Procesando...", end="\r")
                
                # Prompt para Groq
                prompt = f"""Analiza el siguiente texto y extrae SOLO en formato JSON válido:
1. Entidades principales (conceptos, actores, objetos)
2. Relaciones entre entidades

Formato de respuesta JSON exacto:
{{
    "entities": [
        {{"id": "entity_id", "label": "nombre visible", "type": "tipo (articulo/concepto/actor/derecho/obligacion)", "description": "breve descripción"}}
    ],
    "relations": [
        {{"source": "entity_id_1", "target": "entity_id_2", "relation": "tipo_relacion", "weight": 0.8}}
    ]
}}

Texto a analizar:
{chunk[:1500]}

RESPONDE SOLO CON EL JSON, sin explicación."""

                try:
                    response = groq_service.chat_simple(prompt)
                    
                    # Parse JSON response
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        
                        # Agregar entities
                        if "entities" in data:
                            for entity in data.get("entities", []):
                                entity_id = entity.get("id", f"entity_{len(self.nodes)}")
                                if entity_id not in self.nodes:
                                    self.nodes[entity_id] = {
                                        "label": entity.get("label", entity_id),
                                        "type": entity.get("type", "unknown"),
                                        "description": entity.get("description", ""),
                                        "chunk_index": i
                                    }
                        
                        # Agregar relations
                        if "relations" in data:
                            for rel in data.get("relations", []):
                                src = rel.get("source")
                                tgt = rel.get("target")
                                if src and tgt:
                                    # Evitar duplicados
                                    edge_exists = any(
                                        e["source"] == src and e["target"] == tgt 
                                        for e in self.edges
                                    )
                                    if not edge_exists:
                                        self.edges.append({
                                            "source": src,
                                            "target": tgt,
                                            "relation": rel.get("relation", "related_to"),
                                            "weight": float(rel.get("weight", 0.5))
                                        })
                
                except json.JSONDecodeError:
                    # Si el parse falla, continuar sin abortar
                    pass
                except Exception as e:
                    print(f"\n  ⚠️  Error en chunk {i}: {str(e)}")
                
                # Guardar tiempo de este chunk
                chunk_time = time.time() - chunk_start
                self.chunk_times.append(chunk_time)
                
                processed += 1
            
            # Tiempo total
            total_time = time.time() - self.start_time
            total_td = timedelta(seconds=int(total_time))
            
            print(f"\n  ✅ {processed} chunks procesados en {total_td}")
            print(f"✅ Extraídas {len(self.nodes)} entidades, {len(self.edges)} relaciones")
            return True
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def cleanup_graph(self):
        """
        Limpia el grafo:
        - Remueve nodos sin edges
        - Normaliza tipos
        - Agrega estadísticas
        """
        print("\n🧹 Limpiando grafo...")
        
        # Obtener IDs de nodos con al menos una relación
        connected_nodes = set()
        for edge in self.edges:
            connected_nodes.add(edge["source"])
            connected_nodes.add(edge["target"])
        
        # Filtrar solo nodos conectados
        original_count = len(self.nodes)
        self.nodes = {k: v for k, v in self.nodes.items() if k in connected_nodes}
        
        print(f"✅ Removidos {original_count - len(self.nodes)} nodos desconectados")
        print(f"✅ Grafo final: {len(self.nodes)} nodos, {len(self.edges)} relaciones")
    
    def build_graph(self) -> Dict:
        """Construye la estructura del grafo"""
        return {
            "metadata": {
                "source": Path(self.pdf_path).name,
                "total_text_chars": len(self.text),
                "chunks_processed": len(self.chunks),
                "nodes_count": len(self.nodes),
                "edges_count": len(self.edges)
            },
            "nodes": list(self.nodes.values()),
            "edges": self.edges
        }
    
    def save_graph(self, output_path: str = None) -> str:
        """Guarda el grafo en JSON"""
        if output_path is None:
            pdf_name = Path(self.pdf_path).stem
            output_path = f"{pdf_name}_graph.json"
        
        graph = self.build_graph()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Grafo guardado: {output_path}")
        return output_path
    
    def print_stats(self):
        """Imprime estadísticas del grafo"""
        print("\n" + "="*70)
        print("📊 ESTADÍSTICAS DEL GRAFO")
        print("="*70)
        
        # Información general
        print(f"\n📈 Tamaño:")
        print(f"  • Nodos: {len(self.nodes)}")
        print(f"  • Relaciones: {len(self.edges)}")
        print(f"  • Densidad: {len(self.edges) / max(len(self.nodes), 1):.2f} edges por nodo")
        
        # Tipos de entidades
        print(f"\n🏷️  Tipos de entidades:")
        type_counts = {}
        for node_id, node in self.nodes.items():
            node_type = node.get("type", "unknown")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        
        for node_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {node_type}: {count}")
        
        # Relaciones más comunes
        print(f"\n🔗 Tipos de relaciones:")
        rel_counts = {}
        for edge in self.edges:
            rel_type = edge.get("relation", "unknown")
            rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1
        
        for rel_type, count in sorted(rel_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {rel_type}: {count}")
        
        # Nodos más conectados
        print(f"\n⭐ Nodos más conectados:")
        node_degrees = {}
        for node_id in self.nodes:
            degree = sum(1 for e in self.edges if e["source"] == node_id or e["target"] == node_id)
            node_degrees[node_id] = degree
        
        for node_id, degree in sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:5]:
            label = self.nodes[node_id].get("label", node_id)
            print(f"  • {label} ({node_id}): {degree} conexiones")
        
        print("\n" + "="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Construir grafo RAG desde PDF"
    )
    parser.add_argument(
        "pdf", 
        help="Ruta al archivo PDF"
    )
    parser.add_argument(
        "--output", 
        "-o",
        help="Ruta de salida para el JSON (default: PDF_name_graph.json)",
        default=None
    )
    parser.add_argument(
        "--stats",
        "-s",
        action="store_true",
        help="Mostrar estadísticas del grafo"
    )
    parser.add_argument(
        "--max-chunks",
        "-m",
        type=int,
        default=10,
        help="Máximo número de chunks a procesar (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Verificar que el PDF existe
    if not Path(args.pdf).exists():
        print(f"❌ Error: PDF no encontrado: {args.pdf}")
        sys.exit(1)
    
    # Inicio del proceso
    separator = "="*70
    print("\n" + separator)
    print("🔨 CONSTRUCTOR DE GRAFO RAG")
    print(separator)
    
    process_start = time.time()
    
    builder = KnowledgeGraphBuilder(args.pdf)
    
    # Paso 1: Extraer PDF
    if not builder.extract_pdf():
        sys.exit(1)
    
    # Paso 2: Chunking
    if not builder.chunk_text():
        sys.exit(1)
    
    # Paso 3: Extraer entidades y relaciones
    if not builder.extract_entities_and_relations(max_chunks=args.max_chunks):
        sys.exit(1)
    
    # Paso 4: Limpiar grafo
    builder.cleanup_graph()
    
    # Paso 5: Guardar
    output_file = builder.save_graph(args.output)
    
    # Tiempo total
    total_time = time.time() - process_start
    total_td = timedelta(seconds=int(total_time))
    
    # Resumen final
    separator = "="*70
    print("\n" + separator)
    print("✅ GRAFO RAG CREADO EXITOSAMENTE")
    print(separator)
    print(f"\n📁 Archivo: {output_file}")
    print(f"📊 Nodos: {len(builder.nodes)}")
    print(f"🔗 Relaciones: {len(builder.edges)}")
    print(f"⏱️  Tiempo total: {total_td}")
    print()
    
    # Paso 6: Mostrar stats
    if args.stats:
        builder.print_stats()
    else:
        print(f"💡 Usa --stats para ver estadísticas detalladas\n")
    
    print(f"🚀 Próximo paso: Carga este grafo en el sistema RAG\n")


if __name__ == "__main__":
    main()
