@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON_VERSION=3.11.9"
set "LAUNCHER_VERSION=2026.07.10.3"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUNBUFFERED=1"
set "PYTHONNOUSERSITE=1"
set "PYTHONPATH=%~dp0app"
title Gerador de Roteiro

echo.
echo ========================================
echo   GERADOR DE ROTEIRO
echo ========================================
echo.
echo Launcher: %LAUNCHER_VERSION%
echo Arquivo:  %~f0
echo Projeto:  %CD%
echo.

REM --- 1. Validar os arquivos principais ---
if not exist "main.py" (
    echo ERRO: main.py nao foi encontrado em:
    echo %CD%
    goto :erro
)

if not exist "app\gerar_roteiro.py" (
    echo ERRO: app\gerar_roteiro.py nao foi encontrado.
    echo Execute este arquivo dentro da pasta completa do projeto.
    goto :erro
)

REM --- 2. Encontrar Python 3.11 ---
set "PY="
py -3.11 --version >nul 2>&1
if not errorlevel 1 set "PY=py -3.11"

if not defined PY (
    python --version 2>&1 | findstr /R /C:"Python 3\.11\." >nul
    if not errorlevel 1 set "PY=python"
)

if defined PY goto :python_ok

echo Python 3.11 nao encontrado neste PC.
echo.
where winget >nul 2>&1
if errorlevel 1 goto :python_manual

echo Instalando Python %PYTHON_VERSION% via winget...
winget install -e --id Python.Python.3.11 --version %PYTHON_VERSION% --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto :python_manual

echo.
echo Python instalado. Feche esta janela e abra iniciar.bat novamente.
goto :fim

:python_manual
echo Nao foi possivel instalar automaticamente.
echo Baixe Python %PYTHON_VERSION% em:
echo https://www.python.org/downloads/release/python-3119/
echo Na instalacao, marque "Add Python to PATH".
goto :erro

:python_ok
echo Interpretador:
%PY% --version
echo.

REM --- 3. Preparar configuracao local ---
if not exist ".env" (
    if exist ".env.example" (
        copy /Y ".env.example" ".env" >nul
        echo Arquivo .env criado.
        echo Coloque sua XAI_API_KEY nele antes de gerar um roteiro.
        echo.
    ) else (
        echo AVISO: .env nao encontrado.
        echo Crie o arquivo com: XAI_API_KEY=sua_chave
        echo.
    )
)

REM --- 4. Instalar/atualizar dependencias quando necessario ---
echo Verificando dependencias...
%PY% -c "import openai; import dotenv" >nul 2>&1
if errorlevel 1 (
    if not exist "requirements.txt" (
        echo ERRO: requirements.txt nao foi encontrado.
        goto :erro
    )
    echo Instalando dependencias do projeto...
    %PY% -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo ERRO: nao foi possivel instalar as dependencias.
        goto :erro
    )
)
echo Dependencias OK.
echo.

REM --- 5. Iniciar com entrada interativa pelo teclado ---
echo Verificando a interface carregada...
%PY% -X utf8 -c "import entrada; print('Modulo:   ' + entrada.__file__); print('Idiomas:  ' + ' / '.join(entrada.IDIOMAS))"
if errorlevel 1 (
    echo ERRO: nao foi possivel carregar app\entrada.py desta pasta.
    goto :erro
)
echo.
echo Use as setas e ENTER ou o numero de cada opcao nos menus.
echo.
%PY% -X utf8 -B "%~dp0main.py"
set "APP_EXIT=%ERRORLEVEL%"

if not "%APP_EXIT%"=="0" (
    echo.
    echo O programa terminou com erro ^(codigo %APP_EXIT%^).
    goto :erro
)

goto :fim

:erro
echo.
echo Nao foi possivel concluir a operacao.
pause
endlocal & exit /b 1

:fim
echo.
pause
endlocal & exit /b 0
