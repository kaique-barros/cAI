from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....core import models
from .. import schemas

router = APIRouter()

@router.get("/")
def obter_config(db: Session = Depends(get_db)):
    config = db.query(models.Configuracao).first()
    if not config:
        config = models.Configuracao()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.put("/")
def atualizar_config(req: schemas.ConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(models.Configuracao).first()
    if not config:
        config = models.Configuracao()
        db.add(config)
    
    config.contexto_global = req.contexto_global
    config.modelo_padrao = req.modelo_padrao
    db.commit()
    return {"status": "sucesso"}
