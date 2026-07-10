<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/src/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => 'Método não permitido. Use POST.'], JSON_UNESCAPED_UNICODE);
    exit;
}

$input = json_decode(file_get_contents('php://input') ?: '{}', true);
if (!is_array($input)) {
    http_response_code(400);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => 'JSON inválido.'], JSON_UNESCAPED_UNICODE);
    exit;
}

$idioma = trim((string) ($input['idioma'] ?? DEFAULT_LANGUAGE));
$aspectRatio = trim((string) ($input['aspect_ratio'] ?? DEFAULT_ASPECT_RATIO));
$universo = normalizar_universo($input['universo'] ?? DEFAULT_UNIVERSE);
$tema = trim((string) ($input['tema'] ?? ''));
$confirm = (bool) ($input['agent_confirm_between_steps'] ?? AGENT_CONFIRM_BETWEEN_STEPS);
$videosPerStep = max(1, (int) ($input['agent_videos_per_step'] ?? AGENT_VIDEOS_PER_STEP));

if ($tema === '') {
    $tema = DEFAULT_THEME;
}

$dados = [
    'idioma' => $idioma,
    'aspect_ratio' => $aspectRatio,
    'universo' => $universo,
    'tema' => $tema,
    'agent_confirm_between_steps' => $confirm,
    'agent_videos_per_step' => $videosPerStep,
];

header('Content-Type: application/x-ndjson; charset=utf-8');
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');

@ini_set('output_buffering', 'off');
@ini_set('zlib.output_compression', '0');
while (ob_get_level() > 0) {
    ob_end_flush();
}
ob_implicit_flush(true);
set_time_limit(0);

$enviar = static function (string $type, string $message, ?array $extra = null): void {
    $linha = json_encode(
        array_filter([
            'type' => $type,
            'message' => $message,
            'extra' => $extra,
            'time' => date('H:i:s'),
        ], static fn ($v) => $v !== null),
        JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR
    );
    echo $linha . "\n";
    flush();
};

try {
    $resultado = gerar_roteiro($dados, $enviar);

    $sessao = $resultado['sessao'];
    $sessaoRel = str_replace(ROOT_DIR . DIRECTORY_SEPARATOR, '', $sessao);
    $sessaoRel = str_replace('\\', '/', $sessaoRel);

    $enviar('done', 'Roteiro gerado com sucesso.', [
        'sessao' => $sessaoRel,
        'titulo' => $resultado['roteiro']['title'] ?? '',
        'resumo' => $resultado['relatorio']['resumo'] ?? [],
        'elenco' => array_map(
            static fn (array $p) => [
                'name' => $p['name'] ?? '',
                'type' => $p['character_type'] ?? $p['fruit_type'] ?? '',
            ],
            $resultado['elenco']['cast'] ?? []
        ),
        'historia' => mb_substr($resultado['sinopse']['story_summary'] ?? '', 0, 200),
        'arquivos' => [
            'elenco.json',
            'sinopse.json',
            'roteiro.json',
            'log/validacao.json',
        ],
    ]);
} catch (Throwable $e) {
    $enviar('error', $e->getMessage());
    http_response_code(500);
}