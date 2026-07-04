"""
Auditoria narrativa por LLM.

Este passo nao altera o roteiro. Ele gera um relatorio curto de problemas
semanticos que validadores deterministicos dificilmente enxergam: salto causal,
contradicao, personagem mudando de objetivo ou voz emocional oscilando demais.
"""

import json

from api import chamar_api, extrair_json
from narrativa import story_contract_prompt
from schema import AUDITORIA_RESPONSE_FORMAT
from voz import voice_registry_prompt


def _compactar_roteiro(roteiro):
    cenas = []
    for cena in sorted(roteiro.get("scenes", {}).values(), key=lambda c: c.get("SCENE_NUMBER", 0)):
        falas = [
            {
                "SPEAKER": linha.get("SPEAKER", ""),
                "TEXT": linha.get("TEXT", ""),
                "VOICE_IDENTITY_LOCK": linha.get("VOICE_IDENTITY_LOCK", ""),
            }
            for linha in cena.get("DIALOGUE_LINES", [])
            if "TEXT" in linha
        ]
        cenas.append({
            "SCENE_NUMBER": cena.get("SCENE_NUMBER"),
            "SCENE_ROLE": cena.get("SCENE_ROLE"),
            "STORY_POSITION": cena.get("STORY_POSITION"),
            "NARRATIVE_BEAT": cena.get("NARRATIVE_BEAT"),
            "STORY_CONTRACT": cena.get("STORY_CONTRACT", {}),
            "DIALOGUE_LINES": falas,
        })
    return {
        "title": roteiro.get("title", ""),
        "story_summary": roteiro.get("story_summary", ""),
        "scenes": cenas,
    }


def auditar_roteiro(roteiro, sinopse, elenco, idioma):
    roteiro_json = json.dumps(_compactar_roteiro(roteiro), ensure_ascii=False, indent=2)

    system = f"""
Voce e um script doctor especialista em videos curtos seriados.

Audite SOMENTE:
- continuidade causal entre cenas;
- se cada cena cumpre seu STORY_CONTRACT;
- se os dialogos contam uma historia uniforme;
- se algum personagem parece mudar de voz, intencao ou personalidade sem motivo;
- se o cliffhanger final esta claro.

Nao critique visual, camera, cenario ou estilo 3D.
Nao reescreva o roteiro inteiro. Retorne apenas problemas acionaveis.

{voice_registry_prompt(elenco, idioma)}

{story_contract_prompt(sinopse)}
"""

    user = f"""
Idioma: {idioma}

ROTEIRO COMPACTO:
{roteiro_json}

Retorne overall_status:
- "ok" se estiver coeso;
- "needs_revision" se houver saltos, contradicoes ou voz inconsistente.

Em problems, liste no maximo 12 problemas. Se estiver ok, problems deve ser [].
"""

    try:
        resposta = chamar_api(system, user, schema=AUDITORIA_RESPONSE_FORMAT)
        return extrair_json(resposta)
    except Exception as erro:
        return {
            "overall_status": "audit_failed",
            "problems": [
                {
                    "scene_number": 0,
                    "category": "audit_error",
                    "severity": "warning",
                    "issue": f"Auditoria narrativa falhou: {erro}",
                    "suggested_fix": "Rode novamente ou revise validacao.json.",
                }
            ],
        }
