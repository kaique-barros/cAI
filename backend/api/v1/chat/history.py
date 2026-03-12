from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from core.memory import MemoryManager
from core.logger import loggers

router = APIRouter()
log = loggers["chat"]["access"]

class HistoryResponse(BaseModel):
    """
    Esquema de resposta contendo a lista sequencial de mensagens 
    recuperadas da memória cronológica imediata (Flash Memory).
    """
    messages: List[Dict[str, Any]]

# Recupera o histórico cronológico de uma persona específica, utilizando o 
# UUID diretamente na rota e permitindo a definição de um limite de mensagens.
@router.get("/history/{persona_id}", response_model=HistoryResponse)
async def get_history(
    persona_id: str = Path(..., description="O identificador único (UUID) da persona"), 
    limit: int = Query(50, le=200, description="Número máximo de mensagens a recuperar")
):
    try:
        memory = MemoryManager(persona_id)
        context = memory.flash.get_context(limit=limit)
        return {"messages": context}
    except Exception as e:
        log.error(f"ID:{persona_id} | Erro ao buscar histórico: {str(e)}")
        raise HTTPException(status_code=500, detail="Falha ao ler a base de dados local.")
