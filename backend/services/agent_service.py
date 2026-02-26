#!/usr/bin/env python3
"""
Agente LLM que traduce queries del usuario a Artículos del Código del Trabajo

Flujo:
1. Usuario pregunta en lenguaje natural (ej: "¿Cuántas horas puedo trabajar?")
2. Agente analiza la pregunta
3. Agente identifica artículos relevantes (Art. 21, 22, etc.)
4. Sistema RAG busca información en esos artículos
5. Retorna respuesta precisa y fundamentada

Capacidades:
- Traducción multiidioma (entrada en cualquier idioma, búsqueda en español)
- Identificación de temas del Código
- Resolución de sinonimia legal
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
import re

sys.path.insert(0, str(Path(__file__).parent))

from services import groq_service


class LegalAgentCodigoTrabajo:
    """Agente que mapea preguntas a artículos del Código del Trabajo"""
    
    # Mapeo de conceptos a artículos (basado en PDF extraído)
    # NOTA: Todos los valores deben ser strings porque los IDs del grafo se extraen como strings
    TOPIC_TO_ARTICLES = {
        # JORNADA DE TRABAJO
        "jornada": ["24", "25", "28", "29", "30", "34"],
        "horas de trabajo": ["24", "28", "29", "30"],
        "horas extraordinarias": ["30"],
        "trabajo extraordinario": ["30"],
        "descanso": ["34"],
        "descanso dominical": ["34"],
        "feriado": ["71"],
        
        # CONTRATO
        "contrato": ["2", "6", "7", "8", "9", "59"],
        "contrato de trabajo": ["2"],
        "contrato vigente": ["7", "8"],
        "término del contrato": ["6"],
        "despido": ["6"],
        "indemnización": ["6", "9", "10"],
        
        # REMUNERACIÓN
        "sueldo": ["41", "42", "44", "45"],
        "remuneración": ["41", "42", "44", "45", "55", "71"],
        "pago de remuneración": ["55"],
        "gratificación": ["42"],
        "comisión": ["44"],
        "bonificación": ["44"],
        "aprendiz": ["81"],
        
        # SINDICATOS
        "sindicato": ["214", "221", "227", "228", "229", "230", "231", "234"],
        "afiliación": ["214"],
        "afiliarse": ["214"],
        "negociación colectiva": ["221"],
        "representación": ["234"],
        
        # PROTECCIÓN
        "maternidad": ["199", "200"],
        "lactancia": ["199"],
        "licencia": ["199"],
        "protección": ["199"],
        "menores": ["214"],
        
        # TRABAJADORES ESPECIALES
        "trabajador agrícola": ["91"],
        "trabajador portuario": ["16"],
        "chofer": ["25"],
        
        # OTROS
        "derechos": ["23"],
        "obligaciones": ["23"],
    }
    
    # Sinónimos legales para normalización
    LEGAL_SYNONYMS = {
        # JORNADA
        "horas": "jornada",
        "horario": "jornada",
        "laboral": "jornada",
        "extraordinario": "horas extraordinarias",
        "sobretiempo": "horas extraordinarias",
        "extra": "horas extraordinarias",
        "domingo": "descanso dominical",
        "festivo": "feriado",
        
        # JORNADA - ACTOS PREPARATORIOS
        "vestuario": "jornada",
        "uniforme": "jornada",
        "implementos": "jornada",
        "implementos de trabajo": "jornada",
        "ropa de trabajo": "jornada",
        "equipos de protección": "jornada",
        "acto preparatorio": "jornada",
        "cambio de ropa": "jornada",
        "preparación": "jornada",
        "equipo de seguridad": "jornada",
        "protección personal": "jornada",
        "marcar hora": "jornada",
        "reloj control": "jornada",
        
        # CONTRATO
        "cesantía": "término del contrato",
        "terminación": "término del contrato",
        "desvinculación": "término del contrato",
        "despedir": "despido",
        
        # REMUNERACIÓN
        "sueldo": "remuneración",
        "salario": "remuneración",
        "pago": "remuneración",
        "ganancia": "remuneración",
        "bono": "gratificación",
        "regalo": "gratificación",
        "porcentaje": "comisión",
        "adicional": "bonificación",
        
        # SINDICATO
        "sindical": "sindicato",
        "gremio": "sindicato",
        "asociación": "sindicato",
        "afiliarse": "afiliación",
        "asociarse": "afiliación",
        "huelga": "negociación",
        "paro": "negociación",
        
        # PROTECCIÓN
        "embarazo": "maternidad",
        "madre": "maternidad",
        "amamantar": "lactancia",
        "permiso": "licencia",
        "ausencia": "licencia",
        
        # TRABAJADORES
        "empleado": "trabajador",
        "patrón": "empleador",
        "jefe": "empleador",
        "prestación": "prestación de servicios",
        "trabajar": "prestación de servicios",
    }
    
    def __init__(self, articles_graph_path: str = None):
        """
        Inicializa el agente
        
        Args:
            articles_graph_path: Ruta al JSON del grafo de artículos
        """
        self.articles_graph = {}
        self.articles_by_number = {}
        
        if articles_graph_path and Path(articles_graph_path).exists():
            self._load_articles_graph(articles_graph_path)
    
    def _load_articles_graph(self, path: str):
        """Carga el grafo de artículos del JSON"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.articles_graph = json.load(f)
            
            # Construir índice por número
            for node in self.articles_graph.get("nodes", []):
                article_num = node.get("id", node.get("label", "")).replace("Art. ", "")
                self.articles_by_number[article_num] = node
            
            print(f"✅ Grafo de artículos cargado ({len(self.articles_by_number)} artículos)")
        except Exception as e:
            print(f"⚠️ No se pudo cargar grafo: {str(e)}")
    
    def normalize_input(self, user_query: str) -> str:
        """
        Normaliza la query del usuario - SOLO lowercase y cleanup
        
        No modifica la query, apenas la prepara para análisis
        """
        # Solo lowercase y trim
        query = user_query.lower().strip()
        return query
    
    def extract_topics(self, user_query: str) -> List[str]:
        """
        Extrae tópicos del Código de la query del usuario
        
        Retorna lista de tópicos (ej: ["jornada", "descanso"])
        Usa sinónimos para buscar pero NO modifica la query original
        """
        normalized = self.normalize_input(user_query)
        topics = []
        
        # Búsqueda simple por keywords - sin modificar query
        for topic_keyword in self.TOPIC_TO_ARTICLES.keys():
            if topic_keyword in normalized:
                topics.append(topic_keyword)
        
        # También buscar por sinónimos (mapeo inverso)
        # Si encontramos un sinónimo, agregamos su reemplazo como tópico
        for synonym, replacement in self.LEGAL_SYNONYMS.items():
            if synonym in normalized and replacement not in topics:
                # Verificar que el reemplazo es un tópico válido
                if replacement in self.TOPIC_TO_ARTICLES:
                    topics.append(replacement)
        
        return topics
    
    def extract_specific_keywords(self, user_query: str) -> List[str]:
        """
        Extrae palabras clave específicas de la query para búsqueda RAG mejorada
        
        Ej: "vestiario" detecta exactamente ese término
        Retorna lista de keywords específicos detectados
        """
        lower_query = user_query.lower()
        specific_keywords = []
        
        # Keywords importantes para búsqueda
        important_keywords = [
            "vestuario", "uniforme", "implementos", "ropa de trabajo",
            "equipo de protección", "acto preparatorio", "cambio de ropa",
            "marcar hora", "reloj control", "protección personal",
            "jornada", "contrato", "remuneración", "sindicato",
            "despido", "terminación", "licencia", "maternidad"
        ]
        
        for keyword in important_keywords:
            if keyword in lower_query:
                specific_keywords.append(keyword)
        
        return specific_keywords
    
    def get_articles_for_topics(self, topics: List[str]) -> List[str]:
        """
        Mapea tópicos a números de artículos
        
        Args:
            topics: Lista de tópicos (ej: ["jornada", "descanso"])
        
        Returns:
            Lista de números de artículos (ej: ["21", "22", "40"])
        """
        articles = set()
        
        for topic in topics:
            if topic in self.TOPIC_TO_ARTICLES:
                articles.update(self.TOPIC_TO_ARTICLES[topic])
        
        return sorted(list(articles))
    
    def use_llm_for_article_mapping(self, user_query: str) -> List[str]:
        """
        Usa el LLM para mapear la query a artículos relevantes
        
        Útil cuando la query no coincide con keywords simples
        """
        prompt = f"""Eres un experto en Derecho Laboral chileno. 
El usuario hace esta pregunta sobre el Código del Trabajo:

"{user_query}"

Identifica los ARTÍCULOS del Código del Trabajo más relevantes para responder esta pregunta.
Responde SOLO con una lista de números de artículos separados por comas.
Ejemplo: "21, 22, 30, 32"

Si no conoces artículos específicos, devuelve una lista vacía."""
        
        try:
            response = groq_service.chat_simple(prompt)
            
            # Extraer números de la respuesta
            article_nums = re.findall(r'\d+', response)
            
            return article_nums
        
        except Exception as e:
            print(f"⚠️  Error en LLM mapping: {str(e)}")
            return []
    
    def get_best_articles(self, user_query: str, use_llm: bool = True) -> Dict:
        """
        Obtiene los artículos más relevantes para la query
        
        Proceso:
        1. Intenta matching de keywords
        2. Si no encuentra, usa LLM
        3. Retorna artículos con contexto
        """
        # Paso 1: Extraer tópicos
        topics = self.extract_topics(user_query)
        articles = self.get_articles_for_topics(topics)
        
        # Paso 2: Si no encuentra con keywords, usar LLM
        if not articles and use_llm:
            articles = self.use_llm_for_article_mapping(user_query)
        
        # Paso 3: Construir respuesta detallada
        result = {
            "user_query": user_query,
            "topics_found": topics,
            "articles": [],
            "confidence": "alta" if topics else "media" if articles else "baja"
        }
        
        for article_num in articles:
            if article_num in self.articles_by_number:
                node = self.articles_by_number[article_num]
                result["articles"].append({
                    "number": article_num,
                    "label": node.get("label", f"Art. {article_num}"),
                    "title": node.get("title", ""),
                    "description": node.get("description", ""),
                    "context": node.get("context", {})
                })
            else:
                # Artículo identificado pero no en grafo
                result["articles"].append({
                    "number": article_num,
                    "label": f"Art. {article_num}",
                    "title": "(Grafo no contiene este artículo)",
                    "available": False
                })
        
        return result
    
    def translate_query_language(self, user_query: str, source_language: str = "auto") -> str:
        """
        Traduce la query del usuario al español si es necesario
        
        Args:
            user_query: Pregunta del usuario
            source_language: "auto" para detectar automáticamente
        
        Returns:
            Query traducida al español
        """
        # Detectar si está en español
        spanish_keywords = ['qué', 'cuánto', 'cómo', 'dónde', 'por', 'para', 'el', 'la']
        is_spanish = any(kw in user_query.lower() for kw in spanish_keywords)
        
        if is_spanish or source_language == "es":
            return user_query
        
        # Traducir si no está en español
        prompt = f"""Traduce esta pregunta sobre Derecho Laboral al español:

"{user_query}"

Responde SOLO con la traducción, sin explicación."""
        
        try:
            translated = groq_service.chat_simple(prompt)
            return translated.strip()
        except Exception:
            return user_query
    
    def format_agent_response(self, mapping_result: Dict) -> str:
        """
        Formatea la respuesta del agente de manera legible
        """
        output = []
        output.append("\n" + "="*70)
        output.append("🤖 ANÁLISIS DE AGENTE - CÓDIGO DEL TRABAJO")
        output.append("="*70)
        
        output.append(f"\n📝 Tu pregunta:")
        output.append(f"   \"{mapping_result['user_query']}\"")
        
        if mapping_result['topics_found']:
            output.append(f"\n🏷️  Tópicos identificados:")
            for topic in mapping_result['topics_found']:
                output.append(f"   • {topic}")
        
        output.append(f"\n📋 Artículos relevantes (confianza: {mapping_result['confidence']}):")
        
        for article in mapping_result['articles']:
            if article.get("available", True):
                output.append(f"\n   {article['label']}: {article['title']}")
                if article['description']:
                    output.append(f"   → {article['description'][:80]}")
                if article['context']:
                    ctx = article['context']
                    if ctx.get('libro'):
                        output.append(f"   📚 Libro {ctx['libro']}")
            else:
                output.append(f"\n   {article['label']}: {article['title']}")
        
        output.append("\n" + "="*70 + "\n")
        
        return "\n".join(output)


def main():
    """Prueba rápida del agente"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Prueba del agente LLM")
    parser.add_argument("query", help="Pregunta sobre el Código del Trabajo")
    parser.add_argument("--graph", help="Ruta al grafo de artículos JSON")
    
    args = parser.parse_args()
    
    # Crear agente
    agent = LegalAgentCodigoTrabajo(args.graph)
    
    # Procesar query
    mapping = agent.get_best_articles(args.query)
    
    # Mostrar resultado
    print(agent.format_agent_response(mapping))


if __name__ == "__main__":
    main()
