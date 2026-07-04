"""
Gera elenco + sinopse + roteiro em JSONs separados.
Uso: python main.py
"""

import json
import os

from api import chamar_api, extrair_json
from paths import ROOT_DIR
from config import MODEL
from corrigir_dialogos import corrigir_ate_validar
from dialogo import lock_idioma_texto
from entrada import perguntar
from enriquecer import enriquecer_elenco, enriquecer_sinopse, enriquecer_roteiro
from instrucoes_roteiro import bloco_sinopse, bloco_cena
from salvar import criar_sessao, salvar
from schema import (
    ELENCO_RESPONSE_FORMAT,
    SINOPSE_RESPONSE_FORMAT,
    CENA_RESPONSE_FORMAT,
    RESOLUCAO,
    DURACAO_CENA,
    NUM_CENAS,
    DURACAO_TOTAL,
)

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


def carregar_prompt():
    caminho = os.path.join(ROOT_DIR, "prompt.txt")
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


PROMPT_BASE = carregar_prompt()


def _bloco_idioma(idioma):
    lock = lock_idioma_texto(idioma)
    return f"""
IDIOMA INQUEBRÁVEL — REJEIÇÃO AUTOMÁTICA SE VIOLAR:
- Idioma escolhido pelo usuário: {idioma}
- 100% dos TEXT em {idioma}. Nenhuma palavra em inglês/outro idioma.
- VOICE_IDENTITY_LOCK: "{lock}" em TODAS as falas sem exceção.
- Áudio = SOMENTE DIALOGUE_LINES > TEXT.
"""


def gerar_elenco(idioma, tema, aspect_ratio):
    system = PROMPT_BASE + f"""

Crie APENAS o ELENCO.
Tema: {tema}. Formato: {aspect_ratio}. Resolução: {RESOLUCAO}. language: "{idioma}".

- Frutas antropomórficas, pele 100% fruta
- physical_dna e outfit_dna completos
- 2 a 5 personagens com papéis claros na trama (protagonista, antagonista, aliado, etc.)
- ai_image_task por personagem
"""

    user = f"Elenco para vídeo de {DURACAO_TOTAL}s sobre: {tema}"

    print("  [1/4] Gerando elenco...")
    resposta = chamar_api(system, user, schema=ELENCO_RESPONSE_FORMAT)
    return enriquecer_elenco(extrair_json(resposta), aspect_ratio, idioma)


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
    atos_ok = all(
        len(sinopse.get(campo, "").strip()) >= MIN_TAMANHO_ATO
        for campo in ("act_1", "act_2", "act_3")
    )
    return (
        len(sinopse.get("story_summary", "")) > 30
        and len(beats) >= NUM_CENAS
        and atos_ok
    )


def gerar_sinopse(idioma, tema, elenco, tentativa=1):
    elenco_json = json.dumps(elenco, ensure_ascii=False, indent=2)

    reforco = ""
    if tentativa > 1:
        reforco = """
CORREÇÃO: a sinopse anterior veio incompleta.
Preencha OBRIGATORIAMENTE: story_summary, act_1, act_2, act_3 (mínimo 2 frases cada) e beats com 7 itens.
NÃO use rótulos curtos como "início (Cenas 1-2)" — descreva o que acontece em cada ato.
"""

    system = PROMPT_BASE + bloco_sinopse(idioma, tema) + f"""

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
    resposta = chamar_api(system, user, schema=SINOPSE_RESPONSE_FORMAT)
    sinopse = extrair_json(resposta)

    if not _sinopse_valida(sinopse) and tentativa < 3:
        print("  !! Sinopse incompleta. Tentando de novo...\n")
        return gerar_sinopse(idioma, tema, elenco, tentativa + 1)

    if not _sinopse_valida(sinopse):
        raise ValueError(
            "Sinopse veio incompleta da API (sem beats ou story_summary). "
            "Tente rodar de novo."
        )

    return enriquecer_sinopse(sinopse, idioma)


def juntar_cenas_em_roteiro(cenas, sinopse):
    """Monta roteiro.json juntando manualmente as cenas das 7 chamadas à API."""
    titulo = sinopse.get("title", "").replace("Sinopse - ", "").strip() or "Roteiro"
    return {
        "title": titulo,
        "story_summary": sinopse.get("story_summary", ""),
        "scenes": {f"SCENE_{num}": cena for num, cena in sorted(cenas.items())},
    }


def gerar_cena(idioma, tema, aspect_ratio, elenco, sinopse, beat, cena_anterior=None):
    num = beat.get("scene_number", 1)
    elenco_json = json.dumps(elenco, ensure_ascii=False, indent=2)
    sinopse_json = json.dumps(sinopse, ensure_ascii=False, indent=2)
    cena_anterior_json = ""
    if cena_anterior:
        cena_anterior_json = json.dumps(cena_anterior, ensure_ascii=False, indent=2)

    system = PROMPT_BASE + _bloco_idioma(idioma) + bloco_cena(beat, cena_anterior, idioma, tema) + f"""

FORMATO: {aspect_ratio}, {RESOLUCAO}, cena de {DURACAO_CENA}s.
language = "{idioma}".

CONTEXTO FIXO EM TODA CHAMADA:
  1) SINOPSE COMPLETA (blueprint — não mude a história)
  2) CENA ANTERIOR completa (quando existir — mantenha continuidade)

SINOPSE:
{sinopse_json}

ELENCO (nomes exatos em SPEAKER e VISUAL_PROMPT):
{elenco_json}

Campos obrigatórios desta cena:
- SCENE_NUMBER: {num}
- SCENE_NAME: título curto da cena
- SCENE_ROLE: "{ROLES_POR_CENA.get(num, 'scene')}"
- STORY_POSITION: "{beat.get('story_position', '')}"
- NARRATIVE_BEAT, OPENING_HOOK (cena 1), CAMERA_DIRECTION, PHYSICAL_MOVEMENT
- ACTION_DIRECTION, VISUAL_PROMPT, DIALOGUE_LINES, DELIVERY_STYLE
- HAS_DIALOGUE: true, AUDIO_SPEAKER, AUDIO_TARGET, AUDIO_TIMING_CONTROLS
- VOICE_OVERRIDE_METADATA (um entry por SPEAKER)

Retorne APENAS o JSON desta cena — não gere as outras cenas.
"""

    contexto_anterior = ""
    if cena_anterior_json:
        contexto_anterior = f"""
CENA ANTERIOR (JSON completo — esta cena começa onde a anterior parou):
{cena_anterior_json}
"""

    user = f"""
Gere SOMENTE a Cena {num} de {NUM_CENAS}.
Tema: {tema}. Idioma: {idioma}.
Use o beat {num} da sinopse.
{contexto_anterior}
Mantenha continuidade: mesmos personagens, mesmo local/tensão, consequência direta da cena anterior.
"""

    resposta = chamar_api(system, user, schema=CENA_RESPONSE_FORMAT)
    cena = extrair_json(resposta)
    cena["SCENE_NUMBER"] = num
    cena.setdefault("SCENE_ROLE", ROLES_POR_CENA.get(num, "scene"))
    cena.setdefault("STORY_POSITION", beat.get("story_position", ""))
    cena.setdefault("NARRATIVE_BEAT", beat.get("narrative_beat", ""))
    return cena


def gerar_roteiro_cenas(idioma, tema, aspect_ratio, elenco, sinopse, sessao=None):
    beats = sorted(sinopse.get("beats", []), key=lambda b: b.get("scene_number", 0))
    cenas = {}
    cena_anterior = None

    print(f"  [3/4] Gerando roteiro — {NUM_CENAS} chamadas à API (1 cena cada)...")
    for beat in beats:
        num = beat.get("scene_number", len(cenas) + 1)
        print(f"       Chamada {num}/{NUM_CENAS} → Cena {num}...")
        cena = gerar_cena(idioma, tema, aspect_ratio, elenco, sinopse, beat, cena_anterior)
        cenas[num] = cena
        cena_anterior = cena

        if sessao:
            salvar(sessao, f"cena_{num:02d}", cena, em_log=True)
            print(f"       -> log/cena_{num:02d}.json salva")

    print("       Juntando as 7 cenas em roteiro.json...")
    roteiro = juntar_cenas_em_roteiro(cenas, sinopse)
    return enriquecer_roteiro(roteiro, aspect_ratio, idioma, elenco)


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
        print(f"  * {p['name']} ({p['fruit_type']})")

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


def gerar_roteiro():
    dados = perguntar()
    idioma = dados["idioma"]
    tema = dados["tema"]
    aspect_ratio = dados["aspect_ratio"]

    sessao = criar_sessao()

    print(f"\nIdioma: {idioma} | Formato: {aspect_ratio} | {DURACAO_TOTAL}s ({NUM_CENAS} cenas)")
    print(f"Modelo: {MODEL} (xAI)")
    print(f"Tema: {tema}")
    print(f"Pasta: {sessao}\nGerando... aguarde.\n")

    try:
        elenco = gerar_elenco(idioma, tema, aspect_ratio)
        _salvar_passo(sessao, "elenco", elenco)

        sinopse = gerar_sinopse(idioma, tema, elenco)
        _salvar_passo(sessao, "sinopse", sinopse)

        roteiro = gerar_roteiro_cenas(idioma, tema, aspect_ratio, elenco, sinopse, sessao=sessao)
        _salvar_passo(sessao, "roteiro_rascunho", roteiro, em_log=True)

        enriquecer = lambda r: enriquecer_roteiro(r, aspect_ratio, idioma, elenco)
        roteiro = corrigir_ate_validar(roteiro, sinopse, idioma, enriquecer)
        _salvar_passo(sessao, "roteiro", roteiro)
    except Exception as erro:
        print(f"\nErro durante a geração. Arquivos já prontos estão em: {sessao}/")
        raise erro

    relatorio = validar_tudo(elenco, roteiro, sinopse)

    imprimir_relatorio(relatorio)
    _salvar_passo(sessao, "validacao", relatorio, em_log=True)

    mostrar_resumo(elenco, sinopse, roteiro)
    print(f"  Entrega: {sessao}/ (elenco, sinopse, roteiro)")
    print(f"  Logs:    {sessao}/log/\n")