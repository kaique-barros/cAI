from fastapi import APIRouter
from .endpoints import chats, modelos, configuracoes, images

api_router = APIRouter()

# Rota de Chats
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(images.router, prefix="/chats", tags=["images"])

api_router.include_router(chats.router, prefix="/mensagens", tags=["mensagens"])

api_router.include_router(modelos.router, prefix="/modelos", tags=["modelos"])

api_router.include_router(configuracoes.router, prefix="/configuracoes", tags=["configuracoes"])
