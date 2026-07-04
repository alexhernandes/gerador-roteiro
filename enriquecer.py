"""
Garante que os JSONs tenham instruções claras para agentes de IA,
timing de diálogo calculado e metadados corretos.
"""

from dialogo import calcular_timing, normalizar_idioma
from schema import RESOLUCAO, DURACAO_CENA, NUM_CENAS, DURACAO_TOTAL


def _formatar_tempo(segundos):
    mins = segundos // 60
    secs = segundos % 60
    return f"{mins:02d}:{secs:02d}"


def enriquecer_elenco(elenco, aspect_ratio, idioma):
    elenco["aspect_ratio"] = aspect_ratio
    elenco["resolution"] = RESOLUCAO
    elenco["language"] = idioma

    elenco["ai_instructions"] = {
        "task": (
            "AI AGENT: Generate ONE character reference IMAGE for EACH cast member below. "
            "Use physical_dna and outfit_dna as the visual lock. "
            "These images will be used as consistent references for video generation."
        ),
        "resolution": RESOLUCAO,
        "aspect_ratio": aspect_ratio,
        "output": "One full-body character reference image per cast member (PNG or JPG).",
        "style": "Disney-Pixar 3D anthropomorphic fruit character, hyper-realistic PBR textures.",
    }

    for p in elenco.get("cast", []):
        nome = p.get("name", "Character")
        p["ai_image_task"] = (
            f"AI AGENT: Create a {RESOLUCAO} {aspect_ratio} full-body character reference IMAGE "
            f"of {nome}. "
            f"Physical: {p.get('physical_dna', '')} "
            f"Outfit: {p.get('outfit_dna', '')} "
            f"Neutral pose, clear lighting, no background clutter. "
            f"This image locks the character look for all video scenes."
        )

    return elenco


def enriquecer_roteiro(roteiro, aspect_ratio, idioma):
    roteiro["aspect_ratio"] = aspect_ratio
    roteiro["resolution"] = RESOLUCAO
    roteiro["language"] = idioma
    roteiro["scene_duration_seconds"] = DURACAO_CENA
    roteiro["total_duration_seconds"] = DURACAO_TOTAL
    roteiro["total_scenes"] = NUM_CENAS

    codigo = normalizar_idioma(idioma)

    roteiro["ai_instructions"] = {
        "task": (
            f"AI AGENT: Generate exactly {NUM_CENAS} videos of {DURACAO_CENA} seconds each "
            f"({DURACAO_TOTAL}s total). Resolution: {RESOLUCAO}. Aspect ratio: {aspect_ratio}."
        ),
        "resolution": RESOLUCAO,
        "aspect_ratio": aspect_ratio,
        "duration_per_scene_seconds": DURACAO_CENA,
        "total_duration_seconds": DURACAO_TOTAL,
        "total_scenes": NUM_CENAS,
        "audio_source": (
            "ALL spoken audio comes ONLY from DIALOGUE_LINES > TEXT. "
            f"Language: {idioma}. Do NOT translate or change language."
        ),
        "output": f"{NUM_CENAS} video clips of {DURACAO_CENA}s each (MP4), total {DURACAO_TOTAL}s.",
        "style": (
            f"Cinematic 3D animation at {RESOLUCAO}, {aspect_ratio}, "
            "Disney-Pixar style, volumetric lighting."
        ),
    }

    cenas = roteiro.get("scenes", {})
    textos_dialogo = []

    for chave in sorted(cenas, key=lambda k: cenas[k].get("SCENE_NUMBER", 0)):
        cena = cenas[chave]
        num = cena.get("SCENE_NUMBER", 1)
        inicio = (num - 1) * DURACAO_CENA
        fim = num * DURACAO_CENA

        cena["DURATION_SECONDS"] = DURACAO_CENA
        cena["TIMESTAMP"] = f"{_formatar_tempo(inicio)} - {_formatar_tempo(fim)}"

        timing = calcular_timing(cena.get("DIALOGUE_LINES", []), idioma, DURACAO_CENA)
        cena["DIALOGUE_TIMING"] = timing

        dialogo_texto = " | ".join(
            linha["TEXT"]
            for linha in cena.get("DIALOGUE_LINES", [])
            if "TEXT" in linha
        )
        textos_dialogo.append(dialogo_texto)

        cena["AI_VIDEO_TASK"] = (
            f"AI AGENT: Create a {DURACAO_CENA}-second {RESOLUCAO} {aspect_ratio} VIDEO "
            f"for SCENE {num} — '{cena.get('SCENE_NAME', chave)}'. "
            f"Timestamp: {cena['TIMESTAMP']}. "
            f"Story beat: {cena.get('NARRATIVE_BEAT', '')}. "
            f"Hook (first 2s): {cena.get('OPENING_HOOK', '')}. "
            f"Camera: {cena.get('CAMERA_DIRECTION', '')[:400]}. "
            f"Movement: {cena.get('PHYSICAL_MOVEMENT', '')[:200]}. "
            f"Audio language: {idioma}. "
            f"Spoken lines (DIALOGUE_LINES > TEXT only): {dialogo_texto[:300]}. "
            f"Speech: {timing['total_dialogue_seconds']}s / {DURACAO_CENA}s. "
            f"Duration MUST be exactly {DURACAO_CENA} seconds."
        )

    return roteiro