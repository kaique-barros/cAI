from sqlalchemy.orm import Session
from ..core import models
import datetime

class ChatRepository:
    @staticmethod
    def listar_todos_chats(db: Session):
        # Retorna todos os chats ordenados pela data de atualização
        return db.query(models.Chat).order_by(models.Chat.data_atualizacao.desc()).all()

    @staticmethod
    def obter_chat(db: Session, chat_id: int):
        return db.query(models.Chat).filter(models.Chat.id == chat_id).first()

    @staticmethod
    def criar_chat(db: Session, titulo: str):
        novo_chat = models.Chat(titulo=titulo)
        db.add(novo_chat)
        db.commit()
        db.refresh(novo_chat)
        return novo_chat

    @staticmethod
    def salvar_mensagem(db: Session, dados: dict):
        nova_msg = models.Mensagem(**dados)
        db.add(nova_msg)
        
        # Atualiza a data do chat para ele subir para o topo da lista
        chat = db.query(models.Chat).filter(models.Chat.id == dados['chat_id']).first()
        if chat:
            chat.data_atualizacao = datetime.datetime.utcnow()
            
        db.commit()
        db.refresh(nova_msg)
        return nova_msg
