import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI Chat Studio"
    COLAB_URL: str = os.getenv("COLAB_URL", "").rstrip("/")
    
    # Caminho ABSOLUTO para evitar erros de diretório
    BASE_DIR: str = "/home/kaiqbbrs/cAi"
    
    # Aponta para a pasta onde seus dados REAIS estão
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    MEDIA_DIR: str = os.path.join(DATA_DIR, "media")
    
    # DATABASE_URL apontando para o banco antigo
    DATABASE_URL: str = f"sqlite:///{os.path.join(DATA_DIR, 'banco.db')}"

settings = Settings()
