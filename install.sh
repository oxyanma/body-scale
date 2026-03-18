#!/bin/bash
# BioScale Installer — macOS / Linux
set -e

echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║       BioScale — Instalador      ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# Verificar Python 3
if ! command -v python3 &>/dev/null; then
    echo "ERRO: Python 3 não encontrado."
    echo "Instale em: https://www.python.org/downloads/"
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python encontrado: $PY_VERSION"

# Ir para o diretório do script
cd "$(dirname "$0")"

# Criar ambiente virtual
if [ ! -d ".venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv .venv
else
    echo "Ambiente virtual já existe."
fi

# Ativar
source .venv/bin/activate

# Instalar dependências
echo "Instalando dependências..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo ""
echo "Instalação concluída!"
echo ""
echo "Para iniciar o BioScale:"
echo "  ./start.sh"
echo ""
