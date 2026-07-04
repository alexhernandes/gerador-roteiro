def perguntar():
    print("\n=== GERADOR DE ROTEIRO ===\n")

    print("Em qual idioma serão os diálogos?")
    print("Exemplos: Português, English, Español\n")
    idioma = input("Idioma: ").strip()
    while not idioma:
        idioma = input("Idioma (obrigatório): ").strip()

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