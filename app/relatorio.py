"""Formatação compacta de problemas para console e JSON."""


def resumir_problemas(problemas, max_grupos=6):
    """Agrupa problemas por cena para não inundar o console."""
    if not problemas:
        return []

    grupos = {}
    for item in problemas:
        chave = item.split(":", 1)[0].strip()
        grupos.setdefault(chave, []).append(item)

    linhas = []
    for chave, itens in list(grupos.items())[:max_grupos]:
        if len(itens) == 1:
            linhas.append(itens[0])
        else:
            linhas.append(f"{chave}: {len(itens)} problema(s)")
            for detalhe in itens[:2]:
                parte = detalhe.split(":", 1)[-1].strip()
                linhas.append(f"  • {parte}")
            if len(itens) > 2:
                linhas.append(f"  • ... e mais {len(itens) - 2}")

    if len(grupos) > max_grupos:
        linhas.append(f"... e mais {len(grupos) - max_grupos} cena(s)/grupo(s)")

    return linhas


def imprimir_problemas(titulo, problemas):
    if not problemas:
        return

    print(f"\n  !! {titulo} — {len(problemas)} problema(s)")
    for linha in resumir_problemas(problemas):
        print(f"     {linha}")