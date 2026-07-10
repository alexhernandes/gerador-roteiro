<?php
declare(strict_types=1);

/**
 * Valida elenco e roteiro contra as regras do prompt.txt.
 * Gera relatório com explicações e exemplos.
 */

require_once __DIR__ . '/dialogo.php';
require_once __DIR__ . '/narrativa.php';
require_once __DIR__ . '/regras.php';
require_once __DIR__ . '/schema.php';
require_once __DIR__ . '/voz.php';

const PALAVRAS_SANGUE = '/\b(blood|sangue|bleeding|hemorrag)\b/i';
const PALAVRAS_AGRESSAO = '/\b(punch|stab|shoot|kill|murder|matar|soc[oou]|esfaquear|esfaque|agredir|agressão|agressao)\b/i';
const PALAVRAS_CLIFFHANGER = '/\b(wait|espera|part 2|parte 2|to be continued|continua|who is|quem é|what is|o que|'
    . 'did you hear|ouviu|you won.t believe|não vai acreditar|no way|impossible|'
    . 'impossível|plot twist|reviravolta)\b/i';
const PALAVRAS_VISUAL = '/\b(4k|cinematic|volumetric|pbr|disney|pixar)\b/i';
const PALAVRAS_LIPSYNC = '/\b(sequential dialogue|mouth closed|lip.?sync|non.?overlapping|speaker|boca fechada)\b/i';
const PALAVRAS_TRAMA = '/\b(twist|reviravolta|traição|traicao|betrayal|shock|reveal|revelação|revelacao|'
    . 'conflito|conflict|crise|crisis|escalat|tensão|tensao|segredo|secret|mentira|lie|'
    . 'plot|gancho|hook|cliffhanger|virada)\b/i';
const PALAVRAS_HOOK = '/\b(hook|gancho|grita|explod|impact|choc|revel|confront|entra|começa|comeca|'
    . 'olha|escuta|pera|espera|não|nao|what|quem|como|por que|why|soco|corre)\b/i';
const PALAVRAS_CAMERA = '/\b(wide|close.?up|medium|dolly|pan|tilt|zoom|tracking|handheld|shot|angle|'
    . 'rack focus|bokeh|over-the-shoulder|two-shot|pov|pull back|push in|crane|'
    . '0-\d+s|\d-\d+s)\b/i';
const PALAVRAS_FILLER = '/^(oi|olá|ola|hey|hi|tudo bem|e aí|e ai|bom dia|good morning|ok|okay|sim|não|nao)\s*[!.?]*$/i';

const ROLES_TRAMA = ['hook', 'setup', 'conflict', 'twist', 'escalation', 'crisis', 'cliffhanger'];

function _resultado(array $regra, bool $ok, $detalhe = ''): array
{
    if (is_array($detalhe) && isset($detalhe[0])) {
        $detalhe = $detalhe[0];
    } else {
        $detalhe = $detalhe !== null ? (string) $detalhe : '';
    }

    return [
        'id' => $regra['id'],
        'nome' => $regra['nome'],
        'severidade' => $regra['severidade'],
        'ok' => (bool) $ok,
        'detalhe' => $detalhe,
        'explicacao' => $regra['explicacao'],
        'exemplo' => $regra['exemplo'],
    ];
}

function _buscar_regra(string $regraId): array
{
    foreach (REGRAS as $regra) {
        if ($regra['id'] === $regraId) {
            return $regra;
        }
    }

    throw new RuntimeException("Regra não encontrada: {$regraId}");
}

function validar_elenco(array $elenco): array
{
    $resultados = [];
    $cast = $elenco['cast'] ?? [];

    $regra = _buscar_regra('antropomorfico');
    if (empty($cast)) {
        $resultados[] = _resultado($regra, false, 'Elenco vazio.');
        return $resultados;
    }

    foreach ($cast as $personagem) {
        $nome = $personagem['name'] ?? '?';
        $fisico = $personagem['physical_dna'] ?? '';

        if (strlen($fisico) < 30) {
            $resultados[] = _resultado($regra, false, "{$nome}: physical_dna muito curto.");
        } else {
            $resultados[] = _resultado($regra, true, "{$nome}: DNA físico OK.");
        }

        $regraOutfit = _buscar_regra('outfit_dna');
        $roupa = $personagem['outfit_dna'] ?? '';
        if (strlen($roupa) < 30) {
            $resultados[] = _resultado($regraOutfit, false, "{$nome}: outfit_dna incompleto.");
        } else {
            $resultados[] = _resultado($regraOutfit, true, "{$nome}: roupa descrita.");
        }
    }

    $regraIa = _buscar_regra('instrucoes_ia');
    if (!empty($elenco['ai_instructions']['task'])) {
        $resultados[] = _resultado($regraIa, true, 'ai_instructions presente.');
    } else {
        $resultados[] = _resultado($regraIa, false, 'Falta ai_instructions.');
    }

    foreach ($cast as $personagem) {
        $nome = $personagem['name'] ?? '?';
        $ok = !empty($personagem['ai_image_task']);
        $resultados[] = _resultado(
            $regraIa,
            $ok,
            "{$nome}: ai_image_task " . ($ok ? 'OK' : 'ausente') . '.'
        );
    }

    $regraVoice = _buscar_regra('voice_registry');
    $registry = $elenco['voice_registry'] ?? [];
    $vozes = is_array($registry) ? ($registry['voices'] ?? []) : [];
    if (count($vozes) === count($cast) && !empty($vozes)) {
        $resultados[] = _resultado($regraVoice, true, count($vozes) . ' voz(es) canonica(s) no registry.');
    } else {
        $resultados[] = _resultado(
            $regraVoice,
            false,
            'voice_registry incompleto (' . count($vozes) . '/' . count($cast) . ' personagens).'
        );
    }

    $regraRes = _buscar_regra('resolucao_480p');
    $ok = ($elenco['resolution'] ?? null) === RESOLUCAO;
    $resultados[] = _resultado(
        $regraRes,
        $ok,
        $ok ? 'Resolução ' . RESOLUCAO . '.' : 'Esperado ' . RESOLUCAO . ', veio ' . ($elenco['resolution'] ?? 'null') . '.'
    );

    return $resultados;
}

function validar_sinopse(array $sinopse): array
{
    $resultados = [];
    $regra = _buscar_regra('narrativa_coesa');

    if (empty($sinopse)) {
        return $resultados;
    }

    $summary = $sinopse['story_summary'] ?? '';
    if (strlen($summary) < 50) {
        $resultados[] = _resultado($regra, false, 'story_summary muito curto ou ausente.');
    } else {
        $resultados[] = _resultado($regra, true, 'Sinopse: ' . substr($summary, 0, 80) . '...');
    }

    foreach (['act_1', 'act_2', 'act_3'] as $campo) {
        $texto = trim($sinopse[$campo] ?? '');
        if (strlen($texto) < 30) {
            $resultados[] = _resultado(
                $regra,
                false,
                "Sinopse: {$campo} incompleto (" . strlen($texto) . ' chars, mínimo 30).'
            );
        } else {
            $resultados[] = _resultado($regra, true, "Sinopse: {$campo} OK.");
        }
    }

    $beats = $sinopse['beats'] ?? [];
    if (count($beats) !== NUM_CENAS) {
        $resultados[] = _resultado(
            $regra,
            false,
            'Sinopse: ' . count($beats) . ' beats (esperado ' . NUM_CENAS . ').'
        );
    }

    foreach ($beats as $beat) {
        $num = $beat['scene_number'] ?? '?';
        if (strlen($beat['narrative_beat'] ?? '') < 15) {
            $resultados[] = _resultado($regra, false, "Beat {$num}: narrative_beat vazio.");
        }
        if (strlen($beat['dialogue_intent'] ?? '') < 15) {
            $resultados[] = _resultado(
                _buscar_regra('dialogo_narrativo'),
                false,
                "Beat {$num}: dialogue_intent vazio."
            );
        }
    }

    return $resultados;
}

function validar_roteiro(array $roteiro, array $elenco, ?array $sinopse = null): array
{
    $resultados = [];
    $cenas = $roteiro['scenes'] ?? [];
    $cast = $elenco['cast'] ?? [];
    $idioma = $roteiro['language'] ?? ($elenco['language'] ?? 'Português');

    if (empty($cenas)) {
        $resultados[] = [
            'id' => 'cenas',
            'nome' => 'Cenas',
            'severidade' => 'erro',
            'ok' => false,
            'detalhe' => 'Nenhuma cena encontrada.',
            'explicacao' => 'O roteiro precisa ter ' . NUM_CENAS . ' cenas.',
            'exemplo' => 'SCENE_1 até SCENE_7',
        ];
        return $resultados;
    }

    $regraSete = _buscar_regra('sete_cenas');
    $regraIdioma = _buscar_regra('idioma_rigido');
    $regraSource = _buscar_regra('dialogue_source');
    $regraDensidade = _buscar_regra('densidade_dialogo');
    $regraHook = _buscar_regra('hook_2_segundos');
    $regraTrama = _buscar_regra('trama_complexa');
    $regraChar = _buscar_regra('character_lock');
    $regraVisual = _buscar_regra('visual_motor');
    $regraSafety = _buscar_regra('safety_filter');
    $regraLipsync = _buscar_regra('active_speaker');
    $regraPausa = _buscar_regra('pausa_dialogo');
    $regraSolda = _buscar_regra('solda_textil');
    $regraCliff = _buscar_regra('cliffhanger');
    $regraDuracao = _buscar_regra('duracao_cena');
    $regraIa = _buscar_regra('instrucoes_ia');
    $regraRes = _buscar_regra('resolucao_480p');
    $regraNarrativa = _buscar_regra('narrativa_coesa');
    $regraVoice = _buscar_regra('voice_registry');
    $regraCont = _buscar_regra('continuidade_causal');

    $summary = $roteiro['story_summary'] ?? '';
    if (strlen($summary) < 50) {
        $resultados[] = _resultado($regraNarrativa, false, 'story_summary ausente no roteiro.');
    } else {
        $resultados[] = _resultado($regraNarrativa, true, 'História: ' . substr($summary, 0, 80) . '...');
    }

    $qtd = count($cenas);
    $okSete = $qtd === NUM_CENAS;
    $resultados[] = _resultado(
        $regraSete,
        $okSete,
        "{$qtd} cenas (esperado " . NUM_CENAS . '). Total: ' . ($qtd * DURACAO_CENA) . 's / ' . DURACAO_TOTAL . 's.'
    );

    if (($roteiro['total_scenes'] ?? null) !== NUM_CENAS) {
        $resultados[] = _resultado($regraSete, false, 'total_scenes deve ser ' . NUM_CENAS . '.');
    }
    if (($roteiro['total_duration_seconds'] ?? null) !== DURACAO_TOTAL) {
        $resultados[] = _resultado(
            $regraSete,
            false,
            'total_duration_seconds deve ser ' . DURACAO_TOTAL . '.'
        );
    }

    $ai = $roteiro['ai_instructions'] ?? [];
    if (!empty($ai['task']) && str_contains($ai['audio_source'] ?? '', 'DIALOGUE_LINES')) {
        $resultados[] = _resultado($regraSource, true, 'audio_source aponta para DIALOGUE_LINES > TEXT.');
    } elseif (!empty($ai['task'])) {
        $resultados[] = _resultado($regraSource, false, 'audio_source não menciona DIALOGUE_LINES > TEXT.');
    } else {
        $resultados[] = _resultado($regraIa, false, 'Falta ai_instructions.');
    }

    $voiceFalhas = problemas_voice_registry($elenco, $roteiro);
    if (!empty($voiceFalhas)) {
        foreach (array_slice($voiceFalhas, 0, 8) as $falha) {
            $resultados[] = _resultado($regraVoice, false, $falha);
        }
        if (count($voiceFalhas) > 8) {
            $resultados[] = _resultado($regraVoice, false, '... +' . (count($voiceFalhas) - 8) . ' falha(s) de voz.');
        }
    } else {
        $resultados[] = _resultado($regraVoice, true, 'Todas as falas usam o voice_registry canonico.');
    }

    if ($sinopse !== null) {
        $continuidadeFalhas = problemas_continuidade($roteiro, $sinopse);
        if (!empty($continuidadeFalhas)) {
            foreach (array_slice($continuidadeFalhas, 0, 8) as $falha) {
                $resultados[] = _resultado($regraCont, false, $falha);
            }
            if (count($continuidadeFalhas) > 8) {
                $resultados[] = _resultado(
                    $regraCont,
                    false,
                    '... +' . (count($continuidadeFalhas) - 8) . ' falha(s) de continuidade.'
                );
            }
        } else {
            $resultados[] = _resultado($regraCont, true, 'Cenas seguem o story_contract canonico.');
        }
    }

    $cenasOrdenadas = $cenas;
    uasort($cenasOrdenadas, function (array $a, array $b): int {
        return ($a['SCENE_NUMBER'] ?? 0) <=> ($b['SCENE_NUMBER'] ?? 0);
    });

    $rolesEncontrados = [];
    $cenasComTrama = 0;

    foreach ($cenasOrdenadas as $chave => $cena) {
        $visual = $cena['VISUAL_PROMPT'] ?? '';
        $acao = ($cena['ACTION_DIRECTION'] ?? '') . ' ' . ($cena['PHYSICAL_MOVEMENT'] ?? '');
        $num = $cena['SCENE_NUMBER'] ?? $chave;
        $dialogueLines = $cena['DIALOGUE_LINES'] ?? [];

        if (($cena['DURATION_SECONDS'] ?? null) !== DURACAO_CENA) {
            $resultados[] = _resultado(
                $regraDuracao,
                false,
                "Cena {$num}: DURATION_SECONDS=" . ($cena['DURATION_SECONDS'] ?? 'null') . ', esperado ' . DURACAO_CENA . '.'
            );
        } else {
            $resultados[] = _resultado(
                $regraDuracao,
                true,
                "Cena {$num}: " . ($cena['TIMESTAMP'] ?? '?') . ' (' . DURACAO_CENA . 's).'
            );
        }

        $role = strtolower($cena['SCENE_ROLE'] ?? '');
        if ($role !== '') {
            $rolesEncontrados[$role] = true;
        }
        if (preg_match(
            PALAVRAS_TRAMA,
            ($cena['SCENE_NAME'] ?? '') . ' ' . $role . ' ' . _dialogos_texto($cena)
        )) {
            $cenasComTrama++;
        }

        if ($num === 1) {
            $hook = $cena['OPENING_HOOK'] ?? '';
            $primeiroTexto = extrair_textos($dialogueLines);
            $hookOk = strlen($hook) > 15
                && (
                    preg_match(PALAVRAS_HOOK, $hook)
                    || (!empty($primeiroTexto) && preg_match(PALAVRAS_HOOK, $primeiroTexto[0]))
                );
            $resultados[] = _resultado(
                $regraHook,
                $hookOk,
                $hook
                    ? 'SCENE_1 OPENING_HOOK: ' . substr($hook, 0, 80) . (strlen($hook) > 80 ? '...' : '')
                    : 'SCENE_1 sem OPENING_HOOK.'
            );
        }

        $beat = $cena['NARRATIVE_BEAT'] ?? '';
        if (strlen($beat) < 20) {
            $resultados[] = _resultado(
                $regraNarrativa,
                false,
                "Cena {$num}: NARRATIVE_BEAT vazio ou genérico."
            );
        } else {
            $resultados[] = _resultado(
                $regraNarrativa,
                true,
                "Cena {$num}: " . substr($beat, 0, 60) . '...'
            );
        }

        $pos = strtolower($cena['STORY_POSITION'] ?? '');
        if ($num <= 2 && !str_contains($pos, 'início') && !str_contains($pos, 'inicio')) {
            $resultados[] = _resultado(
                $regraNarrativa,
                false,
                "Cena {$num}: STORY_POSITION deveria ser 'início'."
            );
        } elseif ($num >= 3 && $num <= 5 && !str_contains($pos, 'meio')) {
            $resultados[] = _resultado(
                $regraNarrativa,
                false,
                "Cena {$num}: STORY_POSITION deveria ser 'meio'."
            );
        } elseif ($num >= 6 && !str_contains($pos, 'fim')) {
            $resultados[] = _resultado(
                $regraNarrativa,
                false,
                "Cena {$num}: STORY_POSITION deveria ser 'fim'."
            );
        }

        $camera = $cena['CAMERA_DIRECTION'] ?? '';
        if (strlen($camera) < 40) {
            $resultados[] = _resultado(
                $regraCamera = _buscar_regra('camera_detalhada'),
                false,
                "Cena {$num}: CAMERA_DIRECTION muito curto."
            );
        } elseif (!preg_match(PALAVRAS_CAMERA, $camera)) {
            $resultados[] = _resultado(
                $regraCamera,
                false,
                "Cena {$num}: CAMERA_DIRECTION sem shots/movimentos."
            );
        } else {
            $resultados[] = _resultado(
                $regraCamera,
                true,
                "Cena {$num}: câmera detalhada (" . strlen($camera) . ' chars).'
            );
        }

        $idiomaFalhas = [];
        foreach ($dialogueLines as $i => $linha) {
            if (!array_key_exists('TEXT', $linha)) {
                continue;
            }
            $texto = $linha['TEXT'];
            $speaker = $linha['SPEAKER'] ?? '?';

            if (trim($texto) === '') {
                $idiomaFalhas[] = 'TEXT vazio (linha ' . ($i + 1) . ')';
                continue;
            }

            if (preg_match(PALAVRAS_FILLER, trim($texto))) {
                $idiomaFalhas[] = "fala genérica — '" . substr($texto, 0, 40) . "'";
            }

            if (strlen(trim($texto)) < 8) {
                $idiomaFalhas[] = "TEXT muito curto — '" . substr($texto, 0, 40) . "'";
            }

            if (!texto_no_idioma($texto, $idioma)) {
                $idiomaFalhas[] = "{$speaker}: idioma errado — '" . substr($texto, 0, 50) . "' (esperado: {$idioma})";
            }

            $lock = $linha['VOICE_IDENTITY_LOCK'] ?? '';
            if (!voice_lock_valido($lock, $idioma)) {
                $idiomaFalhas[] = "{$speaker}: VOICE_IDENTITY_LOCK sem idioma {$idioma}";
            }
        }

        if (!empty($idiomaFalhas)) {
            $detalhe = "Cena {$num}: " . implode('; ', array_slice($idiomaFalhas, 0, 4));
            if (count($idiomaFalhas) > 4) {
                $detalhe .= '; ... +' . (count($idiomaFalhas) - 4);
            }
            $resultados[] = _resultado($regraIdioma, false, $detalhe);
        }

        $timing = calcular_timing($dialogueLines, $idioma, DURACAO_CENA);
        if ($timing['line_count'] < MIN_FALAS_POR_CENA) {
            $resultados[] = _resultado(
                $regraDensidade,
                false,
                "Cena {$num}: {$timing['line_count']} falas (mínimo " . MIN_FALAS_POR_CENA . ').'
            );
        } elseif ($timing['total_dialogue_seconds'] > DURACAO_CENA) {
            $resultados[] = _resultado(
                $regraDensidade,
                false,
                "Cena {$num}: {$timing['total_dialogue_seconds']}s estoura os " . DURACAO_CENA . 's.'
            );
        } elseif (!$timing['fills_scene']) {
            $resultados[] = _resultado(
                $regraDensidade,
                false,
                "Cena {$num}: {$timing['total_dialogue_seconds']}s de áudio "
                . '(meta ' . MIN_SEGUNDOS_FALA . '-' . MAX_SEGUNDOS_FALA . 's). Pouco diálogo.'
            );
        } else {
            $resultados[] = _resultado(
                $regraDensidade,
                true,
                "Cena {$num}: {$timing['line_count']} falas, {$timing['word_count']} palavras, "
                . "~{$timing['total_dialogue_seconds']}s / " . DURACAO_CENA . 's.'
            );
        }

        if (!empty($cena['AI_VIDEO_TASK'])) {
            $resultados[] = _resultado($regraIa, true, "Cena {$num}: AI_VIDEO_TASK OK.");
        } else {
            $resultados[] = _resultado($regraIa, false, "Cena {$num}: falta AI_VIDEO_TASK.");
        }

        if (preg_match(PALAVRAS_VISUAL, $visual)) {
            $resultados[] = _resultado($regraVisual, true, "Cena {$num}: motor visual OK.");
        } else {
            $resultados[] = _resultado(
                $regraVisual,
                false,
                "Cena {$num}: VISUAL_PROMPT sem termos 4K/cinematic."
            );
        }

        $speakers = array_values(array_unique(_speakers_da_cena($cena)));
        if (!empty($speakers)) {
            $visualUpper = strtoupper($visual);
            $faltando = array_filter($speakers, fn(string $s): bool => !str_contains($visualUpper, $s));
            if (!empty($faltando)) {
                $resultados[] = _resultado(
                    $regraChar,
                    false,
                    "Cena {$num}: faltam no VISUAL_PROMPT: " . implode(', ', $faltando) . '.'
                );
            } else {
                $resultados[] = _resultado($regraChar, true, "Cena {$num}: personagens no VISUAL_PROMPT.");
            }
        }

        $textoCena = $visual . ' ' . $acao . ' ' . _dialogos_texto($cena);
        if (preg_match(PALAVRAS_SANGUE, $textoCena)) {
            $resultados[] = _resultado($regraSafety, false, "Cena {$num}: referência a sangue.");
        } elseif (preg_match(PALAVRAS_AGRESSAO, $textoCena)) {
            $resultados[] = _resultado($regraSafety, false, "Cena {$num}: agressão explícita.");
        } else {
            $resultados[] = _resultado($regraSafety, true, "Cena {$num}: safety OK.");
        }

        if (!empty($cena['HAS_DIALOGUE']) && preg_match(PALAVRAS_LIPSYNC, $acao)) {
            $resultados[] = _resultado($regraLipsync, true, "Cena {$num}: lip-sync OK.");
        } elseif (!empty($cena['HAS_DIALOGUE'])) {
            $resultados[] = _resultado(
                $regraLipsync,
                false,
                "Cena {$num}: sem menção a lip-sync."
            );
        }

        foreach ($dialogueLines as $linha) {
            if (array_key_exists('PAUSE', $linha) && ($linha['PAUSE'] ?? null) != 0.2) {
                $resultados[] = _resultado(
                    $regraPausa,
                    true,
                    "Cena {$num}: pausa {$linha['PAUSE']}s (recomendado 0.2s)."
                );
            }
        }
    }

    $rolesOk = count(array_intersect(array_keys($rolesEncontrados), ROLES_TRAMA)) >= 3;
    $tramaOk = $cenasComTrama >= 3 || $rolesOk;
    $resultados[] = _resultado(
        $regraTrama,
        $tramaOk,
        'Roles: ' . (implode(', ', array_keys($rolesEncontrados)) ?: 'nenhum') . '. '
        . "Cenas com elementos de trama: {$cenasComTrama}/" . NUM_CENAS . '.'
    );

    if (!empty($cast) && count($cenas) > 1) {
        $cenasLista = array_values($cenasOrdenadas);
        $primeira = strtoupper($cenasLista[0]['VISUAL_PROMPT'] ?? '');
        $ultimaVisual = strtoupper($cenasLista[count($cenasLista) - 1]['VISUAL_PROMPT'] ?? '');
        foreach ($cast as $p) {
            $nome = $p['name'] ?? '';
            $trecho = _trecho_roupa($p['outfit_dna'] ?? '');
            if ($trecho !== '' && !str_contains($primeira, $trecho) && !str_contains($ultimaVisual, $trecho)) {
                $resultados[] = _resultado(
                    $regraSolda,
                    false,
                    "{$nome}: roupa pode ter mudado."
                );
            } elseif ($trecho !== '') {
                $resultados[] = _resultado($regraSolda, true, "{$nome}: roupa consistente.");
            }
        }
    }

    if (!empty($cenasOrdenadas)) {
        $cenasLista = array_values($cenasOrdenadas);
        $ultima = $cenasLista[count($cenasLista) - 1];
        $textoFinal = ($ultima['SCENE_NAME'] ?? '') . ' '
            . _dialogos_texto($ultima) . ' '
            . ($ultima['VISUAL_PROMPT'] ?? '')
            . ' ' . ($ultima['OPENING_HOOK'] ?? '');
        if (preg_match(PALAVRAS_CLIFFHANGER, $textoFinal)) {
            $resultados[] = _resultado($regraCliff, true, 'SCENE_7 com cliffhanger.');
        } else {
            $resultados[] = _resultado($regraCliff, false, 'SCENE_7 sem gancho claro.');
        }
    }

    if (($roteiro['resolution'] ?? null) === RESOLUCAO) {
        $resultados[] = _resultado($regraRes, true, 'Roteiro em ' . RESOLUCAO . '.');
    }

    return $resultados;
}

function _speakers_da_cena(array $cena): array
{
    $speakers = [];
    foreach ($cena['DIALOGUE_LINES'] ?? [] as $linha) {
        if (array_key_exists('SPEAKER', $linha)) {
            $speakers[] = strtoupper($linha['SPEAKER']);
        }
    }

    return $speakers;
}

function _dialogos_texto(array $cena): string
{
    return implode(' ', extrair_textos($cena['DIALOGUE_LINES'] ?? []));
}

function _trecho_roupa(string $outfit): string
{
    if (preg_match('/\b(shirt|shorts|dress|sneakers|jersey|skirt|vest|sandal)\b/i', $outfit, $matches)) {
        return strtoupper($matches[0]);
    }

    return '';
}

function validar_tudo(array $elenco, array $roteiro, ?array $sinopse = null): array
{
    $elencoResultados = validar_elenco($elenco);
    $sinopseResultados = $sinopse !== null ? validar_sinopse($sinopse) : [];
    $roteiroResultados = validar_roteiro($roteiro, $elenco, $sinopse);
    $todos = array_merge($elencoResultados, $sinopseResultados, $roteiroResultados);
    $problemas = array_values(array_filter($todos, fn(array $r): bool => !$r['ok']));

    $erros = count(array_filter($problemas, fn(array $r): bool => $r['severidade'] === 'erro'));
    $avisos = count(array_filter($problemas, fn(array $r): bool => $r['severidade'] === 'aviso'));
    $infos = count(array_filter($problemas, fn(array $r): bool => $r['severidade'] === 'info'));

    return [
        'resumo' => [
            'verificacoes' => count($todos),
            'problemas' => count($problemas),
            'erros' => $erros,
            'avisos' => $avisos,
            'infos' => $infos,
        ],
        'problemas' => $problemas,
    ];
}

function tem_erros_criticos(array $relatorio): bool
{
    return ($relatorio['resumo']['erros'] ?? 0) > 0;
}

function imprimir_relatorio(array $relatorio): void
{
    $resumo = $relatorio['resumo'];
    $problemas = $relatorio['problemas'] ?? [];

    echo "\n" . str_repeat('=', 50) . "\n";
    echo "  VALIDAÇÃO DAS REGRAS\n";
    echo str_repeat('=', 50) . "\n";
    echo '  Verificações: ' . $resumo['verificacoes'] . '  |  '
        . 'Problemas: ' . $resumo['problemas'] . '  |  '
        . 'Erros: ' . $resumo['erros'] . '  |  Avisos: ' . $resumo['avisos'] . "\n";
    echo str_repeat('=', 50) . "\n";

    if (empty($problemas)) {
        echo "\n  Tudo certo! Nenhum problema encontrado.\n\n";
        return;
    }

    $vistos = [];
    $icones = ['erro' => 'X', 'aviso' => '!', 'info' => 'i'];
    foreach (array_slice($problemas, 0, 12) as $r) {
        $chave = ($r['id'] ?? '') . '|' . ($r['detalhe'] ?? '');
        if (isset($vistos[$chave])) {
            continue;
        }
        $vistos[$chave] = true;
        $icone = $icones[$r['severidade'] ?? ''] ?? '?';
        echo "\n  [{$icone}] {$r['nome']}\n";
        echo "      {$r['detalhe']}\n";
    }

    if (count($problemas) > 12) {
        echo "\n  ... e mais " . (count($problemas) - 12) . " problema(s) em validacao.json\n";
    }

    echo "\n  " . count($problemas) . " ponto(s) para revisar. Detalhes em log/validacao.json\n\n";
}