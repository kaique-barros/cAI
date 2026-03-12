import json
import os
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from typing import Dict, Any
from core.logger import loggers

router = APIRouter()
log = loggers["persona"]["access"]

class BlockUpdateRequest(BaseModel):
    """
    Esquema genérico para a requisição de atualização.
    Recebe um dicionário flexível correspondente ao bloco modificado.
    """
    data: Dict[str, Any]

class BlockResponse(BaseModel):
    """
    Esquema genérico de resposta, devolvendo o bloco de dados 
    lido ou o status da atualização.
    """
    data: Dict[str, Any]

# Função auxiliar interna que isola a lógica de leitura do disco, 
# recuperando apenas o bloco específico solicitado do arquivo JSON da persona.
def _get_core_block(persona_id: str, block_name: str) -> dict:
    path = f"data/personas/{persona_id}.json"
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Persona não encontrada.")
        
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data.get(block_name, {})
        
    except Exception as e:
        log.error(f"ID:{persona_id} | Erro ao ler {block_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao ler {block_name}.")

# Função auxiliar interna que isola a lógica de escrita, fundindo as 
# alterações parciais recebidas com o bloco existente e salvando em disco.
def _update_core_block(persona_id: str, block_name: str, payload: dict) -> dict:
    path = f"data/personas/{persona_id}.json"
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Persona não encontrada.")
        
    try:
        with open(path, "r") as f:
            data = json.load(f)
            
        if block_name not in data:
            data[block_name] = {}
            
        data[block_name].update(payload)
        
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
            
        log.info(f"ID:{persona_id} | Core: Bloco '{block_name}' atualizado.")
        return {"status": "success", "message": f"Bloco {block_name} atualizado."}
        
    except Exception as e:
        log.error(f"ID:{persona_id} | Erro ao atualizar {block_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar {block_name}.")

# Recupera todos os dados centrais (core) da persona de uma só vez, 
# agrupando os cinco pilares que formam a alma da IA para o frontend.
@router.get("/core/{persona_id}", response_model=BlockResponse)
async def get_full_core(persona_id: str = Path(..., description="UUID da persona")):
    path = f"data/personas/{persona_id}.json"
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Persona não encontrada.")
        
    try:
        with open(path, "r") as f:
            data = json.load(f)
            
        core_data = {
            "identidade_base": data.get("identidade_base", {}),
            "psicologia_profunda": data.get("psicologia_profunda", {}),
            "backstory": data.get("backstory", {}),
            "motor_emocional": data.get("motor_emocional", {}),
            "estilo_de_escrita": data.get("estilo_de_escrita", {})
        }
        
        return {"data": core_data}
        
    except Exception as e:
        log.error(f"ID:{persona_id} | Erro ao ler o core completo: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao ler os dados da persona.")

# ---------------------------------------------------------
# ROTAS INDIVIDUAIS POR ELEMENTO
# ---------------------------------------------------------

# Recupera os dados fundamentais de identidade da persona.
@router.get("/core/{persona_id}/identidade_base", response_model=BlockResponse)
async def get_identidade_base(persona_id: str = Path(..., description="UUID da persona")):
    return {"data": _get_core_block(persona_id, "identidade_base")}

# Atualiza parcialmente os dados de identidade (nome, idade, arquétipo).
@router.patch("/core/{persona_id}/identidade_base", response_model=BlockResponse)
async def update_identidade_base(request: BlockUpdateRequest, persona_id: str = Path(...)):
    return {"data": _update_core_block(persona_id, "identidade_base", request.data)}

# Recupera as configurações psicológicas da persona.
@router.get("/core/{persona_id}/psicologia_profunda", response_model=BlockResponse)
async def get_psicologia_profunda(persona_id: str = Path(...)):
    return {"data": _get_core_block(persona_id, "psicologia_profunda")}

# Atualiza parcialmente os objetivos, medos ou interesses da IA.
@router.patch("/core/{persona_id}/psicologia_profunda", response_model=BlockResponse)
async def update_psicologia_profunda(request: BlockUpdateRequest, persona_id: str = Path(...)):
    return {"data": _update_core_block(persona_id, "psicologia_profunda", request.data)}

# Recupera a história de origem e narrativa da persona.
@router.get("/core/{persona_id}/backstory", response_model=BlockResponse)
async def get_backstory(persona_id: str = Path(...)):
    return {"data": _get_core_block(persona_id, "backstory")}

# Atualiza parcialmente a história de fundo e relacionamentos conhecidos.
@router.patch("/core/{persona_id}/backstory", response_model=BlockResponse)
async def update_backstory(request: BlockUpdateRequest, persona_id: str = Path(...)):
    return {"data": _update_core_block(persona_id, "backstory", request.data)}

# Recupera o estado de repouso emocional (valores basais da Roda de Plutchik).
@router.get("/core/{persona_id}/motor_emocional", response_model=BlockResponse)
async def get_motor_emocional(persona_id: str = Path(...)):
    return {"data": _get_core_block(persona_id, "motor_emocional")}

# Atualiza parcialmente a velocidade de decaimento ou os valores emocionais basais.
@router.patch("/core/{persona_id}/motor_emocional", response_model=BlockResponse)
async def update_motor_emocional(request: BlockUpdateRequest, persona_id: str = Path(...)):
    return {"data": _update_core_block(persona_id, "motor_emocional", request.data)}

# Recupera as manias, vícios de linguagem e nível de formalidade.
@router.get("/core/{persona_id}/estilo_de_escrita", response_model=BlockResponse)
async def get_estilo_de_escrita(persona_id: str = Path(...)):
    return {"data": _get_core_block(persona_id, "estilo_de_escrita")}

# Atualiza parcialmente as definições de como a persona se comunica por texto.
@router.patch("/core/{persona_id}/estilo_de_escrita", response_model=BlockResponse)
async def update_estilo_de_escrita(request: BlockUpdateRequest, persona_id: str = Path(...)):
    return {"data": _update_core_block(persona_id, "estilo_de_escrita", request.data)}
