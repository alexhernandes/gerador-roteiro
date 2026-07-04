@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

set "REPO_URL=https://github.com/alexhernandes/gerador-roteiro.git"
set "BRANCH=main"
set "TMP_CLONE=%TEMP%\gerador-roteiro-update"
set "ERRO=0"

echo.
echo ========================================
echo   ATUALIZAR SISTEMA (BAIXAR DO GITHUB)
echo ========================================
echo.
echo Repositorio: %REPO_URL%
echo Branch: %BRANCH%
echo Pasta local: %~dp0
echo.

REM --- 1. Verificar Git ---
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo Git nao encontrado.
    echo Instale em: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM --- 2. Preservar .env local ---
if exist ".env" (
    copy /Y ".env" ".env.local.bak" >nul
    echo .env local preservado.
)

REM --- 3. Atualizar arquivos ---
if not exist ".git" (
    echo Repositorio Git nao encontrado. Clonando do GitHub...
    echo.

    if exist "%TMP_CLONE%" rmdir /S /Q "%TMP_CLONE%"

    git clone --branch %BRANCH% --single-branch %REPO_URL% "%TMP_CLONE%"
    if %errorlevel% neq 0 (
        echo.
        echo Clone falhou. Verifique conexao e URL do repositorio.
        set "ERRO=1"
        goto :fim
    )

    echo.
    echo Copiando arquivos para a pasta local...
    robocopy "%TMP_CLONE%" "%~dp0" /E /XD .git output terminals __pycache__ /XF .env .env.local.bak /NFL /NDL /NJH /NJS /nc /ns /np
    if %errorlevel% GEQ 8 (
        echo Erro ao copiar arquivos.
        set "ERRO=1"
        goto :fim
    )

    rmdir /S /Q "%TMP_CLONE%"

    git init >nul
    git remote add origin %REPO_URL% 2>nul
    git fetch origin %BRANCH% >nul 2>&1
    git checkout -B %BRANCH% >nul 2>&1
    git branch --set-upstream-to=origin/%BRANCH% %BRANCH% >nul 2>&1

    echo Clone concluido.
) else (
    echo Baixando ultima versao do GitHub...
    echo.

    git remote get-url origin >nul 2>&1
    if %errorlevel% neq 0 (
        git remote add origin %REPO_URL%
    ) else (
        git remote set-url origin %REPO_URL%
    )

    git fetch origin %BRANCH%
    if %errorlevel% neq 0 (
        echo.
        echo Falha ao buscar atualizacoes do GitHub.
        set "ERRO=1"
        goto :fim
    )

    git reset --hard origin/%BRANCH%
    if %errorlevel% neq 0 (
        echo.
        echo Falha ao aplicar atualizacoes locais.
        set "ERRO=1"
        goto :fim
    )

    echo Arquivos atualizados para a versao do GitHub.
)

:fim
if exist ".env.local.bak" (
    copy /Y ".env.local.bak" ".env" >nul
    del ".env.local.bak" >nul
    echo .env local restaurado.
)

echo.
if "!ERRO!"=="1" (
    echo Atualizacao falhou.
    pause
    exit /b 1
)

echo Sistema atualizado com sucesso!
echo Fonte: %REPO_URL%
echo.
echo Dica: sua pasta output/ e o arquivo .env nao foram sobrescritos.
echo.
pause
exit /b 0