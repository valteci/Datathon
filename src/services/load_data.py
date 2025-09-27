import json
import redis
import os

class Load:
    def __init__(self):
        self.redis_url_0 = os.getenv('REDIS_URL_0')
        self.redis_url_1 = os.getenv('REDIS_URL_1')
        self.redis_url_2 = os.getenv('REDIS_URL_2')

        if (not self.redis_url_0) or (not self.redis_url_1) or (not self.redis_url_2) :
            raise RuntimeError("Variável de ambiente REDIS_URL_0, REDIS_URL_1 ou REDIS_URL_2 não encontrada.")

        self.redis_db0 = redis.from_url(self.redis_url_0)
        self.redis_db1 = redis.from_url(self.redis_url_1)
        self.redis_db2 = redis.from_url(self.redis_url_2)


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

    def load_applicants(self,) -> None:
        pass