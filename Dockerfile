FROM python:3.12-slim

WORKDIR /app

RUN apt update && apt install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    iputils-ping \
    net-tools \
    procps \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*


# Instala o Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry


# Copiar arquivos de dependências
COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY . .
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
#CMD ["poetry",  "run", "python3", "run.py"]
CMD ["poetry", "run", "gunicorn", \
        "--bind", "0.0.0.0:5000", \
        "--workers", "1", \
        "--timeout", "120", \
        "wsgi:app" \
]
