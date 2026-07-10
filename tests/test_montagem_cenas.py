import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from enriquecer import enriquecer_roteiro  # noqa: E402
from gerar_roteiro import _montar_cena_producao  # noqa: E402
from narrativa import aplicar_story_contract_roteiro, aplicar_story_contract_sinopse, problemas_continuidade  # noqa: E402
from voz import aplicar_voice_registry_elenco  # noqa: E402


class MontagemCenasTest(unittest.TestCase):
    def setUp(self):
        self.elenco = aplicar_voice_registry_elenco(
            {
                "cast": [
                    {
                        "name": "Falk",
                        "character_type": "raposa",
                        "age": 30,
                        "gender": "Male",
                        "voice_profile": "ruhige tiefe Stimme",
                    },
                    {
                        "name": "Lina",
                        "character_type": "coruja",
                        "age": 28,
                        "gender": "Female",
                        "voice_profile": "klare schnelle Stimme",
                    },
                    {
                        "name": "Mo",
                        "character_type": "axolote",
                        "age": 22,
                        "gender": "Neutral",
                        "voice_profile": "helle neugierige Stimme",
                    },
                ]
            },
            "Deutsch",
        )

    def test_metadados_sao_anexados_sem_regerar_dialogo(self):
        falas = [
            {"SPEAKER": "Falk", "TEXT": "Jetzt ist die Wahrheit endlich heraus."},
            {"PAUSE": 0.2},
            {"SPEAKER": "Lina", "TEXT": "Dann müssen wir sofort handeln."},
            {"PAUSE": 0.2},
            {"SPEAKER": "Falk", "TEXT": "Niemand darf den Schlüssel finden."},
            {"PAUSE": 0.2},
            {"SPEAKER": "Lina", "TEXT": "Zu spät, jemand steht vor der Tür."},
        ]
        cena = _montar_cena_producao(
            {
                "SCENE_NUMBER": 1,
                "SCENE_NAME": "Die Tür",
                "LOCATION_LOCK": "Alte Bibliothek, Nacht",
                "CONTINUITY_IN": "Die Tür ist geschlossen.",
                "CONTINUITY_OUT": "Die Tür öffnet sich.",
                "VISUAL_PROMPT": "Falk and Lina wait inside an old library.",
            },
            {"scene_number": 1, "story_position": "início", "narrative_beat": "A chave aparece."},
            {"DIALOGUE_LINES": falas, "DELIVERY_STYLE": "schnell"},
            self.elenco,
            "Deutsch",
        )
        self.assertEqual(cena["DURATION_SECONDS"], 15)
        self.assertEqual([x.get("TEXT") for x in cena["DIALOGUE_LINES"] if "TEXT" in x], [
            x["TEXT"] for x in falas if "TEXT" in x
        ])
        for linha in cena["DIALOGUE_LINES"]:
            if "TEXT" in linha:
                self.assertIn("Language: German", linha["VOICE_IDENTITY_LOCK"])
        roteiro = enriquecer_roteiro(
            {"title": "Teste", "story_summary": "Resumo", "scenes": {"SCENE_1": cena}},
            "9:16",
            "Deutsch",
            self.elenco,
        )
        self.assertIn(
            "CANONICAL CHARACTER LOCKS:",
            roteiro["scenes"]["SCENE_1"]["VISUAL_PROMPT"],
        )

    def test_timestamps_cobrem_105_segundos(self):
        roteiro = {
            "title": "Teste",
            "story_summary": "Resumo suficientemente longo para o teste.",
            "scenes": {
                f"SCENE_{numero}": {
                    "SCENE_NUMBER": numero,
                    "SCENE_NAME": f"Cena {numero}",
                    "DIALOGUE_LINES": [],
                }
                for numero in range(1, 8)
            },
        }
        pronto = enriquecer_roteiro(roteiro, "9:16", "Deutsch")
        self.assertEqual(pronto["total_duration_seconds"], 105)
        self.assertEqual(pronto["scenes"]["SCENE_1"]["TIMESTAMP"], "00:00 - 00:15")
        self.assertEqual(pronto["scenes"]["SCENE_7"]["TIMESTAMP"], "01:30 - 01:45")

    def test_validador_detecta_quebra_de_anchor_entre_cenas(self):
        beats = [
            {
                "scene_number": numero,
                "story_position": "início" if numero <= 2 else "meio" if numero <= 5 else "fim",
                "narrative_beat": f"O fato exclusivo numero {numero} muda a investigacao.",
                "dialogue_intent": f"Os personagens revelam o fato numero {numero}.",
            }
            for numero in range(1, 8)
        ]
        sinopse = aplicar_story_contract_sinopse({
            "title": "Anchors",
            "story_summary": "Uma investigacao avanca por sete fatos conectados.",
            "act_1": "Os dois primeiros fatos iniciam o misterio.",
            "act_2": "Tres fatos ampliam a suspeita e mudam o caso.",
            "act_3": "Os fatos finais causam a crise e deixam uma pergunta.",
            "beats": beats,
        })
        cenas = {}
        for numero, beat in enumerate(beats, start=1):
            anchor = f"Estado canonico apos cena {numero}"
            cenas[f"SCENE_{numero}"] = {
                "SCENE_NUMBER": numero,
                "SCENE_NAME": f"Fato {numero}",
                "NARRATIVE_BEAT": beat["narrative_beat"],
                "ACTION_DIRECTION": beat["narrative_beat"],
                "LOCATION_LOCK": "Arquivo central",
                "CONTINUITY_IN": "Estado inicial" if numero == 1 else f"Estado canonico apos cena {numero - 1}",
                "CONTINUITY_OUT": anchor,
                "DIALOGUE_LINES": [{"SPEAKER": "Falk", "TEXT": beat["dialogue_intent"]}],
            }
        roteiro = aplicar_story_contract_roteiro({"scenes": cenas}, sinopse)
        self.assertFalse(any("CONTINUITY_IN" in p for p in problemas_continuidade(roteiro, sinopse)))
        roteiro["scenes"]["SCENE_2"]["CONTINUITY_IN"] = "Outro local sem transicao"
        self.assertTrue(any("CONTINUITY_IN" in p for p in problemas_continuidade(roteiro, sinopse)))


if __name__ == "__main__":
    unittest.main()
