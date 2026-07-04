IDIOMAS = {
    "1": "Português (Brasil)",
    "2": "English",
    "3": "Español",
    "4": "Deutsch",
}


def _selecionar_idioma():
    print("Em qual idioma serão os diálogos?")
    print("  1 - Português (Brasil) [padrão]")
    print("  2 - English")
    print("  3 - Español")
    print("  4 - Deutsch\n")

    escolha = input("Idioma (ENTER = 1): ").strip()
    while escolha and escolha not in IDIOMAS:
        print("Opção inválida. Escolha 1, 2, 3 ou 4.")
        escolha = input("Idioma (ENTER = 1): ").strip()

    return IDIOMAS.get(escolha or "1")


def perguntar():
    print("\n=== GERADOR DE ROTEIRO ===\n")

    idioma = _selecionar_idioma()

    print("\nFormato do vídeo?")
    print("  1 - 9:16 (vertical — TikTok/Reels) [padrão]")
    print("  2 - 16:9 (horizontal — YouTube)\n")
    formato = input("Formato (ENTER = 9:16): ").strip()
    if formato in ("2", "16:9", "16x9"):
        aspect_ratio = "16:9"
    else:
        aspect_ratio = "9:16"

    print("\nQual o tema da história? (opcional)")
    print("Exemplos: Traição, Um mata o outro no final, Comédia de bananas\n")
    tema = input("Tema: ").strip()

    return {
        "idioma": idioma,
        "aspect_ratio": aspect_ratio,
        "tema": tema or "Livre — crie uma história viral com drama e humor",
    }
