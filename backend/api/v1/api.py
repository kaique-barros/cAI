from fastapi import APIRouter
from .endpoints import chats, modelos, configuracoes

api_router = APIRouter()

# Rota de Chats
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])

# Rota de Mensagens (Apontando para o mesmo router de chats onde criamos a lógica)
api_router.include_router(chats.router, prefix="/mensagens", tags=["mensagens"])

# Outras Rotas
api_router.include_router(modelos.router, prefix="/modelos", tags=["modelos"])
api_router.include_router(configuracoes.router, prefix="/configuracoes", tags=["configuracoes"])
