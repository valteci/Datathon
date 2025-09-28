from google import genai
from google.genai import types
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from src.services.retrieve_data import Chroma_db

class Teste:
    def __init__(self):
        client = genai.Client()

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
        ids = ["1253", "1254", "1255"]
        chroma = Chroma_db()
        chroma.add_embeddings("candidates", ids, result, texts)
        print("Embeddings armazenados com sucesso!")


        #print(type(embeddings_matrix))

        # similarity_matrix = cosine_similarity(embeddings_matrix)
        # 
        # for i, text1 in enumerate(texts):
        #     for j in range(i + 1, len(texts)):
        #         text2 = texts[j]
        #         similarity = similarity_matrix[i, j]
        #         print(f"Similarity between '{text1}' and '{text2}': {similarity:.4f}")