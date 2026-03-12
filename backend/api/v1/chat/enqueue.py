import asyncio
import json
from fastapi import APIRouter, Path
from pydantic import BaseModel
from typing import List, Dict, Any
from core.engine import Engine
from core.logger import loggers

router = APIRouter()
engine = Engine()
log = loggers["chat"]["access"]

with open("config.json", "r") as f:
    cfg = json.load(f)

BUFFER_DELAY = cfg["parameters"]["buffer_delay_seconds"]
active_queues = {}
completed_responses = {}

class EnqueueRequest(BaseModel):
    """
    Esquema de validação para mensagens curtas que entrarão 
    na fila de espera para agrupamento de contexto.
    """
    user_input: str

class EnqueueResponse(BaseModel):
    """
    Confirmação de recebimento do fragmento, indicando o 
    status atual do buffer na memória.
    """
    status: str
    queued_messages: int
    delay_seconds: int

class PollResponse(BaseModel):
    """
    Esquema de resposta para o polling do frontend, contendo 
    todas as respostas processadas pela IA que aguardam entrega.
    """
    pending_responses: List[Dict[str, Any]]

# Aguarda em segundo plano o tempo de silêncio estipulado. Se não houver 
# interrupção, mescla os fragmentos, aciona o motor e guarda o resultado.
async def process_queue(persona_id: str):
    await asyncio.sleep(BUFFER_DELAY)
    
    queue_data = active_queues.get(persona_id)
    if not queue_data or not queue_data["messages"]:
        return
        
    merged_input = " \n ".join(queue_data["messages"])
    active_queues[persona_id]["messages"] = []
    
    try:
        reply_package = await engine.think(persona_id=persona_id, user_input=merged_input)
        
        if persona_id not in completed_responses:
            completed_responses[persona_id] = []
            
        completed_responses[persona_id].append(reply_package)
        log.info(f"ID:{persona_id} | Fila processada. Resposta pronta para entrega.")
        
    except Exception as e:
        log.error(f"ID:{persona_id} | Erro no processamento em lote: {str(e)}")

# Recebe fragmentos de mensagens do utilizador e reinicia o cronómetro 
# interno (debounce), impedindo chamadas desnecessárias à LLM.
@router.post("/enqueue/{persona_id}", response_model=EnqueueResponse)
async def enqueue_message(
    request: EnqueueRequest,
    persona_id: str = Path(..., description="UUID da persona")
):
    if persona_id not in active_queues:
        active_queues[persona_id] = {"messages": [], "task": None}
        
    active_queues[persona_id]["messages"].append(request.user_input)
    
    if active_queues[persona_id]["task"]:
        active_queues[persona_id]["task"].cancel()
        
    active_queues[persona_id]["task"] = asyncio.create_task(process_queue(persona_id))
    
    log.info(f"ID:{persona_id} | Fragmento retido. Fila: {len(active_queues[persona_id]['messages'])}")
    
    return {
        "status": "enqueued",
        "queued_messages": len(active_queues[persona_id]["messages"]),
        "delay_seconds": BUFFER_DELAY
    }

# Rota de polling para o frontend. Verifica se existem respostas processadas 
# pela background task, devolve-as e limpa o buffer de entrega.
@router.get("/enqueue/{persona_id}", response_model=PollResponse)
async def poll_responses(persona_id: str = Path(..., description="UUID da persona")):
    responses = completed_responses.get(persona_id, [])
    
    if responses:
        completed_responses[persona_id] = []
        
    return {"pending_responses": responses}
