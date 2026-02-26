#!/usr/bin/env python3
"""
Constructor de Grafo basado en ARTÍCULOS del Código del Trabajo

Estrategia:
1. Extrae cada artículo del PDF
2. Identifica contexto (Libro, Título, Capítulo, Párrafo)
3. Detecta referencias entre artículos
4. Crea nodos por artículo
5. Crea relaciones basadas en referencias

Output: JSON con estructura artículo-céntrica
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import timedelta
import time

sys.path.insert(0, str(Path(__file__).parent))

from services.rag_service import RAGService
from services import groq_service


class ArticleGraphBuilder:
    """Construye grafo de Código del Trabajo basado en Artículos"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.articles = {}  # {article_number: {number, title, content, context}}
        self.nodes = {}     # {article_number: node}
        self.edges = []     # Relaciones entre artículos
        self.context_stack = {
            "libro": None,
            "titulo": None,
            "capitulo": None,
            "parrafo": None
        }
    
    def extract_pdf(self) -> bool:
        """Extrae texto del PDF"""
        print("\n📖 Extrayendo texto del PDF...")
        try:
            self.text = RAGService.extract_text_from_pdf(self.pdf_path)
            print(f"✅ {len(self.text):,} caracteres extraídos")
            return True
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def parse_articles(self) -> bool:
        """
        Extrae artículos del texto usando regex inteligente
        
        Detecta:
        - Artículos numerados (Art. 1°, Art. 2, etc.)
        - Artículos con sufijos (Art. 15 bis, Art. 25 ter)
        - Contexto jerárquico (Libro, Título, Capítulo, Párrafo)
        """
        print("\n🔍 Extrayendo artículos...")
        
        try:
            # Patrones para detectar estructura
            libro_pattern = r'(?:^|\n)\s*(?:LIBRO|Libro)\s+([IVX]+|[A-Z]+).*?(?:$|\n)'
            titulo_pattern = r'(?:^|\n)\s*(?:TÍTULO|Título)\s+([IVX]+|[A-Z]+).*?(?:$|\n)'
            capitulo_pattern = r'(?:^|\n)\s*(?:CAPÍTULO|Capítulo)\s+([IVX]+|[A-Z]+).*?(?:$|\n)'
            parrafo_pattern = r'(?:^|\n)\s*(?:Párrafo|PÁRRAFO)\s+([0-9°º]+).*?(?:$|\n)'
            
            # Patrón para artículos: "Art. 1°", "Art. 15 bis", "Art. 25 ter", etc.
            # Captura: Art. [número][opcional sufijo como bis/ter]
            article_pattern = r'(?:^|\n)\s*(?:Art\.?|ARTÍCULO)\s+(\d+)\s*(?:(bis|ter|quáter|bis\s+A|bis\s+B))?\s*[.—\-]?\s*(.+?)(?=(?:\n\s*(?:Art\.?|ARTÍCULO)\s+\d+|$))'
            
            # Extraer contexto
            libro_matches = re.finditer(libro_pattern, self.text, re.MULTILINE | re.IGNORECASE)
            titulo_matches = re.finditer(titulo_pattern, self.text, re.MULTILINE | re.IGNORECASE)
            capitulo_matches = re.finditer(capitulo_pattern, self.text, re.MULTILINE | re.IGNORECASE)
            
            # Construir mapa de posiciones para contexto
            context_positions = {}
            for match in libro_matches:
                context_positions[match.start()] = ('libro', match.group(1))
            for match in titulo_matches:
                context_positions[match.start()] = ('titulo', match.group(1))
            for match in capitulo_matches:
                context_positions[match.start()] = ('capitulo', match.group(1))
            
            # Extraer artículos
            article_matches = re.finditer(article_pattern, self.text, re.MULTILINE | re.DOTALL)
            articles_found = 0
            
            for match in article_matches:
                article_num = match.group(1)
                suffix = match.group(2) or ""
                content = match.group(3).strip()
                
                # Normalizar número
                if suffix:
                    article_id = f"{article_num} {suffix}".replace("\n", " ").strip()
                else:
                    article_id = article_num
                
                # Actualizar contexto basado en posición
                pos = match.start()
                for ctx_pos in sorted(context_positions.keys(), reverse=True):
                    if ctx_pos <= pos:
                        ctx_type, ctx_value = context_positions[ctx_pos]
                        self.context_stack[ctx_type] = ctx_value
                        break
                
                # Crear nodo del artículo
                self.articles[article_id] = {
                    "number": article_id,
                    "numeric": article_num,
                    "content": content[:500],  # Primeros 500 caracteres
                    "full_text": content,
                    "context": {
                        "libro": self.context_stack["libro"],
                        "titulo": self.context_stack["titulo"],
                        "capitulo": self.context_stack["capitulo"],
                        "parrafo": self.context_stack["parrafo"]
                    }
                }
                articles_found += 1
            
            print(f"✅ {articles_found} artículos extraídos")
            return True
        
        except Exception as e:
            print(f"❌ Error extrayendo artículos: {str(e)}")
            return False
    
    def extract_article_references(self) -> bool:
        """
        Detecta referencias entre artículos
        
        Busca patrones como:
        - "artículo 15"
        - "Art. 20"
        - "conforme al artículo 25"
        - "véase el artículo 30"
        """
        print("\n🔗 Extrayendo referencias entre artículos...")
        
        # Patrón para encontrar referencias a artículos
        # Busca: art/artículo [número] [sufijo opcional]
        ref_pattern = r'(?:art\.?|artículo|véase|conforme al|según el?|aplicable el?)\s+(?:artículo\s+)?(\d+)\s*(bis|ter|quáter)?'
        
        references = {}  # {from_article: [to_articles]}
        
        for article_id, article_data in self.articles.items():
            content = article_data["full_text"]
            
            # Buscar referencias en este artículo
            matches = re.finditer(ref_pattern, content, re.IGNORECASE)
            referred_articles = set()
            
            for match in matches:
                ref_num = match.group(1)
                ref_suffix = match.group(2) or ""
                
                if ref_suffix:
                    ref_id = f"{ref_num} {ref_suffix}".replace("\n", " ").strip()
                else:
                    ref_id = ref_num
                
                # Validar que el artículo referenciado existe
                if ref_id in self.articles or ref_num in self.articles:
                    referred_articles.add(ref_id if ref_id in self.articles else ref_num)
            
            if referred_articles:
                references[article_id] = list(referred_articles)
        
        # Crear edges (relaciones)
        for from_article, to_articles in references.items():
            for to_article in to_articles:
                self.edges.append({
                    "source": from_article,
                    "target": to_article,
                    "relation": "references",
                    "weight": 0.8
                })
        
        print(f"✅ {len(self.edges)} referencias encontradas")
        return True
    
    def extract_article_titles(self) -> bool:
        """
        Usa el LLM para extraer un título descriptivo para cada artículo
        
        Esto mejora la legibilidad del grafo
        """
        print("\n🤖 Extrayendo títulos de artículos con LLM...")
        
        articles_to_process = list(self.articles.items())[:50]  # Procesar primeros 50
        
        for i, (article_id, article_data) in enumerate(articles_to_process):
            if i % 10 == 0:
                print(f"  [{i+1}/{len(articles_to_process)}] Procesando...")
            
            try:
                content_preview = article_data["content"][:300]
                
                prompt = f"""Dado este artículo del Código del Trabajo, 
extrae un título conciso (máx 10 palabras) que describa su contenido principal.

Artículo {article_id}:
{content_preview}

RESPONDE SOLO CON EL TÍTULO, sin explicación."""
                
                title = groq_service.chat_simple(prompt).strip()
                # Limpiar resultado
                title = title.replace("**", "").replace('"', '').replace("'", '')[:50]
                
                self.articles[article_id]["title"] = title
                
            except Exception as e:
                # Usar primer párrafo como título si falla
                first_line = article_data["content"].split('.')[0][:50]
                self.articles[article_id]["title"] = first_line
        
        print(f"✅ Títulos extraídos")
        return True
    
    def build_nodes(self) -> bool:
        """Construye nodos del grafo desde artículos"""
        print("\n📈 Construyendo nodos...")
        
        for article_id, article_data in self.articles.items():
            title = article_data.get("title", article_data["content"].split('.')[0])
            
            self.nodes[article_id] = {
                "id": article_id,
                "label": f"Art. {article_id}",
                "title": title,
                "type": "articulo",
                "content_preview": article_data["content"][:200],
                "context": article_data["context"],
                "description": f"Artículo {article_id} - {title}"
            }
        
        print(f"✅ {len(self.nodes)} nodos creados")
        return True
    
    def build_graph(self) -> Dict:
        """Construye estructura final del grafo"""
        return {
            "metadata": {
                "source": Path(self.pdf_path).name,
                "graph_type": "article-based",
                "total_articles": len(self.nodes),
                "total_references": len(self.edges),
                "articles_with_title": sum(1 for n in self.nodes.values() if "title" in n)
            },
            "nodes": list(self.nodes.values()),
            "edges": self.edges
        }
    
    def save_graph(self, output_path: str = None) -> str:
        """Guarda el grafo en JSON"""
        if output_path is None:
            pdf_name = Path(self.pdf_path).stem
            output_path = f"{pdf_name}_articles_graph.json"
        
        graph = self.build_graph()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Grafo guardado: {output_path}")
        return output_path
    
    def print_stats(self):
        """Imprime estadísticas del grafo"""
        print("\n" + "="*70)
        print("📊 ESTADÍSTICAS DEL GRAFO DE ARTÍCULOS")
        print("="*70)
        
        print(f"\n📈 Tamaño:")
        print(f"  • Artículos (nodos): {len(self.nodes)}")
        print(f"  • Referencias (edges): {len(self.edges)}")
        
        print(f"\n🏷️  Contexto jerárquico:")
        libros = set(n.get("context", {}).get("libro") for n in self.nodes.values() if n.get("context"))
        titulos = set(n.get("context", {}).get("titulo") for n in self.nodes.values() if n.get("context"))
        
        print(f"  • Libros: {len([l for l in libros if l])}")
        print(f"  • Títulos: {len([t for t in titulos if t])}")
        
        print(f"\n⭐ Artículos más referenciados:")
        ref_count = {}
        for edge in self.edges:
            target = edge["target"]
            ref_count[target] = ref_count.get(target, 0) + 1
        
        for article_id, count in sorted(ref_count.items(), key=lambda x: x[1], reverse=True)[:10]:
            title = self.nodes.get(article_id, {}).get("title", "?")
            print(f"  • Art. {article_id}: {count} referencias ({title})")
        
        print("\n" + "="*70 + "\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Construir grafo de Código del Trabajo basado en Artículos"
    )
    parser.add_argument("pdf", help="Ruta al archivo PDF")
    parser.add_argument("-o", "--output", help="Ruta de salida para el JSON", default=None)
    parser.add_argument("-s", "--stats", action="store_true", help="Mostrar estadísticas")
    parser.add_argument("--titles", action="store_true", help="Extraer títulos con LLM")
    
    args = parser.parse_args()
    
    if not Path(args.pdf).exists():
        print(f"❌ Error: PDF no encontrado: {args.pdf}")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("🔨 CONSTRUCTOR DE GRAFO - BASADO EN ARTÍCULOS")
    print("="*70)
    
    process_start = time.time()
    
    builder = ArticleGraphBuilder(args.pdf)
    
    # Paso 1: Extraer PDF
    if not builder.extract_pdf():
        sys.exit(1)
    
    # Paso 2: Parsear artículos
    if not builder.parse_articles():
        sys.exit(1)
    
    # Paso 3: Extraer referencias
    if not builder.extract_article_references():
        sys.exit(1)
    
    # Paso 4: Extraer títulos (opcional)
    if args.titles:
        builder.extract_article_titles()
    
    # Paso 5: Construir nodos
    if not builder.build_nodes():
        sys.exit(1)
    
    # Paso 6: Guardar
    output_file = builder.save_graph(args.output)
    
    total_time = time.time() - process_start
    total_td = timedelta(seconds=int(total_time))
    
    print("\n" + "="*70)
    print("✅ GRAFO CREADO EXITOSAMENTE")
    print("="*70)
    print(f"\n📁 Archivo: {output_file}")
    print(f"📊 Artículos: {len(builder.nodes)}")
    print(f"🔗 Referencias: {len(builder.edges)}")
    print(f"⏱️  Tiempo: {total_td}\n")
    
    if args.stats:
        builder.print_stats()


if __name__ == "__main__":
    main()
