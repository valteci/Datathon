# ✨VISÃO GERAL DO PROJETO
O projeto tenta otimizar um dos processos de RH que é o *matching* de candidatos para a empresa [Decision](https://webrh.decisionbr.com.br/).<br><br>

A dor a ser resolvida nesse projeto consiste em fazer um MVP que seja capaz de responder à seguinte pergunta: dado uma vaga específica, quais seriam os melhores candidatos para essa vaga considerando que eu tenho o texto dos currículos dos candidatos armazenados no sistema, utilizando-se de soluções de inteligência artificial.<br><br>

Para isso, foram utilizadas técnicas de *embeddings* e similaridade do cosseno que serão detalhadas ao longo deste documento.<br><br>

## 🎯Objetivo
O projeto em questão é um MVP para achar os melhores candidatos para uma determinada vaga dado que temos os textos dos currículos dos candidatos. Deve ser possível escolher quais são os melhores K candidatos para a vaga. 

## 💡Solução Proposta
**A solução proposta consiste no seguinte:**
* Utilizar a API do Gemini para gerar *embeddings* tanto da vaga requerida como dos currículos dos candidatos cadastrados.<br><br>
* Fazer a similaridade do cosseno entre a vaga específica (a vaga que o usuário quer) e todos os candidatos cadastrados no banco vetorial.<br><br>
* Retornar os K candidatos mais similares à vaga, de modo que o usuário pode escolher o valor de K.<br><br>
* Por fim, logar estatísticas do modelo utilizando MLflow para poder monitorar o desempenho do modelo e possíveis drifts que possam acontecer em produção ao longo do tempo.<br><br>

## Stack Tecnológica:
**Foram utilizados as seguintes tecnologias para construir esse projeto:**
* **Python3 (versão 3.12)**: linguagem de programação utilizada.<br><br>
* **poetry**: gerenciador de pacotes do python.<br><br>
* **Docker e Docker compose**: conteinerização e orquestração dos serviços (API, ChromaDB, Redis e, MLflow).<br><br>
* **ChromaDB**: banco vetorial para armazenar e consultar embeddings semânticos.<br><br>
* **Redis**: armazenamento chave-valor em memória, de alta performance.<br><br>
* **MLflow**: rastreamento de experimentos (parâmetros, métricas e artefatos).<br><br>
* **Flask**: microframework web para a API.<br><br>
* **Gunicorn**: servidor WSGI para produção.<br><br>
* **Geimini-API**: API do modelo LLM.<br><br>



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

### Explicando os arquivos que estão na raiz do projeto:
* **Dockerfile:** arquivo de configuração do Docker, foi utilizado para gerar um container da API do Flask <br><br>
* **LICENSE**: arquivo de licensa do projeto (licenciado sob a MIT License).<br><br>
* **README.md**: este arquivo, com instruções e documentação do projeto.<br><br>
* **config.py**: arquivo usado no padrão Application Factory do Flask, centraliza as configurações para *development*, *test* e *production* (geralmente lendo variáveis do ambiente/.env).<br><br>
* **docker-compose.yml**: arquivo de configuração do Docker compose, é responsável por declarar os serviços do sistema bem como configurar o ambiente de cada um deles.<br><br>
* **poetry.lock**: arquivo de lock do Poetry, tem a responsabilidade de armazenar e travar as versões de cada dependência na árvore de dependências do projeto para garantir a reprodutibilidade.<br><br>
* **pyproject.toml**: arquivo de configuração do Poetry e metadados do projeto, é responsável por armazenar as bibliotecas utilizadas no projeto bem como algumas informações gerais.<br><br>
* **run.py**: arquivo gerado pelo padrão factory do Flask, é utilizado quando se quer executar a aplicação em modo development utilizando o comando "poetry run python3 run.py", não é utilizado em produção.<br><br>
* **wsgi.py**: arquivo que inicia a aplicação em produção. É utilizado pelo servidor web *gunicorn* para iniciar o servidor python da API, ele contém tudo que é preciso para criar e executar a aplicação.<br><br>
* **.env.sample**: arquivo que possui uma amostra das variáveis de ambiente do projeto, basicamente possui o valor de todas as variáveis de ambiente menos a GEMINI_API_KEY, por questões de segurança. O arquivo .env deve ser uma cópia desse arquivo, só que nele você deve preencher o valor de GEMINI_API_KEY.<br><br>

### Explicando os arquivos que estão na pasta docker/:
* **entrypoint.sh**: arquivo que é executado quando é feito o run da imagem docker. Seu propósito é fazer algumas configurações iniciais antes de iniciar a API Flask de fato, como fazer o import dos embeddings dos candidatos e definir o exemperimento no MLflow.<br><br>

### Explicando os arquivos que estão na pasta scripts/:
* **__init__.py**: arquivo que torna a pasta scripts um módulo. Seu propósito é deixar a importação mais fácil.<br><br>
* **export_data.py**: exporta dados do banco vetorial ChromaDB para um arquivo .jsonl. Isso é útil para salvar os embeddings e fazer o load desses dados quando o programa rodar em outra máquina, por exemplo, não precisando gerar os embeddings do zero novamente. Não é usado em produção, mas foi usado em desenvolvimento para gerar o arquivo candidates_dim3072.jsonl.<br><br>
* **generate_embeddings.py**: pega o arquivo de candidatos em database/applicants.json que estava dentro do Redis e gera os embeddings de cada candidato. Pega-se o campo "cv_pt" de cada candidato e gera-se os embeddings desse campo que é salvo no ChromaDB, perceba que esse script foi usado para gerar os embeddings e salvar no ChromaDB enquando o arquivo de cima "export_data.py" é usado para fazer o export desses dados para um arquivo.<br><br>
* **import_data.py**: arquivo que carrega o arquivo de embeddings database/candidates_dim3072.jsonl para dentro do ChromaDB. Ele é chamado pelo docker quando inicia o serviço da API que só é iniciada quando esse import termina, ou seja, ele é bloqueante.<br><br>

### Explicando os arquivos que estão na pasta src/:
* **__init__.py**: arquivo que torna a pasta src um módulo. Seu propósito é deixar a importação mais fácil.<br><br>
* **app.py**: arquivo gerado pelo padrão factory do Flask, mas não utilizado.<br><br>
* **extensions.py**: arquivo gerado pelo padrão factory do Flask, mas não utilizado.<br><br>
* **models.py**: arquivo gerado pelo padrão factory do Flask, mas não utilizado.<br><br>
* **routes.py**: arquivo gerado pelo padrão factory do Flask, contém as rotas da API.<br><br>
* **templates/index.html**: página web do projeto.<br><br>
* **static/css/style.css**: css da página web do projeto.<br><br>
* **static/img/decision_logo.png**: logo da Decision que é usado na página web.<br><br>
* **static/js/script.js**: javascript da página web.<br><br>
* **services/__init__.py**: arquivo que torna a pasta services um módulo. Seu propósito é deixar a importação mais fácil.<br><br>
* **services/chromadb_info.py**: arquivo usado para interagir com o ChromaDB apenas em ambiente de desenvolvimento (excluir dados, ver embeddings, coleções, etc).<br><br>
* **services/Data.py**: arquivo que contém a classe Data, que é responsável por se comunicar com o Redis e acessar os arquivos de vagas e candidatos dentro da pasta database.<br><br>
* **services/gemini_api.py**: arquivo que contém a classe Model, que encapsula a API do Gemini para gerar embeddings. É responsável por interagir com a API do Gemini para gerar embeddings.<br><br>
* **services/log.py**: arquivo responsável por implementar a classe Log, que faz integração com o MLflow via API.<br><br>
* **services/retrieve_data.py**: arquivo responsável por implementar a classe ChromaDB como um singleton. Essa classe é responsável por se comunicar com o banco vetorial ChromaDB.<br><br>


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
* Crie uma pasta chamada "database" na raiz do projeto. A versão entregue aos professores já possui essa pasta, não precisa criá-la caso seja o professor.<br><br>
* Baixe [esse arquivo](https://drive.google.com/file/d/16TV4tOEU45j0Uq457uU2JIp8vEx9lHuv/view?usp=sharing) e coloque-o dentro da pasta database. A versão entregue aos professores já possui esse arquivo, não precisa baixá-lo caso seja o professor.<br><br>
* Criar o arquivo ".env" na raiz do projeto, ele é uma cópia do arquivo .env.sample que já vem no projeto, mas você precisa preencher a variável de ambiente GEMINI_API_KEY com uma chave válida dentro do arquivo .env. A versão entregue aos professores já possui um .env válido, não precisa criá-lo caso seja um professor.<br><br>
* Na raiz do projeto, executar o seguinte comando para rodar a aplicação:
```bash
docker compose up --build
```
* Monitorar a saída do comando no passo anterior. Quando os serviços subirem, o servidor vai precisar fazer o import dos embeddings dos candidatos, o que vai demorar de 1 a 2 minutos na primeira vez que o sistema for executado. A aplicação estará pronta para uso quando os imports forem concluídos (done) e aparecer uma mensagem parecida com essa "[INFO] Booting worker with pid..."<br><br>
* Acesse a aplicação por meio do endereço [localhost:5000](http://localhost:5000)<br><br>


# DEPLOY NO GOOGLE CLOUD
Essa projeto foi implantado do google cloud e pode ser acessado pelo seguinte link: [http://34.39.160.178:5000/](http://34.39.160.178:5000/)


# ROTAS E EXEMPLOS DE CHAMADAS A API


# FLUXO DE PROCESSAMENTO

