import json
import os
from datetime import datetime


def criar_sessao():
    pasta = os.path.join("output", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(pasta, exist_ok=True)
    return pasta


def salvar(sessao, nome, dados):
    arquivo = os.path.join(sessao, f"{nome}.json")
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return arquivo