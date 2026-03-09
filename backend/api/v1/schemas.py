from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class MensagemBase(BaseModel):
    papel: str
    conteudo: Optional[str] = None
    caminho_imagem: Optional[str] = None
    modelo_utilizado: Optional[str] = None

class MensagemResponse(MensagemBase):
    id: int
    chat_id: int
    data_envio: datetime
    model_config = ConfigDict(from_attributes=True)

class ChatResponse(BaseModel):
    id: int
    titulo: str
    icone: Optional[str] = None
    background: Optional[str] = None
    contexto_inicial: Optional[str] = None
    data_atualizacao: datetime
    mensagens: List[MensagemResponse] = []
    model_config = ConfigDict(from_attributes=True)

class ChatCreate(BaseModel):
    titulo: str = "Nova Conversa"

class ChatUpdate(BaseModel):
    titulo: Optional[str] = None
    contexto_inicial: Optional[str] = None
    icone: Optional[str] = None
    background: Optional[str] = None

class GerarRespostaRequest(BaseModel):
    prompt: str
    modelo: str = "llama3"
    stream: bool = True

class ModeloIAResponse(BaseModel):
    id: int
    nome_id: str
    tipo: str
    descricao: Optional[str] = None
    tags: Optional[str] = None
    is_ativo: bool
    model_config = ConfigDict(from_attributes=True)

class ModeloIACreate(BaseModel):
    nome_id: str
    tipo: str
    descricao: Optional[str] = None
    tags: Optional[str] = None

class DownloadRequest(BaseModel):
    modelos: List[str]

class ConfigUpdate(BaseModel):
    contexto_global: str
    modelo_padrao: str

    # Adicione no final do seu arquivo schemas.py
class InterpretacaoImagemRequest(BaseModel):
    prompt: Optional[str] = "Descreva esta imagem com o máximo de detalhes."
    imagem_base64: str
    modelo: str = "llava" # Forçamos o padrão para llava
    stream: bool = True
