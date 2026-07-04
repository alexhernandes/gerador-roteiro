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
    lock_idioma_texto,
    normalizar_idioma,
    PALAVRAS_POR_SEGUNDO,
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
    lock = lock_idioma_texto(idioma)

    return f"""
═══ DIÁLOGOS DENSOS — PREENCHER OS {DURACAO_CENA} SEGUNDOS ═══

Idioma OBRIGATÓRIO: {idioma} (LOCK: "{lock}")

CADA CENA DE {DURACAO_CENA}s PRECISA DE MUITO DIÁLOGO:
  • Mínimo {MIN_FALAS_POR_CENA} falas com TEXT (ideal {MAX_FALAS_POR_CENA})
  • Total de {min_palavras}-{max_palavras} palavras por cena
  • Duração do áudio: {MIN_SEGUNDOS_FALA}-{MAX_SEGUNDOS_FALA}s (quase todo o clipe)
  • Pausa {{"PAUSE": {PAUSA_PADRAO}}} entre CADA fala
  • Falas de 4-12 palavras — curtas e rápidas, estilo TikTok
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

1. CAMERA_DIRECTION — trabalho de câmera com timeline dentro dos 10s:
   • Tipo de shot: wide, medium, close-up, extreme close-up, over-the-shoulder, two-shot, POV
   • Movimento: dolly in/out, pan left/right, tilt up/down, tracking shot, handheld shake, static
   • Zoom: zoom in lento, zoom out rápido, rack focus (troca de foco entre personagens)
   • Ângulo: low angle, high angle, dutch angle, eye level
   • Efeitos: depth of field (bokeh), God rays, lens flare, slow motion
   • OBRIGATÓRIO: dividir os 10s em blocos (ex: "0-2s: wide shot... 2-6s: dolly in para close-up... 6-10s: zoom out reveal")

   Exemplo:
   "0-2s: Wide shot estático do ambiente, Morango entra pelo canto direito.
    2-5s: Dolly in rápido para close-up no rosto dela, rack focus para Laranja ao fundo.
    5-8s: Over-the-shoulder de Morango, zoom in no olhar traidor de Laranja.
    8-10s: Pull back para two-shot, câmera treme levemente (handheld) no choque."

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
Idioma dos diálogos: {idioma}.

Para cada uma das {NUM_CENAS} cenas, defina:
  • story_position: "início", "meio" ou "fim"
  • narrative_beat: o que acontece nesta cena (1-2 frases)
  • dialogue_intent: planeje 4-6 falas curtas que contam o beat da cena (liste: "1) ... 2) ... 3) ...")
  • camera_concept: conceito de câmera (shots e movimentos principais)
  • key_action: ação física principal

A story_summary deve contar a história inteira em 3-5 frases (começo, meio, fim).
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
  • CAMERA_DIRECTION: expanda camera_concept em timeline detalhada de 10s
  • PHYSICAL_MOVEMENT: expanda key_action com detalhes físicos
  • ACTION_DIRECTION: direção integrada (câmera + ação + emoção + lip-sync)
  • DIALOGUE_LINES > TEXT: transforme dialogue_intent em falas reais em {idioma}
  • OPENING_HOOK: na cena 1, descreva o que prende nos primeiros 2 segundos

CHECKLIST antes de entregar:
  ✓ História tem começo (cenas 1-2), meio (3-5) e fim (6-7)?
  ✓ Quem ouve só os diálogos entende a trama?
  ✓ Cada cena conecta com a anterior?
  ✓ CAMERA_DIRECTION tem timeline 0-10s com shots e movimentos?
  ✓ Cena 7 termina com cliffhanger?
"""
    )