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
        Recebe uma lista de IDs (strings ou ints) e retorna uma string JSON com:
        {"candidatos": [{"id": "...", "nome": "...", "cv_pt": "..."}, ...]}
        Requer que self.candidatos (ou similar) seja um dict com os dados carregados.
        """
        # Descobre onde está o dict base (ajuste o nome se o seu atributo for outro)
        base = getattr(self, "candidatos", None) \
            or getattr(self, "applicants", None) \
            or getattr(self, "candidatos_json", None) \
            or getattr(self, "applicants_json", None)

        if base is None or not isinstance(base, dict):
            raise RuntimeError("Base de candidatos não carregada (ex.: self.candidatos deve ser um dict).")

        resultados = []
        for cid in id:
            cid_str = str(cid)
            entry = base.get(cid_str)
            if not entry or not isinstance(entry, dict):
                # Se preferir falhar ao não achar, troque por um raise ou inclua mesmo assim com campos vazios
                continue

            # Nome pode estar em informacoes_pessoais.nome ou infos_basicas.nome
            nome = None
            info_pess = entry.get("informacoes_pessoais") or {}
            if isinstance(info_pess, dict):
                nome = info_pess.get("nome")

            if not nome:
                infos_basicas = entry.get("infos_basicas") or {}
                if isinstance(infos_basicas, dict):
                    nome = infos_basicas.get("nome")

            if not nome:
                # fallback: se por acaso existir na raiz
                nome = entry.get("nome", "")

            cv_pt = entry.get("cv_pt", "")

            resultados.append({
                "id": cid_str,
                "nome": nome or "",
                "cv_pt": cv_pt or ""
            })

        return json.dumps({"candidatos": resultados}, ensure_ascii=False)










