#!/usr/bin/env python3
"""
CLI Chat con MODO DEBUG - Muestra el workflow completo paso a paso
Útil para entender cómo se procesa cada información y dónde optimizar
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
    DIM = '\033[2m'

class CLIChatDebug:
    """Chat interactivo con modo DEBUG verbose"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.documents = []
        self.history = []
        self.agent = None
        self.loaded_graphs = {}
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
        
        print(f"{Colors.YELLOW}⚠️  Grafo no encontrado{Colors.END}\n")
    
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
            print(f"{Colors.YELLOW}⚠️  Agente en modo degradado{Colors.END}\n")
    
    def load_documents(self):
        """Cargar documentos de la BD"""
        try:
            self.documents = self.db.query(Document).all()
            print(f"{Colors.GREEN}✅ {len(self.documents)} documentos cargados{Colors.END}\n")
        except Exception as e:
            print(f"{Colors.RED}❌ Error cargando documentos: {e}{Colors.END}")
            self.documents = []
    
    def print_header(self):
        """Mostrar encabezado de bienvenida"""
        print(f"\n{Colors.HEADER}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}⚖️  ASESOR LEGAL - MODO DEBUG VERBOSE{Colors.END}")
        print(f"{Colors.HEADER}{'='*70}{Colors.END}")
        print(f"{Colors.YELLOW}Chat local 100% privado | 🔧 MODO DEBUG ACTIVO{Colors.END}")
        print(f"{Colors.DIM}Verás cada paso del procesamiento de información{Colors.END}\n")
    
    def print_help(self):
        """Mostrar ayuda"""
        print(f"\n{Colors.CYAN}Comandos disponibles:{Colors.END}")
        print(f"  {Colors.GREEN}?{Colors.END} - Mostrar esta ayuda")
        print(f"\n{Colors.BOLD}📄 Gestión de PDFs:{Colors.END}")
        print(f"  {Colors.GREEN}cargar <ruta>{Colors.END} - Cargar PDF")
        print(f"  {Colors.GREEN}docs{Colors.END} - Listar documentos cargados")
        print(f"  {Colors.GREEN}reset-docs{Colors.END} - Borrar todos los documentos")
        print(f"\n{Colors.BOLD}📊 Información:{Colors.END}")
        print(f"  {Colors.GREEN}grafo{Colors.END} - Ver estadísticas del grafo")
        print(f"  {Colors.GREEN}grafos{Colors.END} - Ver grafos cargados")
        print(f"  {Colors.GREEN}limpiar{Colors.END} - Limpiar pantalla")
        print(f"\n{Colors.BOLD}🚪 Sesión:{Colors.END}")
        print(f"  {Colors.GREEN}salir{Colors.END} - Cerrar aplicación")
        print(f"  {Colors.RED}Tu pregunta{Colors.END} - Chatear con DEBUG\n")
    
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
            result = RAGService.process_pdf(str(pdf_file))
            
            if isinstance(result, dict) and result.get('success'):
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
                print(f"{Colors.GREEN}✅ Documentos borrados.{Colors.END}\n")
            except Exception as e:
                self.db.rollback()
                print(f"{Colors.RED}❌ Error: {str(e)}{Colors.END}\n")
        else:
            print(f"{Colors.YELLOW}❌ Cancelado{Colors.END}\n")
    
    def log_section(self, title: str):
        """Marcar sección importante"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}▶ {title}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    def log_step(self, step_num: int, description: str):
        """Log de un paso specific"""
        print(f"{Colors.BOLD}{Colors.GREEN}[PASO {step_num}] {description}{Colors.END}")
    
    def log_data(self, label: str, data: any, indent: int = 1):
        """Log de datos con indent"""
        prefix = "  " * indent
        print(f"{prefix}{Colors.YELLOW}📌 {label}:{Colors.END}")
        
        if isinstance(data, list):
            for i, item in enumerate(data, 1):
                if isinstance(item, dict):
                    print(f"{prefix}  {Colors.CYAN}[{i}] ", end="")
                    for k, v in item.items():
                        val_str = str(v)[:60] + "..." if len(str(v)) > 60 else str(v)
                        print(f"{Colors.GREEN}{k}:{Colors.END} {val_str} ", end="")
                    print()
                else:
                    print(f"{prefix}  [{i}] {item}")
        elif isinstance(data, dict):
            for k, v in data.items():
                val_str = str(v)[:60] + "..." if len(str(v)) > 60 else str(v)
                print(f"{prefix}  {Colors.GREEN}{k}:{Colors.END} {val_str}")
        else:
            print(f"{prefix}  {data}")
        print()
    
    def chat_debug(self, query: str):
        """Procesar pregunta con DEBUG verbose"""
        self.log_section(f"CONSULTA: {query[:60]}...")
        
        # PASO 0: Input
        self.log_step(0, "Recibir y validar input")
        self.log_data("Query cruda", query)
        
        # PASO 1: Análisis del agente
        if not self.agent:
            print(f"{Colors.YELLOW}⚠️  Agente no disponible{Colors.END}\n")
            return
        
        self.log_step(1, "Análisis LLM Agent - Extraer tópicos y keywords")
        
        # 1a. Extracción de tópicos (sin modificar query)
        topics = self.agent.extract_topics(query)
        self.log_data("Tópicos detectados", topics if topics else "Ninguno", indent=1)
        
        # 1b. Keywords específicos
        keywords = self.agent.extract_specific_keywords(query)
        self.log_data("Keywords específicos", keywords if keywords else "Ninguno", indent=1)
        
        # 1c. Mapeo a artículos
        mapping = self.agent.get_best_articles(query, use_llm=False)
        self.log_data("Artículos mapeados", [f"Art. {a['number']}" for a in mapping['articles'][:8]], indent=1)
        self.log_data("Confianza", mapping['confidence'], indent=1)
        
        # PASO 2: Búsqueda RAG
        self.log_step(2, "Búsqueda Hybrid RAG - Embeddings + BM25 + Grafo")
        self.log_data("Usando grafo", "SÍ" if graph_service.is_loaded else "NO")
        
        # 2a. Búsqueda por query original
        print(f"{Colors.DIM}  Buscando por query principal...{Colors.END}")
        results = RAGService.search_hybrid(query, top_k=3, use_graph=graph_service.is_loaded)
        self.log_data(f"Resultados (query principal)", f"{len(results)} documento(s)", indent=1)
        for r in results[:3]:
            article_info = f"Art. {r.get('article')}" if r.get('article') else "Doc"
            boost = f" + 📊 boost({r.get('graph_boost')*100:.1f}%)" if r.get('graph_boost') else ""
            print(f"    • {article_info}: relevancia {r.get('score')*100:.1f}%{boost}")
        print()
        
        # 2b. Búsqueda por keywords específicos
        if keywords:
            self.log_data("Buscando por keywords adicionales", keywords, indent=1)
            all_keyword_results = []
            for kw in keywords[:3]:
                print(f"{Colors.DIM}    Buscando por '{kw}'...{Colors.END}")
                kw_results = RAGService.search_hybrid(kw, top_k=2, use_graph=graph_service.is_loaded)
                print(f"    → {len(kw_results)} resultado(s)\n")
                all_keyword_results.extend(kw_results)
            results.extend(all_keyword_results)
        
        # PASO 3: Deduplicación y ranking
        self.log_step(3, "Deduplicación de resultados")
        print(f"{Colors.DIM}  Total antes de dedup: {len(results)}{Colors.END}")
        
        seen = set()
        unique_results = []
        for r in results:
            key = (r.get('article'), round(r.get('score', 0), 3))
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        results = sorted(unique_results, key=lambda x: x.get('score', 0), reverse=True)[:5]
        print(f"{Colors.DIM}  Total después dedup: {len(results)}{Colors.END}\n")
        
        self.log_data("Resultados finales", 
                     [f"Art.{r.get('article', 'N/A')} ({r.get('score')*100:.1f}%)" for r in results],
                     indent=1)
        
        # PASO 4: Extraer contenido
        self.log_step(4, "Extraer snippets de documentos")
        relevant_docs = self.db.query(Document).all()  # Simplificado para debug
        print(f"{Colors.DIM}  Documentos disponibles: {len(relevant_docs)}{Colors.END}\n")
        
        if relevant_docs:
            for doc in relevant_docs[:3]:
                snippet = doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                print(f"    • Art.{doc.article_number}: {snippet}")
        print()
        
        # PASO 5: Construir contexto
        self.log_step(5, "Construir contexto para el LLM")
        context_parts = []
        
        for doc in relevant_docs[:3]:
            context_parts.append(f"[Art.{doc.article_number}] {doc.content[:300]}")
        
        context = "\n\n".join(context_parts) if context_parts else f"La pregunta es: {query}"
        context_preview = context[:200] + "..." if len(context) > 200 else context
        self.log_data("Contexto construido", context_preview, indent=1)
        self.log_data("Tamaño del contexto", f"{len(context)} caracteres", indent=1)
        
        # PASO 6: Enriquecer con grafo (si disponible)
        if graph_service.is_loaded:
            self.log_step(6, "Enriquecimiento con Grafo de Conocimiento")
            graph_context = graph_service.enrich_context(query, results[:3], max_entities=3)
            if graph_context:
                print(f"{Colors.DIM}  Contexto de grafo añadido:{Colors.END}")
                print(f"{Colors.DIM}  {graph_context[:150]}...{Colors.END}\n")
                context += "\n" + graph_context
        
        # PASO 7: Llamar al LLM
        self.log_step(7, "Llamar y procesar respuesta del LLM")
        print(f"{Colors.DIM}  Enviando contexto ({len(context)} chars) a Groq...{Colors.END}\n")
        
        try:
            response = chat_with_doc(query, context)
            
            if response and "Error" not in response:
                self.log_section("RESPUESTA GENERADA")
                print(f"{Colors.CYAN}{response}{Colors.END}\n")
                
                # PASO 8: Mostrar fuentes
                self.log_step(8, "Fuentes citadas")
                cities_set = set()
                for result in results:
                    if result.get('article'):
                        cities_set.add(f"Art. {result['article']}")
                
                for source in sorted(cities_set):
                    print(f"  • {source}")
                print()
                
                # Guardar en historial
                self.history.append((query, response))
                
            else:
                print(f"{Colors.RED}❌ Error al generar respuesta: {response}{Colors.END}\n")
        
        except Exception as e:
            print(f"{Colors.RED}❌ Error en LLM: {str(e)}{Colors.END}\n")
    
    def run(self):
        """Loop principal del CLI"""
        self.print_header()
        self.print_help()
        
        try:
            while True:
                try:
                    query = input(f"\n{Colors.BOLD}{Colors.CYAN}💬 Tu pregunta:{Colors.END} ").strip()
                    
                    if not query:
                        continue
                    
                    # Comandos especiales
                    if query.lower() == "?":
                        self.print_help()
                    elif query.lower().startswith("cargar "):
                        pdf_path = query[7:].strip()
                        self.load_pdf(pdf_path)
                    elif query.lower() == "reset-docs":
                        self.reset_documents()
                    elif query.lower() == "docs":
                        print(f"\n{Colors.BOLD}📚 Documentos:{Colors.END} {len(self.documents)} documento(s)\n")
                        if self.documents:
                            articles = {}
                            for doc in self.documents:
                                art = doc.article_number or "Sin especificar"
                                articles[art] = articles.get(art, 0) + 1
                            for art, count in sorted(articles.items()):
                                print(f"  • {art} ({count} chunk{'s' if count > 1 else ''})")
                            print()
                    elif query.lower() == "grafos":
                        print(f"\n{Colors.BOLD}📊 Grafos:{Colors.END} Grafo principal cargado\n")
                    elif query.lower() == "grafo":
                        stats = graph_service.get_stats()
                        print(f"\n{Colors.BOLD}📊 Stats Grafo:{Colors.END}")
                        print(f"  • Nodos: {stats['nodes']}")
                        print(f"  • Aristas: {stats['edges']}\n")
                    elif query.lower() == "limpiar":
                        os.system("clear" if os.name == "posix" else "cls")
                        self.print_header()
                    elif query.lower() in ["salir", "exit", "quit"]:
                        print(f"\n{Colors.YELLOW}👋 ¡Hasta luego!{Colors.END}\n")
                        break
                    else:
                        # Chat con debug
                        self.chat_debug(query)
                
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}👋 ¡Hasta luego!{Colors.END}\n")
                    break
        
        finally:
            self.db.close()

def main():
    """Punto de entrada"""
    try:
        chat = CLIChatDebug()
        chat.run()
    except Exception as e:
        print(f"{Colors.RED}Error fatal: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
