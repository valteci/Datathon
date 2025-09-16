#!/bin/bash
set -e
touch main.cpp
exec "$@" # executa o que vem de CMD no dockerfile
