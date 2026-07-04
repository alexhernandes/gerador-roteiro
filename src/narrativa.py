"""
Contrato narrativo para manter as 7 cenas conectadas.

A sinopse continua sendo gerada pela API, mas este modulo cria um contrato
deterministico em cima dela: cada cena ganha origem, revelacao obrigatoria e
handoff para a proxima. Esse contrato vira contexto de prompt e validacao.
"""

import re

from schema import NUM_CENAS


ROLES_POR_CENA = {
    1: "hook",
    2: "setup",
    3: "conflict",
    4: "twist",
    5: "escalation",
    6: "crisis",
    7: "cliffhanger",
}


STOPWORDS = {
    "a", "o", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos",
    "das", "em", "no", "na", "nos", "nas", "para", "pra", "por", "com", "sem",
    "que", "e", "ou", "mas", "se", "ao", "aos", "pela", "pelo", "pelos", "pelas",
    "the", "and", "or", "but", "with", "from", "into", "that", "this", "for",
    "con", "sin", "los", "las", "una", "uno", "que", "por", "para",
}


def _resumo_curto(texto, limite=180):
    texto = " ".join(str(texto or "").split())
    if len(texto) <= limite:
        return texto
    return texto[: limite - 3].rstrip() + "..."


def _beats_ordenados(sinopse):
    return sorted(
        sinopse.get("beats", []),
        key=lambda b: b.get("scene_number", 0),
    )


def criar_story_contract(sinopse):
    beats = _beats_ordenados(sinopse)
    cenas = {}

    for indice, beat in enumerate(beats):
        num = beat.get("scene_number", indice + 1)
        anterior = beats[indice - 1] if indice > 0 else None
        proximo = beats[indice + 1] if indice + 1 < len(beats) else None
        narrative_beat = beat.get("narrative_beat", "")
        dialogue_intent = beat.get("dialogue_intent", "")

        cenas[str(num)] = {
            "scene_number": num,
            "scene_role": ROLES_POR_CENA.get(num, "scene"),
            "story_position": beat.get("story_position", ""),
            "must_start_from": (
                _resumo_curto(anterior.get("narrative_beat", ""))
                if anterior else "Start immediately with the central hook."
            ),
            "required_reveal": _resumo_curto(narrative_beat),
            "dialogue_must_cover": _resumo_curto(dialogue_intent),
            "must_end_handing_off_to": (
                _resumo_curto(proximo.get("narrative_beat", ""))
                if proximo else "End on an unresolved cliffhanger for Part 2."
            ),
            "continuity_rule": (
                "This scene must be a direct consequence of the previous scene "
                "and must create the exact pressure needed for the next scene."
            ),
        }

    return {
        "version": "story-contract-v1",
        "title": sinopse.get("title", ""),
        "dramatic_question": _resumo_curto(sinopse.get("story_summary", ""), 260),
        "act_1": _resumo_curto(sinopse.get("act_1", ""), 260),
        "act_2": _resumo_curto(sinopse.get("act_2", ""), 260),
        "act_3": _resumo_curto(sinopse.get("act_3", ""), 260),
        "rule": (
            "Do not skip causal steps. Each scene must pay off the previous scene "
            "and plant the next one."
        ),
        "scenes": cenas,
    }


def aplicar_story_contract_sinopse(sinopse):
    sinopse["story_contract"] = criar_story_contract(sinopse)
    return sinopse


def aplicar_story_contract_roteiro(roteiro, sinopse):
    contract = sinopse.get("story_contract") or criar_story_contract(sinopse)
    roteiro["story_contract"] = contract

    for cena in roteiro.get("scenes", {}).values():
        num = str(cena.get("SCENE_NUMBER", ""))
        scene_contract = contract.get("scenes", {}).get(num)
        if scene_contract:
            cena["STORY_CONTRACT"] = scene_contract

    return roteiro


def story_contract_prompt(sinopse, cena_numero=None):
    contract = sinopse.get("story_contract") or criar_story_contract(sinopse)
    linhas = [
        "STORY CONTRACT - CANONICO E OBRIGATORIO:",
        f"Dramatic question: {contract.get('dramatic_question', '')}",
        f"Act 1: {contract.get('act_1', '')}",
        f"Act 2: {contract.get('act_2', '')}",
        f"Act 3: {contract.get('act_3', '')}",
        f"Rule: {contract.get('rule', '')}",
    ]

    cenas = contract.get("scenes", {})
    if cena_numero is not None:
        itens = [(str(cena_numero), cenas.get(str(cena_numero), {}))]
    else:
        itens = sorted(cenas.items(), key=lambda item: int(item[0]))

    for num, dados in itens:
        linhas.append(f"Scene {num} contract:")
        linhas.append(f"  role: {dados.get('scene_role', '')}")
        linhas.append(f"  must_start_from: {dados.get('must_start_from', '')}")
        linhas.append(f"  required_reveal: {dados.get('required_reveal', '')}")
        linhas.append(f"  dialogue_must_cover: {dados.get('dialogue_must_cover', '')}")
        linhas.append(f"  must_end_handing_off_to: {dados.get('must_end_handing_off_to', '')}")

    return "\n".join(linhas)


def _tokens(texto):
    palavras = re.findall(r"[A-Za-zÀ-ÿ0-9_]{3,}", str(texto or "").lower())
    return {p for p in palavras if p not in STOPWORDS}


def _similaridade(a, b):
    ta = _tokens(a)
    tb = _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, min(len(ta), len(tb)))


def _texto_cena(cena):
    falas = " ".join(
        linha.get("TEXT", "")
        for linha in cena.get("DIALOGUE_LINES", [])
        if "TEXT" in linha
    )
    return " ".join([
        cena.get("SCENE_NAME", ""),
        cena.get("NARRATIVE_BEAT", ""),
        cena.get("ACTION_DIRECTION", ""),
        falas,
    ])


def problemas_continuidade(roteiro, sinopse):
    problemas = []
    contract = roteiro.get("story_contract") or sinopse.get("story_contract")
    if not contract:
        return ["Roteiro sem story_contract canonico."]

    cenas = roteiro.get("scenes", {})
    if len(cenas) != NUM_CENAS:
        return problemas

    beats = {
        b.get("scene_number"): b
        for b in sinopse.get("beats", [])
    }

    cenas_ordenadas = sorted(cenas.values(), key=lambda c: c.get("SCENE_NUMBER", 0))
    for cena in cenas_ordenadas:
        num = cena.get("SCENE_NUMBER")
        scene_contract = cena.get("STORY_CONTRACT") or contract.get("scenes", {}).get(str(num))
        if not scene_contract:
            problemas.append(f"Cena {num}: sem STORY_CONTRACT.")
            continue

        beat = beats.get(num, {})
        alvo = " ".join([
            beat.get("narrative_beat", ""),
            beat.get("dialogue_intent", ""),
            scene_contract.get("required_reveal", ""),
        ])
        sim = _similaridade(_texto_cena(cena), alvo)
        if sim < 0.10:
            problemas.append(
                f"Cena {num}: parece distante do beat planejado (similaridade {sim:.2f})."
            )

    for anterior, atual in zip(cenas_ordenadas, cenas_ordenadas[1:]):
        num = atual.get("SCENE_NUMBER")
        prev_texto = anterior.get("NARRATIVE_BEAT", "")
        start_rule = (atual.get("STORY_CONTRACT") or {}).get("must_start_from", "")
        if prev_texto and start_rule and _similaridade(prev_texto, start_rule) < 0.10:
            problemas.append(f"Cena {num}: contrato de inicio nao referencia bem a cena anterior.")

    return problemas
