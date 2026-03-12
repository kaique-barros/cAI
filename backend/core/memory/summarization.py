import httpx
import json
import os
from core.logger import loggers

class Summarizer:
    """
    Gerenciador de compressão de contexto. Responsável por transformar 
    múltiplas interações em um resumo conciso para otimizar o uso de tokens.
    """

    # Carrega as definições de modelo e endpoint do arquivo de configuração 
    # global para preparar as chamadas de inferência de sumarização.
    def __init__(self):
        with open("config.json", "r") as f:
            self.cfg = json.load(f)
        
        provider = self.cfg["active_provider"]
        self.url = f"{self.cfg['endpoints'][provider]}/api/generate"
        self.model = self.cfg["cot_models"]["summarizer"]
        self.log = loggers["system"]["access"]

    # Envia um bloco de mensagens para o LLM com instruções rígidas de 
    # condensação, retornando apenas os fatos essenciais e o estado da conversa.
    async def summarize_messages(self, messages: list):
        formatted_history = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        prompt = f"""
        [INST] SUMARIZE A CONVERSA ABAIXO. 
        Mantenha nomes, datas, promessas e fatos importantes. 
        Seja extremamente conciso e direto ao ponto.
        
        HISTÓRICO:
        {formatted_history}
        [/INST]
        RESUMO FACTUAL:"""

        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                response = await client.post(self.url, json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                })
                
                summary = response.json().get('response', '').strip()
                self.log.info("Summarization: Novo resumo gerado com sucesso.")
                return summary
                
        except Exception as e:
            self.log.error(f"Erro ao gerar resumo: {str(e)}")
            return "Erro ao processar resumo de contexto."

    # Verifica se a quantidade de mensagens no buffer atual justifica uma 
    # nova rodada de sumarização para manter a eficiência do sistema.
    def needs_summarization(self, current_count: int, threshold: int = 15):
        return current_count >= threshold
