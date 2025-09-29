import json
import numpy as np
from src.services.retrieve_data import ChromaDB

def _to_jsonable(x):
    """Converte recursivamente objetos para tipos serializáveis em JSON."""
    # numpy arrays -> list
    if isinstance(x, np.ndarray):
        return x.tolist()
    # numpy escalares -> python escalares
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    # containers
    if isinstance(x, dict):
        return {str(k): _to_jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [_to_jsonable(v) for v in x]
    # tipos comuns já ok: str, int, float, bool, None
    return x


def export_collection_jsonl(dim: int, out_path: str, batch: int = 1000):
    chroma = ChromaDB()
    col = chroma._get_or_create_collection(dim)
    total = col.count()
    with open(out_path, "w", encoding="utf-8") as f:
        for offset in range(0, total, batch):
            res = col.get(limit=batch, offset=offset, include=["metadatas", "embeddings"])
            ids = res.get("ids", [])
            embs = res.get("embeddings", [])
            metas = res.get("metadatas", [{}] * len(ids))

            for i, _id in enumerate(ids):
                embedding = embs[i]
                # garante list de floats
                if isinstance(embedding, np.ndarray):
                    embedding = embedding.astype(float).tolist()
                elif not isinstance(embedding, list):
                    embedding = list(embedding)

                obj = {
                    "id": str(_id),
                    "embedding": embedding,
                    "metadata": _to_jsonable(metas[i]),
                }
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")


#export_collection_jsonl(
#        dim=3072,
#        out_path="candidates_dim3072.jsonl",
#        batch=10000,      # ajuste livremente (explico abaixo)
#)

