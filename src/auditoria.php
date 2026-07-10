<?php
declare(strict_types=1);

/**
 * Auditoria narrativa por LLM.
 *
 * Este passo nao altera o roteiro. Ele gera um relatorio curto de problemas
 * semanticos que validadores deterministicos dificilmente enxergam: salto causal,
 * contradicao, personagem mudando de objetivo ou voz emocional oscilando demais.
 */

require_once __DIR__ . '/api.php';
require_once __DIR__ . '/narrativa.php';
require_once __DIR__ . '/schema.php';
require_once __DIR__ . '/voz.php';

function _compactar_roteiro(array $roteiro): array
{
    $cenas = [];
    $scenes = $roteiro['scenes'] ?? [];

    uasort($scenes, function (array $a, array $b): int {
        return ($a['SCENE_NUMBER'] ?? 0) <=> ($b['SCENE_NUMBER'] ?? 0);
    });

    foreach ($scenes as $cena) {
        $falas = [];
        foreach ($cena['DIALOGUE_LINES'] ?? [] as $linha) {
            if (!array_key_exists('TEXT', $linha)) {
                continue;
            }
            $falas[] = [
                'SPEAKER' => $linha['SPEAKER'] ?? '',
                'TEXT' => $linha['TEXT'] ?? '',
                'VOICE_IDENTITY_LOCK' => $linha['VOICE_IDENTITY_LOCK'] ?? '',
            ];
        }

        $cenas[] = [
            'SCENE_NUMBER' => $cena['SCENE_NUMBER'] ?? null,
            'SCENE_ROLE' => $cena['SCENE_ROLE'] ?? null,
            'STORY_POSITION' => $cena['STORY_POSITION'] ?? null,
            'NARRATIVE_BEAT' => $cena['NARRATIVE_BEAT'] ?? null,
            'STORY_CONTRACT' => $cena['STORY_CONTRACT'] ?? [],
            'DIALOGUE_LINES' => $falas,
        ];
    }

    return [
        'title' => $roteiro['title'] ?? '',
        'story_summary' => $roteiro['story_summary'] ?? '',
        'scenes' => $cenas,
    ];
}

function auditar_roteiro(array $roteiro, array $sinopse, array $elenco, string $idioma): array
{
    $roteiroJson = json_encode(
        _compactar_roteiro($roteiro),
        JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT
    );

    $system = <<<PROMPT
Voce e um script doctor especialista em videos curtos seriados.

Audite SOMENTE:
- continuidade causal entre cenas;
- se cada cena cumpre seu STORY_CONTRACT;
- se os dialogos contam uma historia uniforme;
- se algum personagem parece mudar de voz, intencao ou personalidade sem motivo;
- se o cliffhanger final esta claro.

Nao critique visual, camera, cenario ou estilo 3D.
Nao reescreva o roteiro inteiro. Retorne apenas problemas acionaveis.

PROMPT
        . voice_registry_prompt($elenco, $idioma) . "\n\n"
        . story_contract_prompt($sinopse);

    $user = <<<PROMPT
Idioma: {$idioma}

ROTEIRO COMPACTO:
{$roteiroJson}

Retorne overall_status:
- "ok" se estiver coeso;
- "needs_revision" se houver saltos, contradicoes ou voz inconsistente.

Em problems, liste no maximo 12 problemas. Se estiver ok, problems deve ser [].
PROMPT;

    try {
        global $AUDITORIA_RESPONSE_FORMAT;
        $resposta = chamar_api($system, $user, $AUDITORIA_RESPONSE_FORMAT);
        return extrair_json($resposta);
    } catch (Throwable $erro) {
        return [
            'overall_status' => 'audit_failed',
            'problems' => [
                [
                    'scene_number' => 0,
                    'category' => 'audit_error',
                    'severity' => 'warning',
                    'issue' => 'Auditoria narrativa falhou: ' . $erro->getMessage(),
                    'suggested_fix' => 'Rode novamente ou revise validacao.json.',
                ],
            ],
        ];
    }
}