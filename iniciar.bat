@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PHP_PORT=8080"

echo.
echo ========================================
echo   GERADOR DE ROTEIRO
echo ========================================
echo.

REM --- 1. Verificar PHP ---
where php >nul 2>&1
if %errorlevel% neq 0 (
    echo PHP nao encontrado neste PC.
    echo.
    echo Baixe o PHP em: https://windows.php.net/download/
    echo Na instalacao, adicione o PHP ao PATH do Windows.
    echo.
    pause
    exit /b 1
)

echo PHP:
php --version
echo.

REM --- 2. Arquivo .env ---
if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" >nul
        echo Criado arquivo .env a partir do .env.example
        echo Abra .env e coloque sua XAI_API_KEY antes de gerar roteiros.
        echo.
    ) else (
        echo AVISO: arquivo .env nao encontrado. Crie um com XAI_API_KEY=sua_chave
        echo.
    )
)

REM --- 3. Extensao cURL ---
php -r "if (!extension_loaded('curl')) { fwrite(STDERR, 'Extensao cURL ausente no PHP.'); exit(1); }" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: a extensao cURL do PHP nao esta habilitada.
    echo Edite php.ini e descomente: extension=curl
    pause
    exit /b 1
)

echo Dependencias OK.
echo.
echo Abrindo servidor em http://localhost:%PHP_PORT%
echo Pressione Ctrl+C para encerrar.
echo.

start "" "http://localhost:%PHP_PORT%"
php -S localhost:%PHP_PORT% -t .

if %errorlevel% neq 0 (
    echo.
    echo O servidor terminou com erro.
)

pause