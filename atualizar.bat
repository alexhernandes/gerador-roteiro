@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title Atualizar Gerador de Roteiro

set "REPO_URL=https://github.com/alexhernandes/gerador-roteiro.git"
set "BRANCH=main"
set "TMP_CLONE=%TEMP%\gerador-roteiro-update-%RANDOM%-%RANDOM%"
set "ENV_BACKUP=%TEMP%\gerador-roteiro-env-%RANDOM%-%RANDOM%.bak"
set "ERRO=0"

echo.
echo ========================================
echo   ATUALIZAR GERADOR DE ROTEIRO
echo ========================================
echo.
echo Pasta:  %CD%
echo Branch: %BRANCH%
echo.

REM --- 1. Verificar ferramentas ---
where git >nul 2>&1
if errorlevel 1 (
    echo ERRO: Git nao encontrado.
    echo Instale em: https://git-scm.com/download/win
    set "ERRO=1"
    goto :finalizar
)

REM --- 2. Preservar a chave local fora da pasta do projeto ---
if exist ".env" (
    copy /Y ".env" "%ENV_BACKUP%" >nul
    if errorlevel 1 (
        echo ERRO: nao foi possivel preservar o arquivo .env.
        set "ERRO=1"
        goto :finalizar
    )
    echo Chave local preservada com seguranca.
)

REM --- 3A. Atualizar uma instalacao Git sem apagar mudancas locais ---
if exist ".git" goto :atualizar_git

REM --- 3B. Instalacao sem .git: baixar uma copia e mesclar arquivos ---
echo Instalacao sem repositorio Git. Baixando a versao mais recente...
git clone --depth 1 --branch "%BRANCH%" --single-branch "%REPO_URL%" "%TMP_CLONE%"
if errorlevel 1 (
    echo ERRO: falha ao baixar a atualizacao.
    set "ERRO=1"
    goto :finalizar
)

echo Copiando arquivos novos...
robocopy "%TMP_CLONE%" "%CD%" /E /XD .git output terminals __pycache__ /XF .env /NFL /NDL /NJH /NJS /NC /NS /NP
if errorlevel 8 (
    echo ERRO: falha ao copiar os arquivos da atualizacao.
    set "ERRO=1"
    goto :finalizar
)
goto :sucesso

:atualizar_git
REM Arquivos ignorados como .env e output nao entram nesta verificacao.
for /f "delims=" %%G in ('git status --porcelain --untracked-files=all') do (
    echo ERRO: existem alteracoes locais que impedem uma atualizacao segura.
    echo.
    git status --short
    echo.
    echo Salve, descarte ou faça commit dessas alteracoes e execute novamente.
    set "ERRO=1"
    goto :finalizar
)

git remote get-url origin >nul 2>&1
if errorlevel 1 git remote add origin "%REPO_URL%"

echo Buscando atualizacoes...
git fetch --prune origin "%BRANCH%"
if errorlevel 1 (
    echo ERRO: falha ao buscar atualizacoes do GitHub.
    set "ERRO=1"
    goto :finalizar
)

echo Aplicando atualizacao segura ^(fast-forward^)...
git merge --ff-only "origin/%BRANCH%"
if errorlevel 1 (
    echo ERRO: a atualizacao nao pode ser aplicada automaticamente.
    echo Nenhum reset destrutivo foi executado.
    set "ERRO=1"
    goto :finalizar
)

:sucesso
echo.
echo Sistema atualizado com sucesso.
echo A pasta output e o arquivo .env foram preservados.

:finalizar
REM Restaurar .env mesmo quando download/merge falhar.
if exist "%ENV_BACKUP%" (
    copy /Y "%ENV_BACKUP%" ".env" >nul
    del /Q "%ENV_BACKUP%" >nul 2>&1
)

if exist "%TMP_CLONE%" rmdir /S /Q "%TMP_CLONE%" >nul 2>&1

echo.
if "%ERRO%"=="1" (
    echo Atualizacao nao concluida.
    pause
    endlocal & exit /b 1
)

echo Abra iniciar.bat para executar a nova versao.
pause
endlocal & exit /b 0
