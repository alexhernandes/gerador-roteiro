import os

from dotenv import load_dotenv

from paths import ROOT_DIR

load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Segredo: fica no .env.
XAI_API_KEY = os.getenv("XAI_API_KEY", "")

# API/modelo.
XAI_BASE_URL     = "https://api.x.ai/v1"
MODEL            = "grok-4.3"
REASONING_EFFORT = "low"

# Defaults da interface.
DEFAULT_LANGUAGE     = "Português (Brasil)"
DEFAULT_ASPECT_RATIO = "9:16"
DEFAULT_THEME        = "Livre — crie uma história viral com drama e humor"

# Universo/preset visual dos personagens.
DEFAULT_UNIVERSE = "frutinhas"
UNIVERSE_OPTIONS = [
    "frutinhas",
    "carros",
    "predios_falantes",
    "humanos_desenhados",
]

# Configuração do vídeo/roteiro.
VIDEO_RESOLUTION       = "480p"
SCENE_DURATION_SECONDS = 10
TOTAL_SCENES           = 7
TOTAL_DURATION_SECONDS = SCENE_DURATION_SECONDS * TOTAL_SCENES

# Execução do agente de vídeo.
AGENT_CONFIRM_BETWEEN_STEPS = True
AGENT_VIDEOS_PER_STEP       = 1

# UX local.
OPEN_OUTPUT_FOLDER_ON_FINISH = True
