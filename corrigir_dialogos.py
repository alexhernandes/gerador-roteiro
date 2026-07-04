"""
Passo dedicado: reescreve DIALOGUE_LINES com muitas falas,
idioma correto e timing que preenche os 10 segundos.
"""

import json

from api import chamar_api, extrair_json
from dialogo import (
    analisar_dialogos_roteiro,
    lock_idioma_texto,
    normalizar_idioma,
    PALAVRAS_POR_SEGUNDO,
    MIN_FALAS_POR_CENA,
    MAX_FALAS_POR_CENA,
    MIN_SEGUNDOS_FALA,
    MAX_SEGUNDOS_FALA,
    PAUSA_PADRAO,
)
from schema import CORRECAO_DIALOGOS_RESPONSE_FORMAT, DURACAO_CENA


def _exemplo_dialogo(idioma):
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


def corrigir_dialogos(roteiro, sinopse, idioma, problemas=None):
    codigo = normalizar_idioma(idioma)
    wps = PALAVRAS_POR_SEGUNDO.get(codigo, 3.2)
    min_palavras = int(MIN_SEGUNDOS_FALA * wps)
    max_palavras = int(MAX_SEGUNDOS_FALA * wps)
    lock = lock_idioma_texto(idioma)

    problemas_txt = ""
    if problemas:
        problemas_txt = "PROBLEMAS A CORRIGIR:\n" + "\n".join(f"- {p}" for p in problemas)

    roteiro_json = json.dumps(roteiro, ensure_ascii=False, indent=2)
    sinopse_json = json.dumps(sinopse, ensure_ascii=False, indent=2)

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

Retorne SCENE_NUMBER, DIALOGUE_LINES, DELIVERY_STYLE, VOICE_OVERRIDE_METADATA por cena.

{_exemplo_dialogo(idioma)}
"""

    user = f"""
{problemas_txt}

SINOPSE:
{sinopse_json}

ROTEIRO ATUAL (reescreva só os diálogos):
{roteiro_json}

Reescreva DIALOGUE_LINES das 7 cenas em {idioma}.
Muitas falas curtas. Preencha {MIN_SEGUNDOS_FALA}-{MAX_SEGUNDOS_FALA}s de áudio por cena.
"""

    print("  [4/4] Corrigindo e expandindo diálogos...")
    ultimo_erro = None
    for tentativa in range(1, 4):
        try:
            resposta = chamar_api(system, user, schema=CORRECAO_DIALOGOS_RESPONSE_FORMAT)
            correcao = extrair_json(resposta)
            return _aplicar_correcao(roteiro, correcao)
        except (ValueError, AttributeError) as erro:
            ultimo_erro = erro
            if tentativa < 3:
                print(f"  !! Resposta inválida da API ({erro}). Tentativa {tentativa + 1}/3...")
            continue
    raise ValueError(f"Falha ao corrigir diálogos após 3 tentativas: {ultimo_erro}")


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


def corrigir_ate_validar(roteiro, sinopse, idioma, enriquecer_fn, max_tentativas=3):
    for tentativa in range(1, max_tentativas + 1):
        problemas = analisar_dialogos_roteiro(roteiro, idioma)
        if not problemas:
            print("  -> Diálogos OK.\n")
            return roteiro

        print(f"\n  !! {len(problemas)} problema(s) nos diálogos. Correção {tentativa}/{max_tentativas}...")
        for p in problemas[:5]:
            print(f"     - {p}")
        if len(problemas) > 5:
            print(f"     - ... e mais {len(problemas) - 5}")

        roteiro = corrigir_dialogos(roteiro, sinopse, idioma, problemas)
        roteiro = enriquecer_fn(roteiro)

    return roteiro