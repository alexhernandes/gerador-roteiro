<?php

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');

require_once dirname(__DIR__) . '/src/bootstrap.php';

$idiomas = [
    'Português (Brasil)',
    'English',
    'Español',
    'Deutsch',
];

$formatos = [
    ['value' => '9:16', 'label' => '9:16 (vertical — TikTok/Reels)'],
    ['value' => '16:9', 'label' => '16:9 (horizontal — YouTube)'],
];

$universos = [];
foreach (listar_universos() as $id) {
    $universos[] = [
        'value' => $id,
        'label' => label_universo($id),
    ];
}

$videosPorPasso = [1, 2, 3, 5, 7];
if (!in_array(AGENT_VIDEOS_PER_STEP, $videosPorPasso, true)) {
    $videosPorPasso[] = AGENT_VIDEOS_PER_STEP;
    sort($videosPorPasso);
}

echo json_encode([
    'idiomas' => $idiomas,
    'formatos' => $formatos,
    'universos' => $universos,
    'videos_por_passo' => $videosPorPasso,
    'defaults' => [
        'idioma' => DEFAULT_LANGUAGE,
        'aspect_ratio' => DEFAULT_ASPECT_RATIO,
        'universo' => normalizar_universo(DEFAULT_UNIVERSE),
        'tema' => DEFAULT_THEME,
        'agent_confirm_between_steps' => AGENT_CONFIRM_BETWEEN_STEPS,
        'agent_videos_per_step' => AGENT_VIDEOS_PER_STEP,
    ],
    'meta' => [
        'model' => MODEL,
        'total_scenes' => TOTAL_SCENES,
        'scene_duration' => SCENE_DURATION_SECONDS,
        'total_duration' => TOTAL_DURATION_SECONDS,
        'resolution' => VIDEO_RESOLUTION,
    ],
], JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);