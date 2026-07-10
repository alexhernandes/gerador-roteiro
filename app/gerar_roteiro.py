"""
Gera elenco + sinopse + roteiro em JSONs separados.
Uso: python main.py
"""

import json
import os
import subprocess
import sys

from api import chamar_api, extrair_json, resumo_uso_tokens, zerar_uso_tokens
from auditoria import auditar_roteiro
from paths import ROOT_DIR
from config import (
    MODEL,
    OPEN_OUTPUT_FOLDER_ON_FINISH,
    MAX_TOKENS_CAST,
    MAX_TOKENS_SYNOPSIS,
    MAX_TOKENS_DIALOGUES,
    MAX_TOKENS_SCENES,
)
from corrigir_dialogos import corrigir_ate_validar
from dialogo import (
    ajustar_timing_cena,
    dialogos_de_intent,
    lock_idioma_texto,
    normalizar_idioma,
    MIN_SEGUNDOS_FALA,
    MAX_SEGUNDOS_FALA,
    PALAVRAS_POR_SEGUNDO,
    limites_linha,
    unidade_timing,
)
from entrada import perguntar
from enriquecer import enriquecer_elenco, enriquecer_sinopse, enriquecer_roteiro_com_sinopse
from salvar import criar_sessao, salvar
from schema import (
    ELENCO_CRIATIVO_RESPONSE_FORMAT,
    SINOPSE_RESPONSE_FORMAT,
    CENA_VISUAL_RESPONSE_FORMAT,
    CENAS_VISUAIS_RESPONSE_FORMAT,
    DIALOGOS_CRIATIVOS_RESPONSE_FORMAT,
    TRADUCAO_TEMA_RESPONSE_FORMAT,
    RESOLUCAO,
    DURACAO_CENA,
    NUM_CENAS,
    DURACAO_TOTAL,
)
from universos import carregar_prompt_universo, label_universo
from variacao import criar_brief_variacao
from voz import aplicar_voice_registry_cena

ROLES_POR_CENA = {
    1: "hook",
    2: "setup",
    3: "conflict",
    4: "twist",
    5: "escalation",
    6: "crisis",
    7: "cliffhanger",
}

MIN_TAMANHO_ATO = 30

from validar import validar_tudo, imprimir_relatorio


PROMPT_BASE = """
Voce cria roteiros tecnicos de animacao 3D curta e retorna somente o JSON do schema.
Regras canonicas:
- DIALOGUE_LINES > TEXT e a unica fonte de audio e usa apenas o idioma solicitado.
- Prompts visuais podem usar ingles tecnico; falas nunca mudam de idioma.
- Preserve nomes, DNA visual, figurino/acessorios, voz, local, objetos e estado emocional.
- Cada cena e consequencia da anterior, revela um fato novo e prepara a proxima.
- O universo selecionado define os tipos; character_type e generico, nao exclusivo de frutas.
- Evite filler, estereotipos repetidos, marcas reais e mudancas sem causa narrativa.
- Evite sangue e agressao explicita; use liquido cenico e confronto verbal/gestual nao grafico.
"""


def _json_compacto(dados):
    return json.dumps(dados, ensure_ascii=False, separators=(",", ":"))


def _elenco_compacto(elenco, incluir_voz=False):
    campos = ("name", "character_type", "age", "gender", "physical_dna", "outfit_dna", "voice_profile")
    cast = [
        {campo: p.get(campo, "") for campo in campos if p.get(campo, "") != ""}
        for p in elenco.get("cast", [])
    ]
    resultado = {"cast": cast}
    if incluir_voz:
        resultado["voice_registry"] = elenco.get("voice_registry", {})
    return resultado


def _sinopse_compacta(sinopse):
    return {
        "title": sinopse.get("title", ""),
        "story_summary": sinopse.get("story_summary", ""),
        "act_1": sinopse.get("act_1", ""),
        "act_2": sinopse.get("act_2", ""),
        "act_3": sinopse.get("act_3", ""),
        "beats": sinopse.get("beats", []),
    }


def _contrato_compacto(sinopse):
    contract = sinopse.get("story_contract", {})
    cenas = {}
    for numero, cena in contract.get("scenes", {}).items():
        cenas[numero] = {
            "start": cena.get("must_start_from", ""),
            "reveal": cena.get("required_reveal", ""),
            "handoff": cena.get("must_end_handing_off_to", ""),
            "state_after": cena.get("story_state_after", ""),
        }
    return {"dramatic_question": contract.get("dramatic_question", ""), "scenes": cenas}


def _bloco_idioma(idioma):
    return f"""
IDIOMA INQUEBRÁVEL — REJEIÇÃO AUTOMÁTICA SE VIOLAR:
- Idioma escolhido pelo usuário: {idioma}
- 100% das falas/textos de audio em {idioma}. Nenhuma palavra de outro idioma.
- Nao romanize alfabetos que possuem escrita propria.
- Áudio = SOMENTE DIALOGUE_LINES > TEXT.
"""


def _elenco_variado(elenco):
    cast = elenco.get("cast", [])
    nomes = [str(p.get("name", "")).strip().casefold() for p in cast]
    tipos = [str(p.get("character_type", "")).strip().casefold() for p in cast]
    return (
        3 <= len(cast) <= 5
        and all(nomes)
        and all(tipos)
        and len(set(nomes)) == len(nomes)
        and len(set(tipos)) == len(tipos)
    )


def gerar_elenco(idioma, tema, aspect_ratio, universo, tentativa=1):
    universo_prompt = carregar_prompt_universo(universo)
    variacao_prompt = criar_brief_variacao(universo)
    system = PROMPT_BASE + f"""

Crie APENAS o ELENCO.
Tema: {tema}. Formato: {aspect_ratio}. Resolução: {RESOLUCAO}. language: "{idioma}".

UNIVERSO SELECIONADO: {label_universo(universo)}
{universo_prompt}

- Crie personagens coerentes com o UNIVERSO SELECIONADO
- character_type deve descrever o tipo de personagem dentro desse universo
- physical_dna e outfit_dna completos
- 3 a 5 personagens com papeis claros na trama
- Nomes devem ser naturais no idioma {idioma}, sem repetir sempre aliteracoes previsiveis
- Tipos, silhuetas, idades, personalidades e vozes devem ser perceptivelmente diferentes

BRIEF DE VARIACAO DESTA EXECUCAO:
{variacao_prompt}
{"CORRECAO: o elenco anterior repetiu nomes/tipos; mude radicalmente todos os personagens." if tentativa > 1 else ""}
"""

    user = f"Elenco para vídeo de {DURACAO_TOTAL}s sobre: {tema}"

    print(f"  [1/4] Gerando elenco...{' (nova variacao)' if tentativa > 1 else ''}")
    resposta = chamar_api(
        system,
        user,
        schema=ELENCO_CRIATIVO_RESPONSE_FORMAT,
        max_completion_tokens=MAX_TOKENS_CAST,
    )
    elenco = extrair_json(resposta)
    if not _elenco_variado(elenco) and tentativa < 2:
        print("  !! Elenco repetido. Solicitando uma nova combinacao...")
        return gerar_elenco(idioma, tema, aspect_ratio, universo, tentativa + 1)
    if not _elenco_variado(elenco):
        raise ValueError("A API repetiu nomes ou character_type no elenco apos nova tentativa.")
    return enriquecer_elenco(elenco, aspect_ratio, idioma)


def traduzir_tema(tema, idioma):
    system = f"""
Voce traduz temas de historias curtas para o idioma alvo.

Regras:
- Traduza o tema para: {idioma}.
- Preserve nomes proprios, marcas e nomes de personagens.
- Nao expanda a ideia, nao adicione detalhes novos.
- Retorne apenas o JSON solicitado.
"""
    user = f"""
Tema original:
{tema}

Idioma alvo:
{idioma}
"""
    resposta = chamar_api(
        system,
        user,
        schema=TRADUCAO_TEMA_RESPONSE_FORMAT,
        max_completion_tokens=600,
    )
    dados = extrair_json(resposta)
    traduzido = dados.get("translated_theme", "").strip()
    if not traduzido:
        raise ValueError("Traducao do tema veio vazia.")
    return traduzido


def _sinopse_corrompida(sinopse):
    return (
        "idea" in sinopse
        or ("cast" in sinopse and "beats" not in sinopse)
        or ("scenes" in sinopse and "beats" not in sinopse)
    )


def _sinopse_valida(sinopse):
    if _sinopse_corrompida(sinopse):
        return False

    beats = sinopse.get("beats", [])
    numeros = {int(beat.get("scene_number", 0)) for beat in beats}
    atos_ok = all(
        len(sinopse.get(campo, "").strip()) >= MIN_TAMANHO_ATO
        for campo in ("act_1", "act_2", "act_3")
    )
    return (
        len(sinopse.get("story_summary", "")) > 30
        and len(beats) == NUM_CENAS
        and numeros == set(range(1, NUM_CENAS + 1))
        and atos_ok
    )


def gerar_sinopse(idioma, tema, elenco, universo, tentativa=1):
    elenco_json = _json_compacto(_elenco_compacto(elenco))
    universo_prompt = carregar_prompt_universo(universo)

    reforco = ""
    if tentativa > 1:
        reforco = """
CORREÇÃO: a sinopse anterior veio incompleta.
Preencha OBRIGATORIAMENTE: story_summary, act_1, act_2, act_3 (mínimo 2 frases cada) e beats com 7 itens.
NÃO use rótulos curtos como "início (Cenas 1-2)" — descreva o que acontece em cada ato.
"""

    system = PROMPT_BASE + _bloco_idioma(idioma) + f"""

Crie apenas a sinopse de uma historia de {DURACAO_TOTAL}s em {NUM_CENAS} cenas.
Estrutura causal obrigatoria:
- Cenas 1-2: hook imediato e conflito central.
- Cenas 3-5: escalada, revelacao e consequencia direta.
- Cenas 6-7: crise, climax e cliffhanger ainda compreensivel.
- Cada beat registra o estado que recebe, o fato novo e a pressao deixada para o proximo.
- dialogue_intent deve planejar 4-6 falas REAIS em {idioma}; nao use outro idioma.
- story_position e campo tecnico: use exatamente "início" (1-2), "meio" (3-5), "fim" (6-7).
- story_summary e act_1/act_2/act_3 contam acontecimentos concretos, nao rotulos.

UNIVERSO SELECIONADO: {label_universo(universo)}
Regra visual resumida: {universo_prompt[:600]}

Elenco disponível — use estes personagens na história:
{elenco_json}

Crie a sinopse com EXATAMENTE {NUM_CENAS} beats no array "beats".
theme = "{tema}", language = "{idioma}".
{reforco}
"""

    user = f"""
Planeje a história completa de {DURACAO_TOTAL}s ({NUM_CENAS} cenas) sobre: {tema}
Começo, meio e fim claros. Reviravoltas. 4-6 falas planejadas por cena no dialogue_intent.
"""

    print(f"  [2/4] Planejando sinopse (história)...{' (tentativa ' + str(tentativa) + ')' if tentativa > 1 else ''}")
    resposta = chamar_api(
        system,
        user,
        schema=SINOPSE_RESPONSE_FORMAT,
        max_completion_tokens=MAX_TOKENS_SYNOPSIS,
    )
    sinopse = extrair_json(resposta)

    if not _sinopse_valida(sinopse) and tentativa < 3:
        print("  !! Sinopse incompleta. Tentando de novo...\n")
        return gerar_sinopse(idioma, tema, elenco, universo, tentativa + 1)

    if not _sinopse_valida(sinopse):
        raise ValueError(
            "Sinopse veio incompleta da API (sem beats ou story_summary). "
            "Tente rodar de novo."
        )

    return enriquecer_sinopse(sinopse, idioma)


def juntar_cenas_em_roteiro(cenas, sinopse):
    """Monta roteiro.json com as cenas visuais e os dialogos canonicos."""
    titulo = sinopse.get("title", "").replace("Sinopse - ", "").strip() or "Roteiro"
    return {
        "title": titulo,
        "story_summary": sinopse.get("story_summary", ""),
        "scenes": {f"SCENE_{num}": cena for num, cena in sorted(cenas.items())},
    }


def _nomes_elenco(elenco):
    return [p.get("name") for p in elenco.get("cast", []) if p.get("name")]


def _falas_fallback_beat(beat, speakers, idioma):
    falas = dialogos_de_intent(beat.get("dialogue_intent", ""), speakers, idioma)
    if falas:
        return falas

    speaker_a = speakers[0] if speakers else "PERSONAGEM_1"
    speaker_b = speakers[1] if len(speakers) > 1 else speaker_a
    lock = lock_idioma_texto(idioma)
    codigo = normalizar_idioma(idioma)
    fallback = {
        "pt": [
            "A verdade apareceu agora.",
            "Entao explica isso agora.",
            "Nao da mais pra esconder.",
            "Se for verdade, acabou.",
        ],
        "en": [
            "The truth just came out.",
            "Then explain this right now.",
            "We cannot hide this anymore.",
            "If this is true, we are done.",
        ],
        "es": [
            "La verdad acaba de salir.",
            "Entonces explica esto ahora.",
            "Ya no podemos esconderlo.",
            "Si esto es verdad, se acabo.",
        ],
        "de": [
            "Die Wahrheit ist jetzt heraus.",
            "Dann erklär das sofort.",
            "Wir können das nicht mehr verstecken.",
            "Wenn das wahr ist, ist alles vorbei.",
        ],
        "ja": [
            "今 真実が 明らかに なった。",
            "今すぐ それを 説明して。",
            "もう 隠しては おけない。",
            "本当なら すべて 終わりだ。",
        ],
    }.get(codigo, [
        "A verdade apareceu agora.",
        "Entao explica isso agora.",
        "Nao da mais pra esconder.",
        "Se for verdade, acabou.",
    ])

    return [
        {"SPEAKER": speaker_a, "VOICE_IDENTITY_LOCK": f"{speaker_a} voice. {lock}.", "TEXT": fallback[0]},
        {"PAUSE": 0.2},
        {"SPEAKER": speaker_b, "VOICE_IDENTITY_LOCK": f"{speaker_b} voice. {lock}.", "TEXT": fallback[1]},
        {"PAUSE": 0.2},
        {"SPEAKER": speaker_a, "VOICE_IDENTITY_LOCK": f"{speaker_a} voice. {lock}.", "TEXT": fallback[2]},
        {"PAUSE": 0.2},
        {"SPEAKER": speaker_b, "VOICE_IDENTITY_LOCK": f"{speaker_b} voice. {lock}.", "TEXT": fallback[3]},
    ]


def _fallback_dialogos_globais(sinopse, elenco, idioma):
    speakers = _nomes_elenco(elenco)
    cenas = {}
    for beat in sorted(sinopse.get("beats", []), key=lambda b: b.get("scene_number", 0)):
        num = beat.get("scene_number", len(cenas) + 1)
        cena = {
            "SCENE_NUMBER": num,
            "DIALOGUE_LINES": _falas_fallback_beat(beat, speakers, idioma),
            "DELIVERY_STYLE": (
                "Fast viral drama delivery, emotionally direct, sequential non-overlapping speech."
            ),
            "VOICE_OVERRIDE_METADATA": {},
        }
        ajustar_timing_cena(cena, idioma)
        aplicar_voice_registry_cena(cena, elenco, idioma)
        cenas[f"SCENE_{num}"] = cena
    return {"scenes": cenas}


def _normalizar_dialogos_globais(dialogos, sinopse, elenco, idioma):
    """Canoniza chaves SCENE_N e preenche qualquer cena ausente localmente."""
    fallback = _fallback_dialogos_globais(sinopse, elenco, idioma)
    recebidos = {}
    for chave, cena in (dialogos or {}).get("scenes", {}).items():
        try:
            numero = int(cena.get("SCENE_NUMBER") or str(chave).split("_")[-1])
        except (TypeError, ValueError):
            continue
        if 1 <= numero <= NUM_CENAS and numero not in recebidos:
            recebidos[numero] = cena

    cenas = {}
    for numero in range(1, NUM_CENAS + 1):
        cenas[f"SCENE_{numero}"] = recebidos.get(
            numero, fallback["scenes"][f"SCENE_{numero}"]
        )
        cenas[f"SCENE_{numero}"]["SCENE_NUMBER"] = numero
    return {"scenes": cenas}


def gerar_dialogos_globais(idioma, tema, elenco, sinopse, universo):
    sinopse_json = _json_compacto(_sinopse_compacta(sinopse))
    contrato_json = _json_compacto(_contrato_compacto(sinopse))
    codigo = normalizar_idioma(idioma)
    wps = PALAVRAS_POR_SEGUNDO[codigo]
    min_unidades = int(MIN_SEGUNDOS_FALA * wps)
    max_unidades = int(MAX_SEGUNDOS_FALA * wps)
    min_linha, max_linha = limites_linha(idioma)
    unidade = unidade_timing(idioma)

    system = PROMPT_BASE + _bloco_idioma(idioma) + f"""

Voce e o dialoguista principal. Sua tarefa e escrever o AUDIO COMPLETO das {NUM_CENAS} cenas
antes dos prompts visuais, para que a historia fique uniforme.

ELENCO E PERFIS DE VOZ (use apenas estes nomes em SPEAKER):
{_json_compacto(_elenco_compacto(elenco))}

STORY CONTRACT COMPACTO:
{contrato_json}

REGRAS:
- Use SOMENTE os SPEAKER existentes no VOICE REGISTRY.
- O sistema anexara VOICE_IDENTITY_LOCK e metadata canonicos depois da resposta.
- Cada cena deve ter 4-6 falas curtas, com PAUSE 0.2 entre falas.
- O audio de cada cena deve ocupar {MIN_SEGUNDOS_FALA}-{MAX_SEGUNDOS_FALA}s dos {DURACAO_CENA}s.
- Meta por cena: {min_unidades}-{max_unidades} {unidade}; cada fala com {min_linha}-{max_linha} {unidade}.
- Cada cena deve cobrir required_reveal e terminar plantando must_end_handing_off_to.
- Nao use filler. Cada fala revela, reage ou empurra para a proxima cena.
- Retorne SCENE_NUMBER, DIALOGUE_LINES e DELIVERY_STYLE por cena.
"""

    user = f"""
Tema: {tema}
Idioma: {idioma}

SINOPSE E STORY CONTRACT:
{sinopse_json}

Crie os dialogos globais das {NUM_CENAS} cenas. Esse audio sera congelado e usado nas cenas visuais.
"""

    print("       Criando dialogos globais canonicos...")
    try:
        resposta = chamar_api(
            system,
            user,
            schema=DIALOGOS_CRIATIVOS_RESPONSE_FORMAT,
            max_completion_tokens=MAX_TOKENS_DIALOGUES,
        )
        dialogos = _normalizar_dialogos_globais(
            extrair_json(resposta), sinopse, elenco, idioma
        )
    except Exception as erro:
        print(f"       !! Dialogos globais falharam ({erro}). Usando fallback da sinopse.")
        dialogos = _fallback_dialogos_globais(sinopse, elenco, idioma)

    for cena in dialogos.get("scenes", {}).values():
        aplicar_voice_registry_cena(cena, elenco, idioma)
        ajustar_timing_cena(cena, idioma)
        aplicar_voice_registry_cena(cena, elenco, idioma)

    return dialogos


def _dialogos_compactos(dialogos_globais):
    resultado = {}
    for chave, cena in dialogos_globais.get("scenes", {}).items():
        resultado[chave] = [
            {"speaker": linha.get("SPEAKER", ""), "text": linha.get("TEXT", "")}
            for linha in cena.get("DIALOGUE_LINES", [])
            if "TEXT" in linha
        ]
    return resultado


def _cena_anterior_compacta(cena):
    if not cena:
        return {}
    return {
        "number": cena.get("SCENE_NUMBER"),
        "location": cena.get("LOCATION_LOCK", ""),
        "continuity_out": cena.get("CONTINUITY_OUT", ""),
        "narrative_beat": cena.get("NARRATIVE_BEAT", ""),
        "last_visual": cena.get("VISUAL_PROMPT", "")[-500:],
    }


def _montar_cena_producao(cena, beat, dialogo_planejado, elenco, idioma):
    num = int(beat.get("scene_number", cena.get("SCENE_NUMBER", 1)))
    cena = dict(cena)
    cena["SCENE_NUMBER"] = num
    cena["SCENE_ROLE"] = ROLES_POR_CENA.get(num, cena.get("SCENE_ROLE", "scene"))
    cena["STORY_POSITION"] = beat.get("story_position", cena.get("STORY_POSITION", ""))
    cena["NARRATIVE_BEAT"] = beat.get("narrative_beat", cena.get("NARRATIVE_BEAT", ""))
    cena["DURATION_SECONDS"] = DURACAO_CENA
    cena["TIMESTAMP"] = ""
    cena["AI_VIDEO_TASK"] = ""
    cena["HAS_DIALOGUE"] = True
    cena["AUDIO_SPEAKER"] = "INDIVIDUAL_SEQUENTIAL"
    cena["AUDIO_TARGET"] = "characters_in_scene"
    cena["AUDIO_TIMING_CONTROLS"] = {
        "OVERALL_PACE": (dialogo_planejado or {}).get(
            "DELIVERY_STYLE", "Fast, clear, causal dialogue with no overlap."
        ),
        "SPEECH_PAUSE_SECONDS": 0.2,
    }
    cena["DIALOGUE_LINES"] = (dialogo_planejado or {}).get("DIALOGUE_LINES", [])
    cena["DELIVERY_STYLE"] = (dialogo_planejado or {}).get(
        "DELIVERY_STYLE", "Fast, emotionally clear, sequential delivery."
    )
    cena["VOICE_OVERRIDE_METADATA"] = (dialogo_planejado or {}).get(
        "VOICE_OVERRIDE_METADATA", {}
    )
    aplicar_voice_registry_cena(cena, elenco, idioma)
    return cena


def gerar_cena(idioma, tema, aspect_ratio, elenco, sinopse, beat, universo, cena_anterior=None, dialogo_planejado=None):
    """Fallback/uso externo: gera uma cena visual compacta, sem reescrever audio."""
    num = beat.get("scene_number", 1)
    system = PROMPT_BASE + f"""
Gere apenas a direcao visual da cena {num}/{NUM_CENAS}, {DURACAO_CENA}s, {RESOLUCAO}, {aspect_ratio}.
UNIVERSO: {label_universo(universo)}
{carregar_prompt_universo(universo)}
CAMERA_DIRECTION deve cobrir 0-{DURACAO_CENA}s.
Repita no VISUAL_PROMPT o physical_dna e outfit_dna exatos dos personagens presentes.
LOCATION_LOCK fixa cenario/luz/objetos. CONTINUITY_IN recebe o estado anterior e CONTINUITY_OUT
registra local, posicoes, objetos, aparencia e tensao no ultimo frame.
"""
    user = _json_compacto({
        "theme": tema,
        "language": idioma,
        "cast": _elenco_compacto(elenco),
        "story": _sinopse_compacta(sinopse),
        "contract": _contrato_compacto(sinopse).get("scenes", {}).get(str(num), {}),
        "beat": beat,
        "previous": _cena_anterior_compacta(cena_anterior),
        "frozen_dialogue": _dialogos_compactos({"scenes": {f"SCENE_{num}": dialogo_planejado or {}}}),
    })
    resposta = chamar_api(
        system,
        user,
        schema=CENA_VISUAL_RESPONSE_FORMAT,
        max_completion_tokens=2600,
    )
    return _montar_cena_producao(
        extrair_json(resposta), beat, dialogo_planejado, elenco, idioma
    )


def gerar_cenas_visuais(idioma, tema, aspect_ratio, elenco, sinopse, universo, dialogos_globais):
    """Gera a sequencia visual inteira em uma chamada para reduzir custo e saltos."""
    system = PROMPT_BASE + f"""
Crie APENAS a direcao visual das {NUM_CENAS} cenas em ordem cronologica.
Cada clipe tem EXATAMENTE {DURACAO_CENA}s, formato {aspect_ratio}, resolucao {RESOLUCAO}.

UNIVERSO: {label_universo(universo)}
{carregar_prompt_universo(universo)}

CONTINUIDADE VISUAL OBRIGATORIA:
- Planeje as {NUM_CENAS} cenas como uma unica sequencia antes de responder.
- LOCATION_LOCK fixa arquitetura, horario, luz e objetos ate uma transicao explicita.
- CONTINUITY_OUT registra o ultimo frame: local, posicoes, objetos, danos/roupa e emocao.
- O CONTINUITY_IN seguinte deve continuar exatamente esse estado.
- VISUAL_PROMPT repete literalmente physical_dna e outfit_dna de todo personagem visivel.
- Nao troque especie/modelo, cor, proporcao, roupa, acessorio, voz, objetivo ou objeto de mao.
- CAMERA_DIRECTION traz timeline completa de 0-{DURACAO_CENA}s.
- A acao e o lip-sync servem aos dialogos congelados; nao invente nem reescreva falas.
- Cena N paga a acao/fala anterior, cumpre seu reveal e termina no handoff seguinte.
"""
    user = _json_compacto({
        "theme": tema,
        "dialogue_language": idioma,
        "cast_visual_locks": _elenco_compacto(elenco),
        "story_blueprint": _sinopse_compacta(sinopse),
        "causal_contract": _contrato_compacto(sinopse),
        "frozen_dialogues": _dialogos_compactos(dialogos_globais),
    })
    resposta = chamar_api(
        system,
        user,
        schema=CENAS_VISUAIS_RESPONSE_FORMAT,
        max_completion_tokens=MAX_TOKENS_SCENES,
    )
    dados = extrair_json(resposta)
    visuais = dados.get("scenes", [])
    por_numero = {int(cena.get("SCENE_NUMBER", 0)): cena for cena in visuais}
    esperados = set(range(1, NUM_CENAS + 1))
    if set(por_numero) != esperados:
        raise ValueError(
            f"Cenas visuais invalidas: vieram {sorted(por_numero)}, esperado {sorted(esperados)}."
        )

    beats = {int(b.get("scene_number", 0)): b for b in sinopse.get("beats", [])}
    cenas = {}
    anterior = None
    for num in range(1, NUM_CENAS + 1):
        visual = por_numero[num]
        if anterior:
            visual["CONTINUITY_IN"] = anterior.get("CONTINUITY_OUT", visual.get("CONTINUITY_IN", ""))
        planejado = dialogos_globais.get("scenes", {}).get(f"SCENE_{num}", {})
        cena = _montar_cena_producao(visual, beats[num], planejado, elenco, idioma)
        cenas[num] = cena
        anterior = cena
    return cenas


def gerar_roteiro_cenas(idioma, tema, aspect_ratio, elenco, sinopse, universo, opcoes_agente, sessao=None):
    print("  [3/4] Gerando roteiro — 1 chamada visual para a sequencia completa...")
    dialogos_globais = gerar_dialogos_globais(idioma, tema, elenco, sinopse, universo)
    if sessao:
        salvar(sessao, "dialogos_globais", dialogos_globais, em_log=True)
        print("       -> log/dialogos_globais.json salvo")

    cenas = gerar_cenas_visuais(
        idioma, tema, aspect_ratio, elenco, sinopse, universo, dialogos_globais
    )
    for num, cena in cenas.items():
        if sessao:
            salvar(sessao, f"cena_{num:02d}", cena, em_log=True)
            print(f"       -> log/cena_{num:02d}.json salva")

    print("       Juntando as 7 cenas em roteiro.json...")
    roteiro = juntar_cenas_em_roteiro(cenas, sinopse)
    return enriquecer_roteiro_com_sinopse(
        roteiro,
        aspect_ratio,
        idioma,
        elenco,
        sinopse,
        opcoes_agente=opcoes_agente,
    )


def mostrar_resumo(elenco, sinopse, roteiro):
    print("\n" + "=" * 50)
    print(f"  TITULO:    {roteiro.get('title', elenco.get('title', '?'))}")
    print(f"  TEMA:      {elenco.get('theme', '?')}")
    print(f"  IDIOMA:    {elenco.get('language', '?')}")
    print(f"  DURAÇÃO:   {DURACAO_TOTAL}s ({NUM_CENAS} x {DURACAO_CENA}s)")
    print("=" * 50)

    print(f"\n  HISTÓRIA: {sinopse.get('story_summary', roteiro.get('story_summary', '?'))[:120]}...")

    print("\n--- ELENCO ---\n")
    for p in elenco.get("cast", []):
        print(f"  * {p['name']} ({p.get('character_type', p.get('fruit_type', 'personagem'))})")

    print("\n--- CENAS ---\n")
    cenas = roteiro.get("scenes", {})
    for chave in sorted(cenas, key=lambda k: cenas[k].get("SCENE_NUMBER", 0)):
        c = cenas[chave]
        timing = c.get("DIALOGUE_TIMING", {})
        textos = [l["TEXT"] for l in c.get("DIALOGUE_LINES", []) if "TEXT" in l]
        print(f"  Cena {c.get('SCENE_NUMBER')}: {c.get('SCENE_NAME')} [{c.get('STORY_POSITION', '?')}]")
        print(f"    Beat: {c.get('NARRATIVE_BEAT', '?')[:70]}...")
        if textos:
            print(f"    Fala: \"{textos[0][:50]}...\"" if len(textos[0]) > 50 else f"    Fala: \"{textos[0]}\"")
        print(f"    Câmera: {c.get('CAMERA_DIRECTION', '?')[:70]}...")
        print(f"    Diálogo: {timing.get('word_count', '?')} palavras, ~{timing.get('total_dialogue_seconds', '?')}s")


def _salvar_passo(sessao, nome, dados, em_log=False):
    arquivo = salvar(sessao, nome, dados, em_log=em_log)
    pasta = "log/" if em_log else ""
    print(f"  -> Salvo: {pasta}{nome}.json\n")
    return arquivo


def abrir_pasta_saida(sessao):
    if not OPEN_OUTPUT_FOLDER_ON_FINISH:
        return

    try:
        if os.name == "nt":
            os.startfile(sessao)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", sessao])
        else:
            subprocess.Popen(["xdg-open", sessao])
        print(f"  Pasta aberta: {sessao}\n")
    except Exception as erro:
        print(f"  Nao consegui abrir a pasta automaticamente: {erro}\n")


def gerar_roteiro():
    zerar_uso_tokens()
    dados = perguntar()
    idioma = dados["idioma"]
    tema_original = dados["tema"]
    aspect_ratio = dados["aspect_ratio"]
    universo = dados["universo"]
    opcoes_agente = {
        "confirm_between_steps": dados["agent_confirm_between_steps"],
        "videos_per_step": dados["agent_videos_per_step"],
    }

    sessao = criar_sessao()

    try:
        # O modelo entende o tema original em qualquer idioma. Evitar uma chamada
        # exclusiva de traducao reduz custo e preserva nomes/nuances do pedido.
        tema = tema_original
        _salvar_passo(sessao, "tema", {
            "idioma": idioma,
            "tema_original": tema_original,
            "tema_usado": tema,
            "universo": universo,
            "universo_label": label_universo(universo),
            "opcoes_agente": opcoes_agente,
        }, em_log=True)

        print(f"\nIdioma: {idioma} | Formato: {aspect_ratio} | {DURACAO_TOTAL}s ({NUM_CENAS} cenas)")
        print(f"Modelo: {MODEL} (xAI)")
        print(f"Universo: {label_universo(universo)}")
        print(f"Tema original: {tema_original}")
        print(f"Tema usado: {tema}")
        print(
            "Agente: "
            f"{opcoes_agente['videos_per_step']} vídeo(s) por passo; "
            f"{'pergunta antes de seguir' if opcoes_agente['confirm_between_steps'] else 'segue automaticamente'}"
        )
        print(f"Pasta: {sessao}\nGerando... aguarde.\n")

        elenco = gerar_elenco(idioma, tema, aspect_ratio, universo)
        _salvar_passo(sessao, "elenco", elenco)

        sinopse = gerar_sinopse(idioma, tema, elenco, universo)
        _salvar_passo(sessao, "sinopse", sinopse)

        roteiro = gerar_roteiro_cenas(
            idioma,
            tema,
            aspect_ratio,
            elenco,
            sinopse,
            universo,
            opcoes_agente,
            sessao=sessao,
        )
        _salvar_passo(sessao, "roteiro_rascunho", roteiro, em_log=True)

        enriquecer = lambda r: enriquecer_roteiro_com_sinopse(
            r,
            aspect_ratio,
            idioma,
            elenco,
            sinopse,
            opcoes_agente=opcoes_agente,
        )
        roteiro = corrigir_ate_validar(roteiro, sinopse, idioma, enriquecer, elenco=elenco)
        _salvar_passo(sessao, "roteiro", roteiro)

        auditoria = auditar_roteiro(roteiro, sinopse, elenco, idioma)
        _salvar_passo(sessao, "auditoria_narrativa", auditoria, em_log=True)
    except Exception as erro:
        print(f"\nErro durante a geração. Arquivos já prontos estão em: {sessao}/")
        raise erro

    relatorio = validar_tudo(elenco, roteiro, sinopse)

    imprimir_relatorio(relatorio)
    _salvar_passo(sessao, "validacao", relatorio, em_log=True)

    mostrar_resumo(elenco, sinopse, roteiro)
    uso = resumo_uso_tokens()
    print(
        f"  Tokens API: {uso['prompt']} entrada + {uso['completion']} saida "
        f"= {uso['total']} em {uso['calls']} chamada(s)"
    )
    print(f"  Entrega: {sessao}/ (elenco, sinopse, roteiro)")
    print(f"  Logs:    {sessao}/log/\n")
    abrir_pasta_saida(sessao)
