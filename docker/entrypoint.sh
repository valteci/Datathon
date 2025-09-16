#!/bin/bash
set -e
echo "entrypoint.sh executado com sucesso!"
exec "$@" # executa o que vem de CMD no dockerfile
