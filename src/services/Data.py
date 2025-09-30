import json
import redis
import os

class Data:
    def __init__(self):
        self.redis_url_0 = os.getenv('REDIS_URL_0')
        self.redis_url_1 = os.getenv('REDIS_URL_1')
        self.redis_url_2 = os.getenv('REDIS_URL_2')

        if (not self.redis_url_0) or (not self.redis_url_1) or (not self.redis_url_2) :
            raise RuntimeError("Variável de ambiente REDIS_URL_0, REDIS_URL_1 ou REDIS_URL_2 não encontrada.")

        self.redis_db0 = redis.from_url(self.redis_url_0) # armazena area de atuacao
        self.redis_db1 = redis.from_url(self.redis_url_1) # armazena principais_atividades + competencia_tecnicas_e_comportamentais 
        self.redis_db2 = redis.from_url(self.redis_url_2) # armazena cv_pt do candidato


    def load_vagas(self, vagas_file) -> None:
        """
        Processa vagas.json e salva nos DBs do Redis:
        - DB 0: chave=id_vaga, valor=areas_atuacao
        - DB 1: chave=id_vaga, valor=principais_atividades + ". " + competencia_tecnicas_e_comportamentais
        """
        try:
            vagas_data = json.load(vagas_file)

            for vaga_id, vaga_info in vagas_data.items():
                perfil = vaga_info.get("perfil_vaga", {})

                # Extrair o campo "areas_atuacao" (default vazio)
                areas_atuacao = perfil.get("areas_atuacao", "")

                # Extrair os campos para concatenação
                principais_atividades = perfil.get("principais_atividades", "").strip()
                competencias = perfil.get("competencia_tecnicas_e_comportamentais", "").strip()

                # Monta o valor do DB1
                concat_text = f"{principais_atividades}. {competencias}" if principais_atividades or competencias else ""

                # Salva no Redis
                self.redis_db0.set(vaga_id, areas_atuacao)
                self.redis_db1.set(vaga_id, concat_text)

        except Exception as e:
            raise RuntimeError(f"Erro ao carregar vagas: {e}")


    def load_applicants(self, candidatos_file) -> None:
        """
        Processa candidatos.json e salva no DB 2 do Redis:
        - DB 2: chave=id_candidato, valor=cv_pt
        """
        try:
            candidatos_data = json.load(candidatos_file)

            for candidato_id, candidato_info in candidatos_data.items():
                cv_pt = candidato_info.get("cv_pt", "").strip()

                # Salva no Redis apenas se houver conteúdo no cv_pt
                if cv_pt:
                    self.redis_db2.set(candidato_id, cv_pt)

        except Exception as e:
            raise RuntimeError(f"Erro ao carregar candidatos: {e}")


    def get_vaga_descricao(self, id: str) -> str:
        raw = self.redis_db1.get(id)  # bytes ou None
        if raw is None:
            raise KeyError(f"Vaga com id '{id}' não encontrada.")
        return raw.decode("utf-8")


    def get_candidatos(self, id: list) -> str:
        """
        Lê database/applicants.json e retorna:
        {"candidatos": [{"id": "...", "nome": "...", "cv_pt": "..."}, ...]}
        """
        if not isinstance(id, list):
            raise ValueError("Parâmetro `id` deve ser uma lista.")

        # Carrega o JSON do disco (simples e direto)
        try:
            with open("database/applicants.json", "r", encoding="utf-8") as f:
                base = json.load(f)  # dict com chaves = ids
        except FileNotFoundError:
            raise FileNotFoundError("Arquivo 'database/applicants.json' não encontrado.")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido em 'database/applicants.json': {e}")

        resultados = []
        for cid in id:
            cid_str = str(cid)
            entry = base.get(cid_str)
            if not isinstance(entry, dict):
                # Se preferir levantar erro quando não achar, troque por:
                # raise KeyError(f"Candidato '{cid_str}' não encontrado no JSON.")
                continue

            # `nome` pode estar em informacoes_pessoais.nome ou infos_basicas.nome
            nome = ""
            infos_pessoais = entry.get("informacoes_pessoais")
            if isinstance(infos_pessoais, dict):
                nome = infos_pessoais.get("nome") or ""
            if not nome:
                infos_basicas = entry.get("infos_basicas")
                if isinstance(infos_basicas, dict):
                    nome = infos_basicas.get("nome") or ""

            cv_pt = entry.get("cv_pt", "") or ""

            resultados.append({
                "id": cid_str,
                "nome": nome,
                "cv_pt": cv_pt
            })

        return json.dumps({"candidatos": resultados}, ensure_ascii=False)









