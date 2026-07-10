<?php

declare(strict_types=1);

/** Agrupa problemas por cena para não inundar o console. */
function resumir_problemas(array $problemas, int $max_grupos = 6): array
{
    if ($problemas === []) {
        return [];
    }

    $grupos = [];
    foreach ($problemas as $item) {
        $partes = explode(':', $item, 2);
        $chave = trim($partes[0]);
        $grupos[$chave][] = $item;
    }

    $linhas = [];
    $grupos_lista = array_slice($grupos, 0, $max_grupos, true);

    foreach ($grupos_lista as $chave => $itens) {
        if (count($itens) === 1) {
            $linhas[] = $itens[0];
        } else {
            $linhas[] = "{$chave}: " . count($itens) . ' problema(s)';
            foreach (array_slice($itens, 0, 2) as $detalhe) {
                $parte = trim(explode(':', $detalhe, 2)[1] ?? '');
                $linhas[] = "  • {$parte}";
            }
            if (count($itens) > 2) {
                $linhas[] = '  • ... e mais ' . (count($itens) - 2);
            }
        }
    }

    if (count($grupos) > $max_grupos) {
        $linhas[] = '... e mais ' . (count($grupos) - $max_grupos) . ' cena(s)/grupo(s)';
    }

    return $linhas;
}

function imprimir_problemas(string $titulo, array $problemas): void
{
    if ($problemas === []) {
        return;
    }

    echo "\n  !! {$titulo} — " . count($problemas) . " problema(s)\n";
    foreach (resumir_problemas($problemas) as $linha) {
        echo "     {$linha}\n";
    }
}