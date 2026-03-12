import time
from .flash import FlashMemory
from .rag import RAGMemory
from .graph import WorldGraph
from .summarization import Summarizer
from core.logger import loggers

class MemoryManager:
    """
    Orquestrador unificado de memória. Interface principal que integra 
    os quatro pilares de armazenamento para fornecer contexto à Persona.
    """

    # Inicializa todos os subcomponentes de memória vinculados ao UUID 
    # da persona e prepara o registrador de logs de base de dados.
    def __init__(self, persona_id: str):
        self.persona_id = persona_id
        self.flash = FlashMemory(persona_id)
        self.rag = RAGMemory(persona_id)
        self.graph = WorldGraph(persona_id)
        self.summarizer = Summarizer()
        self.log = loggers["chat"]["db"]

    # Salva uma nova mensagem no histórico linear e na memória vetorial, 
    # garantindo que a informação esteja disponível para RAG e contexto imediato.
    async def record_interaction(self, role: str, content: str, to_rag: bool = True):
        msg_id = self.flash.save(role, content)
        
        if to_rag:
            self.rag.save(content, role, msg_id)
            
        return msg_id

    # Compila um pacote completo de contexto contendo as mensagens recentes, 
    # fatos recuperados do grafo e memórias semânticas relevantes para a query.
    async def get_full_context(self, query: str, context_limit: int = 10):
        flash_msgs = self.flash.get_context(limit=context_limit)
        
        rag_results = self.rag.search(query, n_results=3)
        
        keywords = query.split()
        graph_facts = self.graph.search_facts(keywords)
        
        return {
            "recent_history": flash_msgs,
            "relevant_memories": rag_results,
            "world_facts": graph_facts
        }

    # Processa novos conhecimentos adquiridos durante a conversa, 
    # atualizando o grafo de mundo com novas entidades e relações.
    def learn_new_fact(self, source: str, target: str, relation: str):
        self.graph.add_relation(source, target, relation)
        self.graph.save()
        self.log.info(f"ID:{self.persona_id} | Memory: Fato aprendido e persistido.")

    # Aciona o summarizer para condensar o histórico do Flash. Se gerado, 
    # guarda o resumo no ChromaDB e limpa o SQLite para evitar loops de resumo.
    async def maintenance(self):
        history = self.flash.get_context(limit=50)
        
        if self.summarizer.needs_summarization(len(history)):
            new_summary = await self.summarizer.summarize_messages(history)
            
            summary_id = int(time.time())
            self.rag.save(content=new_summary, role="system_summary", msg_id=summary_id)
            
            self.flash.clear_history()
            
            self.log.info(f"ID:{self.persona_id} | Memory: Resumo guardado e Flash limpo.")
            return new_summary
            
        return None

    # Recebe os fatos estruturados vindos do Actor e os distribui para o 
    # WorldGraph, enquanto garante que a mensagem bruta já esteja no RAG.
    def process_graph_updates(self, facts: list):
        if not facts:
            return

        for fact in facts:
            self.graph.add_relation(
                fact.get("origem"), 
                fact.get("destino"), 
                fact.get("relacao")
            )
        
        self.graph.save()
        self.log.info(f"ID:{self.persona_id} | Memory: {len(facts)} novos fatos integrados.")

    # Localiza e substitui o conteúdo de uma mensagem específica em ambos 
    # os bancos (SQLite e ChromaDB), garantindo a consistência da memória global.
    def update_interaction(self, msg_id: int, new_content: str):
        self.flash.update(msg_id, new_content)
        self.rag.update(msg_id, new_content)
        self.log.info(f"ID:{self.persona_id} | Memory: Interação {msg_id} sincronizada após edição.")
