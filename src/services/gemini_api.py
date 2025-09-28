from google import genai
from google.genai import types
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from src.services.retrieve_data import ChromaDB
import os
class Teste:
    def __init__(self):
        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

        texts = [
            "What is the meaning of life?",
            "What is the purpose of existence?",
            "How do I bake a cake?"]

        result = [
            np.array(e.values) for e in client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")).embeddings
        ]

        # Calculate cosine similarity. Higher scores = greater semantic similarity.

        embeddings_matrix = np.array(result)
        print('matriz original:', embeddings_matrix)
        ids = ["1253", "1254", "1255"]
        chroma = ChromaDB()
        chroma.upsert_embeddings(embeddings=embeddings_matrix, ids=ids)
        query_vec = embeddings_matrix[0]
        res = chroma.query_similar_by_embedding(query_vec, top_k=3)
        print("Query result:")
        print("ids:", res.get("ids"))
        print("distances:", res.get("distances"))
        print("similarities:", res.get("similarities"))