#!/bin/sh
set -euo pipefail

echo "[entrypoint] start $(date -Iseconds)"

APP_DIR="/app"
CHROMA_URL="${CHROMA_URL:-http://chromadb:8000}"

# Logs imediatos do Python
export PYTHONUNBUFFERED=1

# Importa (BLOQUEANTE) — prints agora aparecem em tempo real
if command -v poetry >/dev/null 2>&1; then
  echo "[entrypoint] import: começando (poetry) $(date -Iseconds)"
  PYTHONPATH=. poetry run python3 -u "$APP_DIR/scripts/import_data.py"
else
  echo "[entrypoint] import: começando (python) $(date -Iseconds)"
  python3 -u "$APP_DIR/scripts/import_data.py"
fi
echo "[entrypoint] import: terminado $(date -Iseconds)"

echo "[entrypoint] executando CMD: $*"


#SETANDO EXPERIMENTO NO MLFLOW
#=====
MLFLOW_URL="${MLFLOW_URL:-http://mlflow:5001}"
curl -sS -X POST "$MLFLOW_URL/api/2.0/mlflow/experiments/create" \
  -H "Content-Type: application/json" \
  -d '{"name":"decision-stats"}' \
  || echo "[mlflow] experimento 'decision-stats' já existe (ok)"
#====

exec "$@"
