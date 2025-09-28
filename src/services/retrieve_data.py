from chromadb.client import Client
import os

class Chroma_db:
    _instance = None  # Singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Chroma_db, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "client"):
            chroma_url = os.getenv("CHROMA_URL", "http://localhost:8000")
            self.client = Client(chroma_url)  # já usa API v2

    def test_connection(self):
        """Retorna a lista de coleções existentes no ChromaDB"""
        return self.client.list_collections()

    def add_embeddings(self, collection_name: str, ids: list[str], embeddings: list[list[float]], documents: list[str] = None):
        """
        Adiciona embeddings a uma collection no ChromaDB.
        
        Args:
            collection_name: Nome da coleção
            ids: Lista de IDs (strings únicas)
            embeddings: Lista de embeddings (cada embedding é uma lista de floats)
            documents: Lista opcional com os textos originais
        """
        # Cria ou obtém a collection
        collection = self.client.get_or_create_collection(collection_name)

        # Adiciona os embeddings
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents
        )
        return True
