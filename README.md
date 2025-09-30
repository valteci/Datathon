# ✨VISÃO GERAL DO PROJETO
O projeto tenta otimizar um dos processos de RH que é o *matching* de candidatos para a empresa [Decision](https://webrh.decisionbr.com.br/).

A dor a ser resolvida nesse projeto consiste em fazer um MVP que seja capaz de responder à seguinte pergunta: dado uma vaga específica, quais seriam os melhores candidatos para essa vaga considerando que eu tenho o texto dos currículos dos candidatos armazenados no sistema, utilizando-se de soluções de inteligência artificial.

Para isso, foram utilizadas técnicas de *embeddings* e similaridade do cosseno que serão detalhadas ao longo deste documento.  

## 🎯Objetivo
O projeto em questão é um MVP para achar os melhores candidatos para uma determinada vaga dado que temos os textos dos currículos dos candidatos. Deve ser possível escolher quais são os melhores K candidatos para a vaga. 

## 💡Solução Proposta
A solução proposta consiste no seguinte:
* Utilizar a API do gemini para gerar *embeddings* tanto da vaga requerida como dos currículos dos candidatos cadastrados.
* Fazer a similaridade do cosseno entre a vaga específica (a vaga que o usuário quer) e todos os candidatos cadastrados no banco vetorial.
* Retornar os K candidatos mais similares à vaga, de modo que o usuário pode escolher o valor de K. 
* Por fim, logar estatísticas do modelo utilizando mlflow para poder monitorar o desempenho do modelo e possíveis drifts que possam acontecer em produção ao longo do tempo.

## Stack Tecnológica:
Foram utilizados as seguintes tecnologias para construir esse projeto:
* **Python3 (versão 3.12)**: linguagem de programação utilizada.
* **poetry**: gerenciador de pacotes do python. 
* **Docker e Docker compose**: conteinerização e orquestração dos serviços (API, ChromaDB, Redis e, MLflow).
* **ChromaDB**: banco vetorial para armazenar e consultar embeddings semânticos.
* **Redis**: armazenamento chave-valor em memória, de alta performance.
* **Mlflow**: rastreamento de experimentos (parâmetros, métricas e artefatos).
* **Flask**: microframework web para a API.
* **Gunicorn**: servidor WSGI para produção.
* **Geimini-API**: API do modelo LLM.



# ESTRUTURA DO PROJETO
```
.
├── Dockerfile
├── LICENSE
├── README.md
├── config.py
├── database
│   ├── READ.ME.txt
│   ├── applicants.json
│   ├── candidates_dim3072.jsonl
│   ├── prospects.json
│   └── vagas.json
├── docker
│   └── entrypoint.sh
├── docker-compose.yml
├── poetry.lock
├── pyproject.toml
├── run.py
├── scripts
│   ├── __init__.py
│   ├── export_data.py
│   ├── generate_chromadb_file.py
│   ├── generate_embeddings.py
│   └── import_data.py
├── src
│   ├── __init__.py
│   ├── app.py
│   ├── extensions.py
│   ├── models.py
│   ├── routes.py
│   ├── services
│   │   ├── Data.py
│   │   ├── __init__.py
│   │   ├── chromadb_info.py
│   │   ├── gemini_api.py
│   │   ├── log.py
│   │   └── retrieve_data.py
│   ├── static
│   │   ├── css
│   │   │   └── style.css
│   │   ├── img
│   │   │   └── decision_logo.png
│   │   └── js
│   │       └── script.js
│   └── templates
│       └── index.html
├── .env.sample
└── wsgi.py
```

Explicando os arquivos que estão na raiz do projeto:
* **Dockerfile:** arquivo de configuração do Docker, foi utilizado para gerar um container da API do Flask
* **LICENSE**: arquivo de licensa do projeto (licenciado sob a MIT License).
* **README.md**: este arquivo, com instruções e documentação do projeto.
* **config.py**: arquivo usado no padrão Application Factory do Flask, centraliza as configurações para *development*, *test* e *production* (geralmente lendo variáveis do ambiente/.env).
* **docker-compose.yml**: arquivo de configuração do Docker compose, é responsável por declarar os serviços do sistema bem como configurar o ambiente de cada um deles.
* **poetry.lock**: arquivo de lock do Poetry, tem a responsabilidade de armazenar e travar as versões de cada dependência na árvore de dependências do projeto para garantir a reprodutibilidade.
* **pyproject.toml**: arquivo de configuração do Poetry e metadados do projeto, é reponsável por armazenar as bibliotecas utilizadas no projeto bem como algumas informações gerais.
* **run.py**: arquivo gerado pelo padrão factory do Flask, é utilizado quando se quer executar a aplicação em modo development utilizando o comando "poetry run python3 run.py", não é utilizado em produção.
* **wsgi.py**: arquivo que inicia a aplicação em produção. É utilizado pelo servidor web *gunicorn* para iniciar o servidor python da API, ele contém tudo que é preciso para criar e executar a aplicação.
* **.env.sample**: arquivo que possui uma amostra das variáveis de ambiente do projeto, basicamente possui o valor de todas as variáveis de ambiente menos a GEMINI_API_KEY, por questões de segurança. O arquivo .env deve ser uma cópia desse arquivo, só que nele você deve preencher o valor de GEMINI_API_KEY.

# INSTRUÇÕES DE DEPLOY LOCAL
Para executar o projeto local, você precisa ter o docker e o docker compose instalado na sua máquina e então executar os seguintes passos:
* Baixe o projeto com o seguinte comando:
```bash
git clone https://github.com/valteci/Datathon.git
```
* Entre no diretório do projeto com o comando:
```bash
cd Datathon
```
* Crie uma pasta chamada "database" na raiz do projeto. A versão entregue aos professores já possui essa pasta, não precisa criá-la caso seja o professor.
* Baixe [esse arquivo](https://drive.google.com/file/d/16TV4tOEU45j0Uq457uU2JIp8vEx9lHuv/view?usp=sharing) e coloque-o dentro da pasta database. A versão entregue aos professores já possui esse arquivo, não precisa baixá-lo caso seja o professor.
* Criar o arquivo ".env" na raiz do projeto, ele é uma cópia do arquivo .env.sample que já vem no projeto, mas você precisa preencher a variável de ambiente GEMINI_API_KEY com uma chave válida dentro do arquivo .env. A versão entregue aos professores já possui um .env válido, não precisa criá-lo caso seja um professor.
* Na raiz do projeto, executar o seguinte comando para rodar a aplicação:
```bash
docker compose up --build
```
* Monitorar a saída do comando no passo anterior. Quando os serviços subirem, o servidor vai precisar fazer o import dos embeddings dos candidatos, o que vai demorar de 1 a 2 minutos na primeira vez que o sistema for executado. A aplicação estará pronta para uso quando os imports forem concluídos (done) e aparecer uma mensagem parecida com essa "[INFO] Booting worker with pid..."
* Acesse a aplicação por meio do endereço [localhost:5000](http://localhost:5000)


# DEPLOY NO GOOGLE CLOUD
Essa projeto foi implantado do google cloud e pode ser acessado pelo seguinte link: [http://34.39.160.178:5000/](http://34.39.160.178:5000/)


# ROTAS E EXEMPLOS DE CHAMADAS A API

# FLUXO DE PROCESSAMENTO

