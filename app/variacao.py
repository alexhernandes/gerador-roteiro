"""Briefs compactos para variar o elenco entre execucoes."""

import json
import random
import re
import unicodedata
import uuid
from pathlib import Path

from paths import ROOT_DIR
from universos import normalizar_universo


CATALOGOS = {
    "frutinhas": [
        "acerola", "amora", "atemoia", "caju", "caqui", "carambola",
        "cereja", "coco", "damasco", "figo", "framboesa", "goiaba",
        "graviola", "jabuticaba", "jaca", "kiwi", "lichia", "manga",
        "maracuja", "melancia", "mirtilo", "pera", "pitanga", "pitaya",
        "roma", "tamarindo", "tangerina", "umbu",
    ],
    "carros": [
        "microcarro eletrico", "hatch urbano dos anos 1980", "sedan executivo",
        "perua familiar retro", "cupe esportivo", "conversivel classico",
        "roadster eletrico", "supercarro hibrido", "van de entregas",
        "minivan futurista", "picape compacta", "picape off-road", "SUV de luxo",
        "jipe de trilha", "taxi antigo", "carro de rally", "stock car",
        "lowrider", "hot rod", "limusine", "carro policial", "ambulancia",
        "caminhao guincho", "caminhao de bombeiros", "onibus articulado",
        "moto cafe racer", "scooter eletrica", "trator agricola",
    ],
    "predios_falantes": [
        "casa colonial", "sobrado art nouveau", "torre art deco", "museu brutalista",
        "teatro neoclassico", "biblioteca modernista", "estacao ferroviaria",
        "farol costeiro", "mercado municipal", "fabrica de tijolos", "galpao portuario",
        "hotel belle epoque", "cinema de bairro", "escola contemporanea",
        "hospital futurista", "templo antigo", "ponte suspensa", "estadio",
        "arranha-ceu ecologico", "loja de esquina", "cabana alpina", "casa flutuante",
    ],
    "animais_falantes": [
        "axolote", "capivara", "quati", "tamandua", "lobo-guara", "ornitorrinco",
        "panda-vermelho", "suricato", "feneco", "lontra", "bicho-preguica",
        "coruja", "tucano", "arara", "pinguim", "beija-flor", "camaleao",
        "iguana", "salamandra", "polvo", "arraia", "cavalo-marinho", "tubarao-baleia",
        "caranguejo", "louva-a-deus", "besouro-rinoceronte", "borboleta-monarca",
    ],
    "humanos_desenhados": [
        "inventora aposentada", "chef adolescente", "jardineiro astronomo",
        "pilota de drones", "maestro timido", "detetive de bairro", "dancarino idoso",
        "mecanica prodigio", "guia de museu", "arqueologa urbana", "carteiro poeta",
        "cientista do clima", "skatista bibliotecaria", "costureiro futurista",
    ],
}

ARQUETIPOS = [
    "lider impulsivo", "estrategista reservado", "rival carismatico",
    "aliado desconfiado", "mentor excentrico", "trapaceiro arrependido",
    "otimista teimoso", "cético leal", "novato brilhante", "guardiao cansado",
]

CONTRASTES = [
    "formas arredondadas vs. angulares", "portes pequeno, medio e grande",
    "paletas quente, fria e neutra", "idades e ritmos de fala bem distintos",
    "acabamentos fosco, brilhante e desgastado", "epocas visuais contrastantes",
]


def _tokens_tipo(texto):
    normalizado = unicodedata.normalize("NFKD", str(texto or "").casefold())
    normalizado = "".join(c for c in normalizado if not unicodedata.combining(c))
    genericos = {"carro", "veiculo", "personagem", "antropomorfico", "falante", "adulto"}
    return {
        token for token in re.findall(r"[a-z0-9]+", normalizado)
        if len(token) >= 4 and token not in genericos
    }


def _tipo_similar(a, b):
    a_texto = str(a).casefold()
    b_texto = str(b).casefold()
    return a_texto in b_texto or b_texto in a_texto or bool(_tokens_tipo(a) & _tokens_tipo(b))


def _tipos_recentes(output_dir=None, limite_arquivos=12):
    pasta = Path(output_dir or Path(ROOT_DIR) / "output")
    if not pasta.exists():
        return []
    arquivos = sorted(
        pasta.glob("*/elenco.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )[:limite_arquivos]
    tipos = []
    for arquivo in arquivos:
        try:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for personagem in dados.get("cast", []):
            tipo = str(
                personagem.get("character_type") or personagem.get("fruit_type") or ""
            ).strip().lower()
            if tipo and tipo not in tipos:
                tipos.append(tipo)
    return tipos


def criar_brief_variacao(universo, output_dir=None, rng=None):
    universo = normalizar_universo(universo)
    rng = rng or random.SystemRandom()
    catalogo = CATALOGOS.get(universo, CATALOGOS["humanos_desenhados"])
    recentes = _tipos_recentes(output_dir)
    disponiveis = [
        item for item in catalogo
        if not any(_tipo_similar(recente, item) for recente in recentes)
    ]
    if len(disponiveis) < 8:
        disponiveis = list(catalogo)

    candidatos = rng.sample(disponiveis, min(10, len(disponiveis)))
    arquetipos = rng.sample(ARQUETIPOS, 5)
    contrastes = rng.sample(CONTRASTES, 3)
    excluidos = recentes[:10]
    variacao_id = uuid.uuid4().hex[:10]

    linhas = [
        f"VARIATION_ID: {variacao_id}",
        "Crie 3-5 personagens; nomes, character_type, silhueta, idade, voz e papel devem ser distintos.",
        "Priorize tipos desta amostra combinatoria: " + ", ".join(candidatos) + ".",
        "Mantenha no character_type o termo tecnico da amostra escolhida para permitir controle de repeticao.",
        "Distribua papeis entre: " + ", ".join(arquetipos) + ".",
        "Aplique pelo menos dois contrastes: " + ", ".join(contrastes) + ".",
        "Nao copie nomes de exemplos nem use sempre o tipo mais conhecido do universo.",
    ]
    if excluidos:
        linhas.append(
            "Evite tipos usados recentemente (salvo se o tema exigir): "
            + ", ".join(excluidos)
            + "."
        )
    return "\n".join(linhas)
