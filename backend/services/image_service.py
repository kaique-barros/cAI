import os
import base64
import uuid
from ..core.config import settings

class ImageService:
    @staticmethod
    def salvar_imagem_base64(base64_str, subpasta="uploads"):
        try:
            if "," in base64_str:
                base64_str = base64_str.split(",")[1]
            
            img_data = base64.b64decode(base64_str)
            nome_arquivo = f"{uuid.uuid4().hex}.png"
            
            caminho_relativo = os.path.join("data", "media", subpasta, nome_arquivo)
            caminho_absoluto = os.path.join(settings.BASE_DIR, caminho_relativo)
            
            os.makedirs(os.path.dirname(caminho_absoluto), exist_ok=True)
            
            with open(caminho_absoluto, "wb") as f:
                f.write(img_data)
                
            return caminho_relativo
        except Exception as e:
            print(f"Erro ao processar imagem: {e}")
            return None
