import json
from src.services.retrieve_data import ChromaDB


def import_collection_jsonl(dim: int, in_path: str, batch: int = 1000):
    chroma = ChromaDB()
    col = chroma._get_or_create_collection(dim)
    ids, embs, metas = [], [], []
    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            ids.append(str(rec["id"]))
            embs.append(rec["embedding"])
            metas.append(rec.get("metadata", {}))
            if len(ids) >= batch:
                col.upsert(ids=ids, embeddings=embs, metadatas=metas)
                ids, embs, metas = [], [], []
    if ids:
        col.upsert(ids=ids, embeddings=embs, metadatas=metas)


import_collection_jsonl(
    dim=3072,
    in_path="database/candidates_dim3072.jsonl",
    batch=1000,   # mesmo raciocínio do export
)
print("Import OK")





