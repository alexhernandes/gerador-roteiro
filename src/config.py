import os
from dotenv import load_dotenv

from paths import ROOT_DIR

load_dotenv(os.path.join(ROOT_DIR, ".env"))

XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_BASE_URL = "https://api.x.ai/v1"
MODEL = os.getenv("XAI_MODEL", "grok-4.3")
REASONING_EFFORT = os.getenv("XAI_REASONING_EFFORT", "none")