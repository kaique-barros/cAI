from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from core.engine import Engine
from core.logger import loggers

router = APIRouter()
engine = Engine()
log = loggers["chat"]["access"]

class ProcessMessageRequest(BaseModel):
    """
    Esquema de validação para a requisição de processamento de mensagem.
    Garante a presença do texto do utilizador para envio ao motor.
    """
    user_input: str

class ProcessMessageResponse(BaseModel):
    """
    Esquema de validação para a resposta processada, refletindo o pacote 
    completo gerado pelo sistema cognitivo.
    """
    reply: dict

# Rota principal de interação. Valida a entrada, invoca o núcleo de 
# raciocínio da IA e trata as exceções de comunicação e processamento.
@router.post("/process/{persona_id}", response_model=ProcessMessageResponse)
async def process_message(
    request: ProcessMessageRequest,
    persona_id: str = Path(..., description="UUID da persona")
):
    try:
        response_package = await engine.think(
            persona_id=persona_id,
            user_input=request.user_input
        )
        
        if "error" in response_package:
            log.warning(f"Processamento falhou. Persona não encontrada: {persona_id}")
            raise HTTPException(status_code=404, detail=response_package["error"])
            
        return {"reply": response_package}
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Erro crítico no processamento de mensagem: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno no motor de inferência.")
