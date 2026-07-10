<?php

declare(strict_types=1);

const UNIVERSE_LABELS = [
    'frutinhas' => 'Frutinhas antropomórficas',
    'carros' => 'Carros falantes',
    'predios_falantes' => 'Prédios falantes',
    'humanos_desenhados' => 'Humanos desenhados',
];

define('UNIVERSE_DIR', ROOT_DIR . DIRECTORY_SEPARATOR . 'prompts' . DIRECTORY_SEPARATOR . 'universos');

function normalizar_universo(?string $universo): string
{
    $valor = strtolower(trim((string) $universo));
    $valor = str_replace([' ', '-'], '_', $valor);

    $aliases = [
        'frutas' => 'frutinhas',
        'fruits' => 'frutinhas',
        'fruit' => 'frutinhas',
        'cars' => 'carros',
        'buildings' => 'predios_falantes',
        'predios' => 'predios_falantes',
        'prédios' => 'predios_falantes',
        'humanos' => 'humanos_desenhados',
        'humans' => 'humanos_desenhados',
    ];

    $normalizado = $aliases[$valor] ?? $valor;

    return $normalizado !== '' ? $normalizado : DEFAULT_UNIVERSE;
}

function listar_universos(): array
{
    $ids = [];

    foreach (UNIVERSE_OPTIONS as $universo) {
        $normalizado = normalizar_universo($universo);
        if (!in_array($normalizado, $ids, true)) {
            $ids[] = $normalizado;
        }
    }

    if (is_dir(UNIVERSE_DIR)) {
        $arquivos = glob(UNIVERSE_DIR . DIRECTORY_SEPARATOR . '*.txt');
        if ($arquivos !== false) {
            sort($arquivos);
            foreach ($arquivos as $arquivo) {
                $stem = pathinfo($arquivo, PATHINFO_FILENAME);
                if (!in_array($stem, $ids, true)) {
                    $ids[] = $stem;
                }
            }
        }
    }

    return $ids;
}

function label_universo(?string $universo): string
{
    $universo = normalizar_universo($universo);

    if (array_key_exists($universo, UNIVERSE_LABELS)) {
        return UNIVERSE_LABELS[$universo];
    }

    return ucwords(str_replace('_', ' ', $universo));
}

function carregar_prompt_universo(?string $universo): string
{
    $universo = normalizar_universo($universo);
    $caminho = UNIVERSE_DIR . DIRECTORY_SEPARATOR . $universo . '.txt';

    if (!is_file($caminho)) {
        $caminho = UNIVERSE_DIR . DIRECTORY_SEPARATOR . normalizar_universo(DEFAULT_UNIVERSE) . '.txt';
    }

    if (!is_file($caminho)) {
        return 'UNIVERSO: personagens estilizados consistentes. '
            . 'Crie character_type, physical_dna, outfit_dna, voice_profile e ai_image_task.';
    }

    $conteudo = file_get_contents($caminho);
    if ($conteudo === false) {
        return 'UNIVERSO: personagens estilizados consistentes. '
            . 'Crie character_type, physical_dna, outfit_dna, voice_profile e ai_image_task.';
    }

    return trim($conteudo);
}