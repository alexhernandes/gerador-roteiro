"""
Correções automáticas no roteiro antes da validação.
Evita erros previsíveis sem nova chamada à API.
"""

import re

from dialogo import ajustar_timing_roteiro, lock_idioma_texto, PAUSA_PADRAO

_LIPSYNC_PADRAO = (
    "Clean, non-overlapping sequential dialogue. "
    "Active speaker lip-sync; listeners keep mouth closed with reactive expressions."
)
_VISUAL_SUFIXO = (
    " Cinematic 4K 3D animation. Hyper-realistic PBR textures. "
    "Volumetric lighting. Disney-Pixar style."
)
_PALAVRAS_VISUAL = re.compile(r"\b(4k|cinematic|volumetric|pbr|disney|pixar)\b", re.I)
_PALAVRAS_LIPSYNC = re.compile(
    r"\b(sequential dialogue|mouth closed|lip.?sync|non.?overlapping|speaker)\b",
    re.I,
)
_SUBSTITUICOES_SAFETY = [
    (re.compile(r"\bblood\b", re.I), "deep purple sticky grape juice"),
    (re.compile(r"\bsangue\b", re.I), "suco de uva roxo pegajoso"),
    (re.compile(r"\bpunch\b", re.I), "sudden aggressive arm gesture"),
    (re.compile(r"\bsoco\b", re.I), "gesto agressivo de braço"),
    (re.compile(r"\bkill\b", re.I), "defeat"),
    (re.compile(r"\bmatar\b", re.I), "derrotar"),
    (re.compile(r"\bsangre\b", re.I), "zumo de uva morado y espeso"),
    (re.compile(r"\bgolpear\b", re.I), "hacer un gesto amenazante"),
    (re.compile(r"\bblut\b", re.I), "klebriger dunkelvioletter Traubensaft"),
    (re.compile(r"\btöten\b", re.I), "besiegen"),
    (re.compile(r"\bschlagen\b", re.I), "drohend gestikulieren"),
    (re.compile(r"血(?:液|まみれ)?"), "濃い紫色のぶどうジュース"),
    (re.compile(r"殺す"), "倒す"),
    (re.compile(r"刺す"), "威圧する"),
]


def polir_roteiro(roteiro, elenco, idioma):
    lock = lock_idioma_texto(idioma)

    for cena in roteiro.get("scenes", {}).values():
        _polir_dialogos(cena, lock)
        _polir_acao(cena)
        _polir_visual(cena, elenco)
        _polir_safety(cena)

    ajustar_timing_roteiro(roteiro, idioma)
    return roteiro


def _aplicar_substituicoes(texto):
    if not texto:
        return texto
    for padrao, substituto in _SUBSTITUICOES_SAFETY:
        texto = padrao.sub(substituto, texto)
    return texto


def _polir_safety(cena):
    for campo in (
        "VISUAL_PROMPT",
        "ACTION_DIRECTION",
        "PHYSICAL_MOVEMENT",
        "OPENING_HOOK",
        "NARRATIVE_BEAT",
    ):
        if cena.get(campo):
            cena[campo] = _aplicar_substituicoes(cena[campo])

    for linha in cena.get("DIALOGUE_LINES", []):
        if "TEXT" in linha:
            linha["TEXT"] = _aplicar_substituicoes(linha["TEXT"])


def _polir_dialogos(cena, lock):
    lines = cena.get("DIALOGUE_LINES", [])
    if not lines:
        return

    novas = []
    for linha in lines:
        if "TEXT" in linha:
            if not linha.get("VOICE_IDENTITY_LOCK") or lock.lower() not in linha["VOICE_IDENTITY_LOCK"].lower():
                speaker = linha.get("SPEAKER", "SPEAKER")
                linha["VOICE_IDENTITY_LOCK"] = f"{speaker} voice. {lock}."
            novas.append(linha)
            novas.append({"PAUSE": PAUSA_PADRAO})
        elif "PAUSE" in linha:
            continue

    if novas and "PAUSE" in novas[-1]:
        novas.pop()

    cena["DIALOGUE_LINES"] = novas


def _polir_acao(cena):
    if not cena.get("HAS_DIALOGUE"):
        return

    for campo in ("ACTION_DIRECTION", "PHYSICAL_MOVEMENT"):
        texto = cena.get(campo, "")
        if texto and not _PALAVRAS_LIPSYNC.search(texto):
            cena[campo] = (texto.rstrip() + " " + _LIPSYNC_PADRAO).strip()


def _polir_visual(cena, elenco):
    visual = cena.get("VISUAL_PROMPT", "")
    if not visual:
        return

    if not _PALAVRAS_VISUAL.search(visual):
        cena["VISUAL_PROMPT"] = visual.rstrip() + _VISUAL_SUFIXO

    visual_upper = cena["VISUAL_PROMPT"].upper()
    speakers = list(dict.fromkeys(
        linha["SPEAKER"].upper()
        for linha in cena.get("DIALOGUE_LINES", [])
        if "SPEAKER" in linha
    ))
    faltando = [s for s in speakers if s and s not in visual_upper]
    if faltando:
        cena["VISUAL_PROMPT"] += " Characters in scene: " + ", ".join(faltando) + "."

    visual_upper = cena["VISUAL_PROMPT"].upper()
    presentes = []
    for personagem in elenco.get("cast", []):
        nome = str(personagem.get("name", "")).strip()
        if not nome:
            continue
        marcador = f"{nome}: PHYSICAL_DNA ["
        if (
            (nome.upper() in visual_upper or nome.upper() in speakers)
            and marcador.upper() not in visual_upper
        ):
            presentes.append(
                f"{nome}: PHYSICAL_DNA [{personagem.get('physical_dna', '')}]; "
                f"OUTFIT_DNA [{personagem.get('outfit_dna', '')}]"
            )
    if presentes:
        separador = " | " if "CANONICAL CHARACTER LOCKS:" in cena["VISUAL_PROMPT"] else " CANONICAL CHARACTER LOCKS: "
        cena["VISUAL_PROMPT"] += separador + " | ".join(presentes) + "."
