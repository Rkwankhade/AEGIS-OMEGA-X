#!/bin/bash
# AEGIS OMEGA X — STOP ALL SERVICES
# Usage: ./stop.sh

AEGIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Stopping AEGIS OMEGA X..."

# Stop Python APIs
for pidfile in logs/pdt-api.pid logs/genome-api.pid logs/knowledge-api.pid logs/gateway.pid logs/frontend.pid; do
    if [ -f "${AEGIS_DIR}/${pidfile}" ]; then
        PID=$(cat "${AEGIS_DIR}/${pidfile}")
        kill "$PID" 2>/dev/null && echo "  Stopped PID $PID ($pidfile)" || true
        rm -f "${AEGIS_DIR}/${pidfile}"
    fi
done

# Stop Docker stack
cd "${AEGIS_DIR}/DEPLOY/docker"
docker compose down 2>&1 | tail -3

echo ""
echo "All AEGIS services stopped."
