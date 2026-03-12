import json
import os
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from typing import Dict, Any
from core.logger import loggers

router = APIRouter()
log = loggers["persona"]["access"]

class UIUpdateRequest(BaseModel):
    """
    Esquema para atualização das configurações visuais da persona.
    Espera receber o bloco completo ou parcial de 'aparencia_e_ui'.
    """
    aparencia_e_ui: Dict[str, Any]

class UIResponse(BaseModel):
    """
    Devolve os dados de configuração de interface de utilizador.
    """
    data: Dict[str, Any]

# Lê o ficheiro da persona e devolve exclusivamente o bloco de dados 
# referente à sua aparência física, estilo de vestuário e configurações de chat.
@router.get("/ui/{persona_id}", response_model=UIResponse)
async def get_persona_ui(persona_id: str = Path(..., description="UUID da persona")):
    path = f"data/personas/{persona_id}.json"
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Persona não encontrada.")
        
    try:
        with open(path, "r") as f:
            data = json.load(f)
            
        ui_data = data.get("aparencia_e_ui", {})
        return {"data": ui_data}
        
    except Exception as e:
        log.error(f"ID:{persona_id} | Erro ao ler UI: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao ler as definições de UI.")

# Recebe um dicionário com as novas definições visuais, funde com os dados 
# já existentes no bloco 'aparencia_e_ui' e guarda as alterações em disco.
@router.patch("/ui/{persona_id}", response_model=UIResponse)
async def update_persona_ui(request: UIUpdateRequest, persona_id: str = Path(...)):
    path = f"data/personas/{persona_id}.json"
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Persona não encontrada.")
        
    try:
        with open(path, "r") as f:
            data = json.load(f)
            
        if "aparencia_e_ui" not in data:
            data["aparencia_e_ui"] = {}
            
        data["aparencia_e_ui"].update(request.aparencia_e_ui)
        
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
            
        log.info(f"ID:{persona_id} | UI/Estética atualizada com sucesso.")
        return {"data": {"status": "success", "message": "Definições visuais atualizadas."}}
        
    except Exception as e:
        log.error(f"ID:{persona_id} | Erro ao atualizar UI: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao guardar atualizações visuais.")
