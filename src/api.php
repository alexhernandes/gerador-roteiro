<?php

declare(strict_types=1);

const MAX_TENTATIVAS_API = 3;
const PAUSA_RETRY_SEGUNDOS = 2;
const MAX_COMPLETION_TOKENS = 16000;

function criar_cliente(): void
{
    if (XAI_API_KEY === '') {
        throw new InvalidArgumentException(
            "Coloque sua chave xAI no arquivo .env\n"
            . "Exemplo: XAI_API_KEY=sua_chave_aqui\n"
            . 'Obtenha em: https://console.x.ai/'
        );
    }
}

/** Parâmetros extras para modelos Grok 4.3 na xAI. */
function _kwargs_grok(array $kwargs): array
{
    if (str_contains(MODEL, 'grok-4.3') || str_contains(MODEL, 'grok-4')) {
        $kwargs['reasoning_effort'] = REASONING_EFFORT;
    }
    $kwargs['max_completion_tokens'] = MAX_COMPLETION_TOKENS;

    return $kwargs;
}

function chamar_api(
    string $system_prompt,
    string $user_prompt,
    ?array $schema = null,
    int $max_tentativas = MAX_TENTATIVAS_API
): string {
    criar_cliente();

    $kwargs = [
        'model' => MODEL,
        'messages' => [
            ['role' => 'system', 'content' => $system_prompt],
            ['role' => 'user', 'content' => $user_prompt],
        ],
    ];
    $kwargs = _kwargs_grok($kwargs);

    if ($schema !== null) {
        $kwargs['response_format'] = [
            'type' => 'json_schema',
            'json_schema' => $schema,
        ];
    }

    $ultimo_erro = null;
    for ($tentativa = 1; $tentativa <= $max_tentativas; $tentativa++) {
        try {
            $payload = json_encode($kwargs, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE);

            $ch = curl_init(XAI_BASE_URL . '/chat/completions');
            if ($ch === false) {
                throw new RuntimeException('Não foi possível inicializar cURL.');
            }

            curl_setopt_array($ch, [
                CURLOPT_POST => true,
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_HTTPHEADER => [
                    'Content-Type: application/json',
                    'Authorization: Bearer ' . XAI_API_KEY,
                ],
                CURLOPT_POSTFIELDS => $payload,
                CURLOPT_TIMEOUT => 300,
            ]);

            $resposta_bruta = curl_exec($ch);
            $erro_curl = curl_error($ch);
            $http_code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);

            if ($resposta_bruta === false) {
                throw new RuntimeException('Erro cURL: ' . $erro_curl);
            }

            if ($http_code < 200 || $http_code >= 300) {
                throw new RuntimeException("HTTP {$http_code}: {$resposta_bruta}");
            }

            $resposta = json_decode($resposta_bruta, true, 512, JSON_THROW_ON_ERROR);

            if (empty($resposta['choices'])) {
                throw new RuntimeException('Resposta da API sem choices.');
            }

            $content = $resposta['choices'][0]['message']['content'] ?? null;
            if ($content === null || trim((string) $content) === '') {
                throw new RuntimeException('Resposta vazia da API (content=null).');
            }

            return (string) $content;
        } catch (Throwable $erro) {
            $ultimo_erro = $erro;
            if ($tentativa < $max_tentativas) {
                $pausa = PAUSA_RETRY_SEGUNDOS * $tentativa;
                echo "  !! API falhou ({$erro->getMessage()}). Tentativa " . ($tentativa + 1) . "/{$max_tentativas} em {$pausa}s...\n";
                sleep($pausa);
                continue;
            }
            throw new RuntimeException(
                "API falhou após {$max_tentativas} tentativas: {$ultimo_erro->getMessage()}",
                0,
                $ultimo_erro
            );
        }
    }

    throw new RuntimeException('API falhou sem retorno.');
}

function _limpar_texto(string $texto): string
{
    if ($texto === '') {
        throw new RuntimeException('Resposta vazia da API.');
    }

    $texto = trim($texto);
    if (preg_match_all('/```(?:json)?\s*([\s\S]*?)\s*```/', $texto, $matches) && !empty($matches[1])) {
        $blocos = $matches[1];
        usort($blocos, static fn (string $a, string $b): int => strlen($b) <=> strlen($a));

        return trim($blocos[0]);
    }

    return $texto;
}

function _achar_inicio_json(string $texto): ?int
{
    $len = strlen($texto);
    for ($i = 0; $i < $len; $i++) {
        if ($texto[$i] === '{' || $texto[$i] === '[') {
            return $i;
        }
    }

    return null;
}

/** Equivalente ao json.JSONDecoder().raw_decode() do Python. */
function _raw_decode_json(string $texto, int $idx): ?array
{
    $len = strlen($texto);
    if ($idx >= $len) {
        return null;
    }

    $char = $texto[$idx];
    if ($char !== '{' && $char !== '[') {
        return null;
    }

    $depth = 0;
    $in_string = false;
    $escape = false;

    for ($i = $idx; $i < $len; $i++) {
        $c = $texto[$i];

        if ($escape) {
            $escape = false;
            continue;
        }

        if ($in_string) {
            if ($c === '\\') {
                $escape = true;
            } elseif ($c === '"') {
                $in_string = false;
            }
            continue;
        }

        if ($c === '"') {
            $in_string = true;
            continue;
        }

        if ($c === '{' || $c === '[') {
            $depth++;
        } elseif ($c === '}' || $c === ']') {
            $depth--;
            if ($depth === 0) {
                $json_str = substr($texto, $idx, $i - $idx + 1);
                try {
                    $decoded = json_decode($json_str, true, 512, JSON_THROW_ON_ERROR);
                } catch (JsonException) {
                    return null;
                }

                return [$decoded, $i + 1];
            }
        }
    }

    return null;
}

function extrair_json(string $texto): mixed
{
    $texto = _limpar_texto($texto);
    $inicio = _achar_inicio_json($texto);

    if ($inicio === null) {
        throw new RuntimeException('Nenhum JSON encontrado na resposta da API.');
    }

    $texto = substr($texto, $inicio);
    $objetos = [];
    $idx = 0;
    $len = strlen($texto);

    while ($idx < $len) {
        while ($idx < $len && $texto[$idx] !== '{' && $texto[$idx] !== '[') {
            $idx++;
        }
        if ($idx >= $len) {
            break;
        }

        $resultado = _raw_decode_json($texto, $idx);
        if ($resultado === null) {
            break;
        }

        [$obj, $fim] = $resultado;
        $objetos[] = $obj;
        $idx = $fim;
    }

    if ($objetos === []) {
        throw new RuntimeException('Não consegui ler o JSON da resposta da API.');
    }

    if (count($objetos) === 1) {
        return _normalizar($objetos[0]);
    }

    return _normalizar(_juntar_objetos($objetos));
}

/** Detecta JSON esvaziado pela normalização antiga (title/idea/cast/scenes). */
function _formato_legado_corrompido(mixed $obj): bool
{
    if (!is_array($obj)) {
        return false;
    }

    return array_key_exists('idea', $obj)
        && !array_key_exists('beats', $obj)
        && empty($obj['story_summary'])
        && empty($obj['cast']);
}

function _limpar_lixo_legado(array $obj): array
{
    return array_diff_key($obj, array_flip(['idea', 'scenes']));
}

function _normalizar(mixed $obj): mixed
{
    if (!is_array($obj)) {
        return $obj;
    }

    if (_formato_legado_corrompido($obj)) {
        throw new RuntimeException(
            'JSON corrompido (formato legado sem beats/story_summary). '
            . 'A resposta da API foi descartada pela normalização antiga ou veio incompleta.'
        );
    }

    if (array_key_exists('beats', $obj)) {
        return $obj;
    }

    if (array_key_exists('cast', $obj) && !array_key_exists('beats', $obj)) {
        $tem_cenas_soltas = false;
        foreach (array_keys($obj) as $chave) {
            if (str_starts_with((string) $chave, 'SCENE')) {
                $tem_cenas_soltas = true;
                break;
            }
        }

        $cenas = $obj['scenes'] ?? [];
        if (!$tem_cenas_soltas && $cenas === []) {
            return _limpar_lixo_legado($obj);
        }
    }

    if (!empty($obj['SCENE_NUMBER']) && !array_key_exists('scenes', $obj)) {
        return $obj;
    }

    $scenes = $obj['scenes'] ?? [];
    if (!is_array($scenes)) {
        $scenes = [];
    }

    foreach ($obj as $chave => $valor) {
        if (str_starts_with((string) $chave, 'SCENE') && !array_key_exists($chave, $scenes)) {
            $scenes[$chave] = $valor;
        }
    }

    if ($scenes !== []) {
        $resultado = $obj;
        $resultado['scenes'] = $scenes;

        return $resultado;
    }

    return $obj;
}

/** Junta vários JSONs de cenas em um roteiro. */
function _juntar_objetos(array $objetos): array
{
    $resultado = ['title' => '', 'story_summary' => '', 'scenes' => []];

    foreach ($objetos as $obj) {
        if (!is_array($obj)) {
            continue;
        }

        if (!empty($obj['SCENE_NUMBER']) && !array_key_exists('scenes', $obj)) {
            $num = $obj['SCENE_NUMBER'];
            $resultado['scenes']["SCENE_{$num}"] = $obj;
            continue;
        }

        if (!empty($obj['title'])) {
            $resultado['title'] = $obj['title'];
        }
        if (!empty($obj['story_summary'])) {
            $resultado['story_summary'] = $obj['story_summary'];
        }
        if (!empty($obj['scenes']) && is_array($obj['scenes'])) {
            $resultado['scenes'] = array_merge($resultado['scenes'], $obj['scenes']);
        } else {
            foreach ($obj as $chave => $valor) {
                if (str_starts_with((string) $chave, 'SCENE')) {
                    $resultado['scenes'][$chave] = $valor;
                }
            }
        }
    }

    if ($resultado['scenes'] === []) {
        throw new RuntimeException('JSON encontrado, mas sem cenas.');
    }

    return $resultado;
}