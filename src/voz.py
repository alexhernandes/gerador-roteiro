"""
Registro canonico de vozes.

A geracao visual ja usa locks fortes de personagem. Este modulo aplica a
mesma ideia ao audio: cada personagem recebe uma identidade vocal fixa e as
cenas apenas copiam esse contrato.
"""

import re

from dialogo import lock_idioma_texto, normalizar_idioma


def chave_speaker(nome):
    return re.sub(r"[^A-Z0-9]+", "_", str(nome or "").upper()).strip("_")


def _genero_canonico(gender):
    texto = str(gender or "").lower()
    if any(x in texto for x in ("female", "femin", "mulher", "girl", "woman")):
        return "Strictly Female"
    if any(x in texto for x in ("male", "masc", "homem", "boy", "man")):
        return "Strictly Male"
    return "Androgynous / Character Voice"


def _sintese_forcada(gender, idioma):
    genero = _genero_canonico(gender)
    codigo = normalizar_idioma(idioma).upper()
    if "Female" in genero:
        return f"Female_Adult_Soprano_{codigo}"
    if "Male" in genero:
        return f"Male_Adult_Baritone_{codigo}"
    return f"Adult_Neutral_Character_{codigo}"


def _peso_vocal(gender, fruit_type, voice_profile):
    genero = _genero_canonico(gender)
    fruta = fruit_type or "Fruit"
    perfil = voice_profile or "consistent expressive character voice"
    if "Female" in genero:
        base = "Feminine / clear adult character voice"
    elif "Male" in genero:
        base = "Masculine / clear adult character voice"
    else:
        base = "Neutral / clear adult character voice"
    return f"{base} / {fruta} / {perfil}"


def criar_voice_registry(elenco, idioma):
    lock = lock_idioma_texto(idioma)
    voices = {}

    for personagem in elenco.get("cast", []):
        nome = personagem.get("name", "CHARACTER")
        speaker_key = chave_speaker(nome)
        voice_model_id = f"{speaker_key}_VOICE_LOCK"
        gender = personagem.get("gender", "")
        fruit_type = personagem.get("fruit_type", "")
        voice_profile = personagem.get("voice_profile", "")
        age = personagem.get("age", "")

        identity_lock = (
            f"Voice Model: {voice_model_id}. "
            f"Speaker: {nome}. Age: {age}. Gender: {gender}. "
            f"Fruit Type: {fruit_type}. Tone: {voice_profile}. {lock}."
        )
        override = {
            "VOICE_GENDER": _genero_canonico(gender),
            "VOCAL_WEIGHT": _peso_vocal(gender, fruit_type, voice_profile),
            "TONE_PROFILE": (
                f"{nome}: {voice_profile}. Keep the same pitch, rhythm, accent, "
                "emotional texture, and vocal weight in every scene."
            ),
            "FORCE_SYNTHESIS": _sintese_forcada(gender, idioma),
        }

        voices[nome] = {
            "SPEAKER": nome,
            "SPEAKER_KEY": speaker_key,
            "VOICE_MODEL_ID": voice_model_id,
            "VOICE_IDENTITY_LOCK": identity_lock,
            "VOICE_OVERRIDE_METADATA": override,
        }

    return {
        "version": "voice-registry-v1",
        "language_lock": lock,
        "rule": (
            "Every DIALOGUE_LINES item must use the exact SPEAKER and "
            "VOICE_IDENTITY_LOCK from this registry. Never invent per-scene voices."
        ),
        "voices": voices,
    }


def obter_voice_registry(elenco, idioma):
    registry = elenco.get("voice_registry")
    if isinstance(registry, dict) and registry.get("voices"):
        return registry
    return criar_voice_registry(elenco, idioma)


def aplicar_voice_registry_elenco(elenco, idioma):
    registry = criar_voice_registry(elenco, idioma)
    elenco["voice_registry"] = registry

    for personagem in elenco.get("cast", []):
        nome = personagem.get("name")
        voz = registry["voices"].get(nome)
        if not voz:
            continue
        personagem["voice_id"] = voz["VOICE_MODEL_ID"]
        personagem["voice_identity_lock"] = voz["VOICE_IDENTITY_LOCK"]
        personagem["voice_override_metadata"] = voz["VOICE_OVERRIDE_METADATA"]

    return elenco


def _mapa_por_chave(registry):
    return {
        chave_speaker(nome): voz
        for nome, voz in registry.get("voices", {}).items()
    }


def encontrar_voz(registry, speaker):
    mapa = _mapa_por_chave(registry)
    return mapa.get(chave_speaker(speaker))


def aplicar_voice_registry_cena(cena, elenco, idioma):
    registry = obter_voice_registry(elenco, idioma)
    overrides = {}

    for linha in cena.get("DIALOGUE_LINES", []):
        if "TEXT" not in linha:
            continue
        voz = encontrar_voz(registry, linha.get("SPEAKER"))
        if not voz:
            continue
        linha["SPEAKER"] = voz["SPEAKER"]
        linha["VOICE_IDENTITY_LOCK"] = voz["VOICE_IDENTITY_LOCK"]
        overrides[voz["SPEAKER"]] = voz["VOICE_OVERRIDE_METADATA"]

    if overrides:
        cena["VOICE_OVERRIDE_METADATA"] = overrides

    return cena


def aplicar_voice_registry_roteiro(roteiro, elenco, idioma):
    roteiro["voice_registry"] = obter_voice_registry(elenco, idioma)
    for cena in roteiro.get("scenes", {}).values():
        aplicar_voice_registry_cena(cena, elenco, idioma)
    return roteiro


def voice_registry_prompt(elenco, idioma):
    registry = obter_voice_registry(elenco, idioma)
    linhas = [
        "VOICE REGISTRY - CANONICO E OBRIGATORIO:",
        f"Language lock: {registry['language_lock']}",
        "Use exatamente estes SPEAKER e VOICE_IDENTITY_LOCK. Nao crie vozes novas.",
    ]
    for nome, voz in registry.get("voices", {}).items():
        linhas.append(f"- SPEAKER: {nome}")
        linhas.append(f"  VOICE_IDENTITY_LOCK: {voz['VOICE_IDENTITY_LOCK']}")
        linhas.append(f"  METADATA: {voz['VOICE_OVERRIDE_METADATA']}")
    return "\n".join(linhas)


def problemas_voice_registry(elenco, roteiro):
    problemas = []
    registry = elenco.get("voice_registry", {})
    if not registry.get("voices"):
        return ["Elenco sem voice_registry canonico."]

    vozes_por_chave = _mapa_por_chave(registry)
    cenas = roteiro.get("scenes", {})

    for chave, cena in cenas.items():
        num = cena.get("SCENE_NUMBER", chave)
        metadata = cena.get("VOICE_OVERRIDE_METADATA", {})
        for linha in cena.get("DIALOGUE_LINES", []):
            if "TEXT" not in linha:
                continue
            speaker = linha.get("SPEAKER", "")
            voz = vozes_por_chave.get(chave_speaker(speaker))
            if not voz:
                problemas.append(f"Cena {num}: SPEAKER fora do elenco/registry: {speaker}")
                continue
            if linha.get("SPEAKER") != voz["SPEAKER"]:
                problemas.append(f"Cena {num}: SPEAKER deveria ser {voz['SPEAKER']}, veio {speaker}")
            if linha.get("VOICE_IDENTITY_LOCK") != voz["VOICE_IDENTITY_LOCK"]:
                problemas.append(f"Cena {num} ({speaker}): VOICE_IDENTITY_LOCK diferente do registry")
            if metadata.get(voz["SPEAKER"]) != voz["VOICE_OVERRIDE_METADATA"]:
                problemas.append(f"Cena {num} ({speaker}): VOICE_OVERRIDE_METADATA diferente do registry")

    return problemas
