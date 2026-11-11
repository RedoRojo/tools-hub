#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

HUB_PORT="${HUB_PORT:-7777}"

# Comprobar si el Hub ya está corriendo
if python3 -c "import socket; s = socket.socket(); s.connect(('127.0.0.1', $HUB_PORT)); s.close()" 2>/dev/null; then
    echo "=========================================================="
    echo " Tools Hub ya se encuentra en ejecución en:"
    echo " http://127.0.0.1:$HUB_PORT"
    echo "=========================================================="
else
    echo "Iniciando Tools Hub en http://127.0.0.1:$HUB_PORT ..."
    nohup python3 -u hub.py "$HUB_PORT" </dev/null > hub.log 2>&1 &
    PID=$!
    echo "Tools Hub iniciado en segundo plano (PID: $PID, log: hub.log)"
    
    # Esperar hasta que responda
    for i in {1..20}; do
        if python3 -c "import socket; s = socket.socket(); s.connect(('127.0.0.1', $HUB_PORT)); s.close()" 2>/dev/null; then
            break
        fi
        sleep 0.2
    done
fi

# Abrir en el navegador predeterminado si xdg-open está disponible
if command -v xdg-open >/dev/null 2>&1; then
    echo "Abriendo Tools Hub en tu navegador..."
    xdg-open "http://127.0.0.1:$HUB_PORT" >/dev/null 2>&1 &
fi

echo "=========================================================="
echo " Panel activo: http://127.0.0.1:$HUB_PORT"
echo "=========================================================="
