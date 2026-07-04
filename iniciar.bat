@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON_VERSION=3.11.9"

echo.
echo ========================================
echo   GERADOR DE ROTEIRO
echo ========================================
echo.

REM --- 1. Encontrar Python 3.11.x ---
set "PY="

py -3.11 --version >nul 2>&1
if %errorlevel%==0 (
    set "PY=py -3.11"
    goto :python_ok
)

python --version 2>&1 | findstr /C:"3.11" >nul
if %errorlevel%==0 (
    set "PY=python"
    goto :python_ok
)

REM --- Python 3.11 nao encontrado: tentar instalar ---
echo Python %PYTHON_VERSION% nao encontrado neste PC.
echo.

where winget >nul 2>&1
if %errorlevel%==0 (
    echo Instalando Python %PYTHON_VERSION% via winget...
    echo Aguarde, pode demorar alguns minutos.
    echo.
    winget install -e --id Python.Python.3.11 --version %PYTHON_VERSION% --accept-package-agreements --accept-source-agreements
    echo.
    echo Python instalado! Feche esta janela e abra o iniciar.bat de novo.
    pause
    exit /b 0
)

echo Nao foi possivel instalar automaticamente.
echo Baixe o Python %PYTHON_VERSION% em: https://www.python.org/downloads/release/python3119/
echo Na instalacao, marque "Add Python to PATH".
pause
exit /b 1

:python_ok
echo Python: %PY%
%PY% --version
echo.

REM --- 2. Arquivo .env ---
if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" >nul
        echo Criado arquivo .env a partir do .env.example
        echo Abra .env e coloque sua OPENROUTER_API_KEY antes de gerar roteiros.
        echo.
    ) else (
        echo AVISO: arquivo .env nao encontrado. Crie um com OPENROUTER_API_KEY=sua_chave
        echo.
    )
)

REM --- 3. Instalar dependencias se necessario ---
echo Verificando dependencias...
%PY% -c "import openai; import dotenv" >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando pacotes do requirements.txt...
    %PY% -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Erro ao instalar dependencias.
        pause
        exit /b 1
    )
    echo Dependencias instaladas.
) else (
    echo Dependencias OK.
)
echo.

REM --- 4. Iniciar app ---
set "PYTHONPATH=%~dp0src"
%PY% main.py

if %errorlevel% neq 0 (
    echo.
    echo O programa terminou com erro.
)

pause