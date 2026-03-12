import chromadb
from chromadb.utils import embedding_functions # Importação necessária
from datetime import datetime
import os
import json
import httpx # Importação necessária
from core.logger import loggers

class OllamaEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """
    Adaptador customizado para o ChromaDB. Encaminha as solicitações de 
    vetorização para o endpoint do Ollama configurado no sistema.
    """
    def __init__(self, url: str, model: str):
        self.url = f"{url}/api/embeddings"
        self.model = model

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = []
        with httpx.Client(timeout=60.0) as client:
            for text in input:
                response = client.post(self.url, json={
                    "model": self.model,
                    "prompt": text
                })
                embeddings.append(response.json()["embedding"])
        return embeddings

class RAGMemory:
    """
    Gerenciador de memória semântica de longo prazo. Utiliza o ChromaDB para 
    armazenar e buscar informações baseadas na similaridade de vetores.
    """

    # Carrega as configurações de modelos de embedding, isola o banco de dados 
    # pelo UUID da persona e inicializa a coleção de documentos persistente.
    def __init__(self, persona_id: str):
        with open("config.json", "r") as f:
            self.cfg = json.load(f)

        self.persona_id = persona_id
        self.chroma_path = f"data/chroma/{self.persona_id}"
        self.log = loggers["chat"]["db"]
        
        os.makedirs(self.chroma_path, exist_ok=True)
        
        provider = self.cfg["active_provider"]
        base_url = self.cfg["endpoints"][provider]
        model_name = self.cfg["cot_models"]["embeddings"]

        self.emb_fn = OllamaEmbeddingFunction(url=base_url, model=model_name)
        
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="episodic_memory",
            embedding_function=self.emb_fn
        )

    # Indexa um novo fragmento de informação no banco vetorial, associando 
    # metadados temporais e de autoria para facilitar filtros em buscas futuras.
    def save(self, content: str, role: str, msg_id: int):
        self.collection.add(
            documents=[content],
            metadatas=[{
                "role": role, 
                "timestamp": str(datetime.now()),
                "source_id": msg_id
            }],
            ids=[f"msg_{msg_id}"]
        )
        self.log.info(f"ID:{self.persona_id} | RAG: Fragmento {msg_id} indexado.")

    # Realiza uma busca semântica no banco de dados, retornando os trechos de 
    # memória que possuem a maior proximidade contextual com a consulta realizada.
    def search(self, query: str, n_results: int = 3):
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results['documents'] or not results['documents'][0]:
            return []
            
        self.log.info(f"ID:{self.persona_id} | RAG: Busca realizada para '{query[:30]}...'")
        return results['documents'][0]

    # Localiza uma entrada específica pelo ID e atualiza seu conteúdo textual, 
    # forçando o recálculo dos vetores para manter a precisão da busca.
    def update(self, msg_id: int, new_content: str):
        self.collection.update(
            ids=[f"msg_{msg_id}"],
            documents=[new_content]
        )
        self.log.info(f"ID:{self.persona_id} | RAG: Vetor {msg_id} atualizado.")

    # Deleta permanentemente a coleção de memórias vetoriais da persona, 
    # limpando o armazenamento físico associado ao UUID no sistema.
    def clear(self):
        try:
            self.chroma_client.delete_collection(name="episodic_memory")
        except Exception:
            pass # Ignora se a coleção não existir
        
        self.collection = self.chroma_client.get_or_create_collection(
            name="episodic_memory",
            embedding_function=self.emb_fn
        )
        self.log.info(f"ID:{self.persona_id} | RAG: Memória vetorial reiniciada.")
