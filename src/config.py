import os
from dotenv import load_dotenv

from paths import ROOT_DIR

load_dotenv(os.path.join(ROOT_DIR, ".env"))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-pro")