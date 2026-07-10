"""
Instruções de roteiro — narrativa, câmera e diálogo.
Complementa o prompt.txt com regras que garantem história coesa.
"""

from dialogo import (
    MIN_FALAS_POR_CENA,
    MAX_FALAS_POR_CENA,
    MIN_SEGUNDOS_FALA,
    MAX_SEGUNDOS_FALA,
    PAUSA_PADRAO,
    extrair_textos,
    lock_idioma_texto,
    normalizar_idioma,
    PALAVRAS_POR_SEGUNDO,
    limites_linha,
    unidade_timing,
)
from schema import DURACAO_CENA, NUM_CENAS, DURACAO_TOTAL


def bloco_narrativa(tema):
    return f"""
═══ NARRATIVA — HISTÓRIA COM COMEÇO, MEIO E FIM ═══

Tema: {tema}

ANTES de escrever as cenas, você DEVE planejar uma história curta completa de {DURACAO_TOTAL}s.
A história precisa fazer sentido do início ao fim — cada cena é consequência da anterior.

ESTRUTURA DE 3 ATOS (7 cenas):
  ATO 1 — INÍCIO (Cenas 1-2):
    • Cena 1: HOOK nos primeiros 2s — ação ou fala que prende imediatamente
    • Cena 2: Apresenta o conflito central e os personagens em oposição

  ATO 2 — MEIO (Cenas 3-5):
    • Cena 3: Tensão escala, segredos ou mentiras aparecem
    • Cena 4: PRIMEIRA REVIRAVOLTA — algo que muda tudo
    • Cena 5: Consequências da reviravolta, stakes mais altos

  ATO 3 — FIM (Cenas 6-7):
    • Cena 6: Clímax — confronto máximo, verdade explode
    • Cena 7: Cliffhanger chocante — gancho para Parte 2

REGRA DE CONTINUIDADE:
  • Cada cena começa EXATAMENTE onde a anterior parou (mesmo local, mesma tensão)
  • NARRATIVE_BEAT explica o que muda nesta cena em relação à anterior
  • Nenhuma cena pode ser "solta" — tudo conecta

REGRA DE DIÁLOGO NARRATIVO:
  • Cada fala em DIALOGUE_LINES > TEXT deve AVANÇAR a história
  • Proibido diálogo genérico ("oi", "tudo bem", frases sem contexto)
  • Cada TEXT deve: revelar informação NOVA, reagir ao que acabou de acontecer, ou criar tensão para a próxima cena
  • Os diálogos juntos devem contar a história — quem só ouve o áudio entende o enredo
  • Falas curtas, virais, diretas — mas sempre com propósito narrativo
"""


def bloco_dialogo_denso(idioma):
    codigo = normalizar_idioma(idioma)
    wps = PALAVRAS_POR_SEGUNDO.get(codigo, 3.2)
    min_palavras = int(MIN_SEGUNDOS_FALA * wps)
    max_palavras = int(MAX_SEGUNDOS_FALA * wps)
    min_linha, max_linha = limites_linha(idioma)
    unidade = unidade_timing(idioma)
    lock = lock_idioma_texto(idioma)

    return f"""
═══ DIÁLOGOS DENSOS — PREENCHER OS {DURACAO_CENA} SEGUNDOS ═══

Idioma OBRIGATÓRIO: {idioma} (LOCK: "{lock}")

CADA CENA DE {DURACAO_CENA}s PRECISA DE MUITO DIÁLOGO:
  • Mínimo {MIN_FALAS_POR_CENA} falas com TEXT (ideal {MAX_FALAS_POR_CENA})
  • Total de {min_palavras}-{max_palavras} {unidade} por cena
  • Duração do áudio: {MIN_SEGUNDOS_FALA}-{MAX_SEGUNDOS_FALA}s (quase todo o clipe)
  • Pausa {{"PAUSE": {PAUSA_PADRAO}}} entre CADA fala
  • Falas de {min_linha}-{max_linha} {unidade} — curtas e rápidas, estilo TikTok
  • PROIBIDO monólogo único longo — divida em trocas entre personagens

A HISTÓRIA É CONTADA PELO ÁUDIO:
  • Quem fecha os olhos e só ouve deve entender: quem traiu quem, o que aconteceu, o que vai acontecer
  • Cena 1: hook falado nos primeiros 2s
  • Cada cena responde à anterior e planta a próxima

ESTRUTURA DIALOGUE_LINES por cena (mínimo 7 itens no array):
  Fala 1 → PAUSE → Fala 2 → PAUSE → Fala 3 → PAUSE → Fala 4 → (PAUSE → Fala 5...)
"""


def bloco_camera():
    return f"""
═══ DIREÇÃO DE CÂMERA E AÇÃO (riqueza de detalhes) ═══

Cada cena de {DURACAO_CENA}s precisa de direção cinematográfica DETALHADA em 3 campos:

1. CAMERA_DIRECTION — trabalho de câmera com timeline dentro dos {DURACAO_CENA}s:
   • Tipo de shot: wide, medium, close-up, extreme close-up, over-the-shoulder, two-shot, POV
   • Movimento: dolly in/out, pan left/right, tilt up/down, tracking shot, handheld shake, static
   • Zoom: zoom in lento, zoom out rápido, rack focus (troca de foco entre personagens)
   • Ângulo: low angle, high angle, dutch angle, eye level
   • Efeitos: depth of field (bokeh), God rays, lens flare, slow motion
   • OBRIGATÓRIO: dividir os {DURACAO_CENA}s em blocos (ex: "0-3s: wide shot... 3-8s: dolly in... 8-12s: close-up... 12-{DURACAO_CENA}s: reveal")

   Exemplo:
   "0-3s: Wide shot estático do ambiente e entrada do protagonista.
    3-8s: Dolly in para close-up, rack focus no rival ao fundo.
    8-12s: Over-the-shoulder, zoom in na reação.
    12-{DURACAO_CENA}s: Pull back para two-shot e reveal."

2. PHYSICAL_MOVEMENT — ações físicas dos personagens:
   • Gestos, expressões faciais, deslocamento no espaço, interação com objetos
   • Quem move a boca (Active Speaker) vs quem reage em silêncio
   • Detalhes táteis: suor, tremor, lágrima, punho cerrado

3. ACTION_DIRECTION — direção geral da cena:
   • Ritmo emocional, transições, lip-sync protocol, som ambiente
   • Como a câmera e a ação se combinam para contar o beat narrativo
"""


def bloco_sinopse(idioma, tema):
    return bloco_narrativa(tema) + f"""

Você está criando a SINOPSE — o plano da história ANTES do roteiro detalhado.
Este arquivo é só para consulta/planejamento; agentes de produção NÃO geram mídia a partir dele.
Idioma dos diálogos: {idioma}.

Para cada uma das {NUM_CENAS} cenas, defina:
  • story_position: "início", "meio" ou "fim"
  • narrative_beat: o que acontece nesta cena (1-2 frases)
  • dialogue_intent: planeje 4-6 falas curtas que contam o beat da cena (liste: "1) ... 2) ... 3) ...")
  • camera_concept: conceito de câmera (shots e movimentos principais)
  • key_action: ação física principal

A story_summary deve contar a história inteira em 3-5 frases (começo, meio, fim).

CAMPOS act_1, act_2, act_3 — OBRIGATÓRIOS e DETALHADOS (mínimo 2 frases cada):
  • act_1: resumo narrativo das cenas 1-2 (hook + conflito inicial)
  • act_2: resumo narrativo das cenas 3-5 (tensão, reviravolta, consequências)
  • act_3: resumo narrativo das cenas 6-7 (clímax + cliffhanger)
  PROIBIDO usar só rótulos como "início (Cenas 1-2)" — escreva o que ACONTECE.

Os beats devem formar uma cadeia causal — cena N+1 só faz sentido depois da cena N.
"""


def bloco_roteiro(idioma, tema):
    return (
        bloco_narrativa(tema)
        + bloco_camera()
        + bloco_dialogo_denso(idioma)
        + f"""
═══ EXPANSÃO PARA ROTEIRO COMPLETO ═══

Use a SINOPSE fornecida como blueprint OBRIGATÓRIO. Não mude a história — expanda com detalhes.

Para cada cena preencha:
  • NARRATIVE_BEAT: copie/expanda o narrative_beat da sinopse
  • CAMERA_DIRECTION: expanda camera_concept em timeline detalhada de {DURACAO_CENA}s
  • PHYSICAL_MOVEMENT: expanda key_action com detalhes físicos
  • ACTION_DIRECTION: direção integrada (câmera + ação + emoção + lip-sync)
  • DIALOGUE_LINES > TEXT: transforme dialogue_intent em falas reais em {idioma}
  • OPENING_HOOK: na cena 1, descreva o que prende nos primeiros 2 segundos

CHECKLIST antes de entregar:
  ✓ História tem começo (cenas 1-2), meio (3-5) e fim (6-7)?
  ✓ Quem ouve só os diálogos entende a trama?
  ✓ Cada cena conecta com a anterior?
  ✓ CAMERA_DIRECTION tem timeline 0-{DURACAO_CENA}s com shots e movimentos?
  ✓ Cena 7 termina com cliffhanger?
"""
    )


def bloco_cena(beat, cena_anterior, idioma, tema):
    """Instruções focadas para gerar UMA cena por vez."""
    num = beat.get("scene_number", 1)
    wps = PALAVRAS_POR_SEGUNDO.get(normalizar_idioma(idioma), 3.2)
    min_palavras = int(MIN_SEGUNDOS_FALA * wps)
    max_palavras = int(MAX_SEGUNDOS_FALA * wps)
    min_linha, max_linha = limites_linha(idioma)
    unidade = unidade_timing(idioma)
    lock = lock_idioma_texto(idioma)

    continuidade = ""
    if cena_anterior:
        textos = extrair_textos(cena_anterior.get("DIALOGUE_LINES", []))
        ultima_fala = textos[-1] if textos else "N/A"
        continuidade = f"""
CONTINUIDADE OBRIGATÓRIA — use o JSON completo da cena anterior (no user prompt):
  Cena anterior: {cena_anterior.get('SCENE_NUMBER', num - 1)} — {cena_anterior.get('SCENE_NAME', '')}
  NARRATIVE_BEAT: {cena_anterior.get('NARRATIVE_BEAT', '')}
  Última fala: {ultima_fala}
Esta cena (Cena {num}) começa EXATAMENTE onde a anterior parou (mesmo local, mesma tensão).
"""

    return f"""
═══ GERAR APENAS A CENA {num} DE {NUM_CENAS} ═══

Tema: {tema} | Idioma: {idioma} (LOCK: "{lock}")

BLUEPRINT desta cena (da sinopse — siga fielmente):
  story_position: {beat.get('story_position', '')}
  narrative_beat: {beat.get('narrative_beat', '')}
  dialogue_intent: {beat.get('dialogue_intent', '')}
  camera_concept: {beat.get('camera_concept', '')}
  key_action: {beat.get('key_action', '')}
{continuidade}
DIÁLOGOS — LIMITES RÍGIDOS para caber em {DURACAO_CENA}s:
  • {MIN_FALAS_POR_CENA}-{MAX_FALAS_POR_CENA} falas curtas ({min_linha}-{max_linha} {unidade} cada)
  • Total: {min_palavras}-{max_palavras} {unidade} (~{MIN_SEGUNDOS_FALA}-{MAX_SEGUNDOS_FALA}s de áudio)
  • Pausa {{"PAUSE": {PAUSA_PADRAO}}} entre cada fala
  • Transforme dialogue_intent em falas reais — NÃO copie texto em inglês se idioma for {idioma}
  • PROIBIDO ultrapassar {max_palavras} palavras no total

CÂMERA: expanda camera_concept em timeline 0-{DURACAO_CENA}s com shots e movimentos.
"""
