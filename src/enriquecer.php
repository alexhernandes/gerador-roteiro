<?php
declare(strict_types=1);

/**
 * Garante que os JSONs tenham instruções claras para agentes de IA,
 * timing de diálogo calculado e metadados corretos.
 */

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/dialogo.php';
require_once __DIR__ . '/schema.php';
require_once __DIR__ . '/narrativa.php';
require_once __DIR__ . '/polir.php';
require_once __DIR__ . '/voz.php';

function _agent_settings(?array $opcoesAgente = null): array
{
    $opcoesAgente = $opcoesAgente ?? [];
    $videosPorPasso = (int) ($opcoesAgente['videos_per_step'] ?? AGENT_VIDEOS_PER_STEP);

    return [
        'videos_per_step' => max(1, $videosPorPasso),
        'confirm_between_steps' => (bool) ($opcoesAgente['confirm_between_steps'] ?? AGENT_CONFIRM_BETWEEN_STEPS),
    ];
}

function _texto_execucao_agente(array $settings): string
{
    $n = $settings['videos_per_step'];
    $confirmacao = $settings['confirm_between_steps'];
    $unidade = $n === 1 ? 'scene' : "group of up to {$n} scenes";
    $confirmTxt = $confirmacao
        ? 'After each approved QA pass, ask the user/operator for permission before continuing.'
        : 'After each approved QA pass, continue automatically to the next step.';

    if ($n === 1) {
        return 'Work strictly ONE SCENE AT A TIME: render one scene, run scene QA, fix if needed, '
            . "then proceed. {$confirmTxt}";
    }

    return "Work in controlled batches of up to {$n} scenes: render one {$unidade}, run QA for every scene "
        . "in that group, fix failures, then proceed. {$confirmTxt}";
}

function _formatar_tempo(int $segundos): string
{
    $mins = intdiv($segundos, 60);
    $secs = $segundos % 60;

    return sprintf('%02d:%02d', $mins, $secs);
}

function enriquecer_elenco(array $elenco, string $aspectRatio, string $idioma): array
{
    $elenco['aspect_ratio'] = $aspectRatio;
    $elenco['resolution'] = RESOLUCAO;
    $elenco['language'] = $idioma;

    $elenco['ai_instructions'] = [
        'task' => 'AI AGENT: Generate ONE character reference IMAGE for EACH cast member below. '
            . 'Use physical_dna and outfit_dna as the visual lock. '
            . 'These images will be used as consistent references for video generation.',
        'resolution' => RESOLUCAO,
        'aspect_ratio' => $aspectRatio,
        'output' => 'One full character reference image per cast member (PNG or JPG).',
        'style' => 'Cinematic stylized 3D character design, hyper-realistic PBR textures when applicable.',
    ];

    foreach ($elenco['cast'] ?? [] as $idx => $personagem) {
        $nome = $personagem['name'] ?? 'Character';
        $characterType = $personagem['character_type'] ?? ($personagem['fruit_type'] ?? 'character');
        $elenco['cast'][$idx]['ai_image_task'] = 'AI AGENT: Create a ' . RESOLUCAO . " {$aspectRatio} full character reference IMAGE "
            . "of {$nome} ({$characterType}). "
            . 'Physical: ' . ($personagem['physical_dna'] ?? '') . ' '
            . 'Outfit: ' . ($personagem['outfit_dna'] ?? '') . ' '
            . 'Neutral pose, clear lighting, no background clutter. '
            . 'This image locks the character look for all video scenes.';
    }

    return aplicar_voice_registry_elenco($elenco, $idioma);
}

function _resumir_ato(array $beats, array $numerosCena): string
{
    $partes = [];
    foreach ($beats as $beat) {
        if (
            in_array($beat['scene_number'] ?? null, $numerosCena, true)
            && !empty($beat['narrative_beat'])
        ) {
            $partes[] = $beat['narrative_beat'];
        }
    }

    return trim(implode(' ', $partes));
}

function _preencher_atos_sinopse(array $sinopse): array
{
    $beats = $sinopse['beats'] ?? [];
    if (empty($beats)) {
        return $sinopse;
    }

    $atos = [
        'act_1' => [[1, 2], 'ATO 1 — INÍCIO'],
        'act_2' => [[3, 4, 5], 'ATO 2 — MEIO'],
        'act_3' => [[6, 7], 'ATO 3 — FIM'],
    ];

    foreach ($atos as $campo => [$cenas, $rotulo]) {
        $resumo = _resumir_ato($beats, $cenas);
        $atual = trim($sinopse[$campo] ?? '');
        if (strlen($atual) < 30 && $resumo !== '') {
            $sinopse[$campo] = "{$rotulo}: {$resumo}";
        }
    }

    return $sinopse;
}

function enriquecer_sinopse(array $sinopse, string $idioma): array
{
    $sinopse = _preencher_atos_sinopse($sinopse);
    $sinopse = aplicar_story_contract_sinopse($sinopse);
    $sinopse['ai_instructions'] = [
        'task' => 'REFERENCE ONLY — AI AGENT: Do NOT generate images, videos or audio from this file. '
            . 'This is a story blueprint for consultation during script review and production planning.',
        'purpose' => 'Planning document with story_summary, acts and beats. '
            . 'Use it to understand the narrative arc — not as a generation source.',
        'use_instead' => [
            'character_images' => 'elenco.json → ai_image_task (one reference image per cast member)',
            'scene_videos' => 'roteiro.json → AI_VIDEO_TASK (one 10s video per scene)',
            'spoken_audio' => 'roteiro.json → DIALOGUE_LINES > TEXT only',
        ],
        'language' => $idioma,
        'do_not_generate' => true,
    ];

    return $sinopse;
}

function enriquecer_roteiro(
    array $roteiro,
    string $aspectRatio,
    string $idioma,
    ?array $elenco = null,
    ?array $opcoesAgente = null
): array {
    $agentSettings = _agent_settings($opcoesAgente);
    $execucaoAgente = _texto_execucao_agente($agentSettings);

    $roteiro['aspect_ratio'] = $aspectRatio;
    $roteiro['resolution'] = RESOLUCAO;
    $roteiro['language'] = $idioma;
    $roteiro['scene_duration_seconds'] = DURACAO_CENA;
    $roteiro['total_duration_seconds'] = DURACAO_TOTAL;
    $roteiro['total_scenes'] = NUM_CENAS;

    $roteiro['ai_instructions'] = [
        'task' => 'AI AGENT: Generate exactly ' . NUM_CENAS . ' videos of ' . DURACAO_CENA . ' seconds each '
            . '(' . DURACAO_TOTAL . "s total). Resolution: " . RESOLUCAO . ". Aspect ratio: {$aspectRatio}. "
            . $execucaoAgente,
        'resolution' => RESOLUCAO,
        'aspect_ratio' => $aspectRatio,
        'duration_per_scene_seconds' => DURACAO_CENA,
        'total_duration_seconds' => DURACAO_TOTAL,
        'total_scenes' => NUM_CENAS,
        'audio_source' => 'ALL spoken audio comes ONLY from DIALOGUE_LINES > TEXT. '
            . "Language: {$idioma}. Do NOT translate or change language.",
        'output' => NUM_CENAS . ' video clips of ' . DURACAO_CENA . 's each (MP4), total ' . DURACAO_TOTAL . 's.',
        'style' => 'Cinematic 3D animation at ' . RESOLUCAO . ", {$aspectRatio}, "
            . 'Disney-Pixar style, volumetric lighting.',
        'note' => 'sinopse.json is REFERENCE ONLY (do not generate media from it). '
            . 'Use this roteiro.json and elenco.json as the production sources.',
        'post_generation_qa' => 'MANDATORY TWO-LAYER QA. Scene-level QA: after EACH individual scene render, '
            . 'listen to that scene before moving to the next one; verify every spoken word matches '
            . 'DIALOGUE_LINES > TEXT exactly, the same voice registry identity is used, language is unchanged, '
            . 'audio is clear, no words are missing/invented, no overlap occurs, and active-speaker lip-sync is aligned. '
            . 'Re-render that scene until it passes. Final global QA: after all scenes pass individually, review the '
            . 'complete sequence from SCENE_1 to SCENE_7 for voice consistency, audio continuity, story continuity, '
            . 'timestamps, visual character lock, outfit lock, and cliffhanger integrity. Re-render any failed scene.',
        'agent_execution' => 'videos_per_step=' . $agentSettings['videos_per_step'] . '; '
            . 'confirm_between_steps=' . ($agentSettings['confirm_between_steps'] ? 'true' : 'false') . '; '
            . $execucaoAgente,
    ];
    $roteiro['agent_execution'] = $agentSettings;

    if ($elenco !== null) {
        $roteiro = aplicar_voice_registry_roteiro($roteiro, $elenco, $idioma);
        $roteiro = polir_roteiro($roteiro, $elenco, $idioma);
        $roteiro = aplicar_voice_registry_roteiro($roteiro, $elenco, $idioma);
    }

    $cenas = $roteiro['scenes'] ?? [];
    $textosDialogo = [];

    $chavesOrdenadas = array_keys($cenas);
    usort($chavesOrdenadas, function (string $a, string $b) use ($cenas): int {
        return ($cenas[$a]['SCENE_NUMBER'] ?? 0) <=> ($cenas[$b]['SCENE_NUMBER'] ?? 0);
    });

    foreach ($chavesOrdenadas as $chave) {
        $cena = &$cenas[$chave];
        $num = $cena['SCENE_NUMBER'] ?? 1;
        $inicio = ($num - 1) * DURACAO_CENA;
        $fim = $num * DURACAO_CENA;

        $cena['DURATION_SECONDS'] = DURACAO_CENA;
        $cena['TIMESTAMP'] = _formatar_tempo($inicio) . ' - ' . _formatar_tempo($fim);

        $timing = calcular_timing($cena['DIALOGUE_LINES'] ?? [], $idioma, DURACAO_CENA);
        $cena['DIALOGUE_TIMING'] = $timing;

        $dialogoTexto = implode(' | ', array_map(
            fn(array $linha): string => $linha['TEXT'],
            array_filter(
                $cena['DIALOGUE_LINES'] ?? [],
                fn(array $linha): bool => array_key_exists('TEXT', $linha)
            )
        ));
        $textosDialogo[] = $dialogoTexto;

        $cena['AI_VIDEO_TASK'] = 'AI AGENT: Create a ' . DURACAO_CENA . '-second ' . RESOLUCAO . " {$aspectRatio} VIDEO "
            . "for SCENE {$num} — '" . ($cena['SCENE_NAME'] ?? $chave) . "'. "
            . "{$execucaoAgente} "
            . 'For this task, render ONLY the current scene described here. '
            . 'After rendering this single scene, run scene-level QA before moving on. '
            . "Timestamp: {$cena['TIMESTAMP']}. "
            . 'Story beat: ' . ($cena['NARRATIVE_BEAT'] ?? '') . '. '
            . 'Hook (first 2s): ' . ($cena['OPENING_HOOK'] ?? '') . '. '
            . 'Camera: ' . substr($cena['CAMERA_DIRECTION'] ?? '', 0, 400) . '. '
            . 'Movement: ' . substr($cena['PHYSICAL_MOVEMENT'] ?? '', 0, 200) . '. '
            . "Audio language: {$idioma}. "
            . 'Spoken lines (DIALOGUE_LINES > TEXT only): ' . substr($dialogoTexto, 0, 300) . '. '
            . "Speech: {$timing['total_dialogue_seconds']}s / " . DURACAO_CENA . 's. '
            . 'Duration MUST be exactly ' . DURACAO_CENA . ' seconds. '
            . 'If this scene fails audio, voice, lip-sync, visual lock, timing, or continuity QA, '
            . 're-render this scene before generating the next scene. '
            . 'After ALL scenes are generated one by one: run final global QA per ai_instructions.post_generation_qa.';
    }
    unset($cena);

    $roteiro['scenes'] = $cenas;

    return $roteiro;
}

function enriquecer_roteiro_com_sinopse(
    array $roteiro,
    string $aspectRatio,
    string $idioma,
    array $elenco,
    array $sinopse,
    ?array $opcoesAgente = null
): array {
    $roteiro = enriquecer_roteiro($roteiro, $aspectRatio, $idioma, $elenco, $opcoesAgente);

    return aplicar_story_contract_roteiro($roteiro, $sinopse);
}