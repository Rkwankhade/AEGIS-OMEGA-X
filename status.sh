#!/bin/bash
# AEGIS OMEGA X — LIVE STATUS CHECK
# Usage: ./status.sh

AEGIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check() {
    local name="$1" url="$2"
    if curl -sf --connect-timeout 3 "$url" > /dev/null 2>&1; then
        printf "  ${GREEN}✓${NC}  %-32s ${GREEN}ONLINE${NC}\n" "$name"
    else
        printf "  ${RED}✗${NC}  %-32s ${RED}OFFLINE${NC}\n" "$name"
    fi
}

echo ""
echo "  AEGIS OMEGA X — $(date '+%Y-%m-%d %H:%M:%S')"
echo "  ─────────────────────────────────────────────"
echo ""
echo "  INFRASTRUCTURE"
check  "Neo4j              :7474"  "http://localhost:7474"
check  "PostgreSQL         :5432"  "http://localhost:5432"   # will fail but shows intent
check  "Redis              :6379"  "http://localhost:6379"
check  "Kafka UI           :8080"  "http://localhost:8080"
check  "OpenSearch         :9200"  "http://localhost:9200"
check  "Prometheus         :9090"  "http://localhost:9090/-/healthy"
check  "Grafana            :3000"  "http://localhost:3000/api/health"
echo ""
echo "  AEGIS APIs"
check  "PDT API       L1   :8001"  "http://localhost:8001/health"
check  "Genome API    L2   :8002"  "http://localhost:8002/health"
check  "KU API        L3   :8003"  "http://localhost:8003/health"
check  "Gateway       L4-14:8000"  "http://localhost:8000/health"
echo ""
echo "  FRONTEND"
check  "Next.js           :3001"  "http://localhost:3001"
echo ""

# Show Docker containers
echo "  DOCKER CONTAINERS"
docker ps --format "  {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null \
    | grep aegis \
    | awk '{printf "  %-30s %s\n", $1, $2}' \
    || echo "  Docker not running or no aegis containers"

echo ""
echo "  API QUICK TEST"
echo -n "  PDT health:      "
curl -sf http://localhost:8001/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "offline"
echo -n "  Gateway health:  "
curl -sf http://localhost:8000/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d.get('status','?')} ({d.get('layers','?')} layers)\")" 2>/dev/null || echo "offline"
echo ""
