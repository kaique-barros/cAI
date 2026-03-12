from fastapi import APIRouter

# Importação dos submódulos de Chat
from .chat import process, enqueue, history, edit

# Importação dos submódulos de Persona
from .persona import create, core, assets, ui

# Importação dos submódulos de Sistema
from .system import health, sync

api_router = APIRouter()

# ---------------------------------------------------------
# ROTAS DE CHAT (Prefixo: /chat)
# ---------------------------------------------------------
api_router.include_router(process.router, prefix="/chat", tags=["Chat - Processamento"])
api_router.include_router(enqueue.router, prefix="/chat", tags=["Chat - Fila de Agrupamento"])
api_router.include_router(history.router, prefix="/chat", tags=["Chat - Histórico"])
api_router.include_router(edit.router, prefix="/chat", tags=["Chat - Edição"])

# ---------------------------------------------------------
# ROTAS DE PERSONA (Prefixo: /persona)
# ---------------------------------------------------------
api_router.include_router(create.router, prefix="/persona", tags=["Persona - Criação"])
api_router.include_router(core.router, prefix="/persona", tags=["Persona - Gestão da Alma (Core)"])
api_router.include_router(assets.router, prefix="/persona", tags=["Persona - Multimédia (Assets)"])
api_router.include_router(ui.router, prefix="/persona", tags=["Persona - Interface Visual (UI)"])

# ---------------------------------------------------------
# ROTAS DE SISTEMA (Prefixo: /system)
# ---------------------------------------------------------
api_router.include_router(health.router, prefix="/system", tags=["Sistema - Monitorização"])
api_router.include_router(sync.router, prefix="/system", tags=["Sistema - Sincronização"])
