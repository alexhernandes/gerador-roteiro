import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from dialogo import (  # noqa: E402
    ajustar_timing_cena,
    calcular_timing,
    detectar_idioma_texto,
    lock_idioma_texto,
    normalizar_idioma,
    texto_no_idioma,
    voice_lock_valido,
)
from gerar_roteiro import _falas_fallback_beat  # noqa: E402
from voz import chave_speaker  # noqa: E402


class IdiomasTest(unittest.TestCase):
    AMOSTRAS = {
        "pt": "Agora a verdade apareceu e você sabe de tudo.",
        "en": "Now the truth is out and you know everything.",
        "es": "Ahora la verdad salió y tú lo sabes todo.",
        "de": "Jetzt ist die Wahrheit heraus und du weißt alles.",
        "ja": "ついに真実が明らかになった。もう隠せない。",
    }

    def test_normaliza_todos_os_idiomas_da_interface(self):
        casos = {
            "Português (Brasil)": "pt",
            "English": "en",
            "Español": "es",
            "Spanish": "es",
            "Deutsch": "de",
            "Alemão": "de",
            "日本語 (Japanese)": "ja",
            "Japonês": "ja",
        }
        for rotulo, esperado in casos.items():
            with self.subTest(rotulo=rotulo):
                self.assertEqual(normalizar_idioma(rotulo), esperado)

    def test_detecta_frases_naturais_nos_cinco_idiomas(self):
        for codigo, texto in self.AMOSTRAS.items():
            with self.subTest(codigo=codigo):
                self.assertEqual(detectar_idioma_texto(texto), codigo)
                self.assertTrue(texto_no_idioma(texto, codigo))

    def test_rejeita_idioma_diferente(self):
        for codigo, texto in self.AMOSTRAS.items():
            outro = "ja" if codigo != "ja" else "de"
            with self.subTest(codigo=codigo, outro=outro):
                self.assertFalse(texto_no_idioma(texto, outro))

    def test_locks_de_voz_sao_validos(self):
        for codigo in self.AMOSTRAS:
            lock = lock_idioma_texto(codigo)
            self.assertTrue(voice_lock_valido(lock, codigo))

    def test_japones_usa_caracteres_no_timing(self):
        texto = "これは本当に大切な秘密です。今すぐ話してください。"
        timing = calcular_timing([{"TEXT": texto}], "ja")
        self.assertGreater(timing["word_count"], 15)
        self.assertEqual(timing["words_per_second"], 7.0)

    def test_fallback_alemao_e_japones_nao_voltam_ao_portugues(self):
        for idioma, codigo in (("Deutsch", "de"), ("日本語", "ja")):
            linhas = _falas_fallback_beat({}, ["A", "B"], idioma)
            textos = [linha["TEXT"] for linha in linhas if "TEXT" in linha]
            self.assertEqual(len(textos), 4)
            self.assertTrue(all(texto_no_idioma(texto, codigo) for texto in textos))

    def test_nome_japones_produz_id_de_voz_estavel(self):
        self.assertEqual(chave_speaker("紅葉さん"), "紅葉さん")
        self.assertNotEqual(chave_speaker("紅葉さん"), chave_speaker("青空くん"))

    def test_ajuste_local_nao_inventa_dialogo_para_preencher_tempo(self):
        cena = {
            "DIALOGUE_LINES": [
                {"SPEAKER": "A", "TEXT": "Das ist wahr."},
                {"PAUSE": 0.2},
                {"SPEAKER": "B", "TEXT": "Ich weiß es."},
            ]
        }
        ajustar_timing_cena(cena, "Deutsch")
        self.assertEqual(
            [linha["TEXT"] for linha in cena["DIALOGUE_LINES"] if "TEXT" in linha],
            ["Das ist wahr.", "Ich weiß es."],
        )


if __name__ == "__main__":
    unittest.main()
