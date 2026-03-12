import httpx
import json
import os
from core.logger import loggers

class PrimaryInterpreter:
    """
    Unidade de triagem cognitiva. Responsável por analisar o input bruto, 
    identificar intenções e preparar os gatilhos de busca para o RAG.
    """

    # Carrega as definições de endpoint e o modelo de triagem do config.json, 
    # configurando a temperatura baixa para garantir respostas determinísticas.
    def __init__(self):
        with open("config.json", "r") as f:
            self.cfg = json.load(f)
        
        provider = self.cfg["active_provider"]
        self.url = f"{self.cfg['endpoints'][provider]}/api/generate"
        self.model = self.cfg["cot_models"]["interpreter"]
        self.temp = self.cfg["parameters"]["temperature_interpreter"]
        self.log = loggers["chat"]["access"]

    # Constrói um prompt instrutivo estruturado para o Phi-3.5, processa a 
    # resposta do LLM e valida o JSON resultante para orientar o Engine.
    async def analyze(self, user_input: str, chat_context: str = ""):
        prompt = f"""
        [INST] Sistema de Triagem Cognitiva. 
        Contexto Recente: {chat_context}
        
        Input do Usuário: "{user_input}"
        
        Gere um JSON com:
        1. "fato_resumido": Descrição objetiva em 3ª pessoa.
        2. "query_rag": Palavras-chave para busca em memórias passadas ou "".
        3. "intent": Uma opção entre [conversa_casual, requisicao_memoria, modificacao_persona, analise_midia].
        [/INST]
        JSON:"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.url, json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": self.temp}
                })
                
                raw_response = response.json().get('response', '{}')
                data = json.loads(raw_response)
                
                self.log.info(f"Interpreter: Intent '{data.get('intent')}' identificada.")
                return data
                
        except Exception as e:
            self.log.error(f"Falha na interpretação lógica: {str(e)}")
            return {
                "fato_resumido": user_input, 
                "query_rag": "", 
                "intent": "conversa_casual"
            }
