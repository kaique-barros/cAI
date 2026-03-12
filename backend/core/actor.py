import httpx
import json
import os
from core.logger import loggers

class Actor:
    """
    Controlador de atuação e extração de conhecimento. Converte o estado 
    interno e o contexto em uma resposta JSON estruturada que alimenta 
    os sistemas de chat, emoção e grafos.
    """

    # Carrega as configurações de rede, os modelos de IA e o contrato de 
    # resposta dinâmico definido no arquivo actor_reply.json.
    def __init__(self):
        with open("config.json", "r") as f:
            self.cfg = json.load(f)
        
        with open("data/models/actor_reply.json", "r") as f:
            self.reply_schema = json.load(f)

        provider = self.cfg["active_provider"]
        self.url = f"{self.cfg['endpoints'][provider]}/api/generate"
        self.model = self.cfg["cot_models"]["actor"]
        self.log = loggers["chat"]["access"]

    # Constrói o prompt de sistema injetando a ficha da persona, emoções e 
    # o esquema de resposta, solicitando a extração de fatos para o grafo.
    async def act(self, persona_data: dict, current_emotions: dict, memories: list, history: list, user_input: str):
        id_base = persona_data['identidade_base']
        estilo = persona_data['estilo_de_escrita']
        
        system_prompt = f"""
        [ROLEPLAY SYSTEM - PERSONA: {id_base['nome']}]
        Identidade: {persona_data['psicologia_profunda']}
        Estado Emocional: {json.dumps(current_emotions)}
        Contexto Memória (RAG): {memories}

        TAREFA: Responda ao usuário e extraia fatos novos para sua memória de longo prazo.
        Siga ESTRITAMENTE o formato JSON:
        {json.dumps(self.reply_schema, indent=2)}
        
        REGRAS DE EXTRAÇÃO PARA 'novos_fatos':
        - Se o usuário disser algo pessoal ("Tenho um gato"), adicione: {{"origem": "User", "relacao": "tem_animal", "destino": "gato"}}.
        - Identifique nomes de pessoas, lugares e preferências.
        - Se não houver fatos novos, deixe a lista vazia [].
        
        REGRAS DE FALA:
        - Use o estilo: Formalidade {estilo['formalidade']}, Vícios: {estilo['vicios_de_linguagem']}.
        - Mantenha-se no personagem. Responda apenas com o JSON.
        """

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.url, json={
                    "model": self.model,
                    "system": system_prompt,
                    "prompt": f"Histórico:\n{history}\n\nUsuário: {user_input}\n{id_base['nome']}:",
                    "stream": False,
                    "format": "json",
                    "options": { "temperature": self.cfg["parameters"]["temperature_actor"] }
                })
                
                parsed_reply = json.loads(response.json().get('response', '{}'))
                self.log.info(f"ID:{persona_data['metadata']['persona_id']} | Actor: Resposta e fatos gerados.")
                return parsed_reply
                
        except Exception as e:
            self.log.error(f"Erro no Actor ao processar JSON: {str(e)}")
            fallback = self.reply_schema.copy()
            fallback["interacao"]["mensagens"] = ["Minha mente divagou por um segundo..."]
            return fallback
