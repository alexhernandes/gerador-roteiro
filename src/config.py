import os
from dotenv import load_dotenv

from paths import ROOT_DIR

load_dotenv(os.path.join(ROOT_DIR, ".env"))


def _env_int(nome, padrao):
    try:
        return int(os.getenv(nome, str(padrao)))
    except (TypeError, ValueError):
        return padrao


def _env_bool(nome, padrao):
    valor = os.getenv(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "sim", "y", "s", "on")


def _env_csv(nome, padrao):
    valor = os.getenv(nome, padrao)
    return [item.strip() for item in valor.split(",") if item.strip()]


XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_BASE_URL = "https://api.x.ai/v1"
MODEL = os.getenv("XAI_MODEL", "grok-4.3")
REASONING_EFFORT = os.getenv("XAI_REASONING_EFFORT", "none")

DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "Português (Brasil)")
DEFAULT_ASPECT_RATIO = os.getenv("DEFAULT_ASPECT_RATIO", "9:16")
DEFAULT_THEME = os.getenv("DEFAULT_THEME", "Livre — crie uma história viral com drama e humor")
DEFAULT_UNIVERSE = os.getenv("DEFAULT_UNIVERSE", "frutinhas")
UNIVERSE_OPTIONS = _env_csv(
    "UNIVERSE_OPTIONS",
    "frutinhas,carros,predios_falantes,humanos_desenhados",
)

VIDEO_RESOLUTION = os.getenv("VIDEO_RESOLUTION", "480p")
SCENE_DURATION_SECONDS = _env_int("SCENE_DURATION_SECONDS", 10)
TOTAL_SCENES = _env_int("TOTAL_SCENES", 7)
TOTAL_DURATION_SECONDS = _env_int(
    "TOTAL_DURATION_SECONDS",
    SCENE_DURATION_SECONDS * TOTAL_SCENES,
)

AGENT_CONFIRM_BETWEEN_STEPS = _env_bool("AGENT_CONFIRM_BETWEEN_STEPS", True)
AGENT_VIDEOS_PER_STEP = max(1, _env_int("AGENT_VIDEOS_PER_STEP", 1))
OPEN_OUTPUT_FOLDER_ON_FINISH = _env_bool("OPEN_OUTPUT_FOLDER_ON_FINISH", True)
