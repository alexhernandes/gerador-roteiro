import json
import re
import time
from openai import OpenAI
from config import (
    XAI_API_KEY,
    XAI_BASE_URL,
    MODEL,
    REASONING_EFFORT,
    MAX_TOKENS_DEFAULT,
)

MAX_TENTATIVAS_API = 3
PAUSA_RETRY_SEGUNDOS = 2
USO_TOKENS = {"prompt": 0, "completion": 0, "total": 0, "calls": 0}


def criar_cliente():
    if not XAI_API_KEY:
        raise ValueError(
            "Coloque sua chave xAI no arquivo .env\n"
            "Exemplo: XAI_API_KEY=sua_chave_aqui\n"
            "Obtenha em: https://console.x.ai/"
        )
    return OpenAI(base_url=XAI_BASE_URL, api_key=XAI_API_KEY)


def _kwargs_grok(kwargs, max_completion_tokens=MAX_TOKENS_DEFAULT):
    """Parâmetros extras para modelos Grok 4.3 na xAI."""
    if "grok-4.3" in MODEL or "grok-4" in MODEL:
        kwargs["reasoning_effort"] = REASONING_EFFORT
    kwargs["max_completion_tokens"] = max_completion_tokens
    return kwargs


def _registrar_uso(response):
    usage = getattr(response, "usage", None)
    if not usage:
        return
    prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion = int(getattr(usage, "completion_tokens", 0) or 0)
    total = int(getattr(usage, "total_tokens", prompt + completion) or 0)
    USO_TOKENS["prompt"] += prompt
    USO_TOKENS["completion"] += completion
    USO_TOKENS["total"] += total
    USO_TOKENS["calls"] += 1
    print(
        f"       tokens: {prompt} entrada + {completion} saida = {total} "
        f"(sessao: {USO_TOKENS['total']})"
    )


def resumo_uso_tokens():
    return dict(USO_TOKENS)


def zerar_uso_tokens():
    USO_TOKENS.update({"prompt": 0, "completion": 0, "total": 0, "calls": 0})


def chamar_api(
    system_prompt,
    user_prompt,
    schema=None,
    max_tentativas=MAX_TENTATIVAS_API,
    max_completion_tokens=MAX_TOKENS_DEFAULT,
):
    client = criar_cliente()

    kwargs = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    kwargs = _kwargs_grok(kwargs, max_completion_tokens)

    if schema:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": schema,
        }

    ultimo_erro = None
    for tentativa in range(1, max_tentativas + 1):
        try:
            response = client.chat.completions.create(**kwargs)
            _registrar_uso(response)
            if not response.choices:
                raise ValueError("Resposta da API sem choices.")

            content = response.choices[0].message.content
            if content is None or not str(content).strip():
                raise ValueError("Resposta vazia da API (content=None).")

            return content
        except Exception as erro:
            ultimo_erro = erro
            if tentativa < max_tentativas:
                pausa = PAUSA_RETRY_SEGUNDOS * tentativa
                print(f"  !! API falhou ({erro}). Tentativa {tentativa + 1}/{max_tentativas} em {pausa}s...")
                time.sleep(pausa)
                continue
            raise ValueError(f"API falhou após {max_tentativas} tentativas: {ultimo_erro}") from erro


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

    if "beats" in obj:
        return obj

    if "cast" in obj and "beats" not in obj:
        tem_cenas_soltas = any(k.startswith("SCENE") for k in obj)
        cenas = obj.get("scenes") or {}
        if not tem_cenas_soltas and not cenas:
            return _limpar_lixo_legado(obj)

    if obj.get("SCENE_NUMBER") and "scenes" not in obj:
        return obj

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

        if obj.get("SCENE_NUMBER") and "scenes" not in obj:
            num = obj["SCENE_NUMBER"]
            resultado["scenes"][f"SCENE_{num}"] = obj
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
