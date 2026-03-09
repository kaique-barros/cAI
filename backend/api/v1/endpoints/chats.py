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

@router.post("/{chat_id}/gerar_resposta")
async def gerar_resposta(chat_id: int, req: schemas.GerarRespostaRequest, db: Session = Depends(get_db)):
    chat = ChatRepository.obter_chat(db, chat_id)
    if not chat: raise HTTPException(status_code=404, detail="Chat não encontrado")

    caminho_img_user = None
    if req.imagem_base64:
        caminho_img_user = ImageService.salvar_imagem_base64(req.imagem_base64, "uploads")

    # Salva pergunta do usuário
    ChatRepository.salvar_mensagem(db, {
        "chat_id": chat_id, "papel": "user", "conteudo": req.prompt,
        "modelo_utilizado": req.modelo, "caminho_imagem": caminho_img_user
    })

    # --- LÓGICA DE IMAGEM (STABLE DIFFUSION) ---
    if req.tipo == "imagem":
        # Nota: O req.imagem_base64 aqui permite o Img2Img do seu Colab
        resultado = await AIService.gerar_imagem({
            "prompt": req.prompt, 
            "imagem_base64": req.imagem_base64 
        })
        
        if "error" in resultado:
            raise HTTPException(status_code=500, detail=resultado["error"])
            
        caminho_ia = ImageService.salvar_imagem_base64(resultado["imagem_base64"], "uploads")
        msg_ai = ChatRepository.salvar_mensagem(db, {
            "chat_id": chat_id, "papel": "assistant", "conteudo": "Imagem gerada.",
            "modelo_utilizado": req.modelo, "caminho_imagem": caminho_ia
        })
        
        # Prepara resposta JSON simples para o frontend
        res = schemas.MensagemResponse.model_validate(msg_ai).model_dump()
        res["caminho_imagem"] = res["caminho_imagem"].replace("data/media/", "/media/")
        return res

    async def event_generator():
        texto_acumulado = ""
        payload = req.model_dump(exclude_none=True)
        
        # --- TÁTICA INFALÍVEL DE CONTEXTO ---
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
            # O TRUQUE: Injetamos o contexto de forma "invisível" DIRETAMENTE na pergunta!
            texto_original = payload["prompt"]
            payload["prompt"] = f"Aja estritamente de acordo com as seguintes regras:\n[{contexto_final.strip()}]\n\nPergunta do utilizador: {texto_original}"
        # ------------------------------------

        async for chunk_data in AIService.gerar_texto_stream(payload):
            chunk = chunk_data.get("response", "")
            if chunk:
                texto_acumulado += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
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

    # Lógica de cascata: se apagar a pergunta do user, apaga a resposta da IA seguinte
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
