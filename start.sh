#!/bin/bash
# BioScale — Iniciar servidor
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Ambiente virtual não encontrado. Execute primeiro:"
    echo "  ./install.sh"
    exit 1
fi

source .venv/bin/activate
echo "Iniciando BioScale..."
python main.py "$@"
