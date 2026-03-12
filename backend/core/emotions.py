import networkx as nx
import json
import math
import time
import os
from core.logger import loggers

class EmotionManager:
    """
    Controlador do sistema emocional baseado em grafos. Responsável por 
    armazenar, atualizar e aplicar o decaimento exponencial (erosão) 
    nos eixos de Plutchik da Persona.
    """

    # Inicializa as configurações de decaimento, identifica a persona pelo UUID 
    # e carrega o estado emocional pré-existente ou inicializa um novo.
    def __init__(self, persona_data: dict):
        with open("config.json", "r") as f:
            self.cfg = json.load(f)
            
        self.persona_data = persona_data
        self.persona_id = persona_data["metadata"]["persona_id"]
        self.graph_path = f"data/graphs/{self.persona_id}.json"
        
        motor = persona_data.get("motor_emocional", {})
        self.lambda_const = motor.get("config_erosao", {}).get("lambda_decaimento", 0.0001)
        
        self.log = loggers["chat"]["db"]
        
        os.makedirs(os.path.dirname(self.graph_path), exist_ok=True)
        self.G = self._load_graph()

    # Tenta recuperar o grafo serializado em disco; caso o arquivo não exista, 
    # dispara a criação de um grafo do zero baseado no temperamento basal.
    def _load_graph(self):
        if os.path.exists(self.graph_path):
            with open(self.graph_path, 'r') as f:
                return nx.node_link_graph(json.load(f))
        
        return self._create_base_graph()

    # Constrói a estrutura inicial do grafo NetworkX, vinculando a persona 
    # aos 8 eixos de Plutchik com os valores de repouso extraídos da ficha.
    def _create_base_graph(self):
        G = nx.Graph()
        G.add_node(self.persona_id, type="persona")
        
        basais = self.persona_data["motor_emocional"].get("roda_de_plutchik", {})
        emocoes = [
            "alegria", "confianca", "medo", "surpresa", 
            "tristeza", "nojo", "raiva", "antecipacao"
        ]
        
        for e in emocoes:
            val_basal = basais.get(e, 0.2)
            G.add_node(e, 
                type="emotion", 
                value=val_basal,
                basal=val_basal,
                last_update=time.time()
            )
            G.add_edge(self.persona_id, e)
            
        return G

    # Aplica a fórmula de erosão em todos os nós emocionais, calculando o 
    # retorno ao estado basal conforme o tempo decorrido desde o último update.
    def apply_erosion(self):
        now = time.time()
        for node, data in self.G.nodes(data=True):
            if data.get("type") == "emotion":
                v0 = data["value"]
                t0 = data["last_update"]
                basal = data.get("basal", 0.2)
                
                delta_t = now - t0
                novo_valor = basal + (v0 - basal) * math.exp(-self.lambda_const * delta_t)
                
                self.G.nodes[node]["value"] = round(novo_valor, 4)
                self.G.nodes[node]["last_update"] = now

    # Processa um conjunto de mudanças emocionais (shifts) enviadas pelo Actor, 
    # garantindo que os valores permaneçam no intervalo entre 0.0 e 1.0.
    def update_emotions_batch(self, shifts: dict):
        self.apply_erosion()
        for emotion, shift in shifts.items():
            if emotion in self.G.nodes:
                v_atual = self.G.nodes[emotion]["value"]
                novo_v = max(0.0, min(1.0, v_atual + shift))
                
                self.G.nodes[emotion].update({
                    "value": novo_v, 
                    "last_update": time.time()
                })
        
        self.save_state()

    # Retorna um dicionário com os valores atuais de cada emoção após a erosão, 
    # pronto para ser injetado no prompt de atuação do Actor.
    def get_current_state(self):
        self.apply_erosion()
        return {
            n: d["value"] 
            for n, d in self.G.nodes(data=True) 
            if d.get("type") == "emotion"
        }

    # Converte a estrutura de dados do NetworkX para um formato JSON compatível 
    # e persiste as alterações no sistema de arquivos local.
    def save_state(self):
        data = nx.node_link_data(self.G)
        with open(self.graph_path, 'w') as f:
            json.dump(data, f, indent=4)
        self.log.info(f"ID:{self.persona_id} | Grafo emocional sincronizado.")
