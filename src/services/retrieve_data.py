# chroma_db.py
from __future__ import annotations

import os
import threading
from typing import Iterable, List, Optional, Dict, Any, Union
from urllib.parse import urlparse

import numpy as np

import chromadb
from chromadb.config import Settings


class _Singleton(type):
    """Metaclass para implementar Singleton de forma thread-safe."""
    _instances: Dict[type, "ChromaDB"] = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ChromaDB(metaclass=_Singleton):
    """
    Cliente de alto nível para ChromaDB (servidor HTTP) com:
      - Singleton
      - Coleções separadas por dimensão (ex.: _candidates_dim768)
      - Upsert de matrizes de embeddings com IDs
      - Query de similaridade por embedding (cosine)

    Variáveis de ambiente:
      - CHROMA_URL (ex.: http://chromadb:8000)
      - CHROMA_COLLECTION_PREFIX (opcional; padrão: "candidates")
    """

    DEFAULT_DIM = 768

    def __init__(self, base_url: Optional[str] = None, collection_prefix: Optional[str] = None):
        self._url = base_url or os.environ.get("CHROMA_URL", "http://localhost:8000")
        self._prefix = (collection_prefix or os.environ.get("CHROMA_COLLECTION_PREFIX", "candidates")).strip()
        self._client = self._make_http_client(self._url)
        self._collections_cache = {}  # name -> collection
        self._lock = threading.RLock()

    # ------------------------
    # Inicialização do cliente
    # ------------------------
    @staticmethod
    def _make_http_client(url: str):
        """
        Tenta criar o HttpClient a partir de CHROMA_URL.
        Aceita tanto base_url= quanto host/port, e faz fallback para Settings.
        """
        parsed = urlparse(url)
        scheme = parsed.scheme or "http"
        host = parsed.hostname or "localhost"
        port = parsed.port or 8000
        base_url = f"{scheme}://{host}:{port}"

        # 1) Tentativa: assinatura com base_url (suportada em versões mais novas)
        try:
            return chromadb.HttpClient(base_url=base_url)
        except TypeError:
            pass

        # 2) Tentativa: assinatura host/port/ssl (mais antiga)
        try:
            return chromadb.HttpClient(host=host, port=port, ssl=(scheme == "https"))
        except Exception:
            pass

        # 3) Fallback: via Settings
        return chromadb.Client(Settings(
            chroma_api_impl="rest",
            chroma_server_host=host,
            chroma_server_http_port=port,
            chroma_server_ssl=(scheme == "https"),
        ))

    # ------------------------
    # Helpers de coleção
    # ------------------------
    def _collection_name(self, dim: int) -> str:
        return f"{self._prefix}_dim{int(dim)}"

    def _get_or_create_collection(self, dim: int):
        """
        Cria (ou reutiliza do cache) uma coleção específica para a dimensão.
        Define hnsw:space=cosine para casar com seu uso de similaridade do cosseno.
        """
        name = self._collection_name(dim)
        with self._lock:
            if name in self._collections_cache:
                return self._collections_cache[name]

            col = self._client.get_or_create_collection(
                name=name,
                metadata={
                    "hnsw:space": "cosine",
                    "dimension": dim,
                    "owner": "datathon",
                    "entity": "candidate",
                },
            )
            self._collections_cache[name] = col
            return col

    # ------------------------
    # API pública
    # ------------------------
    def upsert_embeddings(
        self,
        embeddings: Union[List[List[float]], np.ndarray],
        ids: Iterable[str],
        metadatas: Optional[Iterable[Dict[str, Any]]] = None,
        dim: Optional[int] = None,
    ) -> None:
        """
        Insere/atualiza embeddings na coleção correspondente à dimensão.
        - embeddings: matriz [N, D]
        - ids: iterável com N strings (ex.: IDs dos candidatos, "1253", "1254"...)
        - metadatas: opcional; se não vier, cria {"candidate_id": id}
        - dim: opcional; se não vier, inferimos de embeddings.shape[1]

        Levanta ValueError em caso de inconsistência.
        """
        arr = np.asarray(embeddings, dtype=float)
        if arr.ndim != 2:
            raise ValueError("`embeddings` deve ser uma matriz 2D (shape [N, D]).")

        n, d = arr.shape
        ids = list(map(str, ids))
        if len(ids) != n:
            raise ValueError(f"Número de ids ({len(ids)}) difere do número de embeddings ({n}).")

        # Dimensão: inferida se não fornecida; se fornecida, valida
        if dim is None:
            dim = d
        elif int(dim) != d:
            raise ValueError(f"Dimensão informada ({dim}) não bate com embeddings ({d}).")

        col = self._get_or_create_collection(dim)

        if metadatas is None:
            metadatas = [{"candidate_id": _id} for _id in ids]
        else:
            metadatas = list(metadatas)
            if len(metadatas) != n:
                raise ValueError(f"Número de metadados ({len(metadatas)}) difere de N ({n}).")

        # Chroma espera lists nativos (não ndarrays)
        col.upsert(
            ids=ids,
            embeddings=arr.tolist(),
            metadatas=metadatas,
        )


    def query_similar_by_embedding(
        self,
        query_embedding: Union[List[float], np.ndarray],
        top_k: int = 5,
        dim: Optional[int] = None,
        include_embeddings: bool = False,
    ) -> Dict[str, Any]:
        """
        Busca os itens mais similares (cosine) dado um embedding de consulta.
        - query_embedding: shape [D] ou [1, D]
        - top_k: quantidade de vizinhos a retornar
        - dim: opcional; se não vier, inferimos de query_embedding
        - include_embeddings: se True, retorna também os embeddings salvos

        Retorna dicionário no formato do Chroma, com `ids`, `distances`, `metadatas` e,
        adicionalmente, `similarities` (1 - distance) para métrica cosine.
        """
        q = np.asarray(query_embedding, dtype=float)
        if q.ndim == 1:
            q = q.reshape(1, -1)
        if q.ndim != 2 or q.shape[0] != 1:
            raise ValueError("`query_embedding` deve ter shape [D] ou [1, D].")

        d = q.shape[1]
        if dim is not None and int(dim) != d:
            raise ValueError(f"Dimensão informada ({dim}) não bate com o embedding de consulta ({d}).")

        col = self._get_or_create_collection(d)
        include = ["distances", "metadatas"]
        if include_embeddings:
            include.append("embeddings")

        res = col.query(
            query_embeddings=q.tolist(),
            n_results=top_k,
            include=include,
        )

        # Para métrica cosine, o Chroma retorna distância ~ (1 - cosine_similarity)
        # Adicionamos `similarities` para conveniência:
        distances = res.get("distances", [])
        if distances:
            sims = [[1.0 - float(dist) for dist in row] for row in distances]
            res["similarities"] = sims

        return res


    def delete_by_ids(self, ids: Iterable[str], dim: int) -> None:
        """Remove itens por ID na coleção da dimensão informada."""
        ids = list(map(str, ids))
        col = self._get_or_create_collection(dim)
        col.delete(ids=ids)


    def clear_collection(self, dim: int) -> None:
        """Apaga TUDO na coleção da dimensão informada."""
        col = self._get_or_create_collection(dim)
        col.delete(where={})  # deleta geral


    def list_dimensions_available(self) -> List[int]:
        """
        Lista dimensões disponíveis com base nos nomes das coleções.
        Útil para inspeção/admin.
        """
        dims = []
        for c in self._client.list_collections():
            name = c.name  # p.ex.: "candidates_dim768"
            if name.startswith(f"{self._prefix}_dim"):
                try:
                    dims.append(int(name.split("_dim", 1)[1]))
                except Exception:
                    pass
        return sorted(set(dims))

    def drop_collections(self, prefix: str | None = None) -> list[str]:
        """
        Apaga coleções do Chroma.
        - Se `prefix` for None: apaga TODAS as coleções.
        - Se `prefix` for algo (ex.: "candidates"): apaga somente as que começam com esse prefixo.
        Retorna a lista de nomes apagados.
        """
        deleted = []
        cols = self._client.list_collections()

        for c in cols:
            name = getattr(c, "name", None) or c["name"]
            if prefix and not name.startswith(prefix):
                continue

            # Tenta apagar por nome (API mais comum). Se a versão exigir id, tenta por id.
            try:
                self._client.delete_collection(name=name)
            except TypeError:
                col_id = getattr(c, "id", None) or c.get("id")
                if not col_id:
                    raise
                self._client.delete_collection(id=col_id)

            # limpa cache interno
            self._collections_cache.pop(name, None)
            deleted.append(name)

        return deleted



# --------------------------------------
# Exemplo de uso com seu embeddings_matrix
# --------------------------------------
#if __name__ == "__main__":
#    # Supondo que você já obteve algo como:
#    # embeddings_matrix = np.array(result) # shape [N, 768]
#    # ids = ["1253", "1254", "1255"]
#
#    # Exemplo dummy só pra ilustrar:
#    rng = np.random.default_rng(42)
#    embeddings_matrix = rng.normal(size=(3, 768)).astype("float32")
#    ids = ["1253", "1254", "1255"]
#
#    chroma = ChromaDB()  # usa CHROMA_URL do ambiente e prefixo "candidates"
#    chroma.upsert_embeddings(embeddings_matrix, ids)  # dim inferida = 768
#
#    # Retrieve usando o primeiro embedding como consulta:
#    query_vec = embeddings_matrix[0]
#    res = chroma.query_similar_by_embedding(query_vec, top_k=3)
#    print("Query result:")
#    print("ids:", res.get("ids"))
#    print("distances:", res.get("distances"))
#    print("similarities:", res.get("similarities"))
#