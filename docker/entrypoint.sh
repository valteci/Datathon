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
exec "$@"
