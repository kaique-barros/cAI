from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Configuracao(Base):
    __tablename__ = "configuracoes"

    id = Column(Integer, primary_key=True, index=True)
    contexto_global = Column(Text, default="És um assistente inteligente e prestativo.")
    modelo_padrao = Column(String, default="llama3")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True, default="Nova Conversa")
    icone = Column(String, nullable=True)       # Caminho local para a imagem do ícone
    background = Column(String, nullable=True)  # Caminho local para a imagem de fundo
    contexto_inicial = Column(Text, nullable=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento com as mensagens
    mensagens = relationship("Mensagem", back_populates="chat", cascade="all, delete-orphan")

class Mensagem(Base):
    __tablename__ = "mensagens"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    papel = Column(String)  # Geralmente 'user' ou 'assistant'
    conteudo = Column(Text)
    caminho_imagem = Column(String, nullable=True)  # Se for uma imagem gerada pelo Stable Diffusion
    modelo_utilizado = Column(String, nullable=True) # Ex: 'llama3', 'stable-diffusion'
    data_envio = Column(DateTime, default=datetime.utcnow)

    # Relacionamento inverso com o chat
    chat = relationship("Chat", back_populates="mensagens")

class ModeloIA(Base):
    __tablename__ = "modelos_ia"
    
    id = Column(Integer, primary_key=True, index=True)
    nome_id = Column(String, unique=True, index=True) # Ex: llama3, phi3, stabilityai/stable-diffusion-2-1
    tipo = Column(String, default="texto") # "texto" ou "imagem"
    descricao = Column(String, nullable=True)
    tags = Column(String, nullable=True) # Ex: "rápido, código, criativo"
    is_ativo = Column(Boolean, default=False) # Se está de facto instalado no sistema
