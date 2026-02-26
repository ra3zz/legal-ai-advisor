"""
Servicio de Grafo RAG - Integración de Grafo de Conocimiento con RAG
Funcionalidades:
- Cargar grafo JSON desde archivo
- Buscar entidades en el grafo
- Encontrar nodos relacionados
- Reranking de documentos basado en conexiones del grafo
- Enriquecimiento de contexto con información del grafo
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import re


class GraphService:
    """Servicio para manejar el grafo de conocimiento"""
    
    def __init__(self):
        self.graph = None
        self.nodes = {}  # {id: {label, type, description}}
        self.edges = []
        self.node_by_label = {}  # Índice de búsqueda rápida por label
        self.adjacency = {}  # {node_id: set(connected_node_ids)}
        self.is_loaded = False
    
    def load_graph(self, graph_path: str) -> bool:
        """Cargar grafo desde archivo JSON"""
        try:
            if not os.path.exists(graph_path):
                print(f"⚠️  Grafo no encontrado: {graph_path}")
                return False
            
            with open(graph_path, 'r', encoding='utf-8') as f:
                self.graph = json.load(f)
            
            # Parsear nodos - los ID vienen como parte de los edges
            self.nodes = {}
            self.node_by_label = {}
            self.edges = self.graph.get('edges', [])
            
            # Recolectar todos los IDs de los edges para crear nodos
            all_node_ids = set()
            for edge in self.edges:
                all_node_ids.add(edge.get('source'))
                all_node_ids.add(edge.get('target'))
            
            # Procesar nodos del JSON
            for idx, node in enumerate(self.graph.get('nodes', [])):
                # Crear ID si no existe - usar index como fallback
                node_id = f"n{idx}"  # Generar ID consistente
                label = node.get('label', '').lower()
                
                node_data = node.copy()
                node_data['_label_search'] = label  # Para búsqueda
                self.nodes[node_id] = node_data
                
                # Índice por label para búsqueda
                if label not in self.node_by_label:
                    self.node_by_label[label] = []
                self.node_by_label[label].append(node_id)
            
            # IMPORTANTE: mapear IDs de edges a nuestros IDs de nodos basados en labels
            # Los edges tienen IDs como 'E1', 'E2' que corresponden a descripciones
            # Necesitamos normalizar esto
            
            # Primero, crear un mapa de labels encontrados en edges
            edge_labels_map = {}  # {edge_node_id: label}
            
            # Leer el JSON source para obtener información de aristas
            remapped_edges = []
            
            # Construir adyacencia SIN mappings por ahora
            # La idea es usar los IDs directamente del grafo
            self.adjacency = {node_id: set() for node_id in self.nodes.keys()}
            
            # Remapear edges a IDs de nodos válidos
            for edge in self.edges:
                source = edge.get('source')
                target = edge.get('target')
                
                # Buscar source en nodos por label aproximado
                source_node_id = self._find_node_by_id_or_label(source)
                target_node_id = self._find_node_by_id_or_label(target)
                
                if source_node_id and target_node_id:
                    if source_node_id not in self.adjacency:
                        self.adjacency[source_node_id] = set()
                    if target_node_id not in self.adjacency:
                        self.adjacency[target_node_id] = set()
                    
                    self.adjacency[source_node_id].add(target_node_id)
                    self.adjacency[target_node_id].add(source_node_id)  # Grafo no dirigido
                    
                    remapped_edges.append({
                        'source': source_node_id,
                        'target': target_node_id,
                        'relation': edge.get('relation', 'related_to'),
                        'weight': edge.get('weight', 0.5)
                    })
            
            self.edges = remapped_edges
            
            self.is_loaded = True
            metadata = self.graph.get('metadata', {})
            print(f"✅ Grafo cargado: {len(self.nodes)} nodos, "
                  f"{len(self.edges)} relaciones")
            return True
        
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ Error cargando grafo: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _find_node_by_id_or_label(self, node_ref: str) -> Optional[str]:
        """
        Encuentra un nodo por ID o label
        node_ref puede ser un ID como 'E1' o un label
        """
        # Buscar primero por label exact
        for node_id, node in self.nodes.items():
            if node.get('label', '').lower() == node_ref.lower():
                return node_id
        
        # Si no encuentra, buscar por coincidencia parcial
        for node_id, node in self.nodes.items():
            if node_ref.lower() in node.get('label', '').lower():
                return node_id
        
        # Si aún no encuentra y es un ID corto, tomar el primer nodo
        # (fallback para when IDs no corresponden directo)
        if len(self.nodes) > 0 and node_ref.startswith('E'):
            # Intenta convertir E1, E2, etc. a índices
            try:
                idx = int(node_ref[1:]) - 1  # E1 -> 0, E2 -> 1, etc.
                if 0 <= idx < len(self.nodes):
                    return f"n{idx}"
            except:
                pass
        
        return None
    
    def find_nodes_by_text(self, text: str, top_k: int = 5) -> List[Dict]:
        """
        Buscar nodos que coincidan con el texto
        Busca en labels y descriptions
        """
        if not self.is_loaded:
            return []
        
        # Normalizar texto de búsqueda
        search_terms = set(text.lower().split())
        
        scored_nodes = []
        
        for node_id, node in self.nodes.items():
            label = node.get('label', '').lower()
            description = node.get('description', '').lower()
            
            # Score por coincidencia en label (más importante)
            label_score = sum(1 for term in search_terms if term in label)
            
            # Score por coincidencia en description
            desc_score = sum(1 for term in search_terms if term in description) * 0.5
            
            total_score = label_score + desc_score
            
            if total_score > 0:
                scored_nodes.append((node_id, node, total_score))
        
        # Ordenar por score
        scored_nodes.sort(key=lambda x: x[2], reverse=True)
        
        return [{'id': nid, **node, 'match_score': score} 
                for nid, node, score in scored_nodes[:top_k]]
    
    def get_related_nodes(self, node_id: str, max_depth: int = 2) -> Set[str]:
        """
        Obtener todos los nodos relacionados a uno dado
        max_depth: profundidad de búsqueda en el grafo
        """
        if not self.is_loaded or node_id not in self.nodes:
            return set()
        
        related = {node_id}
        to_explore = {node_id}
        current_depth = 0
        
        while to_explore and current_depth < max_depth:
            next_layer = set()
            
            for current in to_explore:
                # Agregar vecinos
                neighbors = self.adjacency.get(current, set())
                for neighbor in neighbors:
                    if neighbor not in related:
                        related.add(neighbor)
                        next_layer.add(neighbor)
            
            to_explore = next_layer
            current_depth += 1
        
        return related
    
    def extract_entities_from_text(self, text: str) -> Dict[str, List[Dict]]:
        """
        Extraer entidades mencionadas en el texto usando el grafo
        Retorna: {entity_type: [{id, label, score}, ...]}
        """
        if not self.is_loaded:
            return {}
        
        text_lower = text.lower()
        entities_found = {}
        
        for node_id, node in self.nodes.items():
            label = node.get('label', '')
            node_type = node.get('type', 'unknown')
            
            # Buscar el label en el texto (case insensitive)
            if label.lower() in text_lower:
                if node_type not in entities_found:
                    entities_found[node_type] = []
                
                entities_found[node_type].append({
                    'id': node_id,
                    'label': label,
                    'type': node_type,
                    'description': node.get('description', '')
                })
        
        return entities_found
    
    def get_entity_context(self, node_id: str) -> str:
        """
        Obtener contexto enriquecido de una entidad
        Incluye: descripción + relaciones principales
        """
        if not self.is_loaded or node_id not in self.nodes:
            return ""
        
        node = self.nodes[node_id]
        context = f"Entidad: {node.get('label', '')}\n"
        context += f"Tipo: {node.get('type', '')}\n"
        
        if node.get('description'):
            context += f"Descripción: {node.get('description')}\n"
        
        # Encontrar edges relacionados
        related_edges = []
        for edge in self.edges:
            if edge.get('source') == node_id or edge.get('target') == node_id:
                related_edges.append(edge)
        
        if related_edges:
            context += "\nRelaciones:\n"
            for edge in related_edges[:5]:  # Limitar a 5 relaciones
                relation = edge.get('relation', 'connected_to')
                if edge.get('source') == node_id:
                    target_id = edge.get('target')
                    target_label = self.nodes.get(target_id, {}).get('label', 'Unknown')
                    context += f"  → {relation}: {target_label}\n"
                else:
                    source_id = edge.get('source')
                    source_label = self.nodes.get(source_id, {}).get('label', 'Unknown')
                    context += f"  ← {relation}: {source_label}\n"
        
        return context
    
    def rerank_documents_with_graph(self, 
                                   query: str, 
                                   documents: List[Dict],
                                   boost_factor: float = 0.3) -> List[Dict]:
        """
        Reranking de documentos usando información del grafo
        
        Estrategia:
        1. Encontrar entidades mencionadas en la query
        2. Para cada documento, ver cuántas entidades relacionadas contiene
        3. Boostar score de documentos con más entidades relacionadas
        
        boost_factor: qué tanto boost dar (0-1, recomendado 0.2-0.4)
        """
        if not self.is_loaded or not documents:
            return documents
        
        # Encontrar entidades en la query
        query_entities = self.extract_entities_from_text(query)
        
        if not query_entities:
            return documents
        
        # Aplanar lista de entidades encontradas
        all_query_entities = []
        for entity_type, entities in query_entities.items():
            all_query_entities.extend([e['id'] for e in entities])
        
        # Para cada documento, calcular factor de boost
        reranked = []
        
        for doc in documents:
            doc_copy = doc.copy()
            
            # Extraer entidades del documento
            doc_entities = self.extract_entities_from_text(doc.get('text', ''))
            doc_entity_ids = []
            for entity_type, entities in doc_entities.items():
                doc_entity_ids.extend([e['id'] for e in entities])
            
            # Calcular superposición de entidades
            matching_entities = set(all_query_entities) & set(doc_entity_ids)
            
            if matching_entities:
                # Calcular también relaciones indirectas
                related_to_query = set()
                for entity_id in all_query_entities:
                    related = self.get_related_nodes(entity_id, max_depth=1)
                    related_to_query.update(related)
                
                connectivity_score = len(matching_entities & related_to_query) / len(related_to_query) if related_to_query else 0
                
                # Aplicar boost
                original_score = doc.get('score', 0)
                boost = connectivity_score * boost_factor
                doc_copy['score'] = original_score + boost
                doc_copy['graph_boost'] = boost
                doc_copy['matching_entities'] = list(matching_entities)
            else:
                doc_copy['graph_boost'] = 0
                doc_copy['matching_entities'] = []
            
            reranked.append(doc_copy)
        
        # Reordenar por nuevo score
        reranked.sort(key=lambda x: x['score'], reverse=True)
        
        return reranked
    
    def enrich_context(self, 
                      query: str,
                      documents: List[Dict],
                      max_entities: int = 5) -> str:
        """
        Enriquecer contexto con información del grafo
        
        Retorna: string con contexto enriquecido del grafo
        """
        if not self.is_loaded:
            return ""
        
        # Encontrar entidades relevantes
        relevant_entities = set()
        
        # De la query
        query_entities = self.extract_entities_from_text(query)
        for entity_type, entities in query_entities.items():
            relevant_entities.update([e['id'] for e in entities])
        
        # De los documentos
        for doc in documents:
            doc_entities = self.extract_entities_from_text(doc.get('text', ''))
            for entity_type, entities in doc_entities.items():
                relevant_entities.update([e['id'] for e in entities])
        
        if not relevant_entities:
            return ""
        
        # Construir contexto del grafo
        context = "📊 CONTEXTO DEL GRAFO DE CONOCIMIENTO:\n\n"
        
        added = 0
        for entity_id in list(relevant_entities)[:max_entities]:
            entity_context = self.get_entity_context(entity_id)
            if entity_context:
                context += entity_context + "\n---\n"
                added += 1
        
        if added > 0:
            return context
        
        return ""
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del grafo"""
        if not self.is_loaded:
            return {'status': 'No loaded'}
        
        entity_types = {}
        for node in self.nodes.values():
            node_type = node.get('type', 'unknown')
            entity_types[node_type] = entity_types.get(node_type, 0) + 1
        
        relation_types = {}
        for edge in self.edges:
            rel_type = edge.get('relation', 'unknown')
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
        
        return {
            'nodes': len(self.nodes),
            'edges': len(self.edges),
            'entity_types': entity_types,
            'relation_types': relation_types,
            'most_connected': sorted(
                [(nid, len(self.adjacency.get(nid, []))) 
                 for nid in self.nodes.keys()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


# Instancia global
graph_service = GraphService()
