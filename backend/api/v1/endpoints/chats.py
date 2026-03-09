from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

from backend.core.database import get_db
from backend.core import models
from backend.repository.chat_repo import ChatRepository
from backend.api.v1 import schemas
from backend.services.ai_service import AIService
from backend.services.image_service import ImageService

router = APIRouter()

@router.get("/", response_model=list[schemas.ChatResponse])
def listar_chats(db: Session = Depends(get_db)):
    chats = ChatRepository.listar_todos_chats(db)
    for chat in chats:
        if chat.icone: chat.icone = chat.icone.replace("data/media/", "/media/")
        for msg in chat.mensagens:
            if msg.caminho_imagem: msg.caminho_imagem = msg.caminho_imagem.replace("data/media/", "/media/")
    return chats

@router.post("/", response_model=schemas.ChatResponse)
def criar_chat(req: schemas.ChatCreate, db: Session = Depends(get_db)):
    return ChatRepository.criar_chat(db, titulo=req.titulo)

@router.put("/{chat_id}")
def atualizar_chat(chat_id: int, req: schemas.ChatUpdate, db: Session = Depends(get_db)):
    chat = ChatRepository.obter_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat não encontrado")
    
    if req.titulo is not None:
        chat.titulo = req.titulo
    if req.contexto_inicial is not None:
        chat.contexto_inicial = req.contexto_inicial
        
    if req.icone:
        if req.icone.startswith("data:image"):
            chat.icone = ImageService.salvar_imagem_base64(req.icone, "icons")
            
    if req.background:
        if req.background.startswith("data:image"):
            chat.background = ImageService.salvar_imagem_base64(req.background, "backgrounds")
        
    db.commit()
    return {"status": "sucesso"}

@router.post("/{chat_id}/send_message/text")
async def gerar_resposta(chat_id: int, req: schemas.GerarRespostaRequest, db: Session = Depends(get_db)):
    chat = ChatRepository.obter_chat(db, chat_id)
    if not chat: raise HTTPException(status_code=404, detail="Chat não encontrado")

    # Salva a pergunta do utilizador (Apenas Texto)
    ChatRepository.salvar_mensagem(db, {
        "chat_id": chat_id, 
        "papel": "user", 
        "conteudo": req.prompt,
        "modelo_utilizado": req.modelo
    })

    async def event_generator():
        texto_acumulado = ""
        mensagens_formatadas = []
        
        # 1. INJETAR CONTEXTO DE SISTEMA
        contexto_final = ""
        try:
            config = db.query(models.Configuracao).first()
            if config and config.contexto_global:
                contexto_final += f"Instrução Global: {config.contexto_global}\n"
        except Exception as e:
            print(f"Aviso: Não foi possível ler o contexto global: {e}")

        if chat.contexto_inicial:
            contexto_final += f"Instrução Específica: {chat.contexto_inicial}\n"
        
        if contexto_final.strip():
            mensagens_formatadas.append({
                "role": "system",
                "content": f"Aja estritamente de acordo com as seguintes regras:\n[{contexto_final.strip()}]"
            })
            
        # 2. INJETAR HISTÓRICO DA CONVERSA
        historico = chat.mensagens[-20:] if len(chat.mensagens) > 20 else chat.mensagens
        for msg in historico:
            if not msg.conteudo: continue
            mensagens_formatadas.append({
                "role": msg.papel,
                "content": msg.conteudo
            })
            
        # 3. INJETAR NOVA PERGUNTA
        mensagens_formatadas.append({
            "role": "user",
            "content": req.prompt
        })

        # Payload limpo, exclusivamente focado em texto e histórico
        payload = {
            "modelo": req.modelo, 
            "messages": mensagens_formatadas,
            "stream": req.stream
        }

        # 4. STREAMING DA RESPOSTA
        async for chunk_data in AIService.gerar_texto_stream(payload):
            chunk = ""
            if "message" in chunk_data and "content" in chunk_data["message"]:
                chunk = chunk_data["message"]["content"]
            elif "response" in chunk_data:
                chunk = chunk_data["response"]
                
            if chunk:
                texto_acumulado += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Guardar resposta final da IA
        msg_ai = ChatRepository.salvar_mensagem(db, {
            "chat_id": chat_id,
            "papel": "assistant",
            "conteudo": texto_acumulado,
            "modelo_utilizado": req.modelo
        })
        yield f"data: {json.dumps({'fim': True, 'id': msg_ai.id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.delete("/{mensagem_id}")
def eliminar_mensagem(mensagem_id: int, db: Session = Depends(get_db)):
    msg = db.query(models.Mensagem).filter(models.Mensagem.id == mensagem_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    chat_id = msg.chat_id
    papel = msg.papel

    if papel == "user":
        proxima_msg = db.query(models.Mensagem).filter(
            models.Mensagem.chat_id == chat_id,
            models.Mensagem.id > mensagem_id
        ).order_by(models.Mensagem.id.asc()).first()
        
        if proxima_msg and proxima_msg.papel == "assistant":
            db.delete(proxima_msg)

    db.delete(msg)
    db.commit()
    return {"status": "sucesso"}

@router.delete("/apagar/{chat_id}")
def apagar_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat não encontrado")
    
    # 1. Apagar as mensagens associadas para evitar erros de integridade (Foreign Key)
    db.query(models.Mensagem).filter(models.Mensagem.chat_id == chat_id).delete()
    
    # 2. Apagar o chat
    db.delete(chat)
    db.commit()
    
    return {"status": "sucesso", "mensagem": "Chat excluído com sucesso"}
