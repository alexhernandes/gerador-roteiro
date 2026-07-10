<?php

declare(strict_types=1);

function _converter_valor(mixed $obj): mixed
{
    if ($obj instanceof DateTimeInterface) {
        return $obj->format('c');
    }

    if (is_object($obj) && method_exists($obj, 'group')) {
        try {
            return $obj->group(0);
        } catch (Throwable) {
            return (string) $obj;
        }
    }

    if (is_resource($obj)) {
        return (string) $obj;
    }

    throw new InvalidArgumentException('Tipo não serializável: ' . get_debug_type($obj));
}

function sanitizar_para_json(mixed $obj): mixed
{
    if (is_array($obj)) {
        $resultado = [];
        foreach ($obj as $chave => $valor) {
            $resultado[$chave] = sanitizar_para_json($valor);
        }

        return $resultado;
    }

    if (is_object($obj)) {
        if ($obj instanceof DateTimeInterface) {
            return $obj->format('c');
        }

        if (method_exists($obj, 'group')) {
            try {
                return $obj->group(0);
            } catch (Throwable) {
                return (string) $obj;
            }
        }

        if ($obj instanceof Stringable) {
            return (string) $obj;
        }

        return (string) $obj;
    }

    if (is_string($obj) || is_int($obj) || is_float($obj) || is_bool($obj) || $obj === null) {
        return $obj;
    }

    return (string) $obj;
}

function criar_sessao(): string
{
    $pasta = ROOT_DIR . DIRECTORY_SEPARATOR . 'output' . DIRECTORY_SEPARATOR . date('Ymd_His');
    if (!is_dir($pasta)) {
        mkdir($pasta, 0777, true);
    }
    if (!is_dir(pasta_log($pasta))) {
        mkdir(pasta_log($pasta), 0777, true);
    }

    return $pasta;
}

function pasta_log(string $sessao): string
{
    return $sessao . DIRECTORY_SEPARATOR . 'log';
}

function salvar(string $sessao, string $nome, mixed $dados, bool $em_log = false): string
{
    $destino = $em_log ? pasta_log($sessao) : $sessao;
    if (!is_dir($destino)) {
        mkdir($destino, 0777, true);
    }

    $arquivo = $destino . DIRECTORY_SEPARATOR . $nome . '.json';
    $limpo = sanitizar_para_json($dados);

    $json = json_encode(
        $limpo,
        JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_THROW_ON_ERROR
    );

    file_put_contents($arquivo, $json);

    return $arquivo;
}