import os
import json
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, Path
from pydantic import BaseModel
from core.logger import loggers

router = APIRouter()
log = loggers["persona"]["access"]

class AssetResponse(BaseModel):
    """
    Esquema de resposta que confirma o sucesso da operação e 
    devolve o caminho relativo onde o ficheiro foi guardado.
    """
    status: str
    file_path: str

# Função auxiliar interna para encapsular a lógica repetitiva de salvamento 
# de arquivos físicos e atualização do dicionário JSON da persona.
def _process_asset_upload(persona_id: str, file: UploadFile, file_prefix: str, json_key: str) -> str:
    json_path = f"data/personas/{persona_id}.json"
    media_dir = f"data/media/{persona_id}"

    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Persona não encontrada.")

    os.makedirs(media_dir, exist_ok=True)
    
    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        if "aparencia_e_ui" not in data:
            data["aparencia_e_ui"] = {}
        if "config_chat" not in data["aparencia_e_ui"]:
            data["aparencia_e_ui"]["config_chat"] = {}

        ext = file.filename.split('.')[-1]
        filename = f"{file_prefix}.{ext}"
        filepath = os.path.join(media_dir, filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        data["aparencia_e_ui"]["config_chat"][json_key] = filepath

        with open(json_path, "w") as f:
            json.dump(data, f, indent=4)

        return filepath

    except Exception as e:
        log.error(f"ID:{persona_id} | Erro ao processar '{file_prefix}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Falha ao guardar o {file_prefix}.")

# Recebe o ficheiro de imagem de perfil (avatar) via formulário multipart, 
# delegando a persistência à função auxiliar e retornando o caminho final.
@router.post("/assets/{persona_id}/avatar", response_model=AssetResponse)
async def upload_avatar(
    file: UploadFile = File(..., description="Imagem de perfil (Avatar)"),
    persona_id: str = Path(..., description="O identificador único (UUID) da persona")
):
    filepath = _process_asset_upload(persona_id, file, "avatar", "avatar_circle")
    log.info(f"ID:{persona_id} | Avatar atualizado com sucesso.")
    return AssetResponse(status="success", file_path=filepath)

# Recebe o ficheiro de imagem de fundo via formulário multipart, 
# delegando a persistência à função auxiliar e retornando o caminho final.
@router.post("/assets/{persona_id}/background", response_model=AssetResponse)
async def upload_background(
    file: UploadFile = File(..., description="Imagem de fundo do chat"),
    persona_id: str = Path(..., description="O identificador único (UUID) da persona")
):
    filepath = _process_asset_upload(persona_id, file, "background", "chat_bg")
    log.info(f"ID:{persona_id} | Background atualizado com sucesso.")
    return AssetResponse(status="success", file_path=filepath)
