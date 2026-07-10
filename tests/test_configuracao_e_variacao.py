import json
import random
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from config import SCENE_DURATION_SECONDS, TOTAL_DURATION_SECONDS, TOTAL_SCENES  # noqa: E402
from api import _kwargs_grok  # noqa: E402
from entrada import IDIOMAS, selecionar_menu  # noqa: E402
from gerar_roteiro import PROMPT_BASE  # noqa: E402
from schema import (  # noqa: E402
    CENAS_VISUAIS_SCHEMA,
    DIALOGOS_CRIATIVOS_SCHEMA,
    ELENCO_CRIATIVO_SCHEMA,
)
from universos import carregar_prompt_universo, listar_universos  # noqa: E402
from variacao import criar_brief_variacao  # noqa: E402


class ConfiguracaoVariacaoTest(unittest.TestCase):
    def test_clipes_tem_15_segundos(self):
        self.assertEqual(SCENE_DURATION_SECONDS, 15)
        self.assertEqual(TOTAL_SCENES, 7)
        self.assertEqual(TOTAL_DURATION_SECONDS, 105)

    def test_interface_tem_japones(self):
        self.assertIn("日本語 (Japanese)", IDIOMAS)

    def test_terminal_sem_tty_ainda_permite_escolher_idioma(self):
        with patch("entrada.sys.stdin.isatty", return_value=False), patch(
            "builtins.input", return_value="4"
        ):
            selecionado = selecionar_menu("Idioma?", IDIOMAS, "Português (Brasil)")
        self.assertEqual(selecionado, "Deutsch")

    def test_entrada_invalida_nao_pula_pergunta(self):
        with patch("entrada.sys.stdin.isatty", return_value=False), patch(
            "builtins.input", side_effect=["x", "5"]
        ):
            selecionado = selecionar_menu("Idioma?", IDIOMAS, "Português (Brasil)")
        self.assertEqual(selecionado, "日本語 (Japanese)")

    def test_animais_falantes_estao_disponiveis(self):
        self.assertIn("animais_falantes", listar_universos())
        prompt = carregar_prompt_universo("animais_falantes")
        self.assertIn("animais", prompt.lower())
        self.assertIn("character_type", prompt)

    def test_brief_muda_elenco_e_evita_historico(self):
        with tempfile.TemporaryDirectory() as pasta:
            sessao = Path(pasta) / "20260101_000000"
            sessao.mkdir()
            (sessao / "elenco.json").write_text(
                json.dumps({"cast": [{"character_type": "acerola"}]}),
                encoding="utf-8",
            )
            brief = criar_brief_variacao(
                "frutinhas", output_dir=pasta, rng=random.Random(42)
            )
        self.assertIn("VARIATION_ID", brief)
        self.assertIn("3-5 personagens", brief)
        self.assertIn("acerola", brief)
        self.assertIn("Evite tipos usados recentemente", brief)

    def test_prompt_ativo_e_compacto_e_sem_ordem_inglesa_legada(self):
        self.assertLess(len(PROMPT_BASE), 1500)
        self.assertNotIn("Diálogos 100% em inglês", PROMPT_BASE)
        self.assertNotIn("SCENE_21", PROMPT_BASE)

    def test_schemas_criativos_nao_pedem_metadados_repetidos(self):
        personagem = ELENCO_CRIATIVO_SCHEMA["properties"]["cast"]["items"]
        self.assertNotIn("ai_image_task", personagem["properties"])
        dialogo = DIALOGOS_CRIATIVOS_SCHEMA["properties"]["scenes"]["additionalProperties"]
        self.assertNotIn("VOICE_OVERRIDE_METADATA", dialogo["properties"])
        self.assertEqual(
            CENAS_VISUAIS_SCHEMA["properties"]["scenes"]["maxItems"], TOTAL_SCENES
        )

    def test_limite_de_saida_e_especifico_por_chamada(self):
        kwargs = _kwargs_grok({}, max_completion_tokens=2200)
        self.assertEqual(kwargs["max_completion_tokens"], 2200)


if __name__ == "__main__":
    unittest.main()
