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

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["tail", "-f", "/dev/null"]
