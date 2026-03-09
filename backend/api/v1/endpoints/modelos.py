from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....core import models
from ....services.ai_service import AIService
from .. import schemas

router = APIRouter()

@router.get("/", response_model=list[schemas.ModeloIAResponse])
def listar_modelos(db: Session = Depends(get_db)):
    return db.query(models.ModeloIA).all()

@router.post("/sincronizar")
async def sincronizar(db: Session = Depends(get_db)):
    online = await AIService.verificar_colab()
    modelos_db = db.query(models.ModeloIA).all()
    
    if not online:
        for mod in modelos_db:
            if mod.tipo == "texto":
                mod.is_ativo = False
        db.commit()
        return {"status": "offline", "msg": "Colab não encontrado"}

    tags = await AIService.obter_tags_ollama()
    tags_limpas = [tag.split(":")[0] for tag in tags]
    
    for mod in modelos_db:
        if mod.tipo == "texto":
            mod.is_ativo = (mod.nome_id in tags) or (mod.nome_id in tags_limpas)
        else:
            mod.is_ativo = True 
            
    db.commit()
    return {"status": "sucesso", "online": True}

# --- ROTA DE DOWNLOAD ATUALIZADA AQUI ---
@router.post("/baixar")
async def baixar_modelos(req: schemas.DownloadRequest, background_tasks: BackgroundTasks):
    # Envia a ordem de download para rodar escondido em segundo plano
    background_tasks.add_task(AIService.iniciar_pull_modelos, req.modelos)
    # Retorna na mesma hora para o frontend fechar a tela de loading!
    return {"status": "concluido", "msg": "Ordens enviadas ao Colab"}
