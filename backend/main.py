from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1.api import api_router
from backend.core.database import engine, Base
import os

# Cria as tabelas no banco de dados se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(title="cAi - Local AI Studio")

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui todas as rotas da v1
app.include_router(api_router, prefix="/api/v1")

app.mount("/media", StaticFiles(directory="data/media"), name="media")

# Se você quiser manter a pasta 'frontend' organizada, 
# garanta que o diretório passado existe:
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
