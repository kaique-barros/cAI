from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from core.memory import MemoryManager
from core.emotions import EmotionManager
from core.logger import loggers
import os
import json

router = APIRouter()
log = loggers["system"]["access"]

class SyncResponse(BaseModel):
    """
    Confirmação de que as estruturas de grafo e o decaimento 
    emocional foram devidamente serializados no formato JSON.
    """
    status: str
    message: str

# Carrega a ficha da persona e aciona os métodos manuais de gravação 
# dos módulos de memória e emoção, prevenindo perda de dados voláteis.
@router.post("/sync/{persona_id}", response_model=SyncResponse)
async def force_sync(persona_id: str = Path(..., description="UUID da persona")):
    path = f"data/personas/{persona_id}.json"
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Persona não encontrada.")
        
    try:
        with open(path, "r") as f:
            persona_data = json.load(f)
            
        memory = MemoryManager(persona_id)
        emotion = EmotionManager(persona_data)
        
        memory.graph.save()
        emotion.save_state()
        
        log.info(f"ID:{persona_id} | System: Sincronização manual concluída.")
        return {"status": "success", "message": "Dados sincronizados com sucesso."}
        
    except Exception as e:
        log.error(f"ID:{persona_id} | System: Falha na sincronização: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno na sincronização.")
