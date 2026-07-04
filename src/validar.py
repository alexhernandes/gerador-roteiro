"""
Valida elenco e roteiro contra as regras do prompt.txt.
Gera relatório com explicações e exemplos.
"""

import re
from dialogo import (
    calcular_timing,
    extrair_textos,
    normalizar_idioma,
    texto_no_idioma,
    voice_lock_valido,
    MIN_FALAS_POR_CENA,
    MIN_SEGUNDOS_FALA,
    MAX_SEGUNDOS_FALA,
)
from regras import REGRAS
from schema import RESOLUCAO, DURACAO_CENA, NUM_CENAS, DURACAO_TOTAL

PALAVRAS_SANGUE = re.compile(r"\b(blood|sangue|bleeding|hemorrag)\b", re.I)
PALAVRAS_AGRESSAO = re.compile(
    r"\b(punch|stab|shoot|kill|murder|matar|soc[oou]|esfaquear|esfaque|agredir|agressão|agressao)\b",
    re.I,
)
PALAVRAS_CLIFFHANGER = re.compile(
    r"\b(wait|espera|part 2|parte 2|to be continued|continua|who is|quem é|what is|o que|"
    r"did you hear|ouviu|you won.t believe|não vai acreditar|no way|impossible|"
    r"impossível|plot twist|reviravolta)\b",
    re.I,
)
PALAVRAS_VISUAL = re.compile(r"\b(4k|cinematic|volumetric|pbr|disney|pixar)\b", re.I)
PALAVRAS_LIPSYNC = re.compile(
    r"\b(sequential dialogue|mouth closed|lip.?sync|non.?overlapping|speaker|boca fechada)\b",
    re.I,
)
PALAVRAS_TRAMA = re.compile(
    r"\b(twist|reviravolta|traição|traicao|betrayal|shock|reveal|revelação|revelacao|"
    r"conflito|conflict|crise|crisis|escalat|tensão|tensao|segredo|secret|mentira|lie|"
    r"plot|gancho|hook|cliffhanger|virada)\b",
    re.I,
)
PALAVRAS_HOOK = re.compile(
    r"\b(hook|gancho|grita|explod|impact|choc|revel|confront|entra|começa|comeca|"
    r"olha|escuta|pera|espera|não|nao|what|quem|como|por que|why|soco|corre)\b",
    re.I,
)
PALAVRAS_CAMERA = re.compile(
    r"\b(wide|close.?up|medium|dolly|pan|tilt|zoom|tracking|handheld|shot|angle|"
    r"rack focus|bokeh|over-the-shoulder|two-shot|pov|pull back|push in|crane|"
    r"0-\d+s|\d-\d+s)\b",
    re.I,
)
PALAVRAS_FILLER = re.compile(
    r"^(oi|olá|ola|hey|hi|tudo bem|e aí|e ai|bom dia|good morning|ok|okay|sim|não|nao)\s*[!.?]*$",
    re.I,
)

ROLES_TRAMA = {"hook", "setup", "conflict", "twist", "escalation", "crisis", "cliffhanger"}


def _resultado(regra, ok, detalhe=""):
    if isinstance(detalhe, re.Match):
        detalhe = detalhe.group(0)
    else:
        detalhe = str(detalhe) if detalhe is not None else ""
    return {
        "id": regra["id"],
        "nome": regra["nome"],
        "severidade": regra["severidade"],
        "ok": bool(ok),
        "detalhe": detalhe,
        "explicacao": regra["explicacao"],
        "exemplo": regra["exemplo"],
    }


def _buscar_regra(regra_id):
    return next(r for r in REGRAS if r["id"] == regra_id)


def validar_elenco(elenco):
    resultados = []
    cast = elenco.get("cast", [])

    regra = _buscar_regra("antropomorfico")
    if not cast:
        resultados.append(_resultado(regra, False, "Elenco vazio."))
        return resultados

    for personagem in cast:
        nome = personagem.get("name", "?")
        fisico = personagem.get("physical_dna", "")

        if len(fisico) < 30:
            resultados.append(_resultado(regra, False, f"{nome}: physical_dna muito curto."))
        elif re.search(r"\bhuman skin\b", fisico, re.I):
            resultados.append(_resultado(regra, False, f"{nome}: menciona pele humana."))
        else:
            resultados.append(_resultado(regra, True, f"{nome}: DNA físico OK."))

        regra_outfit = _buscar_regra("outfit_dna")
        roupa = personagem.get("outfit_dna", "")
        if len(roupa) < 30:
            resultados.append(_resultado(regra_outfit, False, f"{nome}: outfit_dna incompleto."))
        else:
            resultados.append(_resultado(regra_outfit, True, f"{nome}: roupa descrita."))

    regra_ia = _buscar_regra("instrucoes_ia")
    if elenco.get("ai_instructions", {}).get("task"):
        resultados.append(_resultado(regra_ia, True, "ai_instructions presente."))
    else:
        resultados.append(_resultado(regra_ia, False, "Falta ai_instructions."))

    for personagem in cast:
        nome = personagem.get("name", "?")
        ok = bool(personagem.get("ai_image_task"))
        resultados.append(_resultado(
            regra_ia, ok,
            f"{nome}: ai_image_task {'OK' if ok else 'ausente'}.",
        ))

    regra_res = _buscar_regra("resolucao_480p")
    ok = elenco.get("resolution") == RESOLUCAO
    resultados.append(_resultado(
        regra_res, ok,
        f"Resolução {RESOLUCAO}." if ok else f"Esperado {RESOLUCAO}, veio {elenco.get('resolution')}.",
    ))

    return resultados


def validar_sinopse(sinopse):
    resultados = []
    regra = _buscar_regra("narrativa_coesa")

    if not sinopse:
        return resultados

    summary = sinopse.get("story_summary", "")
    if len(summary) < 50:
        resultados.append(_resultado(regra, False, "story_summary muito curto ou ausente."))
    else:
        resultados.append(_resultado(regra, True, f"Sinopse: {summary[:80]}..."))

    for campo in ("act_1", "act_2", "act_3"):
        texto = sinopse.get(campo, "").strip()
        if len(texto) < 30:
            resultados.append(_resultado(
                regra, False,
                f"Sinopse: {campo} incompleto ({len(texto)} chars, mínimo 30).",
            ))
        else:
            resultados.append(_resultado(regra, True, f"Sinopse: {campo} OK."))

    beats = sinopse.get("beats", [])
    if len(beats) != NUM_CENAS:
        resultados.append(_resultado(
            regra, False,
            f"Sinopse: {len(beats)} beats (esperado {NUM_CENAS}).",
        ))

    for beat in beats:
        num = beat.get("scene_number", "?")
        if len(beat.get("narrative_beat", "")) < 15:
            resultados.append(_resultado(regra, False, f"Beat {num}: narrative_beat vazio."))
        if len(beat.get("dialogue_intent", "")) < 15:
            resultados.append(_resultado(
                _buscar_regra("dialogo_narrativo"), False,
                f"Beat {num}: dialogue_intent vazio.",
            ))

    return resultados


def validar_roteiro(roteiro, elenco, sinopse=None):
    resultados = []
    cenas = roteiro.get("scenes", {})
    cast = elenco.get("cast", [])
    nomes = [p.get("name", "").upper() for p in cast if p.get("name")]
    idioma = roteiro.get("language", elenco.get("language", "Português"))

    if not cenas:
        resultados.append({
            "id": "cenas",
            "nome": "Cenas",
            "severidade": "erro",
            "ok": False,
            "detalhe": "Nenhuma cena encontrada.",
            "explicacao": f"O roteiro precisa ter {NUM_CENAS} cenas.",
            "exemplo": "SCENE_1 até SCENE_7",
        })
        return resultados

    regra_sete = _buscar_regra("sete_cenas")
    regra_idioma = _buscar_regra("idioma_rigido")
    regra_source = _buscar_regra("dialogue_source")
    regra_densidade = _buscar_regra("densidade_dialogo")
    regra_hook = _buscar_regra("hook_2_segundos")
    regra_trama = _buscar_regra("trama_complexa")
    regra_char = _buscar_regra("character_lock")
    regra_visual = _buscar_regra("visual_motor")
    regra_safety = _buscar_regra("safety_filter")
    regra_lipsync = _buscar_regra("active_speaker")
    regra_pausa = _buscar_regra("pausa_dialogo")
    regra_solda = _buscar_regra("solda_textil")
    regra_cliff = _buscar_regra("cliffhanger")
    regra_duracao = _buscar_regra("duracao_cena")
    regra_ia = _buscar_regra("instrucoes_ia")
    regra_res = _buscar_regra("resolucao_480p")
    regra_narrativa = _buscar_regra("narrativa_coesa")
    regra_dialogo_narr = _buscar_regra("dialogo_narrativo")
    regra_camera = _buscar_regra("camera_detalhada")

    # Story summary
    summary = roteiro.get("story_summary", "")
    if len(summary) < 50:
        resultados.append(_resultado(regra_narrativa, False, "story_summary ausente no roteiro."))
    else:
        resultados.append(_resultado(regra_narrativa, True, f"História: {summary[:80]}..."))

    # 7 cenas / 70s
    qtd = len(cenas)
    ok_sete = qtd == NUM_CENAS
    resultados.append(_resultado(
        regra_sete, ok_sete,
        f"{qtd} cenas (esperado {NUM_CENAS}). Total: {qtd * DURACAO_CENA}s / {DURACAO_TOTAL}s.",
    ))

    if roteiro.get("total_scenes") != NUM_CENAS:
        resultados.append(_resultado(regra_sete, False, f"total_scenes deve ser {NUM_CENAS}."))
    if roteiro.get("total_duration_seconds") != DURACAO_TOTAL:
        resultados.append(_resultado(
            regra_sete, False,
            f"total_duration_seconds deve ser {DURACAO_TOTAL}.",
        ))

    # Instruções IA
    ai = roteiro.get("ai_instructions", {})
    if ai.get("task") and "DIALOGUE_LINES" in ai.get("audio_source", ""):
        resultados.append(_resultado(regra_source, True, "audio_source aponta para DIALOGUE_LINES > TEXT."))
    elif ai.get("task"):
        resultados.append(_resultado(regra_source, False, "audio_source não menciona DIALOGUE_LINES > TEXT."))
    else:
        resultados.append(_resultado(regra_ia, False, "Falta ai_instructions."))

    cenas_ordenadas = sorted(cenas.items(), key=lambda x: x[1].get("SCENE_NUMBER", 0))
    roles_encontrados = set()
    cenas_com_trama = 0

    for chave, cena in cenas_ordenadas:
        visual = cena.get("VISUAL_PROMPT", "")
        acao = cena.get("ACTION_DIRECTION", "") + " " + cena.get("PHYSICAL_MOVEMENT", "")
        num = cena.get("SCENE_NUMBER", chave)
        dialogue_lines = cena.get("DIALOGUE_LINES", [])

        # Duração
        if cena.get("DURATION_SECONDS") != DURACAO_CENA:
            resultados.append(_resultado(
                regra_duracao, False,
                f"Cena {num}: DURATION_SECONDS={cena.get('DURATION_SECONDS')}, esperado {DURACAO_CENA}.",
            ))
        else:
            resultados.append(_resultado(
                regra_duracao, True,
                f"Cena {num}: {cena.get('TIMESTAMP', '?')} ({DURACAO_CENA}s).",
            ))

        # SCENE_ROLE para trama
        role = cena.get("SCENE_ROLE", "").lower()
        if role:
            roles_encontrados.add(role)
        if PALAVRAS_TRAMA.search(
            cena.get("SCENE_NAME", "") + " " + role + " " + _dialogos_texto(cena)
        ):
            cenas_com_trama += 1

        # Hook cena 1
        if num == 1:
            hook = cena.get("OPENING_HOOK", "")
            primeiro_texto = extrair_textos(dialogue_lines)
            hook_ok = (
                len(hook) > 15
                and (PALAVRAS_HOOK.search(hook) or PALAVRAS_HOOK.search(primeiro_texto[0] if primeiro_texto else ""))
            )
            resultados.append(_resultado(
                regra_hook, hook_ok,
                f"SCENE_1 OPENING_HOOK: {hook[:80]}{'...' if len(hook) > 80 else ''}" if hook else "SCENE_1 sem OPENING_HOOK.",
            ))

        # NARRATIVE_BEAT
        beat = cena.get("NARRATIVE_BEAT", "")
        if len(beat) < 20:
            resultados.append(_resultado(
                regra_narrativa, False,
                f"Cena {num}: NARRATIVE_BEAT vazio ou genérico.",
            ))
        else:
            resultados.append(_resultado(
                regra_narrativa, True,
                f"Cena {num}: {beat[:60]}...",
            ))

        # STORY_POSITION
        pos = cena.get("STORY_POSITION", "").lower()
        if num <= 2 and "início" not in pos and "inicio" not in pos:
            resultados.append(_resultado(
                regra_narrativa, False,
                f"Cena {num}: STORY_POSITION deveria ser 'início'.",
            ))
        elif 3 <= num <= 5 and "meio" not in pos:
            resultados.append(_resultado(
                regra_narrativa, False,
                f"Cena {num}: STORY_POSITION deveria ser 'meio'.",
            ))
        elif num >= 6 and "fim" not in pos:
            resultados.append(_resultado(
                regra_narrativa, False,
                f"Cena {num}: STORY_POSITION deveria ser 'fim'.",
            ))

        # CAMERA_DIRECTION
        camera = cena.get("CAMERA_DIRECTION", "")
        if len(camera) < 40:
            resultados.append(_resultado(
                regra_camera, False,
                f"Cena {num}: CAMERA_DIRECTION muito curto.",
            ))
        elif not PALAVRAS_CAMERA.search(camera):
            resultados.append(_resultado(
                regra_camera, False,
                f"Cena {num}: CAMERA_DIRECTION sem shots/movimentos.",
            ))
        else:
            resultados.append(_resultado(
                regra_camera, True,
                f"Cena {num}: câmera detalhada ({len(camera)} chars).",
            ))

        # Idioma e qualidade das falas (só reporta falhas)
        idioma_falhas = []
        for i, linha in enumerate(dialogue_lines):
            if "TEXT" not in linha:
                continue
            texto = linha["TEXT"]
            speaker = linha.get("SPEAKER", "?")

            if not texto.strip():
                idioma_falhas.append(f"TEXT vazio (linha {i + 1})")
                continue

            if PALAVRAS_FILLER.match(texto.strip()):
                idioma_falhas.append(f"fala genérica — '{texto[:40]}'")

            if len(texto.strip()) < 8:
                idioma_falhas.append(f"TEXT muito curto — '{texto[:40]}'")

            if not texto_no_idioma(texto, idioma):
                idioma_falhas.append(
                    f"{speaker}: idioma errado — '{texto[:50]}' (esperado: {idioma})"
                )

            lock = linha.get("VOICE_IDENTITY_LOCK", "")
            if not voice_lock_valido(lock, idioma):
                idioma_falhas.append(f"{speaker}: VOICE_IDENTITY_LOCK sem idioma {idioma}")

        if idioma_falhas:
            detalhe = f"Cena {num}: " + "; ".join(idioma_falhas[:4])
            if len(idioma_falhas) > 4:
                detalhe += f"; ... +{len(idioma_falhas) - 4}"
            resultados.append(_resultado(regra_idioma, False, detalhe))

        # Densidade e timing
        timing = calcular_timing(dialogue_lines, idioma, DURACAO_CENA)
        if timing["line_count"] < MIN_FALAS_POR_CENA:
            resultados.append(_resultado(
                regra_densidade, False,
                f"Cena {num}: {timing['line_count']} falas (mínimo {MIN_FALAS_POR_CENA}).",
            ))
        elif timing["total_dialogue_seconds"] > DURACAO_CENA:
            resultados.append(_resultado(
                regra_densidade, False,
                f"Cena {num}: {timing['total_dialogue_seconds']}s estoura os {DURACAO_CENA}s.",
            ))
        elif not timing["fills_scene"]:
            resultados.append(_resultado(
                regra_densidade, False,
                f"Cena {num}: {timing['total_dialogue_seconds']}s de áudio "
                f"(meta {MIN_SEGUNDOS_FALA}-{MAX_SEGUNDOS_FALA}s). Pouco diálogo.",
            ))
        else:
            resultados.append(_resultado(
                regra_densidade, True,
                f"Cena {num}: {timing['line_count']} falas, {timing['word_count']} palavras, "
                f"~{timing['total_dialogue_seconds']}s / {DURACAO_CENA}s.",
            ))

        # AI video task
        if cena.get("AI_VIDEO_TASK"):
            resultados.append(_resultado(regra_ia, True, f"Cena {num}: AI_VIDEO_TASK OK."))
        else:
            resultados.append(_resultado(regra_ia, False, f"Cena {num}: falta AI_VIDEO_TASK."))

        # Motor visual
        if PALAVRAS_VISUAL.search(visual):
            resultados.append(_resultado(regra_visual, True, f"Cena {num}: motor visual OK."))
        else:
            resultados.append(_resultado(
                regra_visual, False,
                f"Cena {num}: VISUAL_PROMPT sem termos 4K/cinematic.",
            ))

        # Character lock
        speakers = list(dict.fromkeys(_speakers_da_cena(cena)))
        if speakers:
            faltando = [s for s in speakers if s not in visual.upper()]
            if faltando:
                resultados.append(_resultado(
                    regra_char, False,
                    f"Cena {num}: faltam no VISUAL_PROMPT: {', '.join(faltando)}.",
                ))
            else:
                resultados.append(_resultado(regra_char, True, f"Cena {num}: personagens no VISUAL_PROMPT."))

        # Safety
        texto_cena = visual + " " + acao + " " + _dialogos_texto(cena)
        if PALAVRAS_SANGUE.search(texto_cena):
            resultados.append(_resultado(regra_safety, False, f"Cena {num}: referência a sangue."))
        elif PALAVRAS_AGRESSAO.search(texto_cena):
            resultados.append(_resultado(regra_safety, False, f"Cena {num}: agressão explícita."))
        else:
            resultados.append(_resultado(regra_safety, True, f"Cena {num}: safety OK."))

        # Lip-sync
        if cena.get("HAS_DIALOGUE") and PALAVRAS_LIPSYNC.search(acao):
            resultados.append(_resultado(regra_lipsync, True, f"Cena {num}: lip-sync OK."))
        elif cena.get("HAS_DIALOGUE"):
            resultados.append(_resultado(
                regra_lipsync, False,
                f"Cena {num}: sem menção a lip-sync.",
            ))

        for linha in dialogue_lines:
            if "PAUSE" in linha and linha["PAUSE"] != 0.2:
                resultados.append(_resultado(
                    regra_pausa, True,
                    f"Cena {num}: pausa {linha['PAUSE']}s (recomendado 0.2s).",
                ))

    # Trama complexa
    roles_ok = len(roles_encontrados.intersection(ROLES_TRAMA)) >= 3
    trama_ok = cenas_com_trama >= 3 or roles_ok
    resultados.append(_resultado(
        regra_trama, trama_ok,
        f"Roles: {', '.join(roles_encontrados) or 'nenhum'}. "
        f"Cenas com elementos de trama: {cenas_com_trama}/{NUM_CENAS}.",
    ))

    # Solda têxtil
    if cast and len(cenas) > 1:
        primeira = cenas_ordenadas[0][1].get("VISUAL_PROMPT", "").upper()
        ultima = cenas_ordenadas[-1][1].get("VISUAL_PROMPT", "").upper()
        for p in cast:
            nome = p.get("name", "")
            trecho = _trecho_roupa(p.get("outfit_dna", ""))
            if trecho and trecho not in primeira and trecho not in ultima:
                resultados.append(_resultado(
                    regra_solda, False,
                    f"{nome}: roupa pode ter mudado.",
                ))
            elif trecho:
                resultados.append(_resultado(regra_solda, True, f"{nome}: roupa consistente."))

    # Cliffhanger
    if cenas_ordenadas:
        ultima = cenas_ordenadas[-1][1]
        texto_final = (
            ultima.get("SCENE_NAME", "") + " "
            + _dialogos_texto(ultima) + " "
            + ultima.get("VISUAL_PROMPT", "")
            + " " + ultima.get("OPENING_HOOK", "")
        )
        if PALAVRAS_CLIFFHANGER.search(texto_final):
            resultados.append(_resultado(regra_cliff, True, "SCENE_7 com cliffhanger."))
        else:
            resultados.append(_resultado(regra_cliff, False, "SCENE_7 sem gancho claro."))

    if roteiro.get("resolution") == RESOLUCAO:
        resultados.append(_resultado(regra_res, True, f"Roteiro em {RESOLUCAO}."))

    return resultados


def _speakers_da_cena(cena):
    return [
        linha["SPEAKER"].upper()
        for linha in cena.get("DIALOGUE_LINES", [])
        if "SPEAKER" in linha
    ]


def _dialogos_texto(cena):
    return " ".join(extrair_textos(cena.get("DIALOGUE_LINES", [])))


def _trecho_roupa(outfit):
    palavras = re.findall(r"\b(shirt|shorts|dress|sneakers|jersey|skirt|vest|sandal)\b", outfit, re.I)
    return palavras[0].upper() if palavras else ""


def validar_tudo(elenco, roteiro, sinopse=None):
    elenco_resultados = validar_elenco(elenco)
    sinopse_resultados = validar_sinopse(sinopse) if sinopse else []
    roteiro_resultados = validar_roteiro(roteiro, elenco, sinopse)
    todos = elenco_resultados + sinopse_resultados + roteiro_resultados
    problemas = [r for r in todos if not r["ok"]]

    erros = sum(1 for r in problemas if r["severidade"] == "erro")
    avisos = sum(1 for r in problemas if r["severidade"] == "aviso")
    infos = sum(1 for r in problemas if r["severidade"] == "info")

    return {
        "resumo": {
            "verificacoes": len(todos),
            "problemas": len(problemas),
            "erros": erros,
            "avisos": avisos,
            "infos": infos,
        },
        "problemas": problemas,
    }


def tem_erros_criticos(relatorio):
    return relatorio["resumo"]["erros"] > 0


def imprimir_relatorio(relatorio):
    resumo = relatorio["resumo"]
    problemas = relatorio.get("problemas", [])

    print("\n" + "=" * 50)
    print("  VALIDAÇÃO DAS REGRAS")
    print("=" * 50)
    print(
        f"  Verificações: {resumo['verificacoes']}  |  "
        f"Problemas: {resumo['problemas']}  |  "
        f"Erros: {resumo['erros']}  |  Avisos: {resumo['avisos']}"
    )
    print("=" * 50)

    if not problemas:
        print("\n  Tudo certo! Nenhum problema encontrado.\n")
        return

    vistos = set()
    for r in problemas[:12]:
        chave = (r["id"], r["detalhe"])
        if chave in vistos:
            continue
        vistos.add(chave)
        icone = {"erro": "X", "aviso": "!", "info": "i"}.get(r["severidade"], "?")
        print(f"\n  [{icone}] {r['nome']}")
        print(f"      {r['detalhe']}")

    if len(problemas) > 12:
        print(f"\n  ... e mais {len(problemas) - 12} problema(s) em validacao.json")

    print(f"\n  {len(problemas)} ponto(s) para revisar. Detalhes em log/validacao.json\n")