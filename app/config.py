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
    "animais_falantes",
    "humanos_desenhados",
]

# Configuração do vídeo/roteiro.
VIDEO_RESOLUTION       = "720p"
SCENE_DURATION_SECONDS = 15
TOTAL_SCENES           = 7
TOTAL_DURATION_SECONDS = SCENE_DURATION_SECONDS * TOTAL_SCENES

# Limites por tipo de resposta. Limites menores evitam raciocinio/saida
# desnecessarios e tornam o custo previsivel sem cortar JSONs validos.
MAX_TOKENS_DEFAULT   = 6000
MAX_TOKENS_CAST      = 3200
MAX_TOKENS_SYNOPSIS  = 4200
MAX_TOKENS_DIALOGUES = 5200
MAX_TOKENS_SCENES    = 8000
MAX_TOKENS_REPAIR    = 2600
MAX_TOKENS_AUDIT     = 2200

# Execução do agente de vídeo.
AGENT_CONFIRM_BETWEEN_STEPS = True
AGENT_VIDEOS_PER_STEP       = 1

# UX local.
OPEN_OUTPUT_FOLDER_ON_FINISH = True
