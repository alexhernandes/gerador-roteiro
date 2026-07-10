<?php

declare(strict_types=1);

/**
 * Gera elenco + sinopse + roteiro em JSONs separados.
 * Entrada via formulário web ($dados) — sem equivalente a entrada.py.
 */

require_once __DIR__ . '/paths.php';
require_once __DIR__ . '/config.php';
require_once __DIR__ . '/schema.php';
require_once __DIR__ . '/api.php';
require_once __DIR__ . '/auditoria.php';
require_once __DIR__ . '/corrigir_dialogos.php';
require_once __DIR__ . '/dialogo.php';
require_once __DIR__ . '/enriquecer.php';
require_once __DIR__ . '/instrucoes_roteiro.php';
require_once __DIR__ . '/narrativa.php';
require_once __DIR__ . '/salvar.php';
require_once __DIR__ . '/universos.php';
require_once __DIR__ . '/voz.php';
require_once __DIR__ . '/validar.php';

const MIN_TAMANHO_ATO = 30;

const PROMPT_ATUAL_OVERRIDE = <<<'PROMPT_OVERRIDE'


PROTOCOLO ATUAL DO SISTEMA - SUBSTITUI QUALQUER REGRA ANTIGA CONFLITANTE:
- DIALOGUE_LINES > TEXT deve estar 100% no idioma escolhido pelo usuario.
- Prompts visuais podem usar termos tecnicos em ingles, mas o audio falado nao.
- Toda voz deve copiar o VOICE REGISTRY canonico. Nunca invente voz por cena.
- Toda cena deve seguir o STORY CONTRACT canonico. Nunca pule causalidade.
- O UNIVERSO SELECIONADO substitui qualquer regra antiga de personagens apenas como frutas.
- Use character_type como campo generico do tipo de personagem.
- Agentes de video/render devem trabalhar 1 cena por vez. Nunca processe 3 cenas por lote.
- Todo agente deve fazer pos-verificacao de idioma, voz, audio, continuidade e locks visuais antes de finalizar.
PROMPT_OVERRIDE;

/** @var callable|null */
$_gerar_roteiro_on_progress = null;

function _definir_progresso(?callable $onProgress): void
{
    global $_gerar_roteiro_on_progress;
    $_gerar_roteiro_on_progress = $onProgress;
}

function _emitir(string $type, string $message, ?array $extra = null): void
{
    global $_gerar_roteiro_on_progress;

    if ($_gerar_roteiro_on_progress !== null) {
        ($_gerar_roteiro_on_progress)($type, $message, $extra);

        return;
    }

    echo $message;
    if (!str_ends_with($message, "\n")) {
        echo "\n";
    }
}

function carregar_prompt(): string
{
    $caminho = ROOT_DIR . DIRECTORY_SEPARATOR . 'prompt.txt';
    $conteudo = file_get_contents($caminho);
    if ($conteudo === false) {
        throw new RuntimeException("Não foi possível ler o prompt: {$caminho}");
    }

    return $conteudo;
}

function prompt_base(): string
{
    static $base = null;
    if ($base === null) {
        $base = carregar_prompt() . PROMPT_ATUAL_OVERRIDE;
    }

    return $base;
}

function _bloco_idioma(string $idioma): string
{
    $lock = lock_idioma_texto($idioma);

    return <<<BLOCO


IDIOMA INQUEBRÁVEL — REJEIÇÃO AUTOMÁTICA SE VIOLAR:
- Idioma escolhido pelo usuário: {$idioma}
- 100% dos TEXT em {$idioma}. Nenhuma palavra em inglês/outro idioma.
- VOICE_IDENTITY_LOCK: "{$lock}" em TODAS as falas sem exceção.
- Áudio = SOMENTE DIALOGUE_LINES > TEXT.
BLOCO;
}

function gerar_elenco(string $idioma, string $tema, string $aspect_ratio, string $universo): array
{
    $universo_prompt = carregar_prompt_universo($universo);
    $system = prompt_base() . <<<SYSTEM


Crie APENAS o ELENCO.
Tema: {$tema}. Formato: {$aspect_ratio}. Resolução: {RESOLUCAO}. language: "{$idioma}".

UNIVERSO SELECIONADO: {LABEL}
{$universo_prompt}

- Crie personagens coerentes com o UNIVERSO SELECIONADO
- character_type deve descrever o tipo de personagem dentro desse universo
- physical_dna e outfit_dna completos
- 2 a 5 personagens com papéis claros na trama (protagonista, antagonista, aliado, etc.)
- ai_image_task por personagem
SYSTEM;

    $system = str_replace(
        ['{RESOLUCAO}', '{LABEL}'],
        [RESOLUCAO, label_universo($universo)],
        $system
    );

    $user = 'Elenco para vídeo de ' . DURACAO_TOTAL . "s sobre: {$tema}";

    _emitir('step', '  [1/4] Gerando elenco...');
    $resposta = chamar_api($system, $user, ELENCO_RESPONSE_FORMAT);

    return enriquecer_elenco(extrair_json($resposta), $aspect_ratio, $idioma);
}

function traduzir_tema(string $tema, string $idioma): string
{
    $system = <<<SYSTEM

Voce traduz temas de historias curtas para o idioma alvo.

Regras:
- Traduza o tema para: {$idioma}.
- Preserve nomes proprios, marcas e nomes de personagens.
- Nao expanda a ideia, nao adicione detalhes novos.
- Retorne apenas o JSON solicitado.
SYSTEM;

    $user = <<<USER

Tema original:
{$tema}

Idioma alvo:
{$idioma}
USER;

    $resposta = chamar_api($system, $user, TRADUCAO_TEMA_RESPONSE_FORMAT);
    $dados = extrair_json($resposta);
    if (!is_array($dados)) {
        throw new RuntimeException('Resposta de tradução inválida.');
    }

    $traduzido = trim((string) ($dados['translated_theme'] ?? ''));
    if ($traduzido === '') {
        throw new InvalidArgumentException('Traducao do tema veio vazia.');
    }

    return $traduzido;
}

function _sinopse_corrompida(array $sinopse): bool
{
    return array_key_exists('idea', $sinopse)
        || (array_key_exists('cast', $sinopse) && !array_key_exists('beats', $sinopse))
        || (array_key_exists('scenes', $sinopse) && !array_key_exists('beats', $sinopse));
}

function _sinopse_valida(array $sinopse): bool
{
    if (_sinopse_corrompida($sinopse)) {
        return false;
    }

    $beats = $sinopse['beats'] ?? [];
    $atos_ok = true;
    foreach (['act_1', 'act_2', 'act_3'] as $campo) {
        if (strlen(trim((string) ($sinopse[$campo] ?? ''))) < MIN_TAMANHO_ATO) {
            $atos_ok = false;
            break;
        }
    }

    return strlen((string) ($sinopse['story_summary'] ?? '')) > 30
        && count($beats) >= NUM_CENAS
        && $atos_ok;
}

function gerar_sinopse(
    string $idioma,
    string $tema,
    array $elenco,
    string $universo,
    int $tentativa = 1
): array {
    $elenco_json = json_encode($elenco, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    $universo_prompt = carregar_prompt_universo($universo);

    $reforco = '';
    if ($tentativa > 1) {
        $reforco = <<<'REFORCO'

CORREÇÃO: a sinopse anterior veio incompleta.
Preencha OBRIGATORIAMENTE: story_summary, act_1, act_2, act_3 (mínimo 2 frases cada) e beats com 7 itens.
NÃO use rótulos curtos como "início (Cenas 1-2)" — descreva o que acontece em cada ato.
REFORCO;
    }

    $system = prompt_base() . bloco_sinopse($idioma, $tema) . <<<SYSTEM


UNIVERSO SELECIONADO: {LABEL}
{$universo_prompt}

Elenco disponível — use estes personagens na história:
{$elenco_json}

Crie a sinopse com EXATAMENTE {NUM_CENAS} beats no array "beats".
theme = "{$tema}", language = "{$idioma}".
{$reforco}
SYSTEM;

    $system = str_replace(
        ['{LABEL}', '{NUM_CENAS}'],
        [label_universo($universo), (string) NUM_CENAS],
        $system
    );

    $user = <<<USER

Planeje a história completa de {DURACAO_TOTAL}s ({NUM_CENAS} cenas) sobre: {$tema}
Começo, meio e fim claros. Reviravoltas. 4-6 falas planejadas por cena no dialogue_intent.
USER;

    $user = str_replace(
        ['{DURACAO_TOTAL}', '{NUM_CENAS}'],
        [(string) DURACAO_TOTAL, (string) NUM_CENAS],
        $user
    );

    $msg_tentativa = $tentativa > 1 ? " (tentativa {$tentativa})" : '';
    _emitir('step', "  [2/4] Planejando sinopse (história)...{$msg_tentativa}");
    $resposta = chamar_api($system, $user, SINOPSE_RESPONSE_FORMAT);
    $sinopse = extrair_json($resposta);
    if (!is_array($sinopse)) {
        throw new RuntimeException('Sinopse retornada em formato inválido.');
    }

    if (!_sinopse_valida($sinopse) && $tentativa < 3) {
        _emitir('log', "  !! Sinopse incompleta. Tentando de novo...\n");
        return gerar_sinopse($idioma, $tema, $elenco, $universo, $tentativa + 1);
    }

    if (!_sinopse_valida($sinopse)) {
        throw new RuntimeException(
            'Sinopse veio incompleta da API (sem beats ou story_summary). Tente rodar de novo.'
        );
    }

    return enriquecer_sinopse($sinopse, $idioma);
}

/** Monta roteiro.json juntando manualmente as cenas das 7 chamadas à API. */
function juntar_cenas_em_roteiro(array $cenas, array $sinopse): array
{
    $titulo = trim(str_replace('Sinopse - ', '', (string) ($sinopse['title'] ?? '')));
    if ($titulo === '') {
        $titulo = 'Roteiro';
    }

    ksort($cenas);
    $scenes = [];
    foreach ($cenas as $num => $cena) {
        $scenes["SCENE_{$num}"] = $cena;
    }

    return [
        'title' => $titulo,
        'story_summary' => $sinopse['story_summary'] ?? '',
        'scenes' => $scenes,
    ];
}

function _nomes_elenco(array $elenco): array
{
    $nomes = [];
    foreach ($elenco['cast'] ?? [] as $personagem) {
        $nome = $personagem['name'] ?? null;
        if ($nome !== null && $nome !== '') {
            $nomes[] = $nome;
        }
    }

    return $nomes;
}

function _falas_fallback_beat(array $beat, array $speakers, string $idioma): array
{
    $falas = dialogos_de_intent((string) ($beat['dialogue_intent'] ?? ''), $speakers, $idioma);
    if ($falas !== []) {
        return $falas;
    }

    $speaker_a = $speakers[0] ?? 'PERSONAGEM_1';
    $speaker_b = $speakers[1] ?? $speaker_a;
    $narrativa = trim((string) ($beat['narrative_beat'] ?? 'A verdade aparece agora'));
    $trecho = trim(explode('.', $narrativa)[0]);
    if (strlen($trecho) > 70) {
        $trecho = substr($trecho, 0, 70);
    }
    $trecho = $trecho !== '' ? $trecho : 'A verdade apareceu';

    $lock = lock_idioma_texto($idioma);
    $codigo = normalizar_idioma($idioma);
    $fallback = [
        'pt' => [
            'Entao explica isso agora.',
            'Nao da mais pra esconder.',
            'Se for verdade, acabou.',
        ],
        'en' => [
            'Then explain this right now.',
            'We cannot hide this anymore.',
            'If this is true, we are done.',
        ],
        'es' => [
            'Entonces explica esto ahora.',
            'Ya no podemos esconderlo.',
            'Si esto es verdad, se acabo.',
        ],
        'de' => [
            'Dann erklär das sofort.',
            'Wir können das nicht mehr verstecken.',
            'Wenn das wahr ist, ist alles vorbei.',
        ],
    ][$codigo] ?? [
        'Entao explica isso agora.',
        'Nao da mais pra esconder.',
        'Se for verdade, acabou.',
    ];

    return [
        [
            'SPEAKER' => $speaker_a,
            'VOICE_IDENTITY_LOCK' => "{$speaker_a} voice. {$lock}.",
            'TEXT' => $trecho,
        ],
        ['PAUSE' => 0.2],
        [
            'SPEAKER' => $speaker_b,
            'VOICE_IDENTITY_LOCK' => "{$speaker_b} voice. {$lock}.",
            'TEXT' => $fallback[0],
        ],
        ['PAUSE' => 0.2],
        [
            'SPEAKER' => $speaker_a,
            'VOICE_IDENTITY_LOCK' => "{$speaker_a} voice. {$lock}.",
            'TEXT' => $fallback[1],
        ],
        ['PAUSE' => 0.2],
        [
            'SPEAKER' => $speaker_b,
            'VOICE_IDENTITY_LOCK' => "{$speaker_b} voice. {$lock}.",
            'TEXT' => $fallback[2],
        ],
    ];
}

function _fallback_dialogos_globais(array $sinopse, array $elenco, string $idioma): array
{
    $speakers = _nomes_elenco($elenco);
    $beats = $sinopse['beats'] ?? [];
    usort($beats, static fn (array $a, array $b): int => ($a['scene_number'] ?? 0) <=> ($b['scene_number'] ?? 0));

    $cenas = [];
    foreach ($beats as $beat) {
        $num = (int) ($beat['scene_number'] ?? count($cenas) + 1);
        $cena = [
            'SCENE_NUMBER' => $num,
            'DIALOGUE_LINES' => _falas_fallback_beat($beat, $speakers, $idioma),
            'DELIVERY_STYLE' => 'Fast viral drama delivery, emotionally direct, sequential non-overlapping speech.',
            'VOICE_OVERRIDE_METADATA' => [],
        ];
        ajustar_timing_cena($cena, $idioma);
        aplicar_voice_registry_cena($cena, $elenco, $idioma);
        $cenas["SCENE_{$num}"] = $cena;
    }

    return ['scenes' => $cenas];
}

function gerar_dialogos_globais(
    string $idioma,
    string $tema,
    array $elenco,
    array $sinopse,
    string $universo
): array {
    $sinopse_json = json_encode($sinopse, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    $universo_prompt = carregar_prompt_universo($universo);

    $system = prompt_base() . _bloco_idioma($idioma) . <<<SYSTEM


Voce e o dialoguista principal. Sua tarefa e escrever o AUDIO COMPLETO das {NUM_CENAS} cenas
antes dos prompts visuais, para que a historia fique uniforme.

{VOICE_REGISTRY}

{STORY_CONTRACT}

UNIVERSO SELECIONADO: {LABEL}
{$universo_prompt}

REGRAS:
- Use SOMENTE os SPEAKER existentes no VOICE REGISTRY.
- Copie o VOICE_IDENTITY_LOCK exato do VOICE REGISTRY em cada fala.
- Cada cena deve ter 4-6 falas curtas, com PAUSE 0.2 entre falas.
- Cada cena deve cobrir required_reveal e terminar plantando must_end_handing_off_to.
- Nao use filler. Cada fala revela, reage ou empurra para a proxima cena.
- Retorne SCENE_NUMBER, DIALOGUE_LINES, DELIVERY_STYLE, VOICE_OVERRIDE_METADATA por cena.
SYSTEM;

    $system = str_replace(
        [
            '{NUM_CENAS}',
            '{VOICE_REGISTRY}',
            '{STORY_CONTRACT}',
            '{LABEL}',
        ],
        [
            (string) NUM_CENAS,
            voice_registry_prompt($elenco, $idioma),
            story_contract_prompt($sinopse),
            label_universo($universo),
        ],
        $system
    );

    $user = <<<USER

Tema: {$tema}
Idioma: {$idioma}

SINOPSE E STORY CONTRACT:
{$sinopse_json}

Crie os dialogos globais das {NUM_CENAS} cenas. Esse audio sera congelado e usado nas cenas visuais.
USER;

    $user = str_replace('{NUM_CENAS}', (string) NUM_CENAS, $user);

    _emitir('log', '       Criando dialogos globais canonicos...');
    try {
        $resposta = chamar_api($system, $user, CORRECAO_DIALOGOS_RESPONSE_FORMAT);
        $dialogos = extrair_json($resposta);
        if (!is_array($dialogos)) {
            throw new RuntimeException('Diálogos globais em formato inválido.');
        }
    } catch (Throwable $erro) {
        _emitir('log', "       !! Dialogos globais falharam ({$erro->getMessage()}). Usando fallback da sinopse.");
        $dialogos = _fallback_dialogos_globais($sinopse, $elenco, $idioma);
    }

    foreach ($dialogos['scenes'] ?? [] as $cena) {
        if (!is_array($cena)) {
            continue;
        }
        aplicar_voice_registry_cena($cena, $elenco, $idioma);
        ajustar_timing_cena($cena, $idioma);
        aplicar_voice_registry_cena($cena, $elenco, $idioma);
    }

    return $dialogos;
}

function gerar_cena(
    string $idioma,
    string $tema,
    string $aspect_ratio,
    array $elenco,
    array $sinopse,
    array $beat,
    string $universo,
    ?array $cena_anterior = null,
    ?array $dialogo_planejado = null
): array {
    $num = (int) ($beat['scene_number'] ?? 1);
    $elenco_json = json_encode($elenco, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    $sinopse_json = json_encode($sinopse, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    $dialogo_planejado_json = json_encode($dialogo_planejado ?? [], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    $universo_prompt = carregar_prompt_universo($universo);
    $cena_anterior_json = '';
    if ($cena_anterior !== null) {
        $cena_anterior_json = json_encode($cena_anterior, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    }

    $scene_role = ROLES_POR_CENA[$num] ?? 'scene';

    $system = prompt_base() . _bloco_idioma($idioma) . bloco_cena($beat, $cena_anterior, $idioma, $tema) . <<<SYSTEM


FORMATO: {$aspect_ratio}, {RESOLUCAO}, cena de {DURACAO_CENA}s.
language = "{$idioma}".

CONTEXTO FIXO EM TODA CHAMADA:
  1) SINOPSE COMPLETA (blueprint — não mude a história)
  2) CENA ANTERIOR completa (quando existir — mantenha continuidade)

SINOPSE:
{$sinopse_json}

{STORY_CONTRACT}

{VOICE_REGISTRY}

UNIVERSO SELECIONADO: {LABEL}
{$universo_prompt}

ELENCO (nomes exatos em SPEAKER e VISUAL_PROMPT):
{$elenco_json}

DIALOGOS CONGELADOS DESTA CENA (copie exatamente; nao reescreva):
{$dialogo_planejado_json}

Campos obrigatórios desta cena:
- SCENE_NUMBER: {$num}
- SCENE_NAME: título curto da cena
- SCENE_ROLE: "{$scene_role}"
- STORY_POSITION: "{STORY_POSITION}"
- NARRATIVE_BEAT, OPENING_HOOK (cena 1), CAMERA_DIRECTION, PHYSICAL_MOVEMENT
- ACTION_DIRECTION, VISUAL_PROMPT, DIALOGUE_LINES, DELIVERY_STYLE
- HAS_DIALOGUE: true, AUDIO_SPEAKER, AUDIO_TARGET, AUDIO_TIMING_CONTROLS
- VOICE_OVERRIDE_METADATA copiado do VOICE REGISTRY (um entry por SPEAKER)

Retorne APENAS o JSON desta cena — não gere as outras cenas.
SYSTEM;

    $system = str_replace(
        [
            '{RESOLUCAO}',
            '{DURACAO_CENA}',
            '{STORY_CONTRACT}',
            '{VOICE_REGISTRY}',
            '{LABEL}',
            '{STORY_POSITION}',
        ],
        [
            RESOLUCAO,
            (string) DURACAO_CENA,
            story_contract_prompt($sinopse, $num),
            voice_registry_prompt($elenco, $idioma),
            label_universo($universo),
            (string) ($beat['story_position'] ?? ''),
        ],
        $system
    );

    $contexto_anterior = '';
    if ($cena_anterior_json !== '') {
        $contexto_anterior = <<<CTX


CENA ANTERIOR (JSON completo — esta cena começa onde a anterior parou):
{$cena_anterior_json}
CTX;
    }

    $user = <<<USER

Gere SOMENTE a Cena {$num} de {NUM_CENAS}.
Tema: {$tema}. Idioma: {$idioma}.
Use o beat {$num} da sinopse.
{$contexto_anterior}
Mantenha continuidade: mesmos personagens, mesmo local/tensão, consequência direta da cena anterior.
Use os DIALOGOS CONGELADOS exatamente como fonte de audio. A cena visual deve servir ao audio, nao trocar o audio.
USER;

    $user = str_replace('{NUM_CENAS}', (string) NUM_CENAS, $user);

    $resposta = chamar_api($system, $user, CENA_RESPONSE_FORMAT);
    $cena = extrair_json($resposta);
    if (!is_array($cena)) {
        throw new RuntimeException("Cena {$num} retornada em formato inválido.");
    }

    $cena['SCENE_NUMBER'] = $num;
    if (!array_key_exists('SCENE_ROLE', $cena)) {
        $cena['SCENE_ROLE'] = $scene_role;
    }
    if (!array_key_exists('STORY_POSITION', $cena)) {
        $cena['STORY_POSITION'] = (string) ($beat['story_position'] ?? '');
    }
    if (!array_key_exists('NARRATIVE_BEAT', $cena)) {
        $cena['NARRATIVE_BEAT'] = (string) ($beat['narrative_beat'] ?? '');
    }

    if ($dialogo_planejado !== null) {
        $cena['DIALOGUE_LINES'] = $dialogo_planejado['DIALOGUE_LINES'] ?? $cena['DIALOGUE_LINES'] ?? [];
        $cena['DELIVERY_STYLE'] = $dialogo_planejado['DELIVERY_STYLE'] ?? $cena['DELIVERY_STYLE'] ?? '';
        $cena['VOICE_OVERRIDE_METADATA'] = $dialogo_planejado['VOICE_OVERRIDE_METADATA']
            ?? $cena['VOICE_OVERRIDE_METADATA']
            ?? [];
    }

    aplicar_voice_registry_cena($cena, $elenco, $idioma);

    return $cena;
}

function gerar_roteiro_cenas(
    string $idioma,
    string $tema,
    string $aspect_ratio,
    array $elenco,
    array $sinopse,
    string $universo,
    array $opcoes_agente,
    ?string $sessao = null
): array {
    $beats = $sinopse['beats'] ?? [];
    usort($beats, static fn (array $a, array $b): int => ($a['scene_number'] ?? 0) <=> ($b['scene_number'] ?? 0));

    $cenas = [];
    $cena_anterior = null;

    _emitir('step', '  [3/4] Gerando roteiro — ' . NUM_CENAS . ' chamadas à API (1 cena cada)...');
    $dialogos_globais = gerar_dialogos_globais($idioma, $tema, $elenco, $sinopse, $universo);
    if ($sessao !== null) {
        salvar($sessao, 'dialogos_globais', $dialogos_globais, true);
        _emitir('log', '       -> log/dialogos_globais.json salvo');
    }

    foreach ($beats as $beat) {
        $num = (int) ($beat['scene_number'] ?? count($cenas) + 1);
        _emitir('log', "       Chamada {$num}/" . NUM_CENAS . " → Cena {$num}...");
        $dialogo_planejado = $dialogos_globais['scenes']["SCENE_{$num}"] ?? null;
        $cena = gerar_cena(
            $idioma,
            $tema,
            $aspect_ratio,
            $elenco,
            $sinopse,
            $beat,
            $universo,
            $cena_anterior,
            is_array($dialogo_planejado) ? $dialogo_planejado : null
        );
        $cenas[$num] = $cena;
        $cena_anterior = $cena;

        if ($sessao !== null) {
            $nome_arquivo = sprintf('cena_%02d', $num);
            salvar($sessao, $nome_arquivo, $cena, true);
            _emitir('log', "       -> log/{$nome_arquivo}.json salva");
        }
    }

    _emitir('log', '       Juntando as 7 cenas em roteiro.json...');
    $roteiro = juntar_cenas_em_roteiro($cenas, $sinopse);

    return enriquecer_roteiro_com_sinopse(
        $roteiro,
        $aspect_ratio,
        $idioma,
        $elenco,
        $sinopse,
        $opcoes_agente
    );
}

function mostrar_resumo(array $elenco, array $sinopse, array $roteiro): void
{
    _emitir('log', "\n" . str_repeat('=', 50));
    _emitir('log', '  TITULO:    ' . ($roteiro['title'] ?? $elenco['title'] ?? '?'));
    _emitir('log', '  TEMA:      ' . ($elenco['theme'] ?? '?'));
    _emitir('log', '  IDIOMA:    ' . ($elenco['language'] ?? '?'));
    _emitir(
        'log',
        '  DURAÇÃO:   ' . DURACAO_TOTAL . 's (' . NUM_CENAS . ' x ' . DURACAO_CENA . 's)'
    );
    _emitir('log', str_repeat('=', 50));

    $historia = (string) ($sinopse['story_summary'] ?? $roteiro['story_summary'] ?? '?');
    _emitir('log', "\n  HISTÓRIA: " . substr($historia, 0, 120) . '...');

    _emitir('log', "\n--- ELENCO ---\n");
    foreach ($elenco['cast'] ?? [] as $personagem) {
        $tipo = $personagem['character_type'] ?? $personagem['fruit_type'] ?? 'personagem';
        _emitir('log', "  * {$personagem['name']} ({$tipo})");
    }

    _emitir('log', "\n--- CENAS ---\n");
    $cenas = $roteiro['scenes'] ?? [];
    $chaves = array_keys($cenas);
    usort(
        $chaves,
        static fn (string $a, string $b): int => ($cenas[$a]['SCENE_NUMBER'] ?? 0) <=> ($cenas[$b]['SCENE_NUMBER'] ?? 0)
    );

    foreach ($chaves as $chave) {
        $c = $cenas[$chave];
        $timing = $c['DIALOGUE_TIMING'] ?? [];
        $textos = [];
        foreach ($c['DIALOGUE_LINES'] ?? [] as $linha) {
            if (is_array($linha) && array_key_exists('TEXT', $linha)) {
                $textos[] = $linha['TEXT'];
            }
        }

        _emitir(
            'log',
            '  Cena ' . ($c['SCENE_NUMBER'] ?? '?') . ': '
            . ($c['SCENE_NAME'] ?? '') . ' [' . ($c['STORY_POSITION'] ?? '?') . ']'
        );
        $beat = (string) ($c['NARRATIVE_BEAT'] ?? '?');
        _emitir('log', '    Beat: ' . substr($beat, 0, 70) . '...');

        if ($textos !== []) {
            $fala = $textos[0];
            $fala_exibida = strlen($fala) > 50 ? '"' . substr($fala, 0, 50) . '..."' : "\"{$fala}\"";
            _emitir('log', "    Fala: {$fala_exibida}");
        }

        $camera = (string) ($c['CAMERA_DIRECTION'] ?? '?');
        _emitir('log', '    Câmera: ' . substr($camera, 0, 70) . '...');
        _emitir(
            'log',
            '    Diálogo: ' . ($timing['word_count'] ?? '?') . ' palavras, ~'
            . ($timing['total_dialogue_seconds'] ?? '?') . 's'
        );
    }
}

function _salvar_passo(string $sessao, string $nome, mixed $dados, bool $em_log = false): string
{
    $arquivo = salvar($sessao, $nome, $dados, $em_log);
    $pasta = $em_log ? 'log/' : '';
    _emitir('log', "  -> Salvo: {$pasta}{$nome}.json\n");

    return $arquivo;
}

function abrir_pasta_saida(string $sessao): void
{
    if (!OPEN_OUTPUT_FOLDER_ON_FINISH) {
        return;
    }

    try {
        if (PHP_OS_FAMILY === 'Windows') {
            $comando = 'explorer ' . escapeshellarg($sessao);
            pclose(popen($comando, 'r'));
        } elseif (PHP_OS_FAMILY === 'Darwin') {
            exec('open ' . escapeshellarg($sessao));
        } else {
            exec('xdg-open ' . escapeshellarg($sessao));
        }
        _emitir('log', "  Pasta aberta: {$sessao}\n");
    } catch (Throwable $erro) {
        _emitir('log', "  Nao consegui abrir a pasta automaticamente: {$erro->getMessage()}\n");
    }
}

/**
 * Gera roteiro completo a partir dos dados do formulário web.
 *
 * @param array{
 *     idioma: string,
 *     aspect_ratio: string,
 *     universo: string,
 *     tema: string,
 *     agent_confirm_between_steps?: bool,
 *     agent_videos_per_step?: int
 * } $dados
 * @param callable(string, string, ?array): void|null $onProgress
 * @return array{
 *     sessao: string,
 *     elenco: array,
 *     sinopse: array,
 *     roteiro: array,
 *     relatorio: array,
 *     auditoria: array
 * }
 */
function gerar_roteiro(array $dados, ?callable $onProgress = null): array
{
    _definir_progresso($onProgress);

    $idioma = (string) $dados['idioma'];
    $tema_original = (string) $dados['tema'];
    $aspect_ratio = (string) $dados['aspect_ratio'];
    $universo = (string) $dados['universo'];
    $opcoes_agente = [
        'confirm_between_steps' => (bool) ($dados['agent_confirm_between_steps'] ?? AGENT_CONFIRM_BETWEEN_STEPS),
        'videos_per_step' => (int) ($dados['agent_videos_per_step'] ?? AGENT_VIDEOS_PER_STEP),
    ];

    $sessao = criar_sessao();

    try {
        _emitir('log', "\nTraduzindo tema para {$idioma}...");
        $tema = traduzir_tema($tema_original, $idioma);
        _salvar_passo($sessao, 'tema', [
            'idioma' => $idioma,
            'tema_original' => $tema_original,
            'tema_traduzido' => $tema,
            'universo' => $universo,
            'universo_label' => label_universo($universo),
            'opcoes_agente' => $opcoes_agente,
        ], true);

        _emitir(
            'log',
            "\nIdioma: {$idioma} | Formato: {$aspect_ratio} | " . DURACAO_TOTAL . 's (' . NUM_CENAS . ' cenas)'
        );
        _emitir('log', 'Modelo: ' . MODEL . ' (xAI)');
        _emitir('log', 'Universo: ' . label_universo($universo));
        _emitir('log', "Tema original: {$tema_original}");
        _emitir('log', "Tema traduzido: {$tema}");

        $agente_msg = $opcoes_agente['videos_per_step'] . ' vídeo(s) por passo; '
            . ($opcoes_agente['confirm_between_steps'] ? 'pergunta antes de seguir' : 'segue automaticamente');
        _emitir('log', "Agente: {$agente_msg}");
        _emitir('log', "Pasta: {$sessao}\nGerando... aguarde.\n");

        $elenco = gerar_elenco($idioma, $tema, $aspect_ratio, $universo);
        _salvar_passo($sessao, 'elenco', $elenco);

        $sinopse = gerar_sinopse($idioma, $tema, $elenco, $universo);
        _salvar_passo($sessao, 'sinopse', $sinopse);

        $roteiro = gerar_roteiro_cenas(
            $idioma,
            $tema,
            $aspect_ratio,
            $elenco,
            $sinopse,
            $universo,
            $opcoes_agente,
            $sessao
        );
        _salvar_passo($sessao, 'roteiro_rascunho', $roteiro, true);

        $enriquecerFn = static function (array $r) use (
            $aspect_ratio,
            $idioma,
            $elenco,
            $sinopse,
            $opcoes_agente
        ): array {
            return enriquecer_roteiro_com_sinopse(
                $r,
                $aspect_ratio,
                $idioma,
                $elenco,
                $sinopse,
                $opcoes_agente
            );
        };

        $roteiro = corrigir_ate_validar($roteiro, $sinopse, $idioma, $enriquecerFn, 3, $elenco);
        _salvar_passo($sessao, 'roteiro', $roteiro);

        $auditoria = auditar_roteiro($roteiro, $sinopse, $elenco, $idioma);
        _salvar_passo($sessao, 'auditoria_narrativa', $auditoria, true);
    } catch (Throwable $erro) {
        _emitir('error', "\nErro durante a geração. Arquivos já prontos estão em: {$sessao}/");
        throw $erro;
    }

    $relatorio = validar_tudo($elenco, $roteiro, $sinopse);

    imprimir_relatorio($relatorio);
    _salvar_passo($sessao, 'validacao', $relatorio, true);

    mostrar_resumo($elenco, $sinopse, $roteiro);
    _emitir('done', "  Entrega: {$sessao}/ (elenco, sinopse, roteiro)");
    _emitir('done', "  Logs:    {$sessao}/log/\n");
    abrir_pasta_saida($sessao);

    return [
        'sessao' => $sessao,
        'elenco' => $elenco,
        'sinopse' => $sinopse,
        'roteiro' => $roteiro,
        'relatorio' => $relatorio,
        'auditoria' => $auditoria,
    ];
}