"""
Gera elenco + sinopse + roteiro em JSONs separados.
Uso: python gerar_roteiro.py
"""

import json
import os

from api import chamar_api, extrair_json
from config import MODEL
from corrigir_dialogos import corrigir_ate_validar
from dialogo import lock_idioma_texto
from entrada import perguntar
from enriquecer import enriquecer_elenco, enriquecer_roteiro
from instrucoes_roteiro import bloco_sinopse, bloco_roteiro, bloco_dialogo_denso
from salvar import criar_sessao, salvar
from schema import (
    ELENCO_RESPONSE_FORMAT,
    SINOPSE_RESPONSE_FORMAT,
    ROTEIRO_RESPONSE_FORMAT,
    RESOLUCAO,
    DURACAO_CENA,
    NUM_CENAS,
    DURACAO_TOTAL,
)
from validar import validar_tudo, imprimir_relatorio, tem_erros_criticos


def carregar_prompt():
    caminho = os.path.join(os.path.dirname(__file__), "prompt.txt")
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
    return (
        len(sinopse.get("story_summary", "")) > 30
        and len(beats) >= NUM_CENAS
        and sinopse.get("act_1")
        and sinopse.get("act_2")
        and sinopse.get("act_3")
    )


def gerar_sinopse(idioma, tema, elenco, tentativa=1):
    elenco_json = json.dumps(elenco, ensure_ascii=False, indent=2)

    reforco = ""
    if tentativa > 1:
        reforco = """
CORREÇÃO: a sinopse anterior veio incompleta.
Preencha OBRIGATORIAMENTE: story_summary, act_1, act_2, act_3 e beats com 7 itens.
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

    return sinopse


def gerar_roteiro_cenas(idioma, tema, aspect_ratio, elenco, sinopse, reforco=False):
    elenco_json = json.dumps(elenco, ensure_ascii=False, indent=2)
    sinopse_json = json.dumps(sinopse, ensure_ascii=False, indent=2)

    reforco_txt = ""
    if reforco:
        reforco_txt = f"""
CORREÇÃO: diálogos anteriores estavam no idioma errado.
Reescreva TODOS os TEXT em {idioma}.
"""

    system = PROMPT_BASE + _bloco_idioma(idioma) + bloco_dialogo_denso(idioma) + bloco_roteiro(idioma, tema) + f"""

FORMATO: {aspect_ratio}, {RESOLUCAO}, {NUM_CENAS} cenas x {DURACAO_CENA}s = {DURACAO_TOTAL}s.
language = "{idioma}".

SINOPSE APROVADA (siga fielmente, não mude a história):
{sinopse_json}

ELENCO:
{elenco_json}

Campos obrigatórios por cena:
- STORY_POSITION: "início", "meio" ou "fim"
- NARRATIVE_BEAT: o que acontece nesta cena na história
- CAMERA_DIRECTION: timeline 0-10s com shots, zoom, dolly, pan, ângulos
- PHYSICAL_MOVEMENT: ações físicas dos personagens
- ACTION_DIRECTION: direção integrada + lip-sync
- VISUAL_PROMPT: SET + personagens com outfit completo + iluminação
- DIALOGUE_LINES > TEXT: falas que contam a história (de dialogue_intent da sinopse)

story_summary no root: copie da sinopse.
{reforco_txt}
"""

    user = f"""
Expanda a sinopse em roteiro completo de {NUM_CENAS} cenas.
Tema: {tema}. Idioma: {idioma}.
Cada cena com câmera detalhada e diálogos que avançam a trama.
"""

    print("  [3/4] Gerando roteiro detalhado...")
    resposta = chamar_api(system, user, schema=ROTEIRO_RESPONSE_FORMAT)
    roteiro = extrair_json(resposta)

    if not roteiro.get("story_summary") and sinopse.get("story_summary"):
        roteiro["story_summary"] = sinopse["story_summary"]

    return enriquecer_roteiro(roteiro, aspect_ratio, idioma)


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


def _salvar_passo(sessao, nome, dados):
    arquivo = salvar(sessao, nome, dados)
    print(f"  -> Salvo: {arquivo}\n")
    return arquivo


def gerar_roteiro():
    dados = perguntar()
    idioma = dados["idioma"]
    tema = dados["tema"]
    aspect_ratio = dados["aspect_ratio"]

    sessao = criar_sessao()

    print(f"\nIdioma: {idioma} | Formato: {aspect_ratio} | {DURACAO_TOTAL}s ({NUM_CENAS} cenas)")
    print(f"Modelo: {MODEL}")
    print(f"Tema: {tema}")
    print(f"Pasta: {sessao}\nGerando... aguarde.\n")

    try:
        elenco = gerar_elenco(idioma, tema, aspect_ratio)
        _salvar_passo(sessao, "elenco", elenco)

        sinopse = gerar_sinopse(idioma, tema, elenco)
        _salvar_passo(sessao, "sinopse", sinopse)

        roteiro = gerar_roteiro_cenas(idioma, tema, aspect_ratio, elenco, sinopse)
        _salvar_passo(sessao, "roteiro", roteiro)

        enriquecer = lambda r: enriquecer_roteiro(r, aspect_ratio, idioma)
        roteiro = corrigir_ate_validar(roteiro, sinopse, idioma, enriquecer)
        _salvar_passo(sessao, "roteiro", roteiro)
    except Exception as erro:
        print(f"\nErro durante a geração. Arquivos já prontos estão em: {sessao}/")
        raise erro

    relatorio = validar_tudo(elenco, roteiro, sinopse)

    imprimir_relatorio(relatorio)
    _salvar_passo(sessao, "validacao", relatorio)

    mostrar_resumo(elenco, sinopse, roteiro)
    print(f"  Tudo em: {sessao}/\n")


if __name__ == "__main__":
    try:
        gerar_roteiro()
    except Exception as e:
        print(f"\nErro: {e}\n")
    input("Aperte ENTER para sair...")