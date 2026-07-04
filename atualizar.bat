@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "REPO_URL=https://github.com/alexhernandes/gerador-roteiro.git"
set "BRANCH=main"

echo.
echo ========================================
echo   ATUALIZAR REPOSITORIO (GIT PUSH)
echo ========================================
echo.
echo Repositorio: %REPO_URL%
echo Branch: %BRANCH%
echo.

REM --- 1. Verificar Git ---
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo Git nao encontrado.
    echo Instale em: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM --- 2. Inicializar repo se necessario ---
if not exist ".git" (
    echo Inicializando repositorio Git...
    git init
    git branch -M %BRANCH%
)

REM --- 3. Configurar remote origin ---
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo Configurando remote origin...
    git remote add origin %REPO_URL%
) else (
    git remote set-url origin %REPO_URL%
)

REM --- 4. Status atual ---
echo Alteracoes pendentes:
echo.
git status --short
echo.

REM --- 5. Mensagem do commit ---
set "MSG="
set /p MSG=Mensagem do commit (Enter = atualizacao automatica): 
if "%MSG%"=="" set "MSG=Atualizacao %date% %time%"

REM --- 6. Commit ---
git add -A
git diff --cached --quiet
if %errorlevel%==0 (
    echo Nenhuma alteracao para commitar.
) else (
    echo.
    echo Commit: %MSG%
    git commit -m "%MSG%"
    if %errorlevel% neq 0 (
        echo Erro ao criar commit.
        pause
        exit /b 1
    )
)

REM --- 7. Push ---
echo.
echo Enviando para GitHub...
git push -u origin %BRANCH%
if %errorlevel% neq 0 (
    echo.
    echo Push falhou. Verifique:
    echo   - Conexao com a internet
    echo   - Login no GitHub (git credential manager ou token)
    echo   - Permissao de escrita no repositorio
    echo.
    pause
    exit /b 1
)

echo.
echo Repositorio atualizado com sucesso!
echo %REPO_URL%
echo.
pause