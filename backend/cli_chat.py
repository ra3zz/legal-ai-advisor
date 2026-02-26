#!/usr/bin/env python3
"""
CLI Chat Interactivo - Legal AI Advisor
Chat 100% local en terminal sobre Código del Trabajo Chileno
"""
import sys
import os
import json
from pathlib import Path

# Agregar backend a path
sys.path.insert(0, str(Path(__file__).parent))

from database.database import SessionLocal
from database.models import Document
from services.groq_service import embed_text, chat_with_doc
from services.rag_service import RAGService
from services.graph_service import graph_service
from services.agent_service import LegalAgentCodigoTrabajo
import numpy as np

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class CLIChat:
    """Chat interactivo en terminal"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.documents = []
        self.history = []
        self.agent = None
        self.loaded_graphs = {}  # {nombre: ruta}
        self.debug_mode = False  # Modo verbose para ver workflow completo
        self.load_documents()
        self.load_knowledge_graph()
        self.load_agent()
    
    def load_knowledge_graph(self):
        """Cargar grafo de conocimiento si existe"""
        graph_paths = [
            Path(__file__).parent.parent / "articles-117137_galeria_02_graph.json",
            Path.cwd() / "articles-117137_galeria_02_graph.json",
            Path.cwd() / "backend" / "articles-117137_galeria_02_graph.json",
        ]
        
        for graph_path in graph_paths:
            if graph_path.exists():
                print(f"{Colors.BLUE}📊 Cargando grafo de conocimiento...{Colors.END}")
                if graph_service.load_graph(str(graph_path)):
                    stats = graph_service.get_stats()
                    print(f"{Colors.GREEN}✅ Grafo integrado ({stats['nodes']} nodos, "
                          f"{stats['edges']} relaciones){Colors.END}\n")
                    return
        
        print(f"{Colors.YELLOW}⚠️  Grafo no encontrado (búsqueda será sin grafo){Colors.END}\n")
    
    def load_agent(self):
        """Cargar agente LLM que mapea queries a artículos"""
        graph_paths = [
            Path(__file__).parent.parent / "articles-117137_galeria_02_articles_graph.json",
            Path.cwd() / "articles-117137_galeria_02_articles_graph.json",
            Path.cwd() / "backend" / "articles-117137_galeria_02_articles_graph.json",
        ]
        
        graph_path = None
        for gp in graph_paths:
            if gp.exists():
                graph_path = str(gp)
                break
        
        self.agent = LegalAgentCodigoTrabajo(graph_path)
        if graph_path:
            print(f"{Colors.GREEN}🤖 Agente cargado con grafo de artículos{Colors.END}\n")
        else:
            print(f"{Colors.YELLOW}⚠️  Agente en modo degradado (sin grafo de artículos){Colors.END}\n")
    
    def load_documents(self):
        """Cargar documentos de la BD"""
        try:
            self.documents = self.db.query(Document).all()
            print(f"{Colors.GREEN}✅ {len(self.documents)} documentos cargados{Colors.END}\n")
        except Exception as e:
            print(f"{Colors.RED}❌ Error cargando documentos: {e}{Colors.END}")
            self.documents = []
    
    def search_documents(self, query: str, top_k: int = 3) -> list:
        """
        Buscar documentos usando búsqueda HÍBRIDA: 70% embeddings + 30% BM25
        """
        results = RAGService.search_hybrid(query, top_k=top_k)
        
        # Convertir resultado a documentos
        docs_by_content = {}
        for doc in self.documents:
            docs_by_content[doc.content[:50]] = doc
        
        matched_docs = []
        for result in results:
            for doc in self.documents:
                if doc.content == result['text']:
                    matched_docs.append((doc, result['score']))
                    break
        
        return [doc for doc, _ in matched_docs[:top_k]]
    
    def format_context(self, documents: list) -> str:
        """Formatear documentos como contexto para el LLM"""
        if not documents:
            return ""
        
        context = "INFORMACIÓN RELEVANTE DEL CÓDIGO DEL TRABAJO:\n\n"
        for i, doc in enumerate(documents, 1):
            context += f"[{i}] {doc.article_number if doc.article_number else 'Documento'}\n"
            context += f"{doc.content[:300]}...\n\n"
        
        return context
    
    def print_header(self):
        """Mostrar encabezado de bienvenida"""
        print(f"\n{Colors.HEADER}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}⚖️  ASESOR LEGAL - CÓDIGO DEL TRABAJO CHILENO{Colors.END}")
        print(f"{Colors.HEADER}{'='*70}{Colors.END}")
        print(f"{Colors.YELLOW}Chat local 100% privado | 💾 BD: SQLite | 🤖 LLM: Groq{Colors.END}\n")
    
    def print_help(self):
        """Mostrar ayuda"""
        print(f"{Colors.CYAN}Comandos disponibles:{Colors.END}")
        print(f"  {Colors.GREEN}?{Colors.END} - Mostrar esta ayuda")
        print(f"\n{Colors.BOLD}📄 Gestión de PDFs:{Colors.END}")
        print(f"  {Colors.GREEN}cargar <ruta>{Colors.END} - Cargar PDF (ej: cargar documentos/ley.pdf)")
        print(f"  {Colors.GREEN}docs{Colors.END} - Listar documentos cargados")
        print(f"  {Colors.GREEN}reset-docs{Colors.END} - Borrar todos los documentos")
        print(f"\n{Colors.BOLD}📊 Gestión de Grafos JSON:{Colors.END}")
        print(f"  {Colors.GREEN}cargar-grafo <ruta>{Colors.END} - Cargar JSON (ej: cargar-grafo grafos/codigo.json)")
        print(f"  {Colors.GREEN}grafos{Colors.END} - Listar grafos cargados")
        print(f"  {Colors.GREEN}reset-grafos{Colors.END} - Descargar todos los grafos")
        print(f"\n{Colors.BOLD}📈 Información:{Colors.END}")
        print(f"  {Colors.GREEN}grafo{Colors.END} - Ver estadísticas del grafo de conocimiento")
        print(f"  {Colors.GREEN}historial{Colors.END} - Ver historial de preguntas")
        print(f"  {Colors.GREEN}limpiar{Colors.END} - Limpiar pantalla")
        print(f"\n{Colors.BOLD}🚪 Sesión:{Colors.END}")
        print(f"  {Colors.GREEN}salir{Colors.END} - Cerrar aplicación")
        print(f"  {Colors.RED}Tu pregunta{Colors.END} - Chatear sobre el Código del Trabajo")
        print(f"\n{Colors.YELLOW}💡 El agente analizará automáticamente tus preguntas")
        print(f"   y las mapeará a los artículos más relevantes{Colors.END}\n")
    
    def print_documents(self):
        """Listar documentos disponibles"""
        if not self.documents:
            print(f"{Colors.YELLOW}No hay documentos cargados{Colors.END}\n")
            return
        
        print(f"\n{Colors.BOLD}📚 Documentos disponibles:{Colors.END}")
        articles = {}
        for doc in self.documents:
            art = doc.article_number or "Sin especificar"
            if art not in articles:
                articles[art] = 0
            articles[art] += 1
        
        for art, count in sorted(articles.items()):
            print(f"  • {art} ({count} chunk{'s' if count > 1 else ''})")
        print()
    
    def load_pdf(self, pdf_path: str):
        """Cargar PDF y agregarlo a la BD"""
        pdf_file = Path(pdf_path)
        
        if not pdf_file.exists():
            print(f"{Colors.RED}❌ Archivo no encontrado: {pdf_path}{Colors.END}\n")
            return
        
        if not pdf_file.suffix.lower() == '.pdf':
            print(f"{Colors.RED}❌ Solo se aceptan archivos PDF{Colors.END}\n")
            return
        
        print(f"\n{Colors.BLUE}📥 Cargando PDF: {pdf_file.name}...{Colors.END}")
        
        try:
            # Procesar PDF
            result = RAGService.process_pdf(str(pdf_file))
            
            if isinstance(result, dict) and result.get('success'):
                # Recargar documentos de la BD
                self.load_documents()
                saved = result.get('documents_saved', 0)
                print(f"{Colors.GREEN}✅ PDF procesado: {saved} documento(s) agregado(s){Colors.END}\n")
            else:
                error_msg = result.get('message', 'Error desconocido') if isinstance(result, dict) else str(result)
                print(f"{Colors.YELLOW}⚠️  {error_msg}{Colors.END}\n")
        
        except Exception as e:
            print(f"{Colors.RED}❌ Error al procesar PDF: {str(e)}{Colors.END}\n")
    
    def reset_documents(self):
        """Limpiar todos los documentos de la BD"""
        confirm = input(f"\n{Colors.YELLOW}⚠️  Borrar TODOS los documentos? (sí/no): {Colors.END}").strip().lower()
        
        if confirm == "sí" or confirm == "si":
            try:
                self.db.query(Document).delete()
                self.db.commit()
                self.load_documents()
                print(f"{Colors.GREEN}✅ Documentos borrados. BD lista para nuevos imports.{Colors.END}\n")
            except Exception as e:
                self.db.rollback()
                print(f"{Colors.RED}❌ Error: {str(e)}{Colors.END}\n")
        else:
            print(f"{Colors.YELLOW}❌ Cancelado{Colors.END}\n")
    
    def load_json_graph(self, json_path: str):
        """Cargar grafo JSON y agregarlo a la lista activa"""
        json_file = Path(json_path)
        
        if not json_file.exists():
            print(f"{Colors.RED}❌ Archivo no encontrado: {json_path}{Colors.END}\n")
            return
        
        if not json_file.suffix.lower() == '.json':
            print(f"{Colors.RED}❌ Solo se aceptan archivos JSON{Colors.END}\n")
            return
        
        print(f"\n{Colors.BLUE}📥 Cargando grafo: {json_file.name}...{Colors.END}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                grafo_data = json.load(f)
            
            # Validar estructura básica
            if not isinstance(grafo_data, dict) or 'nodes' not in grafo_data:
                print(f"{Colors.YELLOW}⚠️  Archivo JSON no parece ser un grafo válido (falta 'nodes'){Colors.END}\n")
                return
            
            # Cargar en el servicio de grafos
            if graph_service.load_graph(str(json_file)):
                graph_name = json_file.stem
                self.loaded_graphs[graph_name] = str(json_file)
                stats = graph_service.get_stats()
                print(f"{Colors.GREEN}✅ Grafo '{graph_name}' cargado ({stats['nodes']} nodos, "
                      f"{stats['edges']} relaciones){Colors.END}\n")
            else:
                print(f"{Colors.RED}❌ Error al cargar el grafo en el servicio{Colors.END}\n")
        
        except json.JSONDecodeError:
            print(f"{Colors.RED}❌ Archivo JSON inválido (JSON malformado){Colors.END}\n")
        except Exception as e:
            print(f"{Colors.RED}❌ Error al cargar grafo: {str(e)}{Colors.END}\n")
    
    def print_loaded_graphs(self):
        """Listar grafos cargados"""
        if not self.loaded_graphs:
            print(f"\n{Colors.YELLOW}No hay grafos cargados{Colors.END}\n")
            return
        
        print(f"\n{Colors.BOLD}📊 Grafos disponibles:{Colors.END}")
        for i, (name, path) in enumerate(self.loaded_graphs.items(), 1):
            print(f"  {i}. {Colors.GREEN}{name}{Colors.END}")
            print(f"     📁 {path}")
        
        if graph_service.is_loaded:
            stats = graph_service.get_stats()
            print(f"\n   {Colors.CYAN}Activo: {stats['nodes']} nodos, {stats['edges']} relaciones{Colors.END}")
        print()
    
    def reset_graphs(self):
        """Limpiar todos los grafos cargados"""
        if not self.loaded_graphs:
            print(f"{Colors.YELLOW}No hay grafos cargados para limpiar{Colors.END}\n")
            return
        
        confirm = input(f"\n{Colors.YELLOW}⚠️  Descargar TODOS los grafos ({len(self.loaded_graphs)})? (sí/no): {Colors.END}").strip().lower()
        
        if confirm == "sí" or confirm == "si":
            self.loaded_graphs.clear()
            graph_service.is_loaded = False
            graph_service.nodes = {}
            graph_service.edges = []
            print(f"{Colors.GREEN}✅ Grafos descargados. Sistema listo.{Colors.END}\n")
        else:
            print(f"{Colors.YELLOW}❌ Cancelado{Colors.END}\n")
    
    def print_graph_stats(self):
        """Mostrar estadísticas del grafo de conocimiento"""
        if not graph_service.is_loaded:
            print(f"{Colors.YELLOW}⚠️  Grafo no cargado{Colors.END}\n")
            return
        
        stats = graph_service.get_stats()
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 ESTADÍSTICAS DEL GRAFO{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")
        
        print(f"\n{Colors.GREEN}Tamaño:{Colors.END}")
        print(f"  • Nodos: {stats['nodes']}")
        print(f"  • Relaciones: {stats['edges']}")
        print(f"  • Densidad: {stats['edges']/max(stats['nodes'], 1):.2f} edges por nodo")
        
        print(f"\n{Colors.GREEN}Tipos de entidades:{Colors.END}")
        for entity_type, count in sorted(stats['entity_types'].items(), key=lambda x: x[1], reverse=True):
            print(f"  • {entity_type}: {count}")
        
        print(f"\n{Colors.GREEN}Relaciones más frecuentes:{Colors.END}")
        sorted_rels = sorted(stats['relation_types'].items(), key=lambda x: x[1], reverse=True)[:10]
        for rel_type, count in sorted_rels:
            print(f"  • {rel_type}: {count}")
        
        print(f"\n{Colors.GREEN}Nodos más conectados:{Colors.END}")
        for node_id, connections in stats['most_connected'][:5]:
            node = graph_service.nodes.get(node_id, {})
            label = node.get('label', 'Unknown')
            print(f"  • {label}: {connections} conexiones")
        
        print(f"\n{Colors.CYAN}{'='*60}{Colors.END}\n")
    
    def print_history(self):
        """Mostrar historial de preguntas"""
        if not self.history:
            print(f"{Colors.YELLOW}No hay preguntas en el historial{Colors.END}\n")
            return
        
        print(f"\n{Colors.BOLD}📋 Historial de preguntas:{Colors.END}")
        for i, (query, response) in enumerate(self.history[-10:], 1):
            print(f"\n{i}. {Colors.CYAN}Q: {query}{Colors.END}")
            print(f"   {Colors.GREEN}A: {response[:100]}...{Colors.END}")
        print()
    
    def show_agent_analysis(self, query: str):
        """Mostrar análisis del agente sobre la query"""
        if not self.agent:
            return
        
        mapping = self.agent.get_best_articles(query, use_llm=True)
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}🤖 ANÁLISIS DE AGENTE{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")
        
        if mapping['topics_found']:
            print(f"{Colors.GREEN}Tópicos identificados:{Colors.END}")
            for topic in mapping['topics_found']:
                print(f"  • {topic}")
        
        if mapping['articles']:
            print(f"\n{Colors.GREEN}Artículos relevantes ({mapping['confidence']} confianza):{Colors.END}")
            for article in mapping['articles'][:5]:
                if article.get("available", True):
                    print(f"  • Art. {article['number']}: {article['title']}")
                    if article['context'].get('libro'):
                        print(f"    └─ Libro {article['context']['libro']}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")
    
    def chat(self, query: str):
        """Procesar pregunta y generar respuesta"""
        print(f"\n{Colors.BLUE}🔄 Analizando pregunta...{Colors.END}")
        
        # 0. Análisis del agente (si está disponible)
        if self.agent:
            self.show_agent_analysis(query)
        
        print(f"{Colors.BLUE}🔄 Buscando información relevante...{Colors.END}")
        
        # 1. Búsqueda híbrida: embeddings + BM25 + GRAFO (si disponible)
        results = RAGService.search_hybrid(query, top_k=3, use_graph=graph_service.is_loaded)
        relevant_docs = self.search_documents(query, top_k=3)
        
        # 2. Búsqueda adicional con keywords específicos si el agente detecta palabras clave
        if self.agent:
            specific_keywords = self.agent.extract_specific_keywords(query)
            if specific_keywords:
                for keyword in specific_keywords[:3]:  # Máx 3 keywords adicionales
                    keyword_results = RAGService.search_hybrid(keyword, top_k=2, use_graph=graph_service.is_loaded)
                    results.extend(keyword_results)
        
        # Eliminar duplicados
        seen = set()
        unique_results = []
        for r in results:
            key = (r.get('article'), r.get('score'))
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        results = sorted(unique_results, key=lambda x: x.get('score', 0), reverse=True)[:5]
        
        if not results:
            print(f"{Colors.YELLOW}⚠️  No se encontraron documentos relevantes{Colors.END}\n")
            context = f"La pregunta es: {query}"
        else:
            print(f"{Colors.GREEN}✅ {len(results)} documento(s) encontrado(s):{Colors.END}")
            for result in results:
                article = result['article'] or "Doc"
                relevance = result['score'] * 100
                
                # Mostrar boost del grafo si aplica
                if 'graph_boost' in result and result['graph_boost'] > 0:
                    boost_pct = result['graph_boost'] * 100
                    print(f"   • {article} (relevancia: {relevance:.1f}%) 📊+{boost_pct:.1f}%")
                else:
                    print(f"   • {article} (relevancia: {relevance:.1f}%)")
            
            context = self.format_context(relevant_docs)
            
            # Enriquecer contexto con información del grafo
            if graph_service.is_loaded:
                graph_context = graph_service.enrich_context(query, results, max_entities=5)
                if graph_context:
                    context += "\n" + graph_context
        
        # 2. Generar respuesta con Groq
        print(f"\n{Colors.BLUE}⏳ Generando respuesta...{Colors.END}\n")
        
        try:
            response = chat_with_doc(query, context)
            
            if response and "Error" not in response:
                print(f"{Colors.GREEN}{Colors.BOLD}Respuesta:{Colors.END}")
                print(f"{Colors.CYAN}{response}{Colors.END}\n")
                
                # Guardar en historial
                self.history.append((query, response))
                
                # Mostrar artículos relevantes
                if results:
                    print(f"{Colors.YELLOW}📝 Fuentes:{Colors.END}")
                    for result in results:
                        if result['article']:
                            print(f"   • {result['article']}")
                    print()
            else:
                print(f"{Colors.RED}❌ Error: {response}{Colors.END}\n")
        
        except Exception as e:
            print(f"{Colors.RED}❌ Error al generar respuesta: {e}{Colors.END}\n")
    
    def run(self):
        """Loop principal del CLI"""
        self.print_header()
        self.print_help()
        
        try:
            while True:
                try:
                    query = input(f"{Colors.BOLD}{Colors.CYAN}💬 Tu pregunta:{Colors.END} ").strip()
                    
                    if not query:
                        continue
                    
                    # Comandos especiales
                    if query.lower() == "?":
                        self.print_help()
                    elif query.lower().startswith("cargar "):
                        pdf_path = query[7:].strip()
                        self.load_pdf(pdf_path)
                    elif query.lower().startswith("cargar-grafo "):
                        json_path = query[13:].strip()
                        self.load_json_graph(json_path)
                    elif query.lower() == "reset-docs":
                        self.reset_documents()
                    elif query.lower() == "reset-grafos":
                        self.reset_graphs()
                    elif query.lower() == "grafo":
                        self.print_graph_stats()
                    elif query.lower() == "grafos":
                        self.print_loaded_graphs()
                    elif query.lower() == "historial":
                        self.print_history()
                    elif query.lower() == "docs":
                        self.print_documents()
                    elif query.lower() == "limpiar":
                        os.system("clear" if os.name == "posix" else "cls")
                        self.print_header()
                    elif query.lower() in ["salir", "exit", "quit"]:
                        print(f"\n{Colors.YELLOW}👋 ¡Hasta luego!{Colors.END}\n")
                        break
                    else:
                        # Chat normal
                        self.chat(query)
                
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}👋 ¡Hasta luego!{Colors.END}\n")
                    break
        
        finally:
            self.db.close()

def main():
    """Punto de entrada"""
    try:
        chat = CLIChat()
        chat.run()
    except Exception as e:
        print(f"{Colors.RED}Error fatal: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
