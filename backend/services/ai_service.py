import httpx
import json
from ..core.config import settings

class AIService:
    HEADERS = {"ngrok-skip-browser-warning": "true"}

    @staticmethod
    async def verificar_colab():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.COLAB_URL}/tags", headers=AIService.HEADERS)
                return resp.status_code == 200
        except:
            return False

    @staticmethod
    async def obter_tags_ollama():
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{settings.COLAB_URL}/tags", headers=AIService.HEADERS)
                if resp.status_code == 200:
                    return [m["name"] for m in resp.json().get("models", [])]
            except Exception as e:
                print(f"Erro ao ler tags do Ollama: {e}")
            return []

    @staticmethod
    async def iniciar_pull_modelos(modelos_lista):
        async with httpx.AsyncClient(timeout=None) as client:
            for nome in modelos_lista:
                try:
                    print(f"Iniciando download de {nome} no Colab...")
                    await client.post(f"{settings.COLAB_URL}/pull", json={"name": nome}, headers=AIService.HEADERS)
                    print(f"Download de {nome} concluído!")
                except Exception as e:
                    print(f"Erro ao pedir download do modelo {nome}: {e}")

    @staticmethod
    async def gerar_texto_stream(payload):
        print(f"A enviar pedido de texto ao Colab (Modelo: {payload.get('modelo')})...")
        async with httpx.AsyncClient(timeout=600.0) as client:
            try:
                async with client.stream("POST", f"{settings.COLAB_URL}/gerar_texto", json=payload, headers=AIService.HEADERS) as resp:
                    
                    if resp.status_code != 200:
                        erro_bytes = await resp.aread()
                        erro_str = erro_bytes.decode('utf-8', errors='ignore')
                        print(f"ERRO DO COLAB ({resp.status_code}): {erro_str}")
                        yield {"response": f"\n⚠️ O servidor Colab recusou o pedido (Erro {resp.status_code}):\n{erro_str}"}
                        return

                    async for line in resp.aiter_lines():
                        if line:
                            try:
                                dados = json.loads(line)
                                if "detail" in dados and "response" not in dados:
                                    yield {"response": f"\n⚠️ O Colab não reconheceu o formato enviado: {dados['detail']}"}
                                elif "error" in dados:
                                    yield {"response": f"\n⚠️ Erro interno do Ollama: {dados['error']}"}
                                else:
                                    yield dados
                            except json.JSONDecodeError:
                                print(f"Resposta não suportada (Não-JSON): {line}")
                                yield {"response": f"\n[Resposta não interpretável do Colab: {line}]"}
            except httpx.RequestError as e:
                print(f"Falha de rede: {e}")
                yield {"response": f"\n⚠️ Falha ao contactar o Colab. O servidor poderá estar inativo. Detalhe: {e}"}
