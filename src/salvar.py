import json
import os
from datetime import datetime

from paths import ROOT_DIR


def _serializar_json(obj):
    if hasattr(obj, "group"):
        return obj.group(0)
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Tipo não serializável: {type(obj).__name__}")


def criar_sessao():
    pasta = os.path.join(ROOT_DIR, "output", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(pasta, exist_ok=True)
    return pasta


def salvar(sessao, nome, dados):
    arquivo = os.path.join(sessao, f"{nome}.json")
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2, default=_serializar_json)
    return arquivo