#!/usr/bin/env bash
# ==============================================================================
# Tools Hub - Script de instalación y sincronización de herramientas
# Clona o actualiza todos los repositorios independientes de herramientas.
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

GITHUB_USER="RedoRojo"
TOOLS=(
    "transcript"
    "pdf-toolbox"
    "qr-code"
    "kindle-toolbox"
)

echo "=========================================================="
echo " Sincronizando herramientas de Tools Hub (@$GITHUB_USER)"
echo "=========================================================="

for tool in "${TOOLS[@]}"; do
    if [ -d "$tool/.git" ]; then
        echo "🔄 Actualizando $tool..."
        git -C "$tool" pull --ff-only || echo "⚠️  No se pudo hacer fast-forward en $tool (revisa cambios locales)."
    elif [ -d "$tool" ]; then
        echo "ℹ️  La carpeta '$tool/' ya existe localmente (sin .git o personalizada). Omitiendo clonado."
    else
        echo "📥 Clonando $tool..."
        git clone "https://github.com/$GITHUB_USER/$tool.git" "$tool"
    fi
done

echo ""
echo "✅ Todas las herramientas están listas."
echo "🚀 Ejecuta ./start-hub.sh para abrir el panel en http://localhost:7777"
