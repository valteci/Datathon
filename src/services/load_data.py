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

        self.redis_0 = redis.from_url(self.redis_url_0)
        self.redis_1 = redis.from_url(self.redis_url_1)
        self.redis_2 = redis.from_url(self.redis_url_2)


    def load_vagas(self, vagas_file) -> None:
        """
        Lê o arquivo JSON de vagas e salva no Redis.
        - Key no Redis: "vaga:<id>"
        - Value: objeto da vaga serializado em JSON
        """

        


    def load_applicants(self,) -> None:
        pass