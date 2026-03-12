import json
import uuid
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.memory import MemoryManager
from core.emotions import EmotionManager
from core.logger import loggers

router = APIRouter()
log = loggers["persona"]["access"]

class CreateResponse(BaseModel):
    """
    Esquema de retorno após a criação. Fornece o UUID gerado e 
    uma mensagem de confirmação de que os arquivos físicos estão prontos.
    """
    persona_id: str
    message: str

# Gera um novo identificador único, clona a ficha de persona padrão, salva 
# no diretório correto e inicializa os bancos de memória e emoção.
@router.post("/create", response_model=CreateResponse)
async def create_persona():
    new_id = str(uuid.uuid4())
    
    try:
        with open("data/models/persona.json", "r") as f:
            base_data = json.load(f)
            
        base_data["metadata"]["persona_id"] = new_id
        
        os.makedirs("data/personas", exist_ok=True)
        path = f"data/personas/{new_id}.json"
        
        with open(path, "w") as f:
            json.dump(base_data, f, indent=4)
            
        memory = MemoryManager(new_id)
        emotion = EmotionManager(base_data)
        
        log.info(f"ID:{new_id} | Persona instanciada. Pastas e DBs criados.")
        return {"persona_id": new_id, "message": "Estrutura física inicializada com sucesso."}
        
    except Exception as e:
        log.error(f"Falha ao criar persona: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao gerar estrutura física.")
