from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import re

from backend.core.database import get_db
from backend.core import models
from backend.repository.chat_repo import ChatRepository
from backend.api.v1 import schemas
from backend.services.ai_service import AIService
from backend.services.image_service import ImageService

router = APIRouter()

@router.post("/{chat_id}/send_message/image/interpret")
async def interpretar_imagem(chat_id: int, req: schemas.InterpretacaoImagemRequest, db: Session = Depends(get_db)):
    chat = ChatRepository.obter_chat(db, chat_id)
    if not chat: raise HTTPException(status_code=404, detail="Chat não encontrado")

    # 1. Salvar a imagem localmente para o histórico do chat
    caminho_img_user = ImageService.salvar_imagem_base64(req.imagem_base64, "uploads")

    # 2. Salvar a mensagem do utilizador na Base de Dados
    ChatRepository.salvar_mensagem(db, {
        "chat_id": chat_id, 
        "papel": "user", 
        "conteudo": req.prompt,
        "modelo_utilizado": req.modelo,
        "caminho_imagem": caminho_img_user
    })

    async def event_generator():
        texto_acumulado = ""
        mensagens_formatadas = []
        
        # 3. HISTÓRICO DA CONVERSA (Memória Curta)
        historico = chat.mensagens[-10:] if len(chat.mensagens) > 10 else chat.mensagens
        for msg in historico:
            if not msg.conteudo: continue
            mensagens_formatadas.append({
                "role": msg.papel,
                "content": msg.conteudo
            })

        # 4. LIMPEZA EXTREMA DA BASE64 PARA O OLLAMA
        base64_pura = req.imagem_base64
        if "," in base64_pura:
            base64_pura = base64_pura.split(",", 1)[1]
        
        # Remove espaços, quebras de linha ou tabs que corrompem a leitura do LLaVA
        base64_pura = re.sub(r'\s+', '', base64_pura)
        
        # Aviso de tamanho
        tamanho_mb = len(base64_pura) / (1024 * 1024)
        if tamanho_mb > 4.5:
            aviso = "⚠️ A imagem é muito grande e pode ser bloqueada pela rede. Tentando processar mesmo assim...\n\n"
            dados_json = json.dumps({"chunk": aviso})
            yield f"data: {dados_json}\n\n"

        # 5. MONTAR A MENSAGEM ATUAL COM A IMAGEM
        # Nota: Deliberadamente não injetamos o System Prompt aqui para evitar "Cegueira de Atenção" no LLaVA
        mensagens_formatadas.append({
            "role": "user",
            "content": req.prompt,
            "images": [base64_pura]
        })

        payload = {
            "modelo": req.modelo, 
            "messages": mensagens_formatadas,
            "stream": req.stream
        }

        # 6. ENVIAR PARA O COLAB E STREAMING DA RESPOSTA
        async for chunk_data in AIService.gerar_texto_stream(payload):
            chunk = ""
            if "message" in chunk_data and "content" in chunk_data["message"]:
                chunk = chunk_data["message"]["content"]
            elif "response" in chunk_data:
                chunk = chunk_data["response"]
                
            if chunk:
                texto_acumulado += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # 7. SALVAR RESPOSTA DA IA
        msg_ai = ChatRepository.salvar_mensagem(db, {
            "chat_id": chat_id,
            "papel": "assistant",
            "conteudo": texto_acumulado,
            "modelo_utilizado": req.modelo
        })
        yield f"data: {json.dumps({'fim': True, 'id': msg_ai.id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
