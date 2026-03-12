import httpx
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.logger import loggers

router = APIRouter()
log = loggers["system"]["access"]

class HealthResponse(BaseModel):
    """
    Esquema de resposta para a verificação de integridade do sistema,
    indicando o status do backend local e do provedor de IA remoto.
    """
    status: str
    provider: str
    ai_connection: str

# Efetua uma requisição leve ao provedor de IA configurado para validar 
# se o túnel de rede (ex: Ngrok) e a API do Ollama estão operacionais.
@router.get("/health", response_model=HealthResponse)
async def check_health():
    with open("config.json", "r") as f:
        cfg = json.load(f)
        
    provider = cfg["active_provider"]
    base_url = cfg["endpoints"].get(provider, "")
    
    if not base_url:
        return HealthResponse(
            status="online", 
            provider=provider, 
            ai_connection="unconfigured"
        )
        
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(base_url)
            
            if response.status_code == 200:
                log.info("System: Verificação de health check bem-sucedida.")
                return HealthResponse(
                    status="online", 
                    provider=provider, 
                    ai_connection="online"
                )
            else:
                log.warning(f"System: AI Provider retornou status {response.status_code}")
                return HealthResponse(
                    status="online", 
                    provider=provider, 
                    ai_connection="degraded"
                )
                
    except Exception as e:
        log.error(f"System: Falha de conexão com a IA ({provider}): {str(e)}")
        return HealthResponse(
            status="online", 
            provider=provider, 
            ai_connection="offline"
        )
