<?php
declare(strict_types=1);

require_once __DIR__ . '/schema.php';

const PALAVRAS_POR_SEGUNDO = [
    'pt' => 3.2,
    'en' => 2.8,
    'es' => 3.0,
    'de' => 2.7,
];

const MIN_FALAS_POR_CENA = 4;
const MAX_FALAS_POR_CENA = 6;
const MIN_SEGUNDOS_FALA = 7.5;
const MAX_SEGUNDOS_FALA = 9.5;
const PAUSA_PADRAO = 0.2;

const PALAVRAS_PT = [
    'que', 'nao', 'não', 'voce', 'você', 'é', 'de', 'um', 'uma', 'para', 'com',
    'por', 'mais', 'como', 'mas', 'seu', 'sua', 'ele', 'ela', 'isso', 'aqui',
    'olha', 'amor', 'muito', 'bem', 'ainda', 'também', 'ja', 'já', 'so', 'só',
    'quem', 'onde', 'quando', 'porque', 'entao', 'então', 'agora', 'nunca',
    'sempre', 'tudo', 'nada', 'algo', 'quero', 'preciso', 'sabe', 'escuta',
    'espera', 'meu', 'minha', 'nos', 'nós', 'eles', 'elas', 'essa', 'esse',
    'aquilo', 'sera', 'será', 'esta', 'está', 'foi', 'sao', 'são', 'tem',
    'tinha', 'fazer', 'dizer', 'ver', 'saber', 'dar', 'ir', 'vir', 'fica',
    'calma', 'cara', 'gente', 'tipo', 'ne', 'né', 'pra', 'pro', 'ta', 'tá',
    'voce', 'chegou', 'casar', 'traição', 'mentira', 'desculpa', 'pare',
];

const PALAVRAS_EN = [
    'the', 'you', 'are', 'is', 'what', 'who', 'how', 'why', 'when', 'where',
    'this', 'that', 'with', 'from', 'have', 'been', 'will', 'your', 'they',
    'them', 'there', 'here', 'look', 'wait', 'love', 'never', 'always',
    'everything', 'nothing', "don't", "can't", "won't", "i'm", "you're",
    "it's", "that's", 'wow', 'oh', 'hey', 'yes', 'no', 'good', 'morning',
    'hello', 'today', 'going', 'about', 'right', 'know', 'think',
];

const PALAVRAS_ES = [
    'que', 'no', 'si', 'sí', 'tu', 'tú', 'usted', 'yo', 'el', 'él', 'ella',
    'eso', 'esto', 'aqui', 'aquí', 'ahora', 'nunca', 'siempre', 'todo', 'nada',
    'como', 'cómo', 'cuando', 'cuándo', 'donde', 'dónde', 'porque', 'por',
    'para', 'con', 'pero', 'mas', 'más', 'mira', 'escucha', 'espera', 'amor',
    'verdad', 'mentira', 'secreto', 'traicion', 'traición', 'perdon', 'perdón',
];

const PALAVRAS_DE = [
    'der', 'die', 'das', 'du', 'ich', 'wir', 'ihr', 'sie', 'er', 'ist', 'bist',
    'sind', 'nicht', 'kein', 'keine', 'was', 'wer', 'wie', 'warum', 'wann',
    'wo', 'hier', 'jetzt', 'nie', 'immer', 'alles', 'nichts', 'mit', 'ohne',
    'aber', 'und', 'oder', 'mein', 'meine', 'dein', 'deine', 'schau', 'warte',
    'hör', 'hoer', 'liebe', 'wahrheit', 'lüge', 'luege', 'geheimnis', 'verrat',
    'entschuldigung', 'wirklich', 'doch', 'noch', 'schon', 'wenn', 'dann',
];

const LOCK_IDIOMA = [
    'pt' => 'Language: Portuguese (Brazil)',
    'en' => 'Language: English',
    'es' => 'Language: Spanish',
    'de' => 'Language: German',
];

const _REFORCOS_NARRATIVOS = [
    'pt' => [
        'Isso muda tudo, e voce sabe.',
        'Agora a verdade apareceu de vez.',
        'Se isso sair daqui, acabou.',
    ],
    'en' => [
        'This changes everything, and you know it.',
        'Now the truth is finally out.',
        'If this gets out, we are done.',
    ],
    'es' => [
        'Esto lo cambia todo, y lo sabes.',
        'Ahora la verdad salio de una vez.',
        'Si esto sale de aqui, se acabo.',
    ],
    'de' => [
        'Das ändert alles, und du weißt es.',
        'Jetzt ist die Wahrheit endlich raus.',
        'Wenn das rauskommt, ist alles vorbei.',
    ],
];

const _EXTENSOES = [
    'pt' => ' demais!',
    'en' => ' too much!',
    'es' => ' demasiado!',
    'de' => ' wirklich!',
];

function normalizar_idioma(string $idioma): string
{
    $idioma = strtolower(trim($idioma));
    if (preg_match('/portugu|pt-br|pt_br|brasileiro/', $idioma)) {
        return 'pt';
    }
    if (preg_match('/english|inglês|ingles|inglés/', $idioma)) {
        return 'en';
    }
    if (preg_match('/espan|español|espanol/', $idioma)) {
        return 'es';
    }
    if (preg_match('/alem|deutsch|german|deu/', $idioma)) {
        return 'de';
    }
    if (in_array($idioma, ['pt', 'br'], true)) {
        return 'pt';
    }
    if ($idioma === 'en') {
        return 'en';
    }
    if ($idioma === 'es') {
        return 'es';
    }
    if ($idioma === 'de') {
        return 'de';
    }
    return 'pt';
}

function lock_idioma_texto(string $idioma): string
{
    $codigo = normalizar_idioma($idioma);
    return LOCK_IDIOMA[$codigo] ?? "Language: {$idioma}";
}

function extrair_textos(array $dialogue_lines): array
{
    $textos = [];
    foreach ($dialogue_lines as $linha) {
        if (is_array($linha) && array_key_exists('TEXT', $linha)) {
            $textos[] = $linha['TEXT'];
        }
    }
    return $textos;
}

function contar_falas(array $dialogue_lines): int
{
    return count(extrair_textos($dialogue_lines));
}

function detectar_idioma_texto(string $texto): string
{
    if (!preg_match_all('/\b[\w\']+\b/u', strtolower($texto), $matches)) {
        return 'desconhecido';
    }
    $palavras = $matches[0];
    if ($palavras === []) {
        return 'desconhecido';
    }

    $pt = count(array_filter($palavras, fn(string $p): bool => in_array($p, PALAVRAS_PT, true)));
    $en = count(array_filter($palavras, fn(string $p): bool => in_array($p, PALAVRAS_EN, true)));
    $es = count(array_filter($palavras, fn(string $p): bool => in_array($p, PALAVRAS_ES, true)));
    $de = count(array_filter($palavras, fn(string $p): bool => in_array($p, PALAVRAS_DE, true)));

    $contagens = ['pt' => $pt, 'en' => $en, 'es' => $es, 'de' => $de];
    arsort($contagens);
    $idioma = array_key_first($contagens);
    $pontos = $contagens[$idioma];

    if ($pontos > 0 && count(array_keys($contagens, $pontos, true)) === 1) {
        return $idioma;
    }
    if ($en >= 2 && $pt === 0 && $es === 0 && $de === 0) {
        return 'en';
    }
    if ($de >= 2 && $pt === 0 && $en === 0 && $es === 0) {
        return 'de';
    }
    return 'desconhecido';
}

function texto_no_idioma(string $texto, string $idioma_esperado): bool
{
    $idioma = normalizar_idioma($idioma_esperado);
    $detectado = detectar_idioma_texto($texto);

    if ($detectado === 'desconhecido') {
        if ($idioma === 'pt' && preg_match(
            '/\b(the|you|what|why|hello|good morning|i\'m|you\'re|don\'t|warum|nicht|wahrheit)\b/i',
            $texto
        )) {
            return false;
        }
        if ($idioma === 'de' && preg_match(
            '/\b(the|you|what|why|hello|good morning|voce|você|nao|não|verdad|mentira)\b/i',
            $texto
        )) {
            return false;
        }
        return true;
    }

    return $detectado === $idioma;
}

function voice_lock_valido(string $lock, string $idioma): bool
{
    $codigo = normalizar_idioma($idioma);
    $padroes = [
        'pt' => 'portugu',
        'en' => 'english',
        'es' => 'espan',
        'de' => 'german|deutsch',
    ];
    $padrao = $padroes[$codigo] ?? '';
    if ($padrao === '') {
        return false;
    }
    return (bool) preg_match('/' . $padrao . '/i', $lock);
}

function calcular_timing(array $dialogue_lines, string $idioma, int $duracao_cena = DURACAO_CENA): array
{
    $codigo = normalizar_idioma($idioma);
    $wps = PALAVRAS_POR_SEGUNDO[$codigo] ?? 3.2;

    $textos = extrair_textos($dialogue_lines);
    $total_palavras = array_sum(array_map(
        fn(string $t): int => count(preg_split('/\s+/u', trim($t), -1, PREG_SPLIT_NO_EMPTY)),
        $textos
    ));
    $total_pausas = 0.0;
    foreach ($dialogue_lines as $linha) {
        if (array_key_exists('PAUSE', $linha)) {
            $total_pausas += (float) $linha['PAUSE'];
        }
    }
    $num_falas = count($textos);

    $fala_seg = $total_palavras > 0 ? $total_palavras / $wps : 0.0;
    $total_seg = $fala_seg + $total_pausas;

    $min_palavras = (int) (MIN_SEGUNDOS_FALA * $wps);
    $max_palavras = (int) (MAX_SEGUNDOS_FALA * $wps);

    return [
        'source' => 'DIALOGUE_LINES > TEXT',
        'word_count' => $total_palavras,
        'line_count' => $num_falas,
        'words_per_second' => $wps,
        'estimated_speech_seconds' => round($fala_seg, 1),
        'pause_seconds' => round($total_pausas, 1),
        'total_dialogue_seconds' => round($total_seg, 1),
        'fits_in_scene' => $total_seg <= $duracao_cena,
        'min_words_recommended' => $min_palavras,
        'max_words_recommended' => $max_palavras,
        'min_lines_recommended' => MIN_FALAS_POR_CENA,
        'has_enough_dialogue' => (
            $num_falas >= MIN_FALAS_POR_CENA
            && $total_palavras >= $min_palavras
            && MIN_SEGUNDOS_FALA <= $total_seg && $total_seg <= $duracao_cena
        ),
        'fills_scene' => MIN_SEGUNDOS_FALA <= $total_seg && $total_seg <= MAX_SEGUNDOS_FALA,
    ];
}

function _segundos_das_falas(array $falas, float $wps): float
{
    $palavras = 0;
    foreach ($falas as $fala) {
        $palavras += count(preg_split('/\s+/u', trim($fala['TEXT']), -1, PREG_SPLIT_NO_EMPTY));
    }
    $pausas = max(0, count($falas) - 1) * PAUSA_PADRAO;
    return $palavras / $wps + $pausas;
}

function _montar_linhas_com_pausas(array $falas): array
{
    $linhas = [];
    foreach ($falas as $indice => $fala) {
        $linhas[] = $fala;
        if ($indice < count($falas) - 1) {
            $linhas[] = ['PAUSE' => PAUSA_PADRAO];
        }
    }
    return $linhas;
}

function ajustar_timing_cena(array $cena, string $idioma): array
{
    $falas = [];
    foreach ($cena['DIALOGUE_LINES'] ?? [] as $linha) {
        if (is_array($linha) && array_key_exists('TEXT', $linha)) {
            $falas[] = $linha;
        }
    }
    if ($falas === []) {
        return $cena;
    }

    $codigo = normalizar_idioma($idioma);
    $wps = PALAVRAS_POR_SEGUNDO[$codigo] ?? 3.2;
    $lock = lock_idioma_texto($idioma);
    $reforcos = _REFORCOS_NARRATIVOS[$codigo] ?? _REFORCOS_NARRATIVOS['pt'];

    foreach ($falas as &$fala) {
        $speaker = $fala['SPEAKER'] ?? 'SPEAKER';
        if (!voice_lock_valido($fala['VOICE_IDENTITY_LOCK'] ?? '', $idioma)) {
            $fala['VOICE_IDENTITY_LOCK'] = "{$speaker} voice. {$lock}.";
        }
    }
    unset($fala);

    $segundos = fn(): float => _segundos_das_falas($falas, $wps);

    $indices_editaveis = function () use ($falas): array {
        if (count($falas) <= 2) {
            return array_keys($falas);
        }
        return range(1, count($falas) - 2);
    };

    $tentativas = 0;
    while ($segundos() > MAX_SEGUNDOS_FALA && $tentativas < 20) {
        $tentativas++;
        $candidatos = $indices_editaveis();
        if ($candidatos === []) {
            break;
        }
        $indice = $candidatos[0];
        $maxPalavras = -1;
        foreach ($candidatos as $i) {
            $count = count(preg_split('/\s+/u', trim($falas[$i]['TEXT']), -1, PREG_SPLIT_NO_EMPTY));
            if ($count > $maxPalavras) {
                $maxPalavras = $count;
                $indice = $i;
            }
        }
        $palavras = preg_split('/\s+/u', trim($falas[$indice]['TEXT']), -1, PREG_SPLIT_NO_EMPTY);
        if (count($palavras) > 2) {
            array_pop($palavras);
            $falas[$indice]['TEXT'] = implode(' ', $palavras);
        } elseif (count($falas) > MIN_FALAS_POR_CENA) {
            array_splice($falas, $indice, 1);
        } else {
            $falas[$indice]['TEXT'] = implode(' ', array_slice($palavras, 0, 2));
            break;
        }
    }

    $indice_reforco = 0;
    while ($segundos() < MIN_SEGUNDOS_FALA && count($falas) < MAX_FALAS_POR_CENA) {
        $speaker = $falas[count($falas) - 1]['SPEAKER'] ?? 'PERSONAGEM';
        $falas[] = [
            'SPEAKER' => $speaker,
            'VOICE_IDENTITY_LOCK' => "{$speaker} voice. {$lock}.",
            'TEXT' => $reforcos[$indice_reforco % count($reforcos)],
        ];
        $indice_reforco++;
    }

    $tentativas = 0;
    while ($segundos() < MIN_SEGUNDOS_FALA && $tentativas < 10) {
        $tentativas++;
        $candidatos = $indices_editaveis();
        if ($candidatos === []) {
            $candidatos = array_keys($falas);
        }
        $indice = $candidatos[0];
        $minPalavras = PHP_INT_MAX;
        foreach ($candidatos as $i) {
            $count = count(preg_split('/\s+/u', trim($falas[$i]['TEXT']), -1, PREG_SPLIT_NO_EMPTY));
            if ($count < $minPalavras) {
                $minPalavras = $count;
                $indice = $i;
            }
        }
        $extensao = _EXTENSOES[$codigo] ?? '!';
        $falas[$indice]['TEXT'] = rtrim($falas[$indice]['TEXT'], '!.?') . $extensao;
        if (count(preg_split('/\s+/u', trim($falas[$indice]['TEXT']), -1, PREG_SPLIT_NO_EMPTY)) > 12) {
            break;
        }
    }

    $cena['DIALOGUE_LINES'] = _montar_linhas_com_pausas($falas);
    return $cena;
}

function ajustar_timing_roteiro(array $roteiro, string $idioma): array
{
    foreach ($roteiro['scenes'] ?? [] as $chave => $cena) {
        $roteiro['scenes'][$chave] = ajustar_timing_cena($cena, $idioma);
    }
    return $roteiro;
}

function metas_timing_roteiro(array $roteiro, string $idioma): string
{
    $linhas = [];
    $cenas = $roteiro['scenes'] ?? [];
    uasort($cenas, fn(array $a, array $b): int => ($a['SCENE_NUMBER'] ?? 0) <=> ($b['SCENE_NUMBER'] ?? 0));

    foreach ($cenas as $chave => $cena) {
        $num = $cena['SCENE_NUMBER'] ?? $chave;
        $timing = calcular_timing($cena['DIALOGUE_LINES'] ?? [], $idioma);
        $linhas[] = sprintf(
            'Cena %s: %d falas, %d palavras, %ss → meta %d-%d palavras (%s-%ss)',
            $num,
            $timing['line_count'],
            $timing['word_count'],
            $timing['total_dialogue_seconds'],
            $timing['min_words_recommended'],
            $timing['max_words_recommended'],
            MIN_SEGUNDOS_FALA,
            MAX_SEGUNDOS_FALA
        );
    }
    return implode("\n", $linhas);
}

function extrair_falas_de_intent(string $dialogue_intent): array
{
    if ($dialogue_intent === '') {
        return [];
    }

    if (preg_match_all("/['\"]([^'\"]{3,})['\"]/u", $dialogue_intent, $matches)) {
        return array_values(array_filter(array_map('trim', $matches[1]), fn(string $f): bool => $f !== ''));
    }

    if (preg_match_all('/\d+\)\s*([^0-9]+?)(?=\s*\d+\)|$)/us', $dialogue_intent, $matches)) {
        $falas = [];
        foreach ($matches[1] as $f) {
            $f = trim($f);
            $f = trim($f, "'\"");
            if (strlen($f) >= 3) {
                $falas[] = $f;
            }
        }
        return $falas;
    }

    return [];
}

function dialogos_de_intent(string $dialogue_intent, array $speakers, string $idioma): array
{
    $falas = extrair_falas_de_intent($dialogue_intent);
    if ($falas === [] || $speakers === []) {
        return [];
    }

    $lock = lock_idioma_texto($idioma);
    $linhas = [];
    foreach ($falas as $indice => $texto) {
        $speaker = $speakers[$indice % count($speakers)];
        $linhas[] = [
            'SPEAKER' => $speaker,
            'VOICE_IDENTITY_LOCK' => "{$speaker} voice. {$lock}.",
            'TEXT' => $texto,
        ];
        if ($indice < count($falas) - 1) {
            $linhas[] = ['PAUSE' => PAUSA_PADRAO];
        }
    }
    return $linhas;
}

function cenas_com_problemas(array $problemas): array
{
    $numeros = [];
    foreach ($problemas as $problema) {
        if (preg_match('/Cena\s+(\d+)/i', (string) $problema, $match)) {
            $numeros[(int) $match[1]] = true;
        }
    }
    $resultado = array_keys($numeros);
    sort($resultado);
    return $resultado;
}

function analisar_dialogos_roteiro(array $roteiro, string $idioma): array
{
    $problemas = [];
    $cenas = $roteiro['scenes'] ?? [];
    uasort($cenas, fn(array $a, array $b): int => ($a['SCENE_NUMBER'] ?? 0) <=> ($b['SCENE_NUMBER'] ?? 0));

    foreach ($cenas as $chave => $cena) {
        $num = $cena['SCENE_NUMBER'] ?? $chave;
        $lines = $cena['DIALOGUE_LINES'] ?? [];
        $timing = calcular_timing($lines, $idioma);

        $timing_problema = null;
        if ($timing['line_count'] < MIN_FALAS_POR_CENA) {
            $timing_problema = sprintf(
                'só %d falas (mínimo %d)',
                $timing['line_count'],
                MIN_FALAS_POR_CENA
            );
        } elseif ($timing['total_dialogue_seconds'] > DURACAO_CENA) {
            $timing_problema = sprintf(
                '%ss estoura %ds',
                $timing['total_dialogue_seconds'],
                DURACAO_CENA
            );
        } elseif (!$timing['fills_scene']) {
            $timing_problema = sprintf(
                '%ss fora da meta %s-%ss',
                $timing['total_dialogue_seconds'],
                MIN_SEGUNDOS_FALA,
                MAX_SEGUNDOS_FALA
            );
        }

        if ($timing_problema !== null) {
            $problemas[] = "Cena {$num}: {$timing_problema}";
        }

        foreach ($lines as $linha) {
            if (!is_array($linha) || !array_key_exists('TEXT', $linha)) {
                continue;
            }
            $texto = $linha['TEXT'];
            $speaker = $linha['SPEAKER'] ?? '?';

            if (!texto_no_idioma($texto, $idioma)) {
                $problemas[] = sprintf(
                    "Cena %s (%s): idioma errado — '%s'",
                    $num,
                    $speaker,
                    mb_substr($texto, 0, 50)
                );
            }

            $lock = $linha['VOICE_IDENTITY_LOCK'] ?? '';
            if (!voice_lock_valido($lock, $idioma)) {
                $problemas[] = "Cena {$num} ({$speaker}): VOICE_IDENTITY_LOCK sem idioma correto";
            }
        }
    }

    return $problemas;
}