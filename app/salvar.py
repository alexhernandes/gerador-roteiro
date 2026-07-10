import json
import os
import re
from datetime import date, datetime
from pathlib import Path

from paths import ROOT_DIR


def _converter_valor(obj):
    if isinstance(obj, re.Match):
        return obj.group(0)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if hasattr(obj, "group") and callable(obj.group):
        try:
            return obj.group(0)
        except (IndexError, TypeError):
            return str(obj)
    raise TypeError(f"Tipo não serializável: {type(obj).__name__}")


def sanitizar_para_json(obj):
    """Remove tipos não serializáveis (ex.: re.Match) de estruturas aninhadas."""
    if isinstance(obj, dict):
        return {chave: sanitizar_para_json(valor) for chave, valor in obj.items()}
    if isinstance(obj, list):
        return [sanitizar_para_json(item) for item in obj]
    if isinstance(obj, tuple):
        return [sanitizar_para_json(item) for item in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, re.Match):
        return obj.group(0)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return [sanitizar_para_json(item) for item in obj]
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if hasattr(obj, "group") and callable(obj.group):
        try:
            return obj.group(0)
        except (IndexError, TypeError):
            return str(obj)
    return str(obj)


def criar_sessao():
    pasta = os.path.join(ROOT_DIR, "output", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(pasta, exist_ok=True)
    os.makedirs(pasta_log(pasta), exist_ok=True)
    return pasta


def pasta_log(sessao):
    return os.path.join(sessao, "log")


def salvar(sessao, nome, dados, em_log=False):
    destino = pasta_log(sessao) if em_log else sessao
    os.makedirs(destino, exist_ok=True)
    arquivo = os.path.join(destino, f"{nome}.json")
    limpo = sanitizar_para_json(dados)
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(limpo, f, ensure_ascii=False, indent=2, default=_converter_valor)
    return arquivo