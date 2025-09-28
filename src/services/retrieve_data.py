from chromadb import HttpClient
import os

class Chroma_db:
    _instance = None  # atributo estático para o singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Chroma_db, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "client"):  # garante que só inicializa uma vez
            chroma_url = os.getenv("CHROMA_URL", "http://localhost:8000")
            self.client = HttpClient(host="chromadb", port=8000)

    def test_connection(self):
        """Retorna a lista de coleções existentes no ChromaDB"""
        return self.client.list_collections()






