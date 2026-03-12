import networkx as nx
import json
import os
from core.logger import loggers

class WorldGraph:
    """
    Controlador de memória relacional. Responsável por mapear entidades, 
    conceitos e seus relacionamentos utilizando a estrutura de grafos.
    """

    # Define o caminho do arquivo JSON para persistência, identifica o dono 
    # da memória via UUID e carrega a estrutura do grafo existente.
    def __init__(self, persona_id: str):
        self.persona_id = persona_id
        self.path = f"data/graphs/{self.persona_id}_world.json"
        self.log = loggers["chat"]["db"]
        
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.G = self._load()

    # Tenta ler o grafo serializado do disco; caso não encontre o arquivo, 
    # inicializa um novo grafo com o nó central representando o Usuário.
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                return nx.node_link_graph(json.load(f))
        
        G = nx.Graph()
        G.add_node("User", type="entity", label="Usuário")
        return G

    # Adiciona uma nova entidade (pessoa, lugar, objeto) ao grafo ou atualiza 
    # os atributos de uma entidade já existente na memória.
    def add_entity(self, entity_id: str, attributes: dict):
        self.G.add_node(entity_id, **attributes)
        self.log.info(f"ID:{self.persona_id} | Grafo: Entidade '{entity_id}' adicionada.")

    # Estabelece um vínculo entre duas entidades, definindo a natureza da 
    # relação (ex: 'amigo_de', 'localizado_em') através de uma aresta.
    def add_relation(self, source: str, target: str, relation_type: str):
        if source not in self.G: self.G.add_node(source, type="entity")
        if target not in self.G: self.G.add_node(target, type="entity")
        
        self.G.add_edge(source, target, relation=relation_type)
        self.log.info(f"ID:{self.persona_id} | Grafo: Relação '{source} -> {relation_type} -> {target}' criada.")

    # Localiza todas as conexões diretas de uma entidade específica, permitindo 
    # reconstruir o contexto social ou factual ao redor de um termo.
    def get_connections(self, entity_id: str):
        if entity_id not in self.G:
            return []
            
        connections = []
        for neighbor in self.G.neighbors(entity_id):
            edge_data = self.G.get_edge_data(entity_id, neighbor)
            connections.append({
                "to": neighbor,
                "relation": edge_data.get("relation", "conhece")
            })
        return connections

    # Realiza uma busca profunda no grafo para extrair fatos relevantes baseados 
    # em palavras-chave, retornando uma descrição textual das relações encontradas.
    def search_facts(self, keywords: list):
        facts = []
        for word in keywords:
            if word in self.G:
                conn = self.get_connections(word)
                for c in conn:
                    facts.append(f"{word} é {c['relation']} de {c['to']}")
        
        return facts

    # Converte o estado atual do NetworkX para o formato node-link e persiste 
    # os dados em um arquivo JSON para garantir a durabilidade da memória.
    def save(self):
        data = nx.node_link_data(self.G)
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=4)
        self.log.info(f"ID:{self.persona_id} | Grafo de mundo sincronizado.")
