<?php
declare(strict_types=1);

/**
 * Passo dedicado: reescreve DIALOGUE_LINES com muitas falas,
 * idioma correto e timing que preenche os 10 segundos.
 */

require_once __DIR__ . '/api.php';
require_once __DIR__ . '/dialogo.php';
require_once __DIR__ . '/relatorio.php';
require_once __DIR__ . '/schema.php';
require_once __DIR__ . '/narrativa.php';
require_once __DIR__ . '/voz.php';

$CORRECAO_CENA_RESPONSE_FORMAT = [
    'name' => 'correcao_cena',
    'strict' => true,
    'schema' => $CORRECAO_SCENE,
];

function _exemplo_dialogo(string $idioma): string
{
    if (normalizar_idioma($idioma) === 'de') {
        return <<<'DIALOG_EXAMPLE_DE'

BEISPIEL (5 kurze Zeilen, ~9s, fuellt 10s Szene):
[
  {"SPEAKER": "ERDBEERE", "VOICE_IDENTITY_LOCK": "... Language: German.", "TEXT": "Orange?! Was machst du hier?!"},
  {"PAUSE": 0.2},
  {"SPEAKER": "ORANGE", "VOICE_IDENTITY_LOCK": "... Language: German.", "TEXT": "Beruhig dich... wir haben nur geredet."},
  {"PAUSE": 0.2},
  {"SPEAKER": "TRAUBE", "VOICE_IDENTITY_LOCK": "... Language: German.", "TEXT": "Geredet? Schau auf das Glas."},
  {"PAUSE": 0.2},
  {"SPEAKER": "ERDBEERE", "VOICE_IDENTITY_LOCK": "... Language: German.", "TEXT": "Mein bester Freund verrät mich?!"},
  {"PAUSE": 0.2},
  {"SPEAKER": "TRAUBE", "VOICE_IDENTITY_LOCK": "... Language: German.", "TEXT": "Wir heiraten. Gewöhn dich dran."}
]
DIALOG_EXAMPLE_DE;
    }

    if (normalizar_idioma($idioma) === 'en') {
        return <<<'DIALOG_EXAMPLE_EN'

EXEMPLO (4 speeches, ~9s, fills 10s scene):
[
  {"SPEAKER": "STRAWBERRY", "VOICE_IDENTITY_LOCK": "... Language: English.", "TEXT": "Orange?! What are you doing here?!"},
  {"PAUSE": 0.2},
  {"SPEAKER": "ORANGE", "VOICE_IDENTITY_LOCK": "... Language: English.", "TEXT": "Relax babe... we were just talking."},
  {"PAUSE": 0.2},
  {"SPEAKER": "GRAPE", "VOICE_IDENTITY_LOCK": "... Language: English.", "TEXT": "Talking? Look at my glass, banana."},
  {"PAUSE": 0.2},
  {"SPEAKER": "STRAWBERRY", "VOICE_IDENTITY_LOCK": "... Language: English.", "TEXT": "My best friend... betraying me?!"},
  {"PAUSE": 0.2},
  {"SPEAKER": "GRAPE", "VOICE_IDENTITY_LOCK": "... Language: English.", "TEXT": "We're getting married. Deal with it."}
]
DIALOG_EXAMPLE_EN;
    }

    return <<<'DIALOG_EXAMPLE_PT'

EXEMPLO (4 falas curtas alternadas, ~9s, preenche cena de 10s):
[
  {"SPEAKER": "MORANGO", "VOICE_IDENTITY_LOCK": "... Language: Portuguese (Brazil).", "TEXT": "Laranjito?! O que você tá fazendo aqui?!"},
  {"PAUSE": 0.2},
  {"SPEAKER": "LARANJA", "VOICE_IDENTITY_LOCK": "... Language: Portuguese (Brazil).", "TEXT": "Calma, amor... a gente só tava conversando."},
  {"PAUSE": 0.2},
  {"SPEAKER": "UVA", "VOICE_IDENTITY_LOCK": "... Language: Portuguese (Brazil).", "TEXT": "Conversando? Olha a taça, banana."},
  {"PAUSE": 0.2},
  {"SPEAKER": "MORANGO", "VOICE_IDENTITY_LOCK": "... Language: Portuguese (Brazil).", "TEXT": "Traição... do meu melhor amigo?!"},
  {"PAUSE": 0.2},
  {"SPEAKER": "UVA", "VOICE_IDENTITY_LOCK": "... Language: Portuguese (Brazil).", "TEXT": "A gente vai casar. Aceita ou descasca."}
]
DIALOG_EXAMPLE_PT;
}

function _extrair_dialogos(array $roteiro): array
{
    $cenas = [];
    foreach ($roteiro['scenes'] ?? [] as $chave => $cena) {
        $cenas[$chave] = [
            'SCENE_NUMBER' => $cena['SCENE_NUMBER'] ?? null,
            'NARRATIVE_BEAT' => $cena['NARRATIVE_BEAT'] ?? null,
            'DIALOGUE_LINES' => $cena['DIALOGUE_LINES'] ?? [],
            'DELIVERY_STYLE' => $cena['DELIVERY_STYLE'] ?? '',
            'VOICE_OVERRIDE_METADATA' => $cena['VOICE_OVERRIDE_METADATA'] ?? [],
        ];
    }

    return ['scenes' => $cenas];
}

function _extrair_sinopse_dialogos(array $sinopse): array
{
    $beats = [];
    foreach ($sinopse['beats'] ?? [] as $b) {
        $beats[] = [
            'scene_number' => $b['scene_number'] ?? null,
            'narrative_beat' => $b['narrative_beat'] ?? null,
            'dialogue_intent' => $b['dialogue_intent'] ?? null,
        ];
    }

    return [
        'story_summary' => $sinopse['story_summary'] ?? '',
        'beats' => $beats,
    ];
}

function _problemas_da_cena(array $problemas, int $numero): array
{
    $prefixo = "Cena {$numero}";
    return array_values(array_filter(
        $problemas,
        fn(string $p): bool => str_starts_with($p, $prefixo)
    ));
}

function _chamar_correcao_api(string $system, string $user, array $schema): array
{
    $ultimoErro = null;
    for ($tentativa = 1; $tentativa <= 3; $tentativa++) {
        try {
            $resposta = chamar_api($system, $user, $schema);
            return extrair_json($resposta);
        } catch (Throwable $erro) {
            $ultimoErro = $erro;
            if ($tentativa < 3) {
                echo "  !! Resposta inválida ({$erro->getMessage()}). Tentativa " . ($tentativa + 1) . "/3...\n";
            }
        }
    }

    throw new ValueError("Falha na correção após 3 tentativas: {$ultimoErro->getMessage()}");
}

function _encontrar_cena(array $cenas, int $numero): ?array
{
    foreach ($cenas as $c) {
        if (($c['SCENE_NUMBER'] ?? null) === $numero) {
            return $c;
        }
    }

    return $cenas["SCENE_{$numero}"] ?? null;
}

function corrigir_cena_dialogos(
    array $roteiro,
    array $sinopse,
    string $idioma,
    int $numero,
    ?array $problemas = null,
    ?array $elenco = null
): array {
    $codigo = normalizar_idioma($idioma);
    $wps = PALAVRAS_POR_SEGUNDO[$codigo] ?? 3.2;
    $minPalavras = (int) (MIN_SEGUNDOS_FALA * $wps);
    $maxPalavras = (int) (MAX_SEGUNDOS_FALA * $wps);
    $lock = lock_idioma_texto($idioma);

    $cenas = $roteiro['scenes'] ?? [];
    $cena = _encontrar_cena($cenas, $numero);
    if ($cena === null) {
        return $roteiro;
    }

    $beat = [];
    foreach ($sinopse['beats'] ?? [] as $b) {
        if (($b['scene_number'] ?? null) === $numero) {
            $beat = $b;
            break;
        }
    }

    $problemasTxt = '';
    if (!empty($problemas)) {
        $problemasTxt = "PROBLEMAS:\n" . implode("\n", array_map(fn(string $p): string => "- {$p}", $problemas));
    }

    $voiceTxt = $elenco !== null ? voice_registry_prompt($elenco, $idioma) : '';
    $storyTxt = story_contract_prompt($sinopse, $numero);
    $cenaJson = json_encode(
        _extrair_dialogos(['scenes' => ["SCENE_{$numero}" => $cena]]),
        JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT
    );

    $narrativeBeat = $cena['NARRATIVE_BEAT'] ?? '';
    $dialogueIntent = $beat['dialogue_intent'] ?? '';
    $exemplo = _exemplo_dialogo($idioma);

    $system = <<<PROMPT
Você reescreve DIALOGUE_LINES de UMA cena de PROMPT_DURACAOs.

IDIOMA: {$idioma} — TODO TEXT em {$idioma}. LOCK: "{$lock}".

LIMITES RÍGIDOS:
- PROMPT_MIN_FALAS-PROMPT_MAX_FALAS falas (4-12 palavras cada)
- {$minPalavras}-{$maxPalavras} palavras total (~PROMPT_MIN_SEG-PROMPT_MAX_SEGs)
- Pausa {"PAUSE": PROMPT_PAUSA} entre falas
- NUNCA ultrapasse PROMPT_MAX_SEGs nem fique abaixo de PROMPT_MIN_SEGs

NARRATIVE_BEAT: {$narrativeBeat}
dialogue_intent: {$dialogueIntent}

{$voiceTxt}

{$storyTxt}

REGRAS DE CONTINUIDADE:
- Use somente SPEAKER existentes no VOICE REGISTRY.
- Copie o VOICE_IDENTITY_LOCK canonico quando houver VOICE REGISTRY.
- Preserve required_reveal e must_end_handing_off_to do STORY CONTRACT.
- Nao adicione reacoes genericas que nao avancem o enredo.

{$exemplo}
PROMPT;

    $system = str_replace(
        ['PROMPT_DURACAO', 'PROMPT_MIN_FALAS', 'PROMPT_MAX_FALAS', 'PROMPT_MIN_SEG', 'PROMPT_MAX_SEG', 'PROMPT_PAUSA'],
        [DURACAO_CENA, MIN_FALAS_POR_CENA, MAX_FALAS_POR_CENA, MIN_SEGUNDOS_FALA, MAX_SEGUNDOS_FALA, PAUSA_PADRAO],
        $system
    );

    $user = <<<PROMPT
{$problemasTxt}

Cena {$numero}:
{$cenaJson}

Reescreva só os diálogos desta cena em {$idioma}.
PROMPT;

    global $CORRECAO_CENA_RESPONSE_FORMAT;
    $correcao = _chamar_correcao_api($system, $user, $CORRECAO_CENA_RESPONSE_FORMAT);

    return _aplicar_correcao($roteiro, ['scenes' => ["SCENE_{$numero}" => $correcao]]);
}

function corrigir_dialogos(
    array $roteiro,
    array $sinopse,
    string $idioma,
    ?array $problemas = null,
    ?array $elenco = null
): array {
    $codigo = normalizar_idioma($idioma);
    $wps = PALAVRAS_POR_SEGUNDO[$codigo] ?? 3.2;
    $minPalavras = (int) (MIN_SEGUNDOS_FALA * $wps);
    $maxPalavras = (int) (MAX_SEGUNDOS_FALA * $wps);
    $lock = lock_idioma_texto($idioma);

    $problemasTxt = '';
    if (!empty($problemas)) {
        $problemasTxt = "PROBLEMAS A CORRIGIR:\n" . implode("\n", array_map(fn(string $p): string => "- {$p}", $problemas));
    }

    $roteiroJson = json_encode(_extrair_dialogos($roteiro), JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    $sinopseJson = json_encode(_extrair_sinopse_dialogos($sinopse), JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    $voiceTxt = $elenco !== null ? voice_registry_prompt($elenco, $idioma) : '';
    $storyTxt = story_contract_prompt($sinopse);
    $exemplo = _exemplo_dialogo($idioma);

    $system = <<<PROMPT
Você é um roteirista especialista em diálogos para vídeos virais de 10 segundos.

Sua ÚNICA tarefa: reescrever DIALOGUE_LINES de TODAS as cenas.

IDIOMA INQUEBRÁVEL: {$idioma}
- TODO TEXT em {$idioma}. ZERO palavras em outro idioma.
- VOICE_IDENTITY_LOCK com "{$lock}" em TODAS as falas.

DENSIDADE OBRIGATÓRIA (cada cena = PROMPT_DURACAOs):
- Mínimo PROMPT_MIN_FALAS falas com TEXT por cena (ideal PROMPT_MAX_FALAS)
- Total: {$minPalavras}-{$maxPalavras} palavras por cena (~PROMPT_MIN_SEG-PROMPT_MAX_SEGs de fala)
- Pausa fixa {"PAUSE": PROMPT_PAUSA} entre cada fala
- Falas CURTAS (4-12 palavras cada) — ritmo rápido estilo TikTok
- NÃO faça monólogos longos numa só fala — divida em várias trocas
- O áudio SOZINHO deve contar a história da cena

NARRATIVA:
- Use NARRATIVE_BEAT de cada cena e dialogue_intent da sinopse
- Cada fala avança o enredo — reação, revelação ou tensão
- Alterne personagens quando houver mais de um na cena
- Preserve o STORY CONTRACT: cada cena precisa pagar a anterior e plantar a proxima
- Use somente SPEAKER do VOICE REGISTRY quando ele existir

Retorne SCENE_NUMBER, DIALOGUE_LINES, DELIVERY_STYLE, VOICE_OVERRIDE_METADATA por cena.

{$voiceTxt}

{$storyTxt}

{$exemplo}
PROMPT;

    $system = str_replace(
        ['PROMPT_DURACAO', 'PROMPT_MIN_FALAS', 'PROMPT_MAX_FALAS', 'PROMPT_MIN_SEG', 'PROMPT_MAX_SEG', 'PROMPT_PAUSA'],
        [DURACAO_CENA, MIN_FALAS_POR_CENA, MAX_FALAS_POR_CENA, MIN_SEGUNDOS_FALA, MAX_SEGUNDOS_FALA, PAUSA_PADRAO],
        $system
    );

    $metas = metas_timing_roteiro($roteiro, $idioma);

    $user = <<<PROMPT
{$problemasTxt}

METAS DE TIMING POR CENA (obrigatório respeitar):
{$metas}

SINOPSE:
{$sinopseJson}

ROTEIRO ATUAL (reescreva só os diálogos):
{$roteiroJson}

Reescreva DIALOGUE_LINES das 7 cenas em {$idioma}.
Muitas falas curtas (4-12 palavras). Preencha PROMPT_MIN_SEG-PROMPT_MAX_SEGs de áudio por cena.
NUNCA ultrapasse PROMPT_MAX_SEGs nem fique abaixo de PROMPT_MIN_SEGs.
PROMPT;

    $user = str_replace(
        ['PROMPT_MIN_SEG', 'PROMPT_MAX_SEG'],
        [MIN_SEGUNDOS_FALA, MAX_SEGUNDOS_FALA],
        $user
    );

    $numeros = cenas_com_problemas($problemas ?? []);
    if (!empty($numeros)) {
        echo '  [4/4] Corrigindo diálogos (' . count($numeros) . " cena(s))...\n";
        foreach ($numeros as $numero) {
            echo "       Cena {$numero}...\n";
            $problemasCena = _problemas_da_cena($problemas ?? [], $numero);
            $roteiro = corrigir_cena_dialogos($roteiro, $sinopse, $idioma, $numero, $problemasCena, $elenco);
        }
        return $roteiro;
    }

    echo "  [4/4] Corrigindo e expandindo diálogos (lote)...\n";
    global $CORRECAO_DIALOGOS_RESPONSE_FORMAT;
    $correcao = _chamar_correcao_api($system, $user, $CORRECAO_DIALOGOS_RESPONSE_FORMAT);

    return _aplicar_correcao($roteiro, $correcao);
}

function _aplicar_correcao(array $roteiro, array $correcao): array
{
    $cenasCorr = $correcao['scenes'] ?? [];
    $cenas = $roteiro['scenes'] ?? [];

    foreach ($cenasCorr as $chave => $dados) {
        $alvoChave = null;
        if (isset($cenas[$chave])) {
            $alvoChave = $chave;
        } else {
            $num = $dados['SCENE_NUMBER'] ?? null;
            foreach ($cenas as $k => $v) {
                if (($v['SCENE_NUMBER'] ?? null) === $num) {
                    $alvoChave = $k;
                    break;
                }
            }
        }
        if ($alvoChave === null) {
            continue;
        }

        $cenas[$alvoChave]['DIALOGUE_LINES'] = $dados['DIALOGUE_LINES'];
        $cenas[$alvoChave]['DELIVERY_STYLE'] = $dados['DELIVERY_STYLE']
            ?? ($cenas[$alvoChave]['DELIVERY_STYLE'] ?? '');
        $cenas[$alvoChave]['VOICE_OVERRIDE_METADATA'] = $dados['VOICE_OVERRIDE_METADATA']
            ?? ($cenas[$alvoChave]['VOICE_OVERRIDE_METADATA'] ?? []);
    }

    $roteiro['scenes'] = $cenas;

    return $roteiro;
}

function _ajuste_local_por_cena(array $roteiro, string $idioma, array $problemas): array
{
    $numeros = cenas_com_problemas($problemas);
    $cenas = $roteiro['scenes'] ?? [];
    foreach ($numeros as $numero) {
        foreach ($cenas as $chave => $cena) {
            if (($cena['SCENE_NUMBER'] ?? null) === $numero || $chave === "SCENE_{$numero}") {
                $cenas[$chave] = ajustar_timing_cena($cena, $idioma);
                break;
            }
        }
    }

    $roteiro['scenes'] = $cenas;

    return $roteiro;
}

function corrigir_ate_validar(
    array $roteiro,
    array $sinopse,
    string $idioma,
    callable $enriquecerFn,
    int $maxTentativas = 3,
    ?array $elenco = null
): array {
    for ($tentativa = 1; $tentativa <= $maxTentativas; $tentativa++) {
        $problemas = analisar_dialogos_roteiro($roteiro, $idioma);
        if (empty($problemas)) {
            echo "  -> Diálogos OK.\n\n";
            return $roteiro;
        }

        imprimir_problemas(
            "Diálogos com problemas — correção {$tentativa}/{$maxTentativas}",
            $problemas
        );

        $roteiro = _ajuste_local_por_cena($roteiro, $idioma, $problemas);
        $roteiro = $enriquecerFn($roteiro);

        $problemas = analisar_dialogos_roteiro($roteiro, $idioma);
        if (empty($problemas)) {
            echo "  -> Diálogos OK (ajuste local).\n\n";
            return $roteiro;
        }

        $roteiro = corrigir_dialogos($roteiro, $sinopse, $idioma, $problemas, $elenco);
        $roteiro = $enriquecerFn($roteiro);
    }

    $problemas = analisar_dialogos_roteiro($roteiro, $idioma);
    if (!empty($problemas)) {
        echo "  -> Ajuste local final de timing...\n";
        $roteiro = $enriquecerFn(ajustar_timing_roteiro($roteiro, $idioma));
    }

    $restantes = analisar_dialogos_roteiro($roteiro, $idioma);
    if (!empty($restantes)) {
        imprimir_problemas('Alguns diálogos ainda fora da meta', $restantes);
    } else {
        echo "  -> Diálogos OK.\n\n";
    }

    return $roteiro;
}