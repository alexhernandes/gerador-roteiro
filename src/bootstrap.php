<?php

declare(strict_types=1);

require_once __DIR__ . '/paths.php';

/**
 * Carrega variáveis KEY=VALUE do arquivo .env (sem Composer).
 */
function carregar_env(string $caminho): void
{
    if (!is_file($caminho)) {
        return;
    }

    $linhas = file($caminho, FILE_IGNORE_NEW_LINES);
    if ($linhas === false) {
        return;
    }

    foreach ($linhas as $linha) {
        $linha = trim($linha);
        if ($linha === '' || str_starts_with($linha, '#')) {
            continue;
        }
        if (!str_contains($linha, '=')) {
            continue;
        }

        [$chave, $valor] = explode('=', $linha, 2);
        $chave = trim($chave);
        $valor = trim($valor);

        if (
            (str_starts_with($valor, '"') && str_ends_with($valor, '"'))
            || (str_starts_with($valor, "'") && str_ends_with($valor, "'"))
        ) {
            $valor = substr($valor, 1, -1);
        }

        if (!array_key_exists($chave, $_ENV)) {
            putenv("{$chave}={$valor}");
            $_ENV[$chave] = $valor;
            $_SERVER[$chave] = $valor;
        }
    }
}

carregar_env(ROOT_DIR . DIRECTORY_SEPARATOR . '.env');

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/schema.php';
require_once __DIR__ . '/regras.php';
require_once __DIR__ . '/dialogo.php';
require_once __DIR__ . '/narrativa.php';
require_once __DIR__ . '/voz.php';
require_once __DIR__ . '/polir.php';
require_once __DIR__ . '/enriquecer.php';
require_once __DIR__ . '/instrucoes_roteiro.php';
require_once __DIR__ . '/api.php';
require_once __DIR__ . '/salvar.php';
require_once __DIR__ . '/universos.php';
require_once __DIR__ . '/relatorio.php';
require_once __DIR__ . '/auditoria.php';
require_once __DIR__ . '/corrigir_dialogos.php';
require_once __DIR__ . '/validar.php';
require_once __DIR__ . '/gerar_roteiro.php';