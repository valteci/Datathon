from retrieve_data import ChromaDB

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