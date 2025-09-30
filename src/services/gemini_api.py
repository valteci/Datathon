from google import genai
from google.genai import types
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from src.services.retrieve_data import ChromaDB
import os
class Model:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

    def predict(self, descricao_vaga: str, k: int):
        texts = [descricao_vaga]

        result = [
            np.array(e.values) for e in self.client.models.embed_content(
                model=os.getenv('MODEL','gemini-embedding-001'),
                contents=texts,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")).embeddings
        ]

        vaga_embedding = np.array(result)[0]
        chroma = ChromaDB()
        res = chroma.query_similar_by_embedding(vaga_embedding, top_k=k)
        return res
