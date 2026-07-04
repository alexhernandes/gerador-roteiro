"""
Cálculo de timing de fala e detecção de idioma nos diálogos.
Fonte oficial do áudio: DIALOGUE_LINES > TEXT
"""

import re

from schema import DURACAO_CENA

# Velocidade de fala viral (palavras por segundo)
PALAVRAS_POR_SEGUNDO = {
    "pt": 3.2,
    "en": 2.8,
    "es": 3.0,
}

MIN_FALAS_POR_CENA = 4
MAX_FALAS_POR_CENA = 6
MIN_SEGUNDOS_FALA = 7.5
MAX_SEGUNDOS_FALA = 9.5
PAUSA_PADRAO = 0.2

PALAVRAS_PT = {
    "que", "nao", "não", "voce", "você", "é", "de", "um", "uma", "para", "com",
    "por", "mais", "como", "mas", "seu", "sua", "ele", "ela", "isso", "aqui",
    "olha", "amor", "muito", "bem", "ainda", "também", "ja", "já", "so", "só",
    "quem", "onde", "quando", "porque", "entao", "então", "agora", "nunca",
    "sempre", "tudo", "nada", "algo", "quero", "preciso", "sabe", "escuta",
    "espera", "meu", "minha", "nos", "nós", "eles", "elas", "essa", "esse",
    "aquilo", "sera", "será", "esta", "está", "foi", "sao", "são", "tem",
    "tinha", "fazer", "dizer", "ver", "saber", "dar", "ir", "vir", "fica",
    "calma", "cara", "gente", "tipo", "ne", "né", "pra", "pro", "ta", "tá",
    "voce", "chegou", "casar", "traição", "mentira", "desculpa", "pare",
}

PALAVRAS_EN = {
    "the", "you", "are", "is", "what", "who", "how", "why", "when", "where",
    "this", "that", "with", "from", "have", "been", "will", "your", "they",
    "them", "there", "here", "look", "wait", "love", "never", "always",
    "everything", "nothing", "don't", "can't", "won't", "i'm", "you're",
    "it's", "that's", "wow", "oh", "hey", "yes", "no", "good", "morning",
    "hello", "today", "going", "about", "right", "know", "think",
}

LOCK_IDIOMA = {
    "pt": "Language: Portuguese (Brazil)",
    "en": "Language: English",
    "es": "Language: Spanish",
}


def normalizar_idioma(idioma):
    idioma = idioma.lower().strip()
    if any(x in idioma for x in ("portugu", "pt-br", "pt_br", "brasileiro")):
        return "pt"
    if any(x in idioma for x in ("english", "inglês", "ingles", "inglés")):
        return "en"
    if any(x in idioma for x in ("espan", "español", "espanol")):
        return "es"
    if idioma in ("pt", "br"):
        return "pt"
    if idioma in ("en",):
        return "en"
    if idioma in ("es",):
        return "es"
    return "pt"


def lock_idioma_texto(idioma):
    codigo = normalizar_idioma(idioma)
    return LOCK_IDIOMA.get(codigo, f"Language: {idioma}")


def extrair_textos(dialogue_lines):
    return [
        linha["TEXT"]
        for linha in dialogue_lines
        if isinstance(linha, dict) and "TEXT" in linha
    ]


def contar_falas(dialogue_lines):
    return len(extrair_textos(dialogue_lines))


def detectar_idioma_texto(texto):
    palavras = re.findall(r"\b[\w']+\b", texto.lower())
    if not palavras:
        return "desconhecido"

    pt = sum(1 for p in palavras if p in PALAVRAS_PT)
    en = sum(1 for p in palavras if p in PALAVRAS_EN)

    if pt > en:
        return "pt"
    if en > pt:
        return "en"
    if en >= 2 and pt == 0:
        return "en"
    return "desconhecido"


def texto_no_idioma(texto, idioma_esperado):
    idioma = normalizar_idioma(idioma_esperado)
    detectado = detectar_idioma_texto(texto)

    if detectado == "desconhecido":
        # Texto curto em inglês óbvio
        if idioma == "pt" and re.search(
            r"\b(the|you|what|why|hello|good morning|i'm|you're|don't)\b", texto, re.I
        ):
            return False
        return True

    return detectado == idioma


def voice_lock_valido(lock, idioma):
    codigo = normalizar_idioma(idioma)
    padroes = {
        "pt": r"portugu",
        "en": r"english",
        "es": r"espan",
    }
    return bool(re.search(padroes.get(codigo, ""), lock, re.I))


def calcular_timing(dialogue_lines, idioma, duracao_cena=DURACAO_CENA):
    codigo = normalizar_idioma(idioma)
    wps = PALAVRAS_POR_SEGUNDO.get(codigo, 3.2)

    textos = extrair_textos(dialogue_lines)
    total_palavras = sum(len(t.split()) for t in textos)
    total_pausas = sum(
        linha.get("PAUSE", 0)
        for linha in dialogue_lines
        if "PAUSE" in linha
    )
    num_falas = len(textos)

    fala_seg = total_palavras / wps if total_palavras else 0
    total_seg = fala_seg + total_pausas

    min_palavras = int(MIN_SEGUNDOS_FALA * wps)
    max_palavras = int(MAX_SEGUNDOS_FALA * wps)

    return {
        "source": "DIALOGUE_LINES > TEXT",
        "word_count": total_palavras,
        "line_count": num_falas,
        "words_per_second": wps,
        "estimated_speech_seconds": round(fala_seg, 1),
        "pause_seconds": round(total_pausas, 1),
        "total_dialogue_seconds": round(total_seg, 1),
        "fits_in_scene": total_seg <= duracao_cena,
        "min_words_recommended": min_palavras,
        "max_words_recommended": max_palavras,
        "min_lines_recommended": MIN_FALAS_POR_CENA,
        "has_enough_dialogue": (
            num_falas >= MIN_FALAS_POR_CENA
            and total_palavras >= min_palavras
            and MIN_SEGUNDOS_FALA <= total_seg <= duracao_cena
        ),
        "fills_scene": MIN_SEGUNDOS_FALA <= total_seg <= MAX_SEGUNDOS_FALA,
    }


def _segundos_das_falas(falas, wps):
    palavras = sum(len(f["TEXT"].split()) for f in falas)
    pausas = max(0, len(falas) - 1) * PAUSA_PADRAO
    return palavras / wps + pausas


def _montar_linhas_com_pausas(falas):
    linhas = []
    for indice, fala in enumerate(falas):
        linhas.append(fala)
        if indice < len(falas) - 1:
            linhas.append({"PAUSE": PAUSA_PADRAO})
    return linhas


_REFORCOS_NARRATIVOS = {
    "pt": [
        "Isso muda tudo, e voce sabe.",
        "Agora a verdade apareceu de vez.",
        "Se isso sair daqui, acabou.",
    ],
    "en": [
        "This changes everything, and you know it.",
        "Now the truth is finally out.",
        "If this gets out, we are done.",
    ],
    "es": [
        "Esto lo cambia todo, y lo sabes.",
        "Ahora la verdad salio de una vez.",
        "Si esto sale de aqui, se acabo.",
    ],
}

_EXTENSOES = {
    "pt": " demais!",
    "en": " too much!",
    "es": " demasiado!",
}


def ajustar_timing_cena(cena, idioma):
    """Ajusta falas localmente para caber em 7.5-9.5s sem nova chamada à API."""
    falas = [dict(linha) for linha in cena.get("DIALOGUE_LINES", []) if "TEXT" in linha]
    if not falas:
        return cena

    codigo = normalizar_idioma(idioma)
    wps = PALAVRAS_POR_SEGUNDO.get(codigo, 3.2)
    lock = lock_idioma_texto(idioma)
    reforcos = _REFORCOS_NARRATIVOS.get(codigo, _REFORCOS_NARRATIVOS["pt"])

    for fala in falas:
        speaker = fala.get("SPEAKER", "SPEAKER")
        if not voice_lock_valido(fala.get("VOICE_IDENTITY_LOCK", ""), idioma):
            fala["VOICE_IDENTITY_LOCK"] = f"{speaker} voice. {lock}."

    def segundos():
        return _segundos_das_falas(falas, wps)

    def indices_editaveis():
        if len(falas) <= 2:
            return list(range(len(falas)))
        return list(range(1, len(falas) - 1))

    tentativas = 0
    while segundos() > MAX_SEGUNDOS_FALA and tentativas < 20:
        tentativas += 1
        candidatos = indices_editaveis()
        if not candidatos:
            break
        indice = max(candidatos, key=lambda i: len(falas[i]["TEXT"].split()))
        palavras = falas[indice]["TEXT"].split()
        if len(palavras) > 2:
            falas[indice]["TEXT"] = " ".join(palavras[:-1])
        elif len(falas) > MIN_FALAS_POR_CENA:
            falas.pop(indice)
        else:
            falas[indice]["TEXT"] = " ".join(palavras[:2])
            break

    indice_reforco = 0
    while segundos() < MIN_SEGUNDOS_FALA and len(falas) < MAX_FALAS_POR_CENA:
        speaker = falas[-1].get("SPEAKER", "PERSONAGEM")
        falas.append({
            "SPEAKER": speaker,
            "VOICE_IDENTITY_LOCK": f"{speaker} voice. {lock}.",
            "TEXT": reforcos[indice_reforco % len(reforcos)],
        })
        indice_reforco += 1

    tentativas = 0
    while segundos() < MIN_SEGUNDOS_FALA and tentativas < 10:
        tentativas += 1
        candidatos = indices_editaveis() or list(range(len(falas)))
        indice = min(candidatos, key=lambda i: len(falas[i]["TEXT"].split()))
        falas[indice]["TEXT"] = (
            falas[indice]["TEXT"].rstrip("!.?") + _EXTENSOES.get(codigo, "!")
        )
        if len(falas[indice]["TEXT"].split()) > 12:
            break

    cena["DIALOGUE_LINES"] = _montar_linhas_com_pausas(falas)
    return cena


def ajustar_timing_roteiro(roteiro, idioma):
    for cena in roteiro.get("scenes", {}).values():
        ajustar_timing_cena(cena, idioma)
    return roteiro


def metas_timing_roteiro(roteiro, idioma):
    """Texto com meta de palavras/segundos por cena para a correção por API."""
    linhas = []
    cenas = roteiro.get("scenes", {})
    for chave in sorted(cenas, key=lambda k: cenas[k].get("SCENE_NUMBER", 0)):
        cena = cenas[chave]
        num = cena.get("SCENE_NUMBER", chave)
        timing = calcular_timing(cena.get("DIALOGUE_LINES", []), idioma)
        linhas.append(
            f"Cena {num}: {timing['line_count']} falas, {timing['word_count']} palavras, "
            f"{timing['total_dialogue_seconds']}s → meta {timing['min_words_recommended']}-"
            f"{timing['max_words_recommended']} palavras ({MIN_SEGUNDOS_FALA}-"
            f"{MAX_SEGUNDOS_FALA}s)"
        )
    return "\n".join(linhas)


def extrair_falas_de_intent(dialogue_intent):
    """Extrai textos entre aspas ou após numeração do dialogue_intent da sinopse."""
    if not dialogue_intent:
        return []

    falas = re.findall(r"['\"]([^'\"]{3,})['\"]", dialogue_intent)
    if falas:
        return [f.strip() for f in falas if f.strip()]

    falas = re.findall(r"\d+\)\s*([^0-9]+?)(?=\s*\d+\)|$)", dialogue_intent, re.S)
    return [f.strip().strip("'\"") for f in falas if len(f.strip()) >= 3]


def dialogos_de_intent(dialogue_intent, speakers, idioma):
    """Monta DIALOGUE_LINES iniciais a partir do dialogue_intent planejado na sinopse."""
    falas = extrair_falas_de_intent(dialogue_intent)
    if not falas or not speakers:
        return []

    lock = lock_idioma_texto(idioma)
    linhas = []
    for indice, texto in enumerate(falas):
        speaker = speakers[indice % len(speakers)]
        linhas.append({
            "SPEAKER": speaker,
            "VOICE_IDENTITY_LOCK": f"{speaker} voice. {lock}.",
            "TEXT": texto,
        })
        if indice < len(falas) - 1:
            linhas.append({"PAUSE": PAUSA_PADRAO})
    return linhas


def cenas_com_problemas(problemas):
    """Extrai números de cena a partir das mensagens de problema."""
    numeros = set()
    for problema in problemas:
        match = re.search(r"Cena\s+(\d+)", problema, re.I)
        if match:
            numeros.add(int(match.group(1)))
    return sorted(numeros)


def analisar_dialogos_roteiro(roteiro, idioma):
    """Retorna lista de problemas por cena."""
    problemas = []
    cenas = roteiro.get("scenes", {})

    for chave in sorted(cenas, key=lambda k: cenas[k].get("SCENE_NUMBER", 0)):
        cena = cenas[chave]
        num = cena.get("SCENE_NUMBER", chave)
        lines = cena.get("DIALOGUE_LINES", [])
        timing = calcular_timing(lines, idioma)

        timing_problema = None
        if timing["line_count"] < MIN_FALAS_POR_CENA:
            timing_problema = (
                f"só {timing['line_count']} falas (mínimo {MIN_FALAS_POR_CENA})"
            )
        elif timing["total_dialogue_seconds"] > DURACAO_CENA:
            timing_problema = (
                f"{timing['total_dialogue_seconds']}s estoura {DURACAO_CENA}s"
            )
        elif not timing["fills_scene"]:
            timing_problema = (
                f"{timing['total_dialogue_seconds']}s fora da meta "
                f"{MIN_SEGUNDOS_FALA}-{MAX_SEGUNDOS_FALA}s"
            )

        if timing_problema:
            problemas.append(f"Cena {num}: {timing_problema}")

        for linha in lines:
            if "TEXT" not in linha:
                continue
            texto = linha["TEXT"]
            speaker = linha.get("SPEAKER", "?")

            if not texto_no_idioma(texto, idioma):
                problemas.append(
                    f"Cena {num} ({speaker}): idioma errado — '{texto[:50]}'"
                )

            lock = linha.get("VOICE_IDENTITY_LOCK", "")
            if not voice_lock_valido(lock, idioma):
                problemas.append(
                    f"Cena {num} ({speaker}): VOICE_IDENTITY_LOCK sem idioma correto"
                )

    return problemas
