@echo off
cd /d "%~dp0"

if not exist ".venv" (
    echo Ambiente virtual nao encontrado. Execute primeiro:
    echo   install.bat
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
echo Iniciando BioScale...
python main.py %*
