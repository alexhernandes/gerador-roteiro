import os
import sys

from config import (
    AGENT_CONFIRM_BETWEEN_STEPS,
    AGENT_VIDEOS_PER_STEP,
    DEFAULT_ASPECT_RATIO,
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
    DEFAULT_UNIVERSE,
)
from universos import label_universo, listar_universos, normalizar_universo


IDIOMAS = [
    "Português (Brasil)",
    "English",
    "Español",
    "Deutsch",
    "日本語 (Japanese)",
]

FORMATOS = [
    ("9:16", "9:16 (vertical — TikTok/Reels)"),
    ("16:9", "16:9 (horizontal — YouTube)"),
]


def _limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")


def _indice_padrao(opcoes, valor_padrao):
    for i, opcao in enumerate(opcoes):
        valor = opcao[0] if isinstance(opcao, tuple) else opcao
        if str(valor).lower() == str(valor_padrao).lower():
            return i
    return 0


def _ler_tecla():
    try:
        import msvcrt

        tecla = msvcrt.getwch()
        if tecla in ("\x00", "\xe0"):
            tecla = msvcrt.getwch()
            if tecla == "H":
                return "up"
            if tecla == "P":
                return "down"
            return ""
        if tecla in ("\r", "\n"):
            return "enter"
        if tecla == "\x1b":
            return "esc"
        return tecla
    except ImportError:
        return input().strip()


def _valor_opcao(opcao):
    return opcao[0] if isinstance(opcao, tuple) else opcao


def _selecionar_menu_numerado(titulo, opcoes, valor_padrao=None):
    """Fallback para terminais que nao suportam leitura direta das setas."""
    indice_padrao = _indice_padrao(opcoes, valor_padrao)
    print("\n=== GERADOR DE ROTEIRO ===\n")
    print(titulo)
    print("Digite o número da opção e aperte ENTER:\n")
    for i, opcao in enumerate(opcoes, start=1):
        valor, label = opcao if isinstance(opcao, tuple) else (opcao, opcao)
        padrao = " [padrão]" if i - 1 == indice_padrao else ""
        print(f" {i}. {label}{padrao}")

    while True:
        try:
            resposta = input(f"\nOpção [{indice_padrao + 1}]: ").strip()
        except (EOFError, OSError):
            return _valor_opcao(opcoes[indice_padrao])

        if not resposta:
            return _valor_opcao(opcoes[indice_padrao])
        if resposta.isdigit() and 1 <= int(resposta) <= len(opcoes):
            return _valor_opcao(opcoes[int(resposta) - 1])
        print(f"Opção inválida. Digite um número de 1 a {len(opcoes)}.")


def selecionar_menu(titulo, opcoes, valor_padrao=None):
    if not sys.stdin.isatty():
        return _selecionar_menu_numerado(titulo, opcoes, valor_padrao)

    indice = _indice_padrao(opcoes, valor_padrao)

    while True:
        _limpar_tela()
        print("\n=== GERADOR DE ROTEIRO ===\n")
        print(titulo)
        print("Use ↑/↓ e ENTER ou pressione o número da opção.\n")

        for i, opcao in enumerate(opcoes):
            valor, label = opcao if isinstance(opcao, tuple) else (opcao, opcao)
            marcador = ">" if i == indice else " "
            padrao = " [padrão]" if str(valor).lower() == str(valor_padrao).lower() else ""
            print(f" {marcador} {i + 1}. {label}{padrao}")

        tecla = _ler_tecla()
        if tecla == "up":
            indice = (indice - 1) % len(opcoes)
        elif tecla == "down":
            indice = (indice + 1) % len(opcoes)
        elif tecla == "enter":
            selecionado = opcoes[indice]
            return _valor_opcao(selecionado)
        elif tecla in ("esc",):
            return valor_padrao or _valor_opcao(opcoes[0])
        elif str(tecla).isdigit():
            numero = int(tecla)
            if 1 <= numero <= len(opcoes):
                selecionado = opcoes[numero - 1]
                return _valor_opcao(selecionado)


def _selecionar_idioma():
    return selecionar_menu(
        "Em qual idioma serão os diálogos?",
        IDIOMAS,
        DEFAULT_LANGUAGE,
    )


def _selecionar_formato():
    return selecionar_menu(
        "Formato do vídeo?",
        FORMATOS,
        DEFAULT_ASPECT_RATIO,
    )


def _selecionar_universo():
    opcoes = [(u, label_universo(u)) for u in listar_universos()]
    return selecionar_menu(
        "Universo dos personagens?",
        opcoes,
        normalizar_universo(DEFAULT_UNIVERSE),
    )


def _selecionar_confirmacao_agente():
    valor = selecionar_menu(
        "O agente de IA deve perguntar antes de ir para o próximo passo?",
        [(True, "Sim, pedir confirmação"), (False, "Não, continuar automaticamente")],
        AGENT_CONFIRM_BETWEEN_STEPS,
    )
    return bool(valor)


def _selecionar_videos_por_passo():
    opcoes_base = [1, 2, 3, 5, 7]
    if AGENT_VIDEOS_PER_STEP not in opcoes_base:
        opcoes_base.append(AGENT_VIDEOS_PER_STEP)
        opcoes_base.sort()
    opcoes = [(n, f"{n} vídeo(s) antes do próximo passo") for n in opcoes_base]
    return int(selecionar_menu(
        "Quantos vídeos o agente pode fazer antes do próximo passo?",
        opcoes,
        AGENT_VIDEOS_PER_STEP,
    ))


def perguntar():
    print("\n=== GERADOR DE ROTEIRO ===\n")

    idioma = _selecionar_idioma()
    aspect_ratio = _selecionar_formato()
    universo = _selecionar_universo()
    agent_confirm_between_steps = _selecionar_confirmacao_agente()
    agent_videos_per_step = _selecionar_videos_por_passo()

    _limpar_tela()
    print("\n=== GERADOR DE ROTEIRO ===\n")
    print(f"Idioma: {idioma}")
    print(f"Formato: {aspect_ratio}")
    print(f"Universo: {label_universo(universo)}")
    print(
        "Agente: "
        f"{agent_videos_per_step} vídeo(s) por passo; "
        f"{'pedir confirmação' if agent_confirm_between_steps else 'continuar sem confirmação'}"
    )

    print("\nQual o tema da história? (opcional)")
    print("Exemplos: Traição, segredo de família, corrida proibida, prédio assombrado\n")
    tema = input("Tema: ").strip()

    return {
        "idioma": idioma,
        "aspect_ratio": aspect_ratio,
        "universo": universo,
        "tema": tema or DEFAULT_THEME,
        "agent_confirm_between_steps": agent_confirm_between_steps,
        "agent_videos_per_step": agent_videos_per_step,
    }
