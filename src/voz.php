<?php
declare(strict_types=1);

require_once __DIR__ . '/dialogo.php';

function chave_speaker(string $nome): string
{
    $chave = preg_replace('/[^A-Z0-9]+/', '_', strtoupper($nome));
    return trim((string) $chave, '_');
}

function _genero_canonico(string $gender): string
{
    $texto = strtolower($gender);
    if (preg_match('/female|femin|mulher|girl|woman/', $texto)) {
        return 'Strictly Female';
    }
    if (preg_match('/male|masc|homem|boy|man/', $texto)) {
        return 'Strictly Male';
    }
    return 'Androgynous / Character Voice';
}

function _sintese_forcada(string $gender, string $idioma): string
{
    $genero = _genero_canonico($gender);
    $codigo = strtoupper(normalizar_idioma($idioma));
    if (str_contains($genero, 'Female')) {
        return "Female_Adult_Soprano_{$codigo}";
    }
    if (str_contains($genero, 'Male')) {
        return "Male_Adult_Baritone_{$codigo}";
    }
    return "Adult_Neutral_Character_{$codigo}";
}

function _peso_vocal(string $gender, string $character_type, string $voice_profile): string
{
    $genero = _genero_canonico($gender);
    $tipo = $character_type !== '' ? $character_type : 'Character';
    $perfil = $voice_profile !== '' ? $voice_profile : 'consistent expressive character voice';
    if (str_contains($genero, 'Female')) {
        $base = 'Feminine / clear adult character voice';
    } elseif (str_contains($genero, 'Male')) {
        $base = 'Masculine / clear adult character voice';
    } else {
        $base = 'Neutral / clear adult character voice';
    }
    return "{$base} / {$tipo} / {$perfil}";
}

function criar_voice_registry(array $elenco, string $idioma): array
{
    $lock = lock_idioma_texto($idioma);
    $voices = [];

    foreach ($elenco['cast'] ?? [] as $personagem) {
        $nome = $personagem['name'] ?? 'CHARACTER';
        $speaker_key = chave_speaker($nome);
        $voice_model_id = "{$speaker_key}_VOICE_LOCK";
        $gender = $personagem['gender'] ?? '';
        $character_type = $personagem['character_type'] ?? ($personagem['fruit_type'] ?? '');
        $voice_profile = $personagem['voice_profile'] ?? '';
        $age = $personagem['age'] ?? '';

        $identity_lock = sprintf(
            'Voice Model: %s. Speaker: %s. Age: %s. Gender: %s. Character Type: %s. Tone: %s. %s.',
            $voice_model_id,
            $nome,
            $age,
            $gender,
            $character_type,
            $voice_profile,
            $lock
        );
        $override = [
            'VOICE_GENDER' => _genero_canonico($gender),
            'VOCAL_WEIGHT' => _peso_vocal($gender, (string) $character_type, (string) $voice_profile),
            'TONE_PROFILE' => (
                "{$nome}: {$voice_profile}. Keep the same pitch, rhythm, accent, "
                . 'emotional texture, and vocal weight in every scene.'
            ),
            'FORCE_SYNTHESIS' => _sintese_forcada($gender, $idioma),
        ];

        $voices[$nome] = [
            'SPEAKER' => $nome,
            'SPEAKER_KEY' => $speaker_key,
            'VOICE_MODEL_ID' => $voice_model_id,
            'VOICE_IDENTITY_LOCK' => $identity_lock,
            'VOICE_OVERRIDE_METADATA' => $override,
        ];
    }

    return [
        'version' => 'voice-registry-v1',
        'language_lock' => $lock,
        'rule' => (
            'Every DIALOGUE_LINES item must use the exact SPEAKER and '
            . 'VOICE_IDENTITY_LOCK from this registry. Never invent per-scene voices.'
        ),
        'multi_speaker_rule' => (
            'When a scene has multiple speakers, synthesize one line at a time using the '
            . 'active speaker only. Never blend voices, never reuse another speaker\'s timbre, '
            . 'and never let visual position or camera focus change the assigned voice.'
        ),
        'voices' => $voices,
    ];
}

function obter_voice_registry(array $elenco, string $idioma): array
{
    $registry = $elenco['voice_registry'] ?? null;
    if (is_array($registry) && !empty($registry['voices'])) {
        return $registry;
    }
    return criar_voice_registry($elenco, $idioma);
}

function aplicar_voice_registry_elenco(array $elenco, string $idioma): array
{
    $registry = criar_voice_registry($elenco, $idioma);
    $elenco['voice_registry'] = $registry;

    foreach ($elenco['cast'] ?? [] as $indice => $personagem) {
        $nome = $personagem['name'] ?? null;
        if ($nome === null) {
            continue;
        }
        $voz = $registry['voices'][$nome] ?? null;
        if ($voz === null) {
            continue;
        }
        $elenco['cast'][$indice]['voice_id'] = $voz['VOICE_MODEL_ID'];
        $elenco['cast'][$indice]['voice_identity_lock'] = $voz['VOICE_IDENTITY_LOCK'];
        $elenco['cast'][$indice]['voice_override_metadata'] = $voz['VOICE_OVERRIDE_METADATA'];
    }

    return $elenco;
}

function _mapa_por_chave(array $registry): array
{
    $mapa = [];
    foreach ($registry['voices'] ?? [] as $nome => $voz) {
        $mapa[chave_speaker($nome)] = $voz;
    }
    return $mapa;
}

function encontrar_voz(array $registry, string $speaker): ?array
{
    $mapa = _mapa_por_chave($registry);
    return $mapa[chave_speaker($speaker)] ?? null;
}

function aplicar_voice_registry_cena(array $cena, array $elenco, string $idioma): array
{
    $registry = obter_voice_registry($elenco, $idioma);
    $overrides = [];

    foreach ($cena['DIALOGUE_LINES'] ?? [] as $indice => $linha) {
        if (!is_array($linha) || !array_key_exists('TEXT', $linha)) {
            continue;
        }
        $voz = encontrar_voz($registry, (string) ($linha['SPEAKER'] ?? ''));
        if ($voz === null) {
            continue;
        }
        $cena['DIALOGUE_LINES'][$indice]['SPEAKER'] = $voz['SPEAKER'];
        $cena['DIALOGUE_LINES'][$indice]['VOICE_IDENTITY_LOCK'] = $voz['VOICE_IDENTITY_LOCK'];
        $overrides[$voz['SPEAKER']] = $voz['VOICE_OVERRIDE_METADATA'];
    }

    if ($overrides !== []) {
        $cena['VOICE_OVERRIDE_METADATA'] = $overrides;
    }

    return $cena;
}

function aplicar_voice_registry_roteiro(array $roteiro, array $elenco, string $idioma): array
{
    $roteiro['voice_registry'] = obter_voice_registry($elenco, $idioma);
    foreach ($roteiro['scenes'] ?? [] as $chave => $cena) {
        $roteiro['scenes'][$chave] = aplicar_voice_registry_cena($cena, $elenco, $idioma);
    }
    return $roteiro;
}

function voice_registry_prompt(array $elenco, string $idioma): string
{
    $registry = obter_voice_registry($elenco, $idioma);
    $linhas = [
        'VOICE REGISTRY - CANONICO E OBRIGATORIO:',
        "Language lock: {$registry['language_lock']}",
        'Use exatamente estes SPEAKER e VOICE_IDENTITY_LOCK. Nao crie vozes novas.',
        'Multi-speaker rule: ' . ($registry['multi_speaker_rule'] ?? ''),
    ];
    foreach ($registry['voices'] ?? [] as $nome => $voz) {
        $linhas[] = "- SPEAKER: {$nome}";
        $linhas[] = "  VOICE_IDENTITY_LOCK: {$voz['VOICE_IDENTITY_LOCK']}";
        $linhas[] = '  METADATA: ' . json_encode($voz['VOICE_OVERRIDE_METADATA'], JSON_UNESCAPED_UNICODE);
    }
    return implode("\n", $linhas);
}

function problemas_voice_registry(array $elenco, array $roteiro): array
{
    $problemas = [];
    $registry = $elenco['voice_registry'] ?? [];
    if (empty($registry['voices'])) {
        return ['Elenco sem voice_registry canonico.'];
    }

    $vozes_por_chave = _mapa_por_chave($registry);
    $cenas = $roteiro['scenes'] ?? [];

    foreach ($cenas as $chave => $cena) {
        $num = $cena['SCENE_NUMBER'] ?? $chave;
        $metadata = $cena['VOICE_OVERRIDE_METADATA'] ?? [];
        foreach ($cena['DIALOGUE_LINES'] ?? [] as $linha) {
            if (!is_array($linha) || !array_key_exists('TEXT', $linha)) {
                continue;
            }
            $speaker = $linha['SPEAKER'] ?? '';
            $voz = $vozes_por_chave[chave_speaker($speaker)] ?? null;
            if ($voz === null) {
                $problemas[] = "Cena {$num}: SPEAKER fora do elenco/registry: {$speaker}";
                continue;
            }
            if (($linha['SPEAKER'] ?? null) !== $voz['SPEAKER']) {
                $problemas[] = "Cena {$num}: SPEAKER deveria ser {$voz['SPEAKER']}, veio {$speaker}";
            }
            if (($linha['VOICE_IDENTITY_LOCK'] ?? null) !== $voz['VOICE_IDENTITY_LOCK']) {
                $problemas[] = "Cena {$num} ({$speaker}): VOICE_IDENTITY_LOCK diferente do registry";
            }
            if (($metadata[$voz['SPEAKER']] ?? null) !== $voz['VOICE_OVERRIDE_METADATA']) {
                $problemas[] = "Cena {$num} ({$speaker}): VOICE_OVERRIDE_METADATA diferente do registry";
            }
        }
    }

    return $problemas;
}