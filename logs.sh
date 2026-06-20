#!/bin/bash
# AEGIS OMEGA X — VIEW LOGS
# Usage: ./logs.sh [service]
# Services: pdt | genome | ku | gateway | frontend | docker

AEGIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE="${1:-all}"

case "$SERVICE" in
    pdt)      tail -f "${AEGIS_DIR}/logs/pdt-api.log" ;;
    genome)   tail -f "${AEGIS_DIR}/logs/genome-api.log" ;;
    ku)       tail -f "${AEGIS_DIR}/logs/knowledge-api.log" ;;
    gateway)  tail -f "${AEGIS_DIR}/logs/gateway.log" ;;
    frontend) tail -f "${AEGIS_DIR}/logs/frontend.log" ;;
    docker)   cd "${AEGIS_DIR}/DEPLOY/docker" && docker compose logs -f ;;
    all)
        echo "=== PDT API ===" && tail -20 "${AEGIS_DIR}/logs/pdt-api.log" 2>/dev/null
        echo "=== GENOME API ===" && tail -20 "${AEGIS_DIR}/logs/genome-api.log" 2>/dev/null
        echo "=== KU API ===" && tail -20 "${AEGIS_DIR}/logs/knowledge-api.log" 2>/dev/null
        echo "=== GATEWAY ===" && tail -20 "${AEGIS_DIR}/logs/gateway.log" 2>/dev/null
        ;;
    *)
        echo "Usage: ./logs.sh [pdt|genome|ku|gateway|frontend|docker|all]"
        ;;
esac
