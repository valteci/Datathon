import os
from typing import List, Tuple
import redis
from google import genai
from google.genai import types
import numpy as np
from src.services.retrieve_data import ChromaDB


def chunk_candidates_from_redis(
    env_var: str = "REDIS_URL_2",
    chunk_size: int = 1000,
    scan_count: int = 1000,
    match: str = "*",
) -> List[List[Tuple[str, str]]]:
    """
    Lê todas as chaves do Redis (id do candidato) e seus valores (texto do currículo)
    e retorna uma lista de listas, em que cada sublista contém até `chunk_size`
    tuplas (id, texto).

    Parâmetros:
        env_var: nome da variável de ambiente com a URL do Redis (já no DB 2).
        chunk_size: tamanho máximo de cada sublista (padrão: 1000).
        scan_count: hint de tamanho do lote para o SCAN/MGET (padrão: 1000).
        match: padrão de chaves para filtrar (padrão: "*").

    Observações:
        - Usa decode_responses=True para retornar strings.
        - Chaves removidas entre SCAN e GET são ignoradas (valor None).
        - A ordem das chaves não é garantida (SCAN é incremental). Se precisar
          de ordem determinística, será necessário ordenar (custo extra).
    """
    url = os.getenv(env_var)
    if not url:
        raise ValueError(f"Variável de ambiente {env_var} não definida.")

    r = redis.from_url(url, decode_responses=True)  # garante str em vez de bytes

    chunks: List[List[Tuple[str, str]]] = []
    atual: List[Tuple[str, str]] = []

    pipe = r.pipeline()
    buffer_keys: List[str] = []

    # Itera as chaves com SCAN e busca os valores em lotes com MGET via pipeline
    for key in r.scan_iter(match=match, count=scan_count):
        buffer_keys.append(key)
        if len(buffer_keys) >= scan_count:
            pipe.mget(buffer_keys)
            values = pipe.execute()[0]  # resultado do MGET
            for k, v in zip(buffer_keys, values):
                if v is None:
                    continue
                atual.append((k, v))
                if len(atual) == chunk_size:
                    chunks.append(atual)
                    atual = []
            buffer_keys.clear()

    # Flush do último lote de chaves (se existir)
    if buffer_keys:
        pipe.mget(buffer_keys)
        values = pipe.execute()[0]
        for k, v in zip(buffer_keys, values):
            if v is None:
                continue
            atual.append((k, v))
            if len(atual) == chunk_size:
                chunks.append(atual)
                atual = []

    # Última sublista (parcial)
    if atual:
        chunks.append(atual)

    return chunks


print(chunk_candidates_from_redis())



