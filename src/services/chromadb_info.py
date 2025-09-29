from retrieve_data import ChromaDB
from typing import Iterable, Optional, Sequence, Any
from collections.abc import Sequence

chroma = ChromaDB()

def diagnostico():
    # a) Listar coleções existentes (nome + metadata + contagem)
    for c in chroma._client.list_collections():
        col = chroma._client.get_collection(c.name)
        print(f"Coleção: {c.name}")
        print(f"  metadata: {col.metadata}")
        print(f"  itens: {col.count()}")
        print("-" * 40)

    # b) Se quiser pegar só as dimensões que você está usando (conforme a nossa classe):
    print("Dimensões disponíveis:", chroma.list_dimensions_available())

    # c) Inspecionar o conteúdo de uma coleção específica (ex.: dim 768)
    col = chroma._get_or_create_collection(768)  # usa/abre a coleção "candidates_dim768" por padrão

    # Pegue alguns itens sem baixar embeddings (mais leve)
    sample = col.get(limit=5, include=["metadatas"])  # ids vêm sempre; embeddings só se pedir
    print("IDs:", sample["ids"])
    print("Metadatas:", sample["metadatas"])

    # Se realmente quiser ver embeddings (cuidado com payload)
    # sample_full = col.get(limit=2, include=["metadatas", "embeddings"])
    # print("IDs:", sample_full["ids"])
    # print("Embeddings[0].len:", len(sample_full["embeddings"][0]))


def apagar():
    apagadas = chroma.drop_collections()                 # cuidado!
    print("Coleções apagadas:", apagadas)



def ver_dados(
    dim: int = 768,
    limit: int = 20,
    page_size: int = 100,
    incluir_documento: bool = True,
    incluir_embeddings: bool = False,
    preview_chars: int = 120,
    where: Optional[dict] = None,
    where_document: Optional[dict] = None,
    ids: Optional[Sequence[str]] = None,
    doc_key_em_metadata: Optional[str] = None,  # ex.: "texto" se você guardou o texto dentro de metadata
) -> list[dict]:
    """
    Lista linhas (id + metadados + documento) de uma coleção do Chroma.

    - dim: dimensão da coleção (ex.: 768 => "candidates_dim768")
    - limit: total desejado de linhas
    - page_size: tamanho do lote por chamada .get (evita baixar tudo de uma vez)
    - incluir_documento: inclui uma prévia do documento (ou de um campo de metadata se indicado)
    - incluir_embeddings: NÃO recomendado para debug (pesado). Se True, mostra só len dos embeddings.
    - preview_chars: quantos caracteres do documento mostrar como prévia
    - where / where_document: filtros do Chroma
    - ids: caso queira inspecionar ids específicos (ignora paginação/offset)
    - doc_key_em_metadata: se o texto estiver em metadata (ex.: {"texto": "..."}), passe a chave aqui

    Retorna: lista de dicts por linha
    """
    col = chroma._get_or_create_collection(dim)

    # monta o include de forma enxuta
    include = ["metadatas"]
    if incluir_documento:
        include.append("documents")
    if incluir_embeddings:
        include.append("embeddings")

    linhas: list[dict] = []

    # caminho 1: ids específicos
    if ids is not None:
        # busca em fatias para não estourar payload
        for i in range(0, len(ids), page_size):
            fatia = ids[i:i + page_size]
            dados = col.get(ids=fatia, include=include)
            linhas.extend(_consolidar_linhas(dados, preview_chars, doc_key_em_metadata))
        _imprimir_tabela(linhas, incluir_documento, incluir_embeddings)
        return linhas

    # caminho 2: paginação por offset/limit
    obtidos = 0
    offset = 0
    while obtidos < limit:
        pegar = min(page_size, limit - obtidos)
        # algumas versões aceitam offset; se a sua não aceitar, caímos no fallback
        try:
            dados = col.get(
                limit=pegar,
                offset=offset,
                include=include,
                where=where,
                where_document=where_document
            )
            n = len(dados.get("ids", []))
            if n == 0:
                break
            linhas.extend(_consolidar_linhas(dados, preview_chars, doc_key_em_metadata))
            obtidos += n
            offset += n
            if n < pegar:
                # não há mais registros
                break
        except TypeError:
            # Fallback para implementações sem "offset": usamos apenas o primeiro "limit"
            dados = col.get(limit=limit, include=include, where=where, where_document=where_document)
            linhas.extend(_consolidar_linhas(dados, preview_chars, doc_key_em_metadata))
            break

    _imprimir_tabela(linhas, incluir_documento, incluir_embeddings)
    return linhas


def _as_seq_or_fallback(val: Any, n: int) -> Any:
    """
    Retorna `val` se não for None. Se for None, retorna [None] * n.
    Se for list/tuple vazio e n>0 (campo ausente), retorna [None] * n.
    NÃO usa `or` para evitar ambiguidade com numpy arrays.
    """
    if val is None:
        return [None] * n
    if isinstance(val, (list, tuple)) and len(val) == 0 and n > 0:
        return [None] * n
    return val


def _consolidar_linhas(dados: dict, preview_chars: int, doc_key_em_metadata: Optional[str]) -> list[dict]:
    """Converte o dict do Chroma (ids/metadatas/documents/embeddings) em 'linhas' (dict por item)."""
    # ids pode vir como numpy array; convertemos para list p/ iteração segura
    ids_raw = dados.get("ids", [])
    ids = list(ids_raw) if isinstance(ids_raw, Sequence) else []

    metadatas = _as_seq_or_fallback(dados.get("metadatas"), len(ids))
    documents = _as_seq_or_fallback(dados.get("documents"), len(ids))
    embeddings = _as_seq_or_fallback(dados.get("embeddings"), len(ids))

    linhas = []
    n = len(ids)
    for i in range(n):
        row = {"id": ids[i]}

        md = metadatas[i] if i < len(metadatas) else None
        if not isinstance(md, dict):
            md = {}
        for k, v in md.items():
            row[str(k)] = v

        doc = documents[i] if i < len(documents) else None
        if (doc is None) and doc_key_em_metadata:
            doc = md.get(doc_key_em_metadata)
        if doc is not None:
            s = str(doc)
            row["document_preview"] = s[:preview_chars] + ("…" if len(s) > preview_chars else "")

        emb = embeddings[i] if i < len(embeddings) else None
        if emb is not None:
            # Mostra o tamanho do vetor de embedding sem imprimir o vetor
            try:
                row["embedding_len"] = len(emb)
            except TypeError:
                # Caso seja um tipo estranho sem __len__
                shape = getattr(emb, "shape", None)
                row["embedding_len"] = shape[-1] if shape else None

        linhas.append(row)
    return linhas


def _imprimir_tabela(linhas: list[dict], incluir_documento: bool, incluir_embeddings: bool) -> None:
    """Imprime as 'linhas' com colunas fixas (id + metadados + doc_preview + embedding_len)."""
    if not linhas:
        print("Nenhuma linha encontrada.")
        return

    # chaves de metadados = todas menos as colunas fixas
    colunas_fixas = {"id", "document_preview", "embedding_len"}
    meta_keys = sorted({k for r in linhas for k in r.keys()} - colunas_fixas)

    headers = ["id"] + meta_keys
    if incluir_documento:
        headers.append("document_preview")
    if incluir_embeddings:
        headers.append("embedding_len")

    print(f"Total de linhas retornadas: {len(linhas)}")
    print("\t".join(headers))

    for r in linhas:
        vals = [str(r.get("id", ""))] + [str(r.get(k, "")) for k in meta_keys]
        if incluir_documento:
            vals.append(str(r.get("document_preview", "")))
        if incluir_embeddings:
            vals.append(str(r.get("embedding_len", "")))
        print("\t".join(vals))


def _normalize_seq(val: Any, fallback_len: int) -> list:
    """
    Converte o campo retornado pelo Chroma em uma lista segura para indexação.
    - Se None -> [None] * fallback_len
    - Se numpy.ndarray -> list(val) (linhas)
    - Se list/tuple -> list(val)
    - Caso contrário -> [val]
    """
    if val is None:
        return [None] * fallback_len

    # Evita depender de numpy aqui: checa via duck typing
    # Se tiver atributo 'shape' e 'tolist', usamos tolist()
    tolist = getattr(val, "tolist", None)
    shape = getattr(val, "shape", None)
    if callable(tolist):
        try:
            as_list = tolist()
            # Se veio 1D/2D, garantimos lista
            return list(as_list) if isinstance(as_list, Sequence) and not isinstance(as_list, (str, bytes)) else [as_list]
        except Exception:
            pass

    if isinstance(val, Sequence) and not isinstance(val, (str, bytes)):
        return list(val)

    return [val]


def _pad_or_trim(seq: list, n: int) -> list:
    """Garante que a sequência tenha exatamente n elementos."""
    if len(seq) < n:
        return seq + [None] * (n - len(seq))
    if len(seq) > n:
        return seq[:n]
    return seq


def ver_embeddings_preview(
    dim: int = 3072,
    limit: int = 3,
    n: int = 8,
    ids: Optional[list[str]] = None,
) -> None:
    """
    Mostra, para alguns itens, o tamanho do embedding e os primeiros N valores.
    Também tenta mostrar um preview de texto (em documents ou em alguma chave de metadata).
    """
    col = chroma._get_or_create_collection(dim)
    include = ["embeddings", "documents", "metadatas"]

    dados = col.get(ids=ids, limit=None if ids else limit, include=include)

    ids_list   = _normalize_seq(dados.get("ids"),        0)
    total      = len(ids_list)

    embs       = _pad_or_trim(_normalize_seq(dados.get("embeddings"), total), total)
    docs       = _pad_or_trim(_normalize_seq(dados.get("documents"),  total), total)
    metas      = _pad_or_trim(_normalize_seq(dados.get("metadatas"),  total), total)

    for i, _id in enumerate(ids_list):
        emb = embs[i]

        if emb is None:
            print(f"ID: {_id} | SEM embedding")
            continue

        # Converte vetor para lista imprimível (head)
        if hasattr(emb, "tolist"):
            try:
                vec = emb.tolist()
            except Exception:
                vec = list(emb) if isinstance(emb, Sequence) else [emb]
        else:
            vec = list(emb) if isinstance(emb, Sequence) else [emb]

        head = vec[:n]
        print(f"ID: {_id} | len={len(vec)} | head({n})={head}")

        # Preview de texto
        doc = docs[i]
        md  = metas[i] if isinstance(metas[i], dict) else {}

        preview = None
        origem = None

        if isinstance(doc, str) and doc:
            preview = doc[:120]
            origem = "documents"
        else:
            # tente chaves comuns; ajuste conforme seu esquema
            for k in ("texto", "text", "resume", "curriculo", "content"):
                v = md.get(k)
                if isinstance(v, str) and v:
                    preview = v[:120]
                    origem = f"metadata.{k}"
                    break

        if preview:
            print(f"  {origem}: {preview}{'…' if len(preview) == 120 else ''}")
        else:
            print("  doc/preview: <vazio>")

#diagnostico()


# 1) Ver um "snapshot" de 20 linhas da coleção 768 (com prévia do documento)
#ver_dados(dim=768, limit=20)

# 2) Ver com filtro por metadata (ex.: apenas candidatos de SP)
#ver_dados(dim=768, limit=50, where={"uf": "SP"})

# 3) Se o texto do currículo foi salvo em metadata (ex.: {"texto": "..."}):
#ver_dados(dim=768, limit=20, incluir_documento=True, doc_key_em_metadata="texto")

# 4) Conferir ids específicos
#ver_dados(dim=768, ids=["cand_001", "cand_002", "cand_003"])

# 5) (Opcional) ver o tamanho dos embeddings (sem despejar os vetores)
#ver_dados(dim=3072, limit=10, incluir_embeddings=True)



#ver_embeddings_preview(dim=3072, limit=3, n=10)
# ou para IDs específicos:
#ver_embeddings_preview(dim=3072, ids=["36545", "30624"], n=6)
