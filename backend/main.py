import uvicorn
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api.v1.router import api_router
from core.logger import loggers

# Inicializa a aplicação FastAPI com metadados para a documentação automática.
app = FastAPI(
    title="Aura AI - Hybrid Persona System",
    description="Sistema de backend para personas de IA com memória e emoções.",
    version="2.1.0"
)

# Configuração de CORS para permitir que o seu frontend (Arch Linux local) 
# comunique com a API sem bloqueios de segurança do navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Garante a existência da diretoria de média e a monta como ficheiros estáticos.
# Isto permite aceder a imagens em: http://localhost:8000/media/uuid/avatar.png
os.makedirs("data/media", exist_ok=True)
app.mount("/media", StaticFiles(directory="data/media"), name="media")

# Inclui o roteador central que unifica Chat, Persona e System.
app.include_router(api_router, prefix="/api/v1")

log = loggers["system"]["access"]

@app.on_event("startup")
async def startup_event():
    log.info("Aura: Servidor iniciado e rotas mapeadas.")

@app.get("/")
async def root():
    """Rota de verificação básica de status do servidor."""
    return {
        "status": "online",
        "system": "Aura AI",
        "docs": "/docs"
    }

# Bloco de execução para iniciar o servidor via 'python main.py' no terminal.
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
