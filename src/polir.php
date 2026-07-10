<?php
declare(strict_types=1);

require_once __DIR__ . '/dialogo.php';

const _LIPSYNC_PADRAO = (
    'Clean, non-overlapping sequential dialogue. '
    . 'Active speaker lip-sync; listeners keep mouth closed with reactive expressions.'
);

const _VISUAL_SUFIXO = (
    ' Cinematic 4K 3D animation. Hyper-realistic PBR textures. '
    . 'Volumetric lighting. Disney-Pixar style.'
);

const _SUBSTITUICOES_SAFETY = [
    ['/\bblood\b/i', 'deep purple sticky grape juice'],
    ['/\bsangue\b/i', 'suco de uva roxo pegajoso'],
    ['/\bpunch\b/i', 'sudden aggressive arm gesture'],
    ['/\bsoco\b/i', 'gesto agressivo de braço'],
    ['/\bkill\b/i', 'defeat'],
    ['/\bmatar\b/i', 'derrotar'],
];

function polir_roteiro(array $roteiro, array $elenco, string $idioma): array
{
    $lock = lock_idioma_texto($idioma);

    foreach ($roteiro['scenes'] ?? [] as $chave => $cena) {
        $cena = _polir_dialogos($cena, $lock);
        $cena = _polir_acao($cena);
        $cena = _polir_visual($cena);
        $cena = _polir_safety($cena);
        $roteiro['scenes'][$chave] = $cena;
    }

    return ajustar_timing_roteiro($roteiro, $idioma);
}

function _aplicar_substituicoes(string $texto): string
{
    if ($texto === '') {
        return $texto;
    }
    foreach (_SUBSTITUICOES_SAFETY as [$padrao, $substituto]) {
        $texto = (string) preg_replace($padrao, $substituto, $texto);
    }
    return $texto;
}

function _polir_safety(array $cena): array
{
    foreach ([
        'VISUAL_PROMPT',
        'ACTION_DIRECTION',
        'PHYSICAL_MOVEMENT',
        'OPENING_HOOK',
        'NARRATIVE_BEAT',
    ] as $campo) {
        if (!empty($cena[$campo])) {
            $cena[$campo] = _aplicar_substituicoes((string) $cena[$campo]);
        }
    }

    foreach ($cena['DIALOGUE_LINES'] ?? [] as $indice => $linha) {
        if (is_array($linha) && array_key_exists('TEXT', $linha)) {
            $cena['DIALOGUE_LINES'][$indice]['TEXT'] = _aplicar_substituicoes((string) $linha['TEXT']);
        }
    }

    return $cena;
}

function _polir_dialogos(array $cena, string $lock): array
{
    $lines = $cena['DIALOGUE_LINES'] ?? [];
    if ($lines === []) {
        return $cena;
    }

    $novas = [];
    foreach ($lines as $linha) {
        if (!is_array($linha)) {
            continue;
        }
        if (array_key_exists('TEXT', $linha)) {
            $lockLower = strtolower($lock);
            $voiceLock = $linha['VOICE_IDENTITY_LOCK'] ?? '';
            if ($voiceLock === '' || !str_contains(strtolower($voiceLock), $lockLower)) {
                $speaker = $linha['SPEAKER'] ?? 'SPEAKER';
                $linha['VOICE_IDENTITY_LOCK'] = "{$speaker} voice. {$lock}.";
            }
            $novas[] = $linha;
            $novas[] = ['PAUSE' => PAUSA_PADRAO];
        } elseif (array_key_exists('PAUSE', $linha)) {
            continue;
        }
    }

    if ($novas !== [] && array_key_exists('PAUSE', $novas[count($novas) - 1])) {
        array_pop($novas);
    }

    $cena['DIALOGUE_LINES'] = $novas;
    return $cena;
}

function _polir_acao(array $cena): array
{
    if (empty($cena['HAS_DIALOGUE'])) {
        return $cena;
    }

    foreach (['ACTION_DIRECTION', 'PHYSICAL_MOVEMENT'] as $campo) {
        $texto = $cena[$campo] ?? '';
        if ($texto !== '' && !preg_match(
            '/\b(sequential dialogue|mouth closed|lip.?sync|non.?overlapping|speaker)\b/i',
            $texto
        )) {
            $cena[$campo] = trim(rtrim($texto) . ' ' . _LIPSYNC_PADRAO);
        }
    }

    return $cena;
}

function _polir_visual(array $cena): array
{
    $visual = $cena['VISUAL_PROMPT'] ?? '';
    if ($visual === '') {
        return $cena;
    }

    if (!preg_match('/\b(4k|cinematic|volumetric|pbr|disney|pixar)\b/i', $visual)) {
        $cena['VISUAL_PROMPT'] = rtrim($visual) . _VISUAL_SUFIXO;
    }

    $visual_upper = strtoupper($cena['VISUAL_PROMPT']);
    $speakers = [];
    foreach ($cena['DIALOGUE_LINES'] ?? [] as $linha) {
        if (is_array($linha) && array_key_exists('SPEAKER', $linha)) {
            $speaker = strtoupper((string) $linha['SPEAKER']);
            if ($speaker !== '' && !in_array($speaker, $speakers, true)) {
                $speakers[] = $speaker;
            }
        }
    }

    $faltando = [];
    foreach ($speakers as $s) {
        if ($s !== '' && !str_contains($visual_upper, $s)) {
            $faltando[] = $s;
        }
    }
    if ($faltando !== []) {
        $cena['VISUAL_PROMPT'] .= ' Characters in scene: ' . implode(', ', $faltando) . '.';
    }

    return $cena;
}