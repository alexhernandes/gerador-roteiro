import json
import re
from openai import OpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL


def criar_cliente():
    if not OPENROUTER_API_KEY:
        raise ValueError(
            "Coloque sua chave no arquivo .env\n"
            "Exemplo: OPENROUTER_API_KEY=sua_chave_aqui"
        )
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)


def chamar_api(system_prompt, user_prompt, schema=None):
    client = criar_cliente()

    kwargs = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    if schema:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": schema,
        }

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def _limpar_texto(texto):
    if not texto:
        raise ValueError("Resposta vazia da API.")
    texto = texto.strip()
    blocos = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", texto)
    if blocos:
        return max(blocos, key=len).strip()
    return texto


def _achar_inicio_json(texto):
    for i, char in enumerate(texto):
        if char in "{[":
            return i
    return None


def extrair_json(texto):
    texto = _limpar_texto(texto)
    inicio = _achar_inicio_json(texto)

    if inicio is None:
        raise ValueError("Nenhum JSON encontrado na resposta da API.")

    texto = texto[inicio:]
    decoder = json.JSONDecoder()
    objetos = []
    idx = 0

    while idx < len(texto):
        while idx < len(texto) and texto[idx] not in "{[":
            idx += 1
        if idx >= len(texto):
            break
        try:
            obj, fim = decoder.raw_decode(texto, idx)
            objetos.append(obj)
            idx = fim
        except json.JSONDecodeError:
            break

    if not objetos:
        raise ValueError("Não consegui ler o JSON da resposta da API.")

    if len(objetos) == 1:
        return _normalizar(objetos[0])

    return _normalizar(_juntar_objetos(objetos))


def _formato_legado_corrompido(obj):
    """Detecta JSON esvaziado pela normalização antiga (title/idea/cast/scenes)."""
    if not isinstance(obj, dict):
        return False
    return (
        "idea" in obj
        and "beats" not in obj
        and not obj.get("story_summary")
        and not obj.get("cast")
    )


def _limpar_lixo_legado(obj):
    return {chave: valor for chave, valor in obj.items() if chave not in ("idea", "scenes")}


def _normalizar(obj):
    """
    Normaliza só roteiros com cenas soltas (SCENE_1, SCENE_2...).
    Sinopse, elenco e outros JSONs passam intactos.
    """
    if not isinstance(obj, dict):
        return obj

    if _formato_legado_corrompido(obj):
        raise ValueError(
            "JSON corrompido (formato legado sem beats/story_summary). "
            "A resposta da API foi descartada pela normalização antiga ou veio incompleta."
        )

    # Sinopse — manter todos os campos (beats, story_summary, etc.)
    if "beats" in obj:
        return obj

    # Elenco — manter todos os campos (cast, ai_instructions, etc.)
    if "cast" in obj and "beats" not in obj:
        tem_cenas_soltas = any(k.startswith("SCENE") for k in obj)
        cenas = obj.get("scenes") or {}
        if not tem_cenas_soltas and not cenas:
            return _limpar_lixo_legado(obj)

    # Roteiro — juntar cenas que vieram soltas no root
    scenes = dict(obj.get("scenes", {}))
    for chave, valor in obj.items():
        if chave.startswith("SCENE") and chave not in scenes:
            scenes[chave] = valor

    if scenes:
        resultado = dict(obj)
        resultado["scenes"] = scenes
        return resultado

    return obj


def _juntar_objetos(objetos):
    """Junta vários JSONs de cenas em um roteiro."""
    resultado = {"title": "", "story_summary": "", "scenes": {}}

    for obj in objetos:
        if not isinstance(obj, dict):
            continue

        if obj.get("title"):
            resultado["title"] = obj["title"]
        if obj.get("story_summary"):
            resultado["story_summary"] = obj["story_summary"]
        if obj.get("scenes"):
            resultado["scenes"].update(obj["scenes"])
        else:
            for chave, valor in obj.items():
                if chave.startswith("SCENE"):
                    resultado["scenes"][chave] = valor

    if not resultado["scenes"]:
        raise ValueError("JSON encontrado, mas sem cenas.")

    return resultado