"""
Universos visuais/personagens.

Cada universo tem um prompt base em prompts/universos/*.txt. Isso evita que
o sistema fique preso em frutinhas e permite trocar para carros, predios,
humanos desenhados etc. sem reescrever o pipeline.
"""

from pathlib import Path

from config import DEFAULT_UNIVERSE, UNIVERSE_OPTIONS
from paths import ROOT_DIR


UNIVERSE_LABELS = {
    "frutinhas": "Frutinhas antropomórficas",
    "carros": "Carros falantes",
    "predios_falantes": "Prédios falantes",
    "humanos_desenhados": "Humanos desenhados",
}

UNIVERSE_DIR = Path(ROOT_DIR) / "prompts" / "universos"


def normalizar_universo(universo):
    valor = str(universo or "").strip().lower()
    valor = valor.replace(" ", "_").replace("-", "_")
    aliases = {
        "frutas": "frutinhas",
        "fruits": "frutinhas",
        "fruit": "frutinhas",
        "cars": "carros",
        "buildings": "predios_falantes",
        "predios": "predios_falantes",
        "prédios": "predios_falantes",
        "humanos": "humanos_desenhados",
        "humans": "humanos_desenhados",
    }
    return aliases.get(valor, valor or DEFAULT_UNIVERSE)


def listar_universos():
    ids = []
    for universo in UNIVERSE_OPTIONS:
        normalizado = normalizar_universo(universo)
        if normalizado not in ids:
            ids.append(normalizado)

    if UNIVERSE_DIR.exists():
        for arquivo in sorted(UNIVERSE_DIR.glob("*.txt")):
            if arquivo.stem not in ids:
                ids.append(arquivo.stem)

    return ids


def label_universo(universo):
    universo = normalizar_universo(universo)
    return UNIVERSE_LABELS.get(universo, universo.replace("_", " ").title())


def carregar_prompt_universo(universo):
    universo = normalizar_universo(universo)
    caminho = UNIVERSE_DIR / f"{universo}.txt"
    if not caminho.is_file():
        caminho = UNIVERSE_DIR / f"{normalizar_universo(DEFAULT_UNIVERSE)}.txt"
    if not caminho.is_file():
        return (
            "UNIVERSO: personagens estilizados consistentes. "
            "Crie character_type, physical_dna, outfit_dna, voice_profile e ai_image_task."
        )
    return caminho.read_text(encoding="utf-8").strip()
