"""
Passo dedicado: reescreve DIALOGUE_LINES com muitas falas,
idioma correto e timing que preenche os 10 segundos.
"""

import json

from api import chamar_api, extrair_json
from dialogo import (
    ajustar_timing_cena,
    ajustar_timing_roteiro,
    analisar_dialogos_roteiro,
    cenas_com_problemas,
    lock_idioma_texto,
    metas_timing_roteiro,
    normalizar_idioma,
    PALAVRAS_POR_SEGUNDO,
    MIN_FALAS_POR_CENA,
    MAX_FALAS_POR_CENA,
    MIN_SEGUNDOS_FALA,
    MAX_SEGUNDOS_FALA,
    PAUSA_PADRAO,
)
from relatorio import imprimir_problemas
from schema import CORRECAO_DIALOGOS_RESPONSE_FORMAT, CORRECAO_SCENE, DURACAO_CENA
from narrativa import story_contract_prompt
from voz import voice_registry_prompt

CORRECAO_CENA_RESPONSE_FORMAT = {
    "name": "correcao_cena",
    "strict": True,
    "schema": CORRECAO_SCENE,
}


def _exemplo_dialogo(idioma):
    if normalizar_idioma(idioma) == "de":
        return """
BEISPIEL (5 kurze Zeilen, ~9s, fuellt 10s Szene):
[
  {"SPEAKER": "ERDBEERE", "VOICE_IDENTITY_LOCK": "... Language: German.", "TEXT": "Orange?! Was machst du hier?!"},
  {"PAUSE": 0.2},
  {"SPEAKER": "ORANGE", "VOICE_IDENTITY_LOCK": "... Language: German.", "TEXT": "Beruhig dich... wir haben nur geredet."},
  {"PAUSE": 0.2},
  {"SPEAKER": "TRAUBE", "VOICE_IDENTITY_LOCK": "... Language: German.", "TEXT": "Geredet? Schau auf das Glas."},
  {"PAUSE": 0.2},
  {"SPEAKER": "ERDBEERE", "VOICE_IDENTITY_LOCK": "... Language: German.", "TEXT": "Mein bester Freund verrät mich?!"},
  {"PAUSE": 0.2},
  {"SPEAKER": "TRAUBE", "VOICE_IDENTITY_LOCK": "... Language: German.", "TEXT": "Wir heiraten. Gewöhn dich dran."}
]
"""
    if normalizar_idioma(idioma) == "en":
        return """
EXEMPLO (4 speeches, ~9s, fills 10s scene):
[
  {"SPEAKER": "STRAWBERRY", "VOICE_IDENTITY_LOCK": "... Language: English.", "TEXT": "Orange?! What are you doing here?!"},
  {"PAUSE": 0.2},
  {"SPEAKER": "ORANGE", "VOICE_IDENTITY_LOCK": "... Language: English.", "TEXT": "Relax babe... we were just talking."},
  {"PAUSE": 0.2},
  {"SPEAKER": "GRAPE", "VOICE_IDENTITY_LOCK": "... Language: English.", "TEXT": "Talking? Look at my glass, banana."},
  {"PAUSE": 0.2},
  {"SPEAKER": "STRAWBERRY", "VOICE_IDENTITY_LOCK": "... Language: English.", "TEXT": "My best friend... betraying me?!"},
  {"PAUSE": 0.2},
  {"SPEAKER": "GRAPE", "VOICE_IDENTITY_LOCK": "... Language: English.", "TEXT": "We're getting married. Deal with it."}
]
"""
    return """
EXEMPLO (4 falas curtas alternadas, ~9s, preenche cena de 10s):
[
  {"SPEAKER": "MORANGO", "VOICE_IDENTITY_LOCK": "... Language: Portuguese (Brazil).", "TEXT": "Laranjito?! O que você tá fazendo aqui?!"},
  {"PAUSE": 0.2},
  {"SPEAKER": "LARANJA", "VOICE_IDENTITY_LOCK": "... Language: Portuguese (Brazil).", "TEXT": "Calma, amor... a gente só tava conversando."},
  {"PAUSE": 0.2},
  {"SPEAKER": "UVA", "VOICE_IDENTITY_LOCK": "... Language: Portuguese (Brazil).", "TEXT": "Conversando? Olha a taça, banana."},
  {"PAUSE": 0.2},
  {"SPEAKER": "MORANGO", "VOICE_IDENTITY_LOCK": "... Language: Portuguese (Brazil).", "TEXT": "Traição... do meu melhor amigo?!"},
  {"PAUSE": 0.2},
  {"SPEAKER": "UVA", "VOICE_IDENTITY_LOCK": "... Language: Portuguese (Brazil).", "TEXT": "A gente vai casar. Aceita ou descasca."}
]
"""


def _extrair_dialogos(roteiro):
    cenas = {}
    for chave, cena in roteiro.get("scenes", {}).items():
        cenas[chave] = {
            "SCENE_NUMBER": cena.get("SCENE_NUMBER"),
            "NARRATIVE_BEAT": cena.get("NARRATIVE_BEAT"),
            "DIALOGUE_LINES": cena.get("DIALOGUE_LINES", []),
            "DELIVERY_STYLE": cena.get("DELIVERY_STYLE", ""),
            "VOICE_OVERRIDE_METADATA": cena.get("VOICE_OVERRIDE_METADATA", {}),
        }
    return {"scenes": cenas}


def _extrair_sinopse_dialogos(sinopse):
    return {
        "story_summary": sinopse.get("story_summary", ""),
        "beats": [
            {
                "scene_number": b.get("scene_number"),
                "narrative_beat": b.get("narrative_beat"),
                "dialogue_intent": b.get("dialogue_intent"),
            }
            for b in sinopse.get("beats", [])
        ],
    }


def _problemas_da_cena(problemas, numero):
    prefixo = f"Cena {numero}"
    return [p for p in problemas if p.startswith(prefixo)]


def _chamar_correcao_api(system, user, schema):
    ultimo_erro = None
    for tentativa in range(1, 4):
        try:
            resposta = chamar_api(system, user, schema=schema)
            return extrair_json(resposta)
        except (ValueError, AttributeError) as erro:
            ultimo_erro = erro
            if tentativa < 3:
                print(f"  !! Resposta inválida ({erro}). Tentativa {tentativa + 1}/3...")
            continue
    raise ValueError(f"Falha na correção após 3 tentativas: {ultimo_erro}")


def corrigir_cena_dialogos(roteiro, sinopse, idioma, numero, problemas=None, elenco=None):
    """Corrige diálogos de uma única cena — chamada menor e mais confiável."""
    codigo = normalizar_idioma(idioma)
    wps = PALAVRAS_POR_SEGUNDO.get(codigo, 3.2)
    min_palavras = int(MIN_SEGUNDOS_FALA * wps)
    max_palavras = int(MAX_SEGUNDOS_FALA * wps)
    lock = lock_idioma_texto(idioma)

    cenas = roteiro.get("scenes", {})
    cena = next(
        (c for c in cenas.values() if c.get("SCENE_NUMBER") == numero),
        cenas.get(f"SCENE_{numero}"),
    )
    if not cena:
        return roteiro

    beat = next(
        (b for b in sinopse.get("beats", []) if b.get("scene_number") == numero),
        {},
    )

    problemas_txt = ""
    if problemas:
        problemas_txt = "PROBLEMAS:\n" + "\n".join(f"- {p}" for p in problemas)

    voice_txt = voice_registry_prompt(elenco, idioma) if elenco else ""
    story_txt = story_contract_prompt(sinopse, numero)
    cena_json = json.dumps(_extrair_dialogos({"scenes": {f"SCENE_{numero}": cena}}), ensure_ascii=False, indent=2)

    system = f"""
Você reescreve DIALOGUE_LINES de UMA cena de {DURACAO_CENA}s.

IDIOMA: {idioma} — TODO TEXT em {idioma}. LOCK: "{lock}".

LIMITES RÍGIDOS:
- {MIN_FALAS_POR_CENA}-{MAX_FALAS_POR_CENA} falas (4-12 palavras cada)
- {min_palavras}-{max_palavras} palavras total (~{MIN_SEGUNDOS_FALA}-{MAX_SEGUNDOS_FALA}s)
- Pausa {{"PAUSE": {PAUSA_PADRAO}}} entre falas
- NUNCA ultrapasse {MAX_SEGUNDOS_FALA}s nem fique abaixo de {MIN_SEGUNDOS_FALA}s

NARRATIVE_BEAT: {cena.get('NARRATIVE_BEAT', '')}
dialogue_intent: {beat.get('dialogue_intent', '')}

{voice_txt}

{story_txt}

REGRAS DE CONTINUIDADE:
- Use somente SPEAKER existentes no VOICE REGISTRY.
- Copie o VOICE_IDENTITY_LOCK canonico quando houver VOICE REGISTRY.
- Preserve required_reveal e must_end_handing_off_to do STORY CONTRACT.
- Nao adicione reacoes genericas que nao avancem o enredo.

{_exemplo_dialogo(idioma)}
"""

    user = f"""
{problemas_txt}

Cena {numero}:
{cena_json}

Reescreva só os diálogos desta cena em {idioma}.
"""

    correcao = _chamar_correcao_api(system, user, CORRECAO_CENA_RESPONSE_FORMAT)
    return _aplicar_correcao(roteiro, {"scenes": {f"SCENE_{numero}": correcao}})


def corrigir_dialogos(roteiro, sinopse, idioma, problemas=None, elenco=None):
    codigo = normalizar_idioma(idioma)
    wps = PALAVRAS_POR_SEGUNDO.get(codigo, 3.2)
    min_palavras = int(MIN_SEGUNDOS_FALA * wps)
    max_palavras = int(MAX_SEGUNDOS_FALA * wps)
    lock = lock_idioma_texto(idioma)

    problemas_txt = ""
    if problemas:
        problemas_txt = "PROBLEMAS A CORRIGIR:\n" + "\n".join(f"- {p}" for p in problemas)

    roteiro_json = json.dumps(_extrair_dialogos(roteiro), ensure_ascii=False, indent=2)
    sinopse_json = json.dumps(_extrair_sinopse_dialogos(sinopse), ensure_ascii=False, indent=2)
    voice_txt = voice_registry_prompt(elenco, idioma) if elenco else ""
    story_txt = story_contract_prompt(sinopse)

    system = f"""
Você é um roteirista especialista em diálogos para vídeos virais de 10 segundos.

Sua ÚNICA tarefa: reescrever DIALOGUE_LINES de TODAS as cenas.

IDIOMA INQUEBRÁVEL: {idioma}
- TODO TEXT em {idioma}. ZERO palavras em outro idioma.
- VOICE_IDENTITY_LOCK com "{lock}" em TODAS as falas.

DENSIDADE OBRIGATÓRIA (cada cena = {DURACAO_CENA}s):
- Mínimo {MIN_FALAS_POR_CENA} falas com TEXT por cena (ideal {MAX_FALAS_POR_CENA})
- Total: {min_palavras}-{max_palavras} palavras por cena (~{MIN_SEGUNDOS_FALA}-{MAX_SEGUNDOS_FALA}s de fala)
- Pausa fixa {{"PAUSE": {PAUSA_PADRAO}}} entre cada fala
- Falas CURTAS (4-12 palavras cada) — ritmo rápido estilo TikTok
- NÃO faça monólogos longos numa só fala — divida em várias trocas
- O áudio SOZINHO deve contar a história da cena

NARRATIVA:
- Use NARRATIVE_BEAT de cada cena e dialogue_intent da sinopse
- Cada fala avança o enredo — reação, revelação ou tensão
- Alterne personagens quando houver mais de um na cena
- Preserve o STORY CONTRACT: cada cena precisa pagar a anterior e plantar a proxima
- Use somente SPEAKER do VOICE REGISTRY quando ele existir

Retorne SCENE_NUMBER, DIALOGUE_LINES, DELIVERY_STYLE, VOICE_OVERRIDE_METADATA por cena.

{voice_txt}

{story_txt}

{_exemplo_dialogo(idioma)}
"""

    metas = metas_timing_roteiro(roteiro, idioma)

    user = f"""
{problemas_txt}

METAS DE TIMING POR CENA (obrigatório respeitar):
{metas}

SINOPSE:
{sinopse_json}

ROTEIRO ATUAL (reescreva só os diálogos):
{roteiro_json}

Reescreva DIALOGUE_LINES das 7 cenas em {idioma}.
Muitas falas curtas (4-12 palavras). Preencha {MIN_SEGUNDOS_FALA}-{MAX_SEGUNDOS_FALA}s de áudio por cena.
NUNCA ultrapasse {MAX_SEGUNDOS_FALA}s nem fique abaixo de {MIN_SEGUNDOS_FALA}s.
"""

    numeros = cenas_com_problemas(problemas or [])
    if numeros:
        print(f"  [4/4] Corrigindo diálogos ({len(numeros)} cena(s))...")
        for numero in numeros:
            print(f"       Cena {numero}...")
            problemas_cena = _problemas_da_cena(problemas, numero)
            roteiro = corrigir_cena_dialogos(roteiro, sinopse, idioma, numero, problemas_cena, elenco=elenco)
        return roteiro

    print("  [4/4] Corrigindo e expandindo diálogos (lote)...")
    correcao = _chamar_correcao_api(system, user, CORRECAO_DIALOGOS_RESPONSE_FORMAT)
    return _aplicar_correcao(roteiro, correcao)


def _aplicar_correcao(roteiro, correcao):
    cenas_corr = correcao.get("scenes", {})
    cenas = roteiro.get("scenes", {})

    for chave, dados in cenas_corr.items():
        alvo = cenas.get(chave)
        if not alvo:
            num = dados.get("SCENE_NUMBER")
            for v in cenas.values():
                if v.get("SCENE_NUMBER") == num:
                    alvo = v
                    break
        if not alvo:
            continue

        alvo["DIALOGUE_LINES"] = dados["DIALOGUE_LINES"]
        alvo["DELIVERY_STYLE"] = dados.get("DELIVERY_STYLE", alvo.get("DELIVERY_STYLE", ""))
        alvo["VOICE_OVERRIDE_METADATA"] = dados.get(
            "VOICE_OVERRIDE_METADATA", alvo.get("VOICE_OVERRIDE_METADATA", {})
        )

    return roteiro


def _ajuste_local_por_cena(roteiro, idioma, problemas):
    """Tenta corrigir timing localmente antes de chamar a API."""
    numeros = cenas_com_problemas(problemas)
    cenas = roteiro.get("scenes", {})
    for numero in numeros:
        cena = next(
            (c for c in cenas.values() if c.get("SCENE_NUMBER") == numero),
            cenas.get(f"SCENE_{numero}"),
        )
        if cena:
            ajustar_timing_cena(cena, idioma)
    return roteiro


def corrigir_ate_validar(roteiro, sinopse, idioma, enriquecer_fn, max_tentativas=3, elenco=None):
    for tentativa in range(1, max_tentativas + 1):
        problemas = analisar_dialogos_roteiro(roteiro, idioma)
        if not problemas:
            print("  -> Diálogos OK.\n")
            return roteiro

        imprimir_problemas(
            f"Diálogos com problemas — correção {tentativa}/{max_tentativas}",
            problemas,
        )

        roteiro = _ajuste_local_por_cena(roteiro, idioma, problemas)
        roteiro = enriquecer_fn(roteiro)

        problemas = analisar_dialogos_roteiro(roteiro, idioma)
        if not problemas:
            print("  -> Diálogos OK (ajuste local).\n")
            return roteiro

        roteiro = corrigir_dialogos(roteiro, sinopse, idioma, problemas, elenco=elenco)
        roteiro = enriquecer_fn(roteiro)

    problemas = analisar_dialogos_roteiro(roteiro, idioma)
    if problemas:
        print("  -> Ajuste local final de timing...")
        roteiro = enriquecer_fn(ajustar_timing_roteiro(roteiro, idioma))

    restantes = analisar_dialogos_roteiro(roteiro, idioma)
    if restantes:
        imprimir_problemas("Alguns diálogos ainda fora da meta", restantes)
    else:
        print("  -> Diálogos OK.\n")

    return roteiro
