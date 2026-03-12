import json
import os
from core.memory import MemoryManager
from core.emotions import EmotionManager
from core.interpreter import PrimaryInterpreter
from core.actor import Actor
from core.logger import loggers

class Engine:
    """
    Núcleo de processamento central. Orquestra a execução da Chain of Thought, 
    unificando a percepção lógica, a sensibilidade emocional e a memória.
    """

    # Inicializa as instâncias dos módulos core e carrega a configuração global, 
    # preparando o ambiente para o processamento de interações.
    def __init__(self):
        with open("config.json", "r") as f:
            self.cfg = json.load(f)
        
        self.interpreter = PrimaryInterpreter()
        self.actor = Actor()
        self.log = loggers["system"]["access"]

    # Carrega o arquivo de identidade da persona do diretório de dados 
    # utilizando o UUID para garantir que o estado base esteja acessível.
    def _load_persona_data(self, persona_id: str):
        path = f"data/personas/{persona_id}.json"
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    # Executa o ciclo completo de resposta, cruzando a análise do input com 
    # o contexto de memória recente antes de acionar a geração da fala.
    async def think(self, persona_id: str, user_input: str):
        persona_data = self._load_persona_data(persona_id)
        if not persona_data:
            return {"error": "Persona não encontrada"}

        memory = MemoryManager(persona_id)
        emotion = EmotionManager(persona_data)

        flash_context = memory.flash.get_context(limit=5)
        formatted_flash = "\n".join([f"{m['role']}: {m['content']}" for m in flash_context])

        analysis = await self.interpreter.analyze(user_input, chat_context=formatted_flash)
        
        rag_query = analysis.get("query_rag") or user_input
        context = await memory.get_full_context(query=rag_query, context_limit=10)
        current_emotions = emotion.get_current_state()

        reply_package = await self.actor.act(
            persona_data=persona_data,
            current_emotions=current_emotions,
            memories=context["relevant_memories"],
            history=context["recent_history"],
            user_input=user_input
        )

        await self._finalize_interaction(
            memory=memory,
            emotion=emotion,
            reply_package=reply_package,
            user_input=user_input
        )

        return reply_package

    # Extrai as informações do pacote de resposta gerado pelo Actor e as 
    # distribui para os respectivos bancos de dados e sistemas de estado.
    async def _finalize_interaction(self, memory, emotion, reply_package, user_input):
        await memory.record_interaction(role="user", content=user_input)
        
        full_response = " ".join(reply_package["interacao"]["mensagens"])
        await memory.record_interaction(role="assistant", content=full_response)
        
        shifts = reply_package["modificacoes_internas"]["roda_de_plutchik"]
        emotion.update_emotions_batch(shifts)
        
        new_facts = reply_package["atualizacoes_de_grafo"].get("novos_fatos", [])
        memory.process_graph_updates(new_facts)
        
        await memory.maintenance()
        self.log.info(f"Engine: Ciclo finalizado para {memory.persona_id}")
