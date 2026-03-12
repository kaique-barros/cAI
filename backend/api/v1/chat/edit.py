from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from core.memory import MemoryManager
from api.v1.chat.enqueue import active_queues
from core.logger import loggers

router = APIRouter()
log = loggers["chat"]["access"]

class EditRequest(BaseModel):
    """
    Esquema para a requisição de edição. Exige o ID da mensagem (se aplicável)
    e o novo conteúdo em texto que substituirá o fragmento anterior.
    """
    msg_id: int = None 
    new_content: str

class EditResponse(BaseModel):
    """
    Confirmação da alteração, indicando onde a retificação ocorreu 
    (na fila de buffer ou diretamente de forma global no SQLite e RAG).
    """
    status: str
    location: str

# Localiza a mensagem pendente na fila de agrupamento e a substitui, ou 
# aplica a correção globalmente na base de dados relacional e vetorial.
@router.patch("/edit/{persona_id}", response_model=EditResponse)
async def edit_message(
    request: EditRequest,
    persona_id: str = Path(..., description="UUID da persona")
):
    if persona_id in active_queues and active_queues[persona_id]["messages"]:
        active_queues[persona_id]["messages"][-1] = request.new_content
        log.info(f"ID:{persona_id} | Edit: Última mensagem na fila retificada.")
        return {"status": "success", "location": "buffer_queue"}
        
    if request.msg_id is not None:
        try:
            memory = MemoryManager(persona_id)
            memory.update_interaction(request.msg_id, request.new_content)
            log.info(f"ID:{persona_id} | Edit: Mensagem {request.msg_id} alterada globalmente.")
            return {"status": "success", "location": "database_and_rag"}
        except Exception as e:
            log.error(f"ID:{persona_id} | Erro ao editar memórias: {str(e)}")
            raise HTTPException(status_code=500, detail="Erro ao editar a base de dados.")

    raise HTTPException(status_code=400, detail="Nenhuma mensagem na fila e ID não fornecido.")
