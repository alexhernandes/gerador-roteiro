<?php
declare(strict_types=1);

require_once __DIR__ . '/schema.php';

const ROLES_POR_CENA = [
    1 => 'hook',
    2 => 'setup',
    3 => 'conflict',
    4 => 'twist',
    5 => 'escalation',
    6 => 'crisis',
    7 => 'cliffhanger',
];

const STOPWORDS = [
    'a', 'o', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'de', 'do', 'da', 'dos',
    'das', 'em', 'no', 'na', 'nos', 'nas', 'para', 'pra', 'por', 'com', 'sem',
    'que', 'e', 'ou', 'mas', 'se', 'ao', 'aos', 'pela', 'pelo', 'pelos', 'pelas',
    'the', 'and', 'or', 'but', 'with', 'from', 'into', 'that', 'this', 'for',
    'con', 'sin', 'los', 'las', 'una', 'uno', 'que', 'por', 'para',
];

function _resumo_curto(string $texto, int $limite = 180): string
{
    $texto = preg_replace('/\s+/u', ' ', trim((string) $texto));
    if (mb_strlen($texto) <= $limite) {
        return $texto;
    }
    return rtrim(mb_substr($texto, 0, $limite - 3)) . '...';
}

function _beats_ordenados(array $sinopse): array
{
    $beats = $sinopse['beats'] ?? [];
    usort($beats, fn(array $a, array $b): int => ($a['scene_number'] ?? 0) <=> ($b['scene_number'] ?? 0));
    return $beats;
}

function criar_story_contract(array $sinopse): array
{
    $beats = _beats_ordenados($sinopse);
    $cenas = [];
    $fatos_acumulados = [];

    foreach ($beats as $indice => $beat) {
        $num = $beat['scene_number'] ?? ($indice + 1);
        $anterior = $indice > 0 ? $beats[$indice - 1] : null;
        $proximo = ($indice + 1 < count($beats)) ? $beats[$indice + 1] : null;
        $narrative_beat = $beat['narrative_beat'] ?? '';
        $dialogue_intent = $beat['dialogue_intent'] ?? '';
        $fatos_antes = implode(' ', array_slice($fatos_acumulados, -3));
        if ($fatos_antes === '') {
            $fatos_antes = 'No prior facts. Establish the hook clearly.';
        }
        $fatos_acumulados[] = _resumo_curto($narrative_beat, 140);
        $fatos_depois = implode(' ', array_slice($fatos_acumulados, -4));

        $cenas[(string) $num] = [
            'scene_number' => $num,
            'scene_role' => ROLES_POR_CENA[$num] ?? 'scene',
            'story_position' => $beat['story_position'] ?? '',
            'must_start_from' => $anterior !== null
                ? _resumo_curto($anterior['narrative_beat'] ?? '')
                : 'Start immediately with the central hook.',
            'required_reveal' => _resumo_curto($narrative_beat),
            'known_facts_before' => _resumo_curto($fatos_antes, 260),
            'new_fact_added' => _resumo_curto($narrative_beat, 220),
            'open_loops_after' => _resumo_curto(
                $proximo !== null
                    ? ($proximo['narrative_beat'] ?? '')
                    : 'The final unresolved question must remain alive.',
                220
            ),
            'story_state_after' => _resumo_curto($fatos_depois, 320),
            'dialogue_must_cover' => _resumo_curto($dialogue_intent),
            'must_end_handing_off_to' => $proximo !== null
                ? _resumo_curto($proximo['narrative_beat'] ?? '')
                : 'End on an unresolved cliffhanger for Part 2.',
            'continuity_rule' => (
                'This scene must be a direct consequence of the previous scene '
                . 'and must create the exact pressure needed for the next scene.'
            ),
        ];
    }

    return [
        'version' => 'story-contract-v1',
        'title' => $sinopse['title'] ?? '',
        'dramatic_question' => _resumo_curto($sinopse['story_summary'] ?? '', 260),
        'act_1' => _resumo_curto($sinopse['act_1'] ?? '', 260),
        'act_2' => _resumo_curto($sinopse['act_2'] ?? '', 260),
        'act_3' => _resumo_curto($sinopse['act_3'] ?? '', 260),
        'rule' => (
            'Do not skip causal steps. Each scene must pay off the previous scene '
            . 'and plant the next one.'
        ),
        'scenes' => $cenas,
    ];
}

function aplicar_story_contract_sinopse(array $sinopse): array
{
    $sinopse['story_contract'] = criar_story_contract($sinopse);
    return $sinopse;
}

function aplicar_story_contract_roteiro(array $roteiro, array $sinopse): array
{
    $contract = $sinopse['story_contract'] ?? criar_story_contract($sinopse);
    $roteiro['story_contract'] = $contract;

    foreach ($roteiro['scenes'] ?? [] as $chave => $cena) {
        $num = (string) ($cena['SCENE_NUMBER'] ?? '');
        $scene_contract = $contract['scenes'][$num] ?? null;
        if ($scene_contract !== null) {
            $roteiro['scenes'][$chave]['STORY_CONTRACT'] = $scene_contract;
        }
    }

    return $roteiro;
}

function story_contract_prompt(array $sinopse, ?int $cena_numero = null): string
{
    $contract = $sinopse['story_contract'] ?? criar_story_contract($sinopse);
    $linhas = [
        'STORY CONTRACT - CANONICO E OBRIGATORIO:',
        'Dramatic question: ' . ($contract['dramatic_question'] ?? ''),
        'Act 1: ' . ($contract['act_1'] ?? ''),
        'Act 2: ' . ($contract['act_2'] ?? ''),
        'Act 3: ' . ($contract['act_3'] ?? ''),
        'Rule: ' . ($contract['rule'] ?? ''),
    ];

    $cenas = $contract['scenes'] ?? [];
    if ($cena_numero !== null) {
        $itens = [(string) $cena_numero => ($cenas[(string) $cena_numero] ?? [])];
    } else {
        $itens = $cenas;
        uksort($itens, fn(string $a, string $b): int => (int) $a <=> (int) $b);
    }

    foreach ($itens as $num => $dados) {
        $linhas[] = "Scene {$num} contract:";
        $linhas[] = '  role: ' . ($dados['scene_role'] ?? '');
        $linhas[] = '  must_start_from: ' . ($dados['must_start_from'] ?? '');
        $linhas[] = '  known_facts_before: ' . ($dados['known_facts_before'] ?? '');
        $linhas[] = '  required_reveal: ' . ($dados['required_reveal'] ?? '');
        $linhas[] = '  new_fact_added: ' . ($dados['new_fact_added'] ?? '');
        $linhas[] = '  dialogue_must_cover: ' . ($dados['dialogue_must_cover'] ?? '');
        $linhas[] = '  must_end_handing_off_to: ' . ($dados['must_end_handing_off_to'] ?? '');
        $linhas[] = '  open_loops_after: ' . ($dados['open_loops_after'] ?? '');
        $linhas[] = '  story_state_after: ' . ($dados['story_state_after'] ?? '');
    }

    return implode("\n", $linhas);
}

function _tokens(string $texto): array
{
    if (!preg_match_all('/[A-Za-zÀ-ÿ0-9_]{3,}/u', strtolower((string) $texto), $matches)) {
        return [];
    }
    $tokens = [];
    foreach ($matches[0] as $palavra) {
        if (!in_array($palavra, STOPWORDS, true)) {
            $tokens[$palavra] = true;
        }
    }
    return array_keys($tokens);
}

function _similaridade(string $a, string $b): float
{
    $ta = array_flip(_tokens($a));
    $tb = array_flip(_tokens($b));
    if ($ta === [] || $tb === []) {
        return 0.0;
    }
    $intersecao = count(array_intersect_key($ta, $tb));
    return $intersecao / max(1, min(count($ta), count($tb)));
}

function _texto_cena(array $cena): string
{
    $falas = [];
    foreach ($cena['DIALOGUE_LINES'] ?? [] as $linha) {
        if (is_array($linha) && array_key_exists('TEXT', $linha)) {
            $falas[] = $linha['TEXT'];
        }
    }
    return implode(' ', [
        $cena['SCENE_NAME'] ?? '',
        $cena['NARRATIVE_BEAT'] ?? '',
        $cena['ACTION_DIRECTION'] ?? '',
        implode(' ', $falas),
    ]);
}

function problemas_continuidade(array $roteiro, array $sinopse): array
{
    $problemas = [];
    $contract = $roteiro['story_contract'] ?? ($sinopse['story_contract'] ?? null);
    if ($contract === null) {
        return ['Roteiro sem story_contract canonico.'];
    }

    $cenas = $roteiro['scenes'] ?? [];
    if (count($cenas) !== NUM_CENAS) {
        return $problemas;
    }

    $beats = [];
    foreach ($sinopse['beats'] ?? [] as $b) {
        $beats[$b['scene_number'] ?? 0] = $b;
    }

    $cenas_ordenadas = array_values($cenas);
    usort($cenas_ordenadas, fn(array $a, array $b): int => ($a['SCENE_NUMBER'] ?? 0) <=> ($b['SCENE_NUMBER'] ?? 0));

    foreach ($cenas_ordenadas as $cena) {
        $num = $cena['SCENE_NUMBER'] ?? null;
        $scene_contract = $cena['STORY_CONTRACT'] ?? ($contract['scenes'][(string) $num] ?? null);
        if ($scene_contract === null) {
            $problemas[] = "Cena {$num}: sem STORY_CONTRACT.";
            continue;
        }

        $beat = $beats[$num] ?? [];
        $alvo = implode(' ', [
            $beat['narrative_beat'] ?? '',
            $beat['dialogue_intent'] ?? '',
            $scene_contract['required_reveal'] ?? '',
        ]);
        $sim = _similaridade(_texto_cena($cena), $alvo);
        if ($sim < 0.10) {
            $problemas[] = sprintf(
                'Cena %s: parece distante do beat planejado (similaridade %.2f).',
                $num,
                $sim
            );
        }
    }

    for ($i = 1, $total = count($cenas_ordenadas); $i < $total; $i++) {
        $anterior = $cenas_ordenadas[$i - 1];
        $atual = $cenas_ordenadas[$i];
        $num = $atual['SCENE_NUMBER'] ?? null;
        $prev_texto = $anterior['NARRATIVE_BEAT'] ?? '';
        $start_rule = ($atual['STORY_CONTRACT'] ?? [])['must_start_from'] ?? '';
        if ($prev_texto !== '' && $start_rule !== '' && _similaridade($prev_texto, $start_rule) < 0.10) {
            $problemas[] = "Cena {$num}: contrato de inicio nao referencia bem a cena anterior.";
        }
    }

    return $problemas;
}