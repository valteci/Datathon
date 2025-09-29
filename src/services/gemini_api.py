from google import genai
from google.genai import types
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from src.services.retrieve_data import ChromaDB
import os
class Model:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))



        # Calculate cosine similarity. Higher scores = greater semantic similarity.

        #embeddings_matrix = np.array(result)
        #print('matriz original:', embeddings_matrix)
        #ids = ["1253", "1254", "1255"]
        #chroma = ChromaDB()
        #chroma.upsert_embeddings(embeddings=embeddings_matrix, ids=ids)
        #query_vec = embeddings_matrix[0]
        #res = chroma.query_similar_by_embedding(query_vec, top_k=3)
        #print("Query result:")
        #print("ids:", res.get("ids"))
        #print("distances:", res.get("distances"))
        #print("similarities:", res.get("similarities"))



    def predict(self, descricao_vaga: str):
        # 1842
        x = """• - .net full stack. • Experiência com tecnologias .net Core, .net Framework, C#, Razor e Orientação a Objetos.\n• Conhecimento em banco de dados, especialmente PostgreSQL.\n• Boa comunicação escrita e oral, pois terá contato direto com área usuária e demais fornecedores do cliente.\n• Experiência com metodologia Ágil (Scrum/Kanban).\n• Senso de organização e comprometimento com o time e suas demandas.\n• Ensino Superior Completo (áreas relacionadas a tecnologia da informação).\n• Conhecimento considerados diferenciais:\no Amazon Web Service (AWS);\no Pipelines;\no Testes Automatizados;\no Mercado financeiro, resseguro, previdência, etc."""
        texts = [x]

        result = [
            np.array(e.values) for e in self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")).embeddings
        ]

        vaga_embedding = np.array(result)[0]
        chroma = ChromaDB()
        res = chroma.query_similar_by_embedding(vaga_embedding, top_k=1)
        return res
