#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  AEGIS OMEGA X — FAST START (services already installed)    ║
# ║  Usage: ./start.sh                                          ║
# ╚══════════════════════════════════════════════════════════════╝

AEGIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${AEGIS_DIR}/logs"
mkdir -p "$LOG_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; WHITE='\033[1;37m'; NC='\033[0m'

log()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()   { echo -e "${YELLOW}[!]${NC} $1"; }
error()  { echo -e "${RED}[✗]${NC} $1"; }
info()   { echo -e "${CYAN}[→]${NC} $1"; }
banner() { echo -e "${WHITE}$1${NC}"; }

banner "
 █████╗ ███████╗ ██████╗ ██╗███████╗     ██████╗ ███╗   ███╗███████╗ ██████╗  █████╗     ██╗  ██╗
██╔══██╗██╔════╝██╔════╝ ██║██╔════╝    ██╔═══██╗████╗ ████║██╔════╝██╔════╝ ██╔══██╗    ╚██╗██╔╝
███████║█████╗  ██║  ███╗██║███████╗    ██║   ██║██╔████╔██║█████╗  ██║  ███╗███████║     ╚███╔╝
██╔══██║██╔══╝  ██║   ██║██║╚════██║    ██║   ██║██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║     ██╔██╗
██║  ██║███████╗╚██████╔╝██║███████║    ╚██████╔╝██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║    ██╔╝ ██╗
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝     ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝    ╚═╝  ╚═╝
                          v14.0.0 — FAST START
"

# ── 1. Kill anything already on our ports ──────────────────────
info "Clearing ports 8000-8003, 3001..."
for port in 8000 8001 8002 8003 3001; do
    pids=$(ss -tlnp "sport = :$port" 2>/dev/null \
           | grep -oP 'pid=\K[0-9]+' | sort -u)
    [ -n "$pids" ] && kill $pids 2>/dev/null && warn "  Killed stale process on :$port"
done
sleep 2

# ── 2. Docker infrastructure ───────────────────────────────────
info "Checking Docker infrastructure..."
CONTAINERS=(aegis-neo4j aegis-postgres aegis-redis aegis-kafka
            aegis-zookeeper aegis-opensearch aegis-grafana
            aegis-prometheus aegis-loki aegis-kafka-ui)

NOT_RUNNING=()
for c in "${CONTAINERS[@]}"; do
    status=$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null)
    if [ "$status" != "running" ]; then
        NOT_RUNNING+=("$c")
    fi
done

if [ ${#NOT_RUNNING[@]} -gt 0 ]; then
    warn "Starting Docker containers: ${NOT_RUNNING[*]}"
    cd "${AEGIS_DIR}/DEPLOY/docker"
    docker compose up -d 2>&1 | tail -5
    info "Waiting 30s for infrastructure..."
    sleep 30
    cd "$AEGIS_DIR"
else
    log "All Docker containers already running"
fi

# ── 3. Kafka topics (idempotent) ───────────────────────────────
info "Ensuring Kafka topics exist..."
TOPICS=(
    "telemetry.assets:8"       "telemetry.identities:8"
    "telemetry.vulnerabilities:4" "telemetry.configurations:4"
    "telemetry.network:4"      "telemetry.controls:4"
    "genome.mutations:8"       "genome.risk_updates:8"
    "knowledge.ingest:16"      "knowledge.embed_queue:8"
    "soc.alerts:8"             "soc.incidents:4"
    "agent.tasks:8"            "agent.results:8"
)
for t in "${TOPICS[@]}"; do
    TOPIC="${t%%:*}"; PARTS="${t##*:}"
    docker exec aegis-kafka kafka-topics \
        --bootstrap-server localhost:29092 \
        --create --topic "$TOPIC" \
        --partitions "$PARTS" --replication-factor 1 \
        --if-not-exists 2>/dev/null || true
done
log "Kafka topics ready"

# ── 4. Neo4j constraints (idempotent) ─────────────────────────
info "Ensuring Neo4j constraints..."
docker exec aegis-neo4j cypher-shell -u neo4j -p AegisOmegaX2024! \
    "CREATE CONSTRAINT entity_id   IF NOT EXISTS FOR (e:Entity)       REQUIRE e.entity_id IS UNIQUE;
     CREATE CONSTRAINT asset_id    IF NOT EXISTS FOR (a:Asset)         REQUIRE a.asset_id  IS UNIQUE;
     CREATE CONSTRAINT genome_node IF NOT EXISTS FOR (n:GenomeNode)    REQUIRE n.node_id   IS UNIQUE;
     CREATE CONSTRAINT ku_node     IF NOT EXISTS FOR (n:KnowledgeNode) REQUIRE n.node_id   IS UNIQUE;" \
    2>/dev/null || true
log "Neo4j constraints ready"

# ── 5. Environment ────────────────────────────────────────────
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASS="AegisOmegaX2024!"
export POSTGRES_URL="postgresql://aegis:AegisOmegaX2024!@localhost:5432/aegis_omega"
export REDIS_URL="redis://localhost:6379"
export KAFKA_BROKERS="localhost:9092"

# ── 6. Start APIs ─────────────────────────────────────────────
info "Starting AEGIS API services..."

# Layer 1 — PDT
cd "${AEGIS_DIR}/MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/services"
nohup uvicorn pdt_api:app --host 0.0.0.0 --port 8001 --log-level warning \
    > "${LOG_DIR}/pdt-api.log" 2>&1 &
echo $! > "${LOG_DIR}/pdt-api.pid"
log "PDT API        :8001 → PID $!"

# Layer 2 — Genome
cd "${AEGIS_DIR}/MEGA-LAYER-2-SECURITY-GENOME/services"
nohup uvicorn genome_api:app --host 0.0.0.0 --port 8002 --log-level warning \
    > "${LOG_DIR}/genome-api.log" 2>&1 &
echo $! > "${LOG_DIR}/genome-api.pid"
log "Genome API     :8002 → PID $!"

# Layer 3 — Knowledge Universe
cd "${AEGIS_DIR}/MEGA-LAYER-3-KNOWLEDGE-UNIVERSE/services"
nohup uvicorn knowledge_api:app --host 0.0.0.0 --port 8003 --log-level warning \
    > "${LOG_DIR}/knowledge-api.log" 2>&1 &
echo $! > "${LOG_DIR}/knowledge-api.pid"
log "Knowledge API  :8003 → PID $!"

# Layers 4-14 — Unified Gateway
cd "${AEGIS_DIR}/MEGA-LAYERS-5-14"
nohup uvicorn complete_implementation:gateway --host 0.0.0.0 --port 8000 --log-level warning \
    > "${LOG_DIR}/gateway.log" 2>&1 &
echo $! > "${LOG_DIR}/gateway.pid"
log "Gateway L4-14  :8000 → PID $!"

cd "$AEGIS_DIR"

# ── 7. Start Frontend ─────────────────────────────────────────
info "Starting Next.js frontend..."
cd "${AEGIS_DIR}/aegis-frontend"
cat > .env.local << 'ENV'
NEXT_PUBLIC_PDT_API_URL=http://localhost:8001
NEXT_PUBLIC_GENOME_API_URL=http://localhost:8002
NEXT_PUBLIC_KNOWLEDGE_API_URL=http://localhost:8003
NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8001/ws
ENV
nohup npm run dev > "${LOG_DIR}/frontend.log" 2>&1 &
echo $! > "${LOG_DIR}/frontend.pid"
log "Frontend       :3001 → PID $!"
cd "$AEGIS_DIR"

# ── 8. Health check ───────────────────────────────────────────
info "Waiting 12s for services to initialize..."
sleep 12

check_service() {
    local name="$1" url="$2"
    if curl -sf --connect-timeout 4 "$url" > /dev/null 2>&1; then
        printf "  ${GREEN}✓${NC}  %-32s ${GREEN}ONLINE${NC}\n" "$name"
    else
        printf "  ${RED}✗${NC}  %-32s ${RED}OFFLINE${NC}\n" "$name"
    fi
}

echo ""
banner "═══════════════════════════════════════════════════"
banner "              SERVICE HEALTH STATUS"
banner "═══════════════════════════════════════════════════"
check_service "Neo4j Browser      :7474"  "http://localhost:7474"
check_service "Kafka UI           :8080"  "http://localhost:8080"
check_service "OpenSearch         :9200"  "http://localhost:9200"
check_service "Prometheus         :9090"  "http://localhost:9090/-/healthy"
check_service "Grafana            :3000"  "http://localhost:3000/api/health"
check_service "PDT API      L1    :8001"  "http://localhost:8001/health"
check_service "Genome API   L2    :8002"  "http://localhost:8002/health"
check_service "KU API       L3    :8003"  "http://localhost:8003/health"
check_service "Gateway      L4-14 :8000"  "http://localhost:8000/health"
check_service "Frontend           :3001"  "http://localhost:3001"
banner "═══════════════════════════════════════════════════"

# ── 9. Access info ────────────────────────────────────────────
echo ""
banner "╔══════════════════════════════════════════════════════════════╗"
banner "║              AEGIS OMEGA X — READY                          ║"
banner "╠══════════════════════════════════════════════════════════════╣"
banner "║  DASHBOARDS                                                  ║"
banner "║    Master:    http://localhost:3001/master                   ║"
banner "║    PDT:       http://localhost:3001/pdt                      ║"
banner "║    Genome:    http://localhost:3001/genome                   ║"
banner "║    Knowledge: http://localhost:3001/knowledge                ║"
banner "║                                                              ║"
banner "║  API DOCS                                                    ║"
banner "║    PDT:       http://localhost:8001/docs                     ║"
banner "║    Genome:    http://localhost:8002/docs                     ║"
banner "║    KU:        http://localhost:8003/docs                     ║"
banner "║    Gateway:   http://localhost:8000/docs                     ║"
banner "║                                                              ║"
banner "║  MONITORING                                                  ║"
banner "║    Grafana:   http://localhost:3000  admin/AegisOmegaX2024!  ║"
banner "║    Kafka UI:  http://localhost:8080                          ║"
banner "║    Neo4j:     http://localhost:7474  neo4j/AegisOmegaX2024!  ║"
banner "║                                                              ║"
banner "║  MANAGEMENT                                                  ║"
banner "║    Stop:      ./stop.sh                                      ║"
banner "║    Logs:      ./logs.sh                                      ║"
banner "║    Test:      ./test.sh                                      ║"
banner "╚══════════════════════════════════════════════════════════════╝"
echo ""
