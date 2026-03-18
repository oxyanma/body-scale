@echo off
chcp 65001 >nul 2>&1

echo.
echo   ======================================
echo        BioScale — Instalador
echo   ======================================
echo.

:: Verificar Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python 3 nao encontrado.
    echo Instale em: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PY_VERSION=%%i
echo Python encontrado: %PY_VERSION%

:: Ir para o diretório do script
cd /d "%~dp0"

:: Criar ambiente virtual
if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
) else (
    echo Ambiente virtual ja existe.
)

:: Ativar
call .venv\Scripts\activate.bat

:: Instalar dependências
echo Instalando dependencias...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo.
echo Instalacao concluida!
echo.
echo Para iniciar o BioScale:
echo   start.bat
echo.
pause
