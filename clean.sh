#!/usr/bin/env bash
# clean.sh — Resetear el estado local para corridas limpias de testeo
# Elimina el manifest, archivos descargados de Moodle y contenido auto-generado.
# Uso: bash clean.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "Limpiando estado de kdef..."

# Manifest
if [ -f "$REPO_ROOT/data/manifest.json" ]; then
    rm "$REPO_ROOT/data/manifest.json"
    echo "  ✓ data/manifest.json eliminado"
fi

# Descargas temporales de Moodle
for dir in /tmp/kdef-moodle-*; do
    [ -d "$dir" ] && rm -rf "$dir" && echo "  ✓ $dir eliminado"
done

# Contenido auto-generado
if [ -d "$REPO_ROOT/content/notas-automaticas" ]; then
    find "$REPO_ROOT/content/notas-automaticas" -mindepth 1 -not -name '.gitkeep' -delete
    echo "  ✓ content/notas-automaticas/ vaciado"
fi

echo "Listo. Podés correr el pipeline desde cero."
