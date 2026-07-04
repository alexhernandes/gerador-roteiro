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


def analisar_dialogos_roteiro(roteiro, idioma):
    """Retorna lista de problemas por cena."""
    problemas = []
    cenas = roteiro.get("scenes", {})

    for chave in sorted(cenas, key=lambda k: cenas[k].get("SCENE_NUMBER", 0)):
        cena = cenas[chave]
        num = cena.get("SCENE_NUMBER", chave)
        lines = cena.get("DIALOGUE_LINES", [])
        timing = calcular_timing(lines, idioma)

        if timing["line_count"] < MIN_FALAS_POR_CENA:
            problemas.append(
                f"Cena {num}: só {timing['line_count']} falas (mínimo {MIN_FALAS_POR_CENA})"
            )

        if not timing["fills_scene"]:
            problemas.append(
                f"Cena {num}: {timing['total_dialogue_seconds']}s de áudio "
                f"(meta {MIN_SEGUNDOS_FALA}-{MAX_SEGUNDOS_FALA}s em {DURACAO_CENA}s)"
            )

        if timing["total_dialogue_seconds"] > DURACAO_CENA:
            problemas.append(
                f"Cena {num}: diálogo estoura os {DURACAO_CENA}s ({timing['total_dialogue_seconds']}s)"
            )

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