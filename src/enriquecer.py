"""
Garante que os JSONs tenham instruções claras para agentes de IA,
timing de diálogo calculado e metadados corretos.
"""

from dialogo import calcular_timing
from config import AGENT_CONFIRM_BETWEEN_STEPS, AGENT_VIDEOS_PER_STEP
from narrativa import aplicar_story_contract_sinopse, aplicar_story_contract_roteiro
from polir import polir_roteiro
from schema import RESOLUCAO, DURACAO_CENA, NUM_CENAS, DURACAO_TOTAL
from voz import aplicar_voice_registry_elenco, aplicar_voice_registry_roteiro


def _agent_settings(opcoes_agente=None):
    opcoes_agente = opcoes_agente or {}
    videos_por_passo = int(opcoes_agente.get("videos_per_step", AGENT_VIDEOS_PER_STEP))
    return {
        "videos_per_step": max(1, videos_por_passo),
        "confirm_between_steps": bool(
            opcoes_agente.get("confirm_between_steps", AGENT_CONFIRM_BETWEEN_STEPS)
        ),
    }


def _texto_execucao_agente(settings):
    n = settings["videos_per_step"]
    confirmacao = settings["confirm_between_steps"]
    unidade = "scene" if n == 1 else f"group of up to {n} scenes"
    confirm_txt = (
        "After each approved QA pass, ask the user/operator for permission before continuing."
        if confirmacao
        else "After each approved QA pass, continue automatically to the next step."
    )
    if n == 1:
        return (
            "Work strictly ONE SCENE AT A TIME: render one scene, run scene QA, fix if needed, "
            f"then proceed. {confirm_txt}"
        )
    return (
        f"Work in controlled batches of up to {n} scenes: render one {unidade}, run QA for every scene "
        f"in that group, fix failures, then proceed. {confirm_txt}"
    )


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
        "output": "One full character reference image per cast member (PNG or JPG).",
        "style": "Cinematic stylized 3D character design, hyper-realistic PBR textures when applicable.",
    }

    for p in elenco.get("cast", []):
        nome = p.get("name", "Character")
        character_type = p.get("character_type", p.get("fruit_type", "character"))
        p["ai_image_task"] = (
            f"AI AGENT: Create a {RESOLUCAO} {aspect_ratio} full character reference IMAGE "
            f"of {nome} ({character_type}). "
            f"Physical: {p.get('physical_dna', '')} "
            f"Outfit: {p.get('outfit_dna', '')} "
            f"Neutral pose, clear lighting, no background clutter. "
            f"This image locks the character look for all video scenes."
        )

    return aplicar_voice_registry_elenco(elenco, idioma)


def _resumir_ato(beats, numeros_cena):
    partes = [
        beat.get("narrative_beat", "")
        for beat in beats
        if beat.get("scene_number") in numeros_cena and beat.get("narrative_beat")
    ]
    return " ".join(partes).strip()


def _preencher_atos_sinopse(sinopse):
    beats = sinopse.get("beats", [])
    if not beats:
        return sinopse

    atos = {
        "act_1": ([1, 2], "ATO 1 — INÍCIO"),
        "act_2": ([3, 4, 5], "ATO 2 — MEIO"),
        "act_3": ([6, 7], "ATO 3 — FIM"),
    }

    for campo, (cenas, rotulo) in atos.items():
        resumo = _resumir_ato(beats, cenas)
        atual = sinopse.get(campo, "").strip()
        if len(atual) < 30 and resumo:
            sinopse[campo] = f"{rotulo}: {resumo}"

    return sinopse


def enriquecer_sinopse(sinopse, idioma):
    sinopse = _preencher_atos_sinopse(sinopse)
    sinopse = aplicar_story_contract_sinopse(sinopse)
    sinopse["ai_instructions"] = {
        "task": (
            "REFERENCE ONLY — AI AGENT: Do NOT generate images, videos or audio from this file. "
            "This is a story blueprint for consultation during script review and production planning."
        ),
        "purpose": (
            "Planning document with story_summary, acts and beats. "
            "Use it to understand the narrative arc — not as a generation source."
        ),
        "use_instead": {
            "character_images": "elenco.json → ai_image_task (one reference image per cast member)",
            "scene_videos": "roteiro.json → AI_VIDEO_TASK (one 10s video per scene)",
            "spoken_audio": "roteiro.json → DIALOGUE_LINES > TEXT only",
        },
        "language": idioma,
        "do_not_generate": True,
    }
    return sinopse


def enriquecer_roteiro(roteiro, aspect_ratio, idioma, elenco=None, opcoes_agente=None):
    agent_settings = _agent_settings(opcoes_agente)
    execucao_agente = _texto_execucao_agente(agent_settings)

    roteiro["aspect_ratio"] = aspect_ratio
    roteiro["resolution"] = RESOLUCAO
    roteiro["language"] = idioma
    roteiro["scene_duration_seconds"] = DURACAO_CENA
    roteiro["total_duration_seconds"] = DURACAO_TOTAL
    roteiro["total_scenes"] = NUM_CENAS

    roteiro["ai_instructions"] = {
        "task": (
            f"AI AGENT: Generate exactly {NUM_CENAS} videos of {DURACAO_CENA} seconds each "
            f"({DURACAO_TOTAL}s total). Resolution: {RESOLUCAO}. Aspect ratio: {aspect_ratio}. "
            f"{execucao_agente}"
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
        "note": (
            "sinopse.json is REFERENCE ONLY (do not generate media from it). "
            "Use this roteiro.json and elenco.json as the production sources."
        ),
        "post_generation_qa": (
            "MANDATORY TWO-LAYER QA. Scene-level QA: after EACH individual scene render, "
            "listen to that scene before moving to the next one; verify every spoken word matches "
            "DIALOGUE_LINES > TEXT exactly, the same voice registry identity is used, language is unchanged, "
            "audio is clear, no words are missing/invented, no overlap occurs, and active-speaker lip-sync is aligned. "
            "Re-render that scene until it passes. Final global QA: after all scenes pass individually, review the "
            "complete sequence from SCENE_1 to SCENE_7 for voice consistency, audio continuity, story continuity, "
            "timestamps, visual character lock, outfit lock, and cliffhanger integrity. Re-render any failed scene."
        ),
        "agent_execution": (
            f"videos_per_step={agent_settings['videos_per_step']}; "
            f"confirm_between_steps={agent_settings['confirm_between_steps']}; "
            f"{execucao_agente}"
        ),
    }
    roteiro["agent_execution"] = agent_settings

    if elenco:
        roteiro = aplicar_voice_registry_roteiro(roteiro, elenco, idioma)
        roteiro = polir_roteiro(roteiro, elenco, idioma)
        roteiro = aplicar_voice_registry_roteiro(roteiro, elenco, idioma)

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
            f"{execucao_agente} "
            "For this task, render ONLY the current scene described here. "
            "After rendering this single scene, run scene-level QA before moving on. "
            f"Timestamp: {cena['TIMESTAMP']}. "
            f"Story beat: {cena.get('NARRATIVE_BEAT', '')}. "
            f"Hook (first 2s): {cena.get('OPENING_HOOK', '')}. "
            f"Camera: {cena.get('CAMERA_DIRECTION', '')[:400]}. "
            f"Movement: {cena.get('PHYSICAL_MOVEMENT', '')[:200]}. "
            f"Audio language: {idioma}. "
            f"Spoken lines (DIALOGUE_LINES > TEXT only): {dialogo_texto[:300]}. "
            f"Speech: {timing['total_dialogue_seconds']}s / {DURACAO_CENA}s. "
            f"Duration MUST be exactly {DURACAO_CENA} seconds. "
            "If this scene fails audio, voice, lip-sync, visual lock, timing, or continuity QA, "
            "re-render this scene before generating the next scene. "
            "After ALL scenes are generated one by one: run final global QA per ai_instructions.post_generation_qa."
        )

    return roteiro


def enriquecer_roteiro_com_sinopse(
    roteiro,
    aspect_ratio,
    idioma,
    elenco,
    sinopse,
    opcoes_agente=None,
):
    roteiro = enriquecer_roteiro(roteiro, aspect_ratio, idioma, elenco, opcoes_agente)
    return aplicar_story_contract_roteiro(roteiro, sinopse)
