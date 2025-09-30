import os
from typing import List, Tuple
import redis
from google import genai
from google.genai import types
import numpy as np
from src.services.retrieve_data import ChromaDB
from time import sleep


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


candidatos = chunk_candidates_from_redis(chunk_size=100)
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
contador = 0
for chunk in candidatos:
    ids = []
    curriculos = []
    for curriculo in chunk:
        ids.append(curriculo[0]) # id
        curriculos.append(curriculo[1]) # texto do currículo

    texts = curriculos

    result = [
        np.array(e.values) for e in client.models.embed_content(
            model=os.getenv('MODEL', 'gemini-embedding-001'),
            contents=texts,
            config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")).embeddings
    ]

    embeddings_matrix = np.array(result)
    #embeddings_matrix = np.array([e.values for e in result], dtype=np.float32)
    chroma = ChromaDB()
    chroma.upsert_embeddings(embeddings=embeddings_matrix, ids=ids)
    contador += 100
    print('tudo certo!', contador)
    sleep(20)


#client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
#texts = [
#    r'   \n\n\ncontato\ndomingos de morais, 1368 - aptº\nluciano bessegato\n1404 - vila mariana - são paulo /sp consultor de ti na finality consultores associados\n\n- analista responsável do projeto de implantação da suíte oracle\nprincipais competências primavera p6 eppm nas empresas angloamerican, alcoa,\nmicrosoft office bradesco, braskem, ems, vale e valefértil, csn.\npython\ntecnologia da informação - administração dos produtos pfsense, zabbix, administração\nde office e sharepoint 365 e serviços de rede windows e linux\ncertifications redhat.\noracle primavera cloud solution\nengineer specialist - participação em projetos na implantação do oracle unifier.\nprimavera unifier solution engineer - trabalho analítico com o microsoft power bi, conectando os dados\nspecialist\ndo p6 a partir do azure.\nprimavera p6 eppm solution\nengineer specialist\nitil foundation certificate in it - desenvolvimento de sistema financeiro java orientado à\nservice management webcom adoção da tecnologia javaserver faces (jsf), facelets\ndesegurança, adoção de ferramentas como hibernate/jpa.\n\n\n- desenvolvimento do projeto de artigos de tecnologia, utilizando\nnodejs, javascript, vuejs, html5, css3, em base de dados\nmongodb e postgree.- conhecimento em plataformas de\ndesenvolvimento: python, java, javascript, nodejs, php, angular9,\nhtml5 e css3 -conhecimento em framework: jquery, angular,\nreact, vue,express e bootstrap.\n\n- conhecimento em base de dados: sql server, oracle database,\npostgree, mongodb e mysql.\n\n\n\nexperiência\nfinality consultores associados\nconsultor de ti\nsetembro de 2020 - present (1 ano 9 meses)\nsão paulo, são paulo, brasil\n\n- participação na migração dos dados para oracle unifier em itapu.\n\n\n  page 1 of 4\n   \n\n\n- administração do servidor\n- participação no projeto de implantação do oracle unifier para irani papel e\nembalagens\n- analista responsável na implantação do oracle primavera p6 eppm na\nusiminas.\n- analista responsável na atualização do oracle primavera p6 eppm - csn\n(engenharia).\n- analista responsável na instalação e configuração do oracle primavera\np6 eppm (águas azuis), configurando a autenticação ldap, e utilizando a\nnavegação via ssl\n\n\nverano engenharia de sistemas\nanalista de ti\nmarço de 1999 - agosto de 2020 (21 anos 6 meses)\nsão paulo, são paulo, brasil\n\nsoftware microsoft project: 2003 a server\n• banco de dados :sql server-oracle database, mysql, postgree e\nmongodb\n• elaboração do lay-out físico da empresa proporcionando maior flexibilidade e\notimização nas mudanças internas;\n• elaboração do lay-out da rede de telefonia favorecendo a manutenção e\ncontrole das ocorrências;\n• migração das versões do windows 2003 para windows 2008 r2;\n• migração do exchange 2007 para exchange 2010 windows 2008 r2;\n• participação no projeto de atualização do primavera na vale corporativo;\n• participação no projeto de instalação do primavera no bradesco corporativo;\n• manutenção e administração em base de dados sql server 2005 e oracle;\n• responsável pela instalação/configuração do primavera p6 eppm,\ncontemplando a suíte também foi instalado configurado o oracle universal\ncontent management 12g e oracle bi publisher12g.\n- administração de servidores dhcp e dns em linux- administração de\nservidores apache2 e confguração com nginx\n- instalação, configuração e administração do proxy com squid.\n- instalação, configuração e administração de servidores de arquivos com\nsamba.\n- instalação, configuração e administração de servidores firewall com\niptables.\n- instalação, configuração e administração openldap.\n\n\n\n  page 2 of 4\n   \n\n\n- analista responsável em atualizar a suíte primavera na ems, onde foi\ninstalada e configurada as últimas versões do oracle primavera, oracle\nbusiness inteligence enterprise, oracle web content, sendo executados em\nred hat 7.3.\n- instalação, configuração e administração do pfsense.- instalação,\nconfiguração e adminitração do zabbix.\n- administração do office e sharepoint 365\n- sistema financeiro java orientado à web com adoção da\ntecnologiajavaserver faces (jsf), facelets de segurança, adoção de\nferramentascomo hibernate/jpa.\n- projeto de artigos de tecnologia, nodejs, javascript, vuejs, html5, css3,\nem base de dados mongodb e postgree.\n\n\ncamera municipal de getulina\nanalista de sistema\nagosto de 1996 - janeiro de 1997 (6 meses)\ngetulina, são paulo, brazil\n\ndesenvolvimento e implantação do sistema de consulta de leis.\nutilizando a linguagem clipper para a implantação do sistema, e realizando\ntoda documentação da análise realizada.\n\n\nsanta casa de misericórdia de getulina - sp\n1 ano 6 meses\n\nanalista de sistema\njaneiro de 1996 - junho de 1996 (6 meses)\ngetulina, são paulo, brazil\n\ndesenvolvimento e implantação do sistema de prontuários médicos.\nutilizando a linguagem clipper para a implantação do sistema, e realizando\ntoda documentação da análise realizada.\n\nanalista de sistema\njaneiro de 1995 - dezembro de 1995 (1 ano)\ngetulina, são paulo, brazil\n\ndesenvolvimento e implantação do sistema de controle da farmácia.\nutilizando a linguagem clipper para a implantação do sistema, e realizando\ntoda documentação da análise realizada.\n\n\nmicrocamp tecnologia\nprofessor\njaneiro de 1994 - dezembro de 1994 (1 ano)\npiracicaba, são paulo, brazil\n\n  page 3 of 4\n   \n\n\nministrava aula de sistema operacional\n\n\n\n\nformação acadêmica\nunilins - centro universitário de lins\npós-graduação lato sensu - especialização, análise de sistemas de\ncomputação · (dezembro de 1997)\n\n\nunilins - centro universitário de lins\ntecnólogo em processamento de dados, tecnologia da\ninformação · (dezembro de 1993)\n\n\n\n\n  page 4 of 4\n'
#]
#result = [
#    np.array(e.values) for e in client.models.embed_content(
#        model="gemini-embedding-001",
#        contents=texts,
#        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")).embeddings
#]
#
#print(result)