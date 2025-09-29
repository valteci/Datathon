# import_chroma_safe.py (ou no mesmo arquivo onde você já tem o import)
import json
from typing import List
from src.services.retrieve_data import ChromaDB

def _safe_upsert(col, ids: List[str], embs: List[list], metas: List[dict]):
    """Upsert com fallback: se 413 (payload muito grande), divide o lote recursivamente."""
    if not ids:
        return
    try:
        col.upsert(ids=ids, embeddings=embs, metadatas=metas)
    except Exception as e:
        msg = str(e).lower()
        if "payload too large" in msg or "413" in msg:
            if len(ids) == 1:
                raise
            mid = len(ids) // 2
            _safe_upsert(col, ids[:mid], embs[:mid], metas[:mid])
            _safe_upsert(col, ids[mid:], embs[mid:], metas[mid:])
        else:
            raise

def should_skip_import(dim: int, in_path: str, sample: int = 10, require_all: bool = True) -> bool:
    """
    Retorna True se devemos pular o import.
    Estratégia:
      1) Se a coleção está vazia (count==0) -> NÃO pula.
      2) Se a coleção tem itens, lê até `sample` linhas do arquivo, pega os IDs e
         verifica se eles já existem. Se todos (require_all=True) existirem -> pula.
         Caso contrário -> importa (upsert atualizará o que já existe).
    """
    chroma = ChromaDB()
    col = chroma._get_or_create_collection(dim)
    total = col.count()
    if total == 0:
        return False  # não tem nada, precisamos importar

    # Coleta amostra de IDs do arquivo (sem carregar tudo)
    sample_ids = []
    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                sample_ids.append(str(rec["id"]))
                if len(sample_ids) >= sample:
                    break
            except Exception:
                # linha inválida/ruim -> ignora
                continue

    if not sample_ids:
        # arquivo vazio ou ilegível -> não há o que importar
        return True

    got = col.get(ids=sample_ids)  # retorna somente os que existirem
    existing_ids = set(got.get("ids", []))

    if require_all:
        # só pula se TODOS da amostra já existem
        return all(i in existing_ids for i in sample_ids)
    else:
        # pula se >=80% da amostra já existe
        return len(existing_ids.intersection(sample_ids)) / len(sample_ids) >= 0.8

def import_collection_jsonl(
    dim: int,
    in_path: str,
    batch: int = 200,
    skip_if_present: bool = True,
    sample_check: int = 10,
    require_all_sample: bool = True,
):
    """
    Importa JSONL para a coleção `dim`.
    - `skip_if_present`: se True, verifica se já existem dados e dá skip.
    - `sample_check`: tamanho da amostra de IDs usada na verificação.
    - `require_all_sample`: se True, só dá skip se TODOS IDs da amostra existirem.
    """
    chroma = ChromaDB()
    col = chroma._get_or_create_collection(dim)
    col_name = chroma._collection_name(dim)

    if skip_if_present and should_skip_import(dim, in_path, sample=sample_check, require_all=require_all_sample):
        print(f"[SKIP] Import ignorado: coleção '{col_name}' já possui dados compatíveis com '{in_path}'.")
        return

    print(f"[IMPORT] Iniciando import para coleção '{col_name}' a partir de '{in_path}' ...")
    ids, embs, metas = [], [], []
    total_lines = 0
    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            ids.append(str(rec["id"]))
            embs.append(rec["embedding"])          # lista de floats vinda do JSONL
            metas.append(rec.get("metadata", {}))
            total_lines += 1

            if len(ids) >= batch:
                _safe_upsert(col, ids, embs, metas)
                print(f"[IMPORT] Upsert de {len(ids)} itens (parcial).")
                ids, embs, metas = [], [], []

    if ids:
        _safe_upsert(col, ids, embs, metas)
        print(f"[IMPORT] Upsert final de {len(ids)} itens.")

    print(f"[DONE] Import concluído para '{col_name}'. Registros lidos: {total_lines}.")


import_collection_jsonl(
        dim=3072,
        in_path="database/candidates_dim3072.jsonl",
        batch=1000,                 # ajuste conforme memória/rede
        skip_if_present=True,      # <- evita reimportar
        sample_check=10,           # lê 10 IDs do arquivo
        require_all_sample=True,   # só pula se os 10 já existirem
    )
