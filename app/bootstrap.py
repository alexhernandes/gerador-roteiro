"""Carrega .env e prepara o ambiente (equivalente ao bootstrap.php)."""

from pathlib import Path

from dotenv import load_dotenv

from paths import ROOT_DIR

load_dotenv(ROOT_DIR / ".env")

# Re-exporta config após carregar o .env
import config  # noqa: E402, F401
