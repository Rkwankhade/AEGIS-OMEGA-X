#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║          AEGIS OMEGA X — MASTER RUN SCRIPT                                 ║
# ║          Single entry point — Run on Kali Linux                            ║
# ║          Usage: chmod +x run.sh && ./run.sh                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

set -euo pipefail

AEGIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AEGIS_VERSION="14.0.0"
LOG_FILE="${AEGIS_DIR}/aegis-setup.log"
VENV_DIR="${AEGIS_DIR}/.venv"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"; }
info()  { echo -e "${CYAN}[→]${NC} $1" | tee -a "$LOG_FILE"; }
banner(){ echo -e "${WHITE}$1${NC}"; }

# ─────────────────────────────────────────────────────────────
banner "
 █████╗ ███████╗ ██████╗ ██╗███████╗     ██████╗ ███╗   ███╗███████╗ ██████╗  █████╗     ██╗  ██╗
██╔══██╗██╔════╝██╔════╝ ██║██╔════╝    ██╔═══██╗████╗ ████║██╔════╝██╔════╝ ██╔══██╗    ╚██╗██╔╝
███████║█████╗  ██║  ███╗██║███████╗    ██║   ██║██╔████╔██║█████╗  ██║  ███╗███████║     ╚███╔╝ 
██╔══██║██╔══╝  ██║   ██║██║╚════██║    ██║   ██║██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║     ██╔██╗ 
██║  ██║███████╗╚██████╔╝██║███████║    ╚██████╔╝██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║    ██╔╝ ██╗
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝     ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝    ╚═╝  ╚═╝
                          v${AEGIS_VERSION} — Augmented Enterprise Global Intelligence & Security
"

echo "Setup log: $LOG_FILE"
echo "Project dir: $AEGIS_DIR"
echo ""

# ─────────────────────────────────────────────────────────────
# DETECT OS
# ─────────────────────────────────────────────────────────────
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_NAME="$NAME"
        OS_ID="$ID"
    else
        OS_NAME="Unknown"
        OS_ID="unknown"
    fi
    info "Detected OS: $OS_NAME ($OS_ID)"
}

# ─────────────────────────────────────────────────────────────
# CHECK ROOT / SUDO
# ─────────────────────────────────────────────────────────────
check_privileges() {
    if [ "$EUID" -eq 0 ]; then
        warn "Running as root. Proceeding."
    elif sudo -n true 2>/dev/null; then
        log "Sudo available"
    else
        error "Need sudo privileges. Run: sudo ./run.sh"
        exit 1
    fi
}

# ─────────────────────────────────────────────────────────────
# INSTALL SYSTEM DEPS
# ─────────────────────────────────────────────────────────────
install_system_deps() {
    info "Installing system dependencies..."
    sudo apt-get update -qq 2>&1 | tail -1
    sudo apt-get install -y -qq \
        curl wget git vim unzip zip jq tree \
        build-essential gcc g++ make \
        software-properties-common \
        apt-transport-https ca-certificates gnupg lsb-release \
        python3 python3-pip python3-venv python3-dev \
        libssl-dev libffi-dev libpq-dev \
        postgresql-client redis-tools netcat-openbsd \
        2>&1 | tail -3
    log "System dependencies installed"
}

# ─────────────────────────────────────────────────────────────
# INSTALL DOCKER
# ─────────────────────────────────────────────────────────────
install_docker() {
    if command -v docker &>/dev/null; then
        log "Docker already installed: $(docker --version)"
        return 0
    fi
    info "Installing Docker..."
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    curl -fsSL https://download.docker.com/linux/debian/gpg \
        | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg 2>/dev/null
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
        https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo systemctl enable docker --now
    sudo usermod -aG docker "$USER" 2>/dev/null || true
    log "Docker installed: $(docker --version)"
}

# ─────────────────────────────────────────────────────────────
# INSTALL NODE.JS
# ─────────────────────────────────────────────────────────────
install_nodejs() {
    if command -v node &>/dev/null && node --version | grep -q "v2[0-9]"; then
        log "Node.js already installed: $(node --version)"
        return 0
    fi
    info "Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - 2>/dev/null
    sudo apt-get install -y -qq nodejs
    log "Node.js installed: $(node --version)"
}

# ─────────────────────────────────────────────────────────────
# INSTALL RUST
# ─────────────────────────────────────────────────────────────
install_rust() {
    if command -v cargo &>/dev/null; then
        log "Rust already installed: $(rustc --version)"
        return 0
    fi
    info "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
        | sh -s -- -y --default-toolchain stable 2>&1 | tail -3
    source "$HOME/.cargo/env" 2>/dev/null || true
    export PATH="$HOME/.cargo/bin:$PATH"
    log "Rust installed: $(rustc --version 2>/dev/null || echo 'requires shell restart')"
}

# ─────────────────────────────────────────────────────────────
# INSTALL PYTHON VENV
# ─────────────────────────────────────────────────────────────
setup_python_venv() {
    if [ -f "${VENV_DIR}/bin/activate" ]; then
        log "Python venv already exists"
        return 0
    fi
    info "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "${VENV_DIR}/bin/activate"
    pip install --upgrade pip -q
    info "Installing Python packages..."
    pip install -q \
        fastapi uvicorn[standard] \
        neo4j aiokafka \
        redis aioredis \
        asyncpg psycopg2-binary \
        pydantic \
        httpx aiohttp \
        numpy scikit-learn \
        stix2 taxii2-client \
        pyyaml \
        prometheus-client \
        pytest pytest-asyncio \
        2>&1 | tail -5
    log "Python environment ready"
}

# ─────────────────────────────────────────────────────────────
# START DOCKER INFRASTRUCTURE
# ─────────────────────────────────────────────────────────────
start_infrastructure() {
    info "Starting AEGIS infrastructure stack..."
    cd "${AEGIS_DIR}/DEPLOY/docker"

    # Start core infrastructure first
    docker compose up -d \
        neo4j postgres redis \
        zookeeper kafka opensearch \
        2>&1 | tail -5

    info "Waiting 60s for databases to initialize..."
    for i in $(seq 1 12); do
        echo -ne "\r  Progress: [$(printf '#%.0s' $(seq 1 $i))$(printf ' %.0s' $(seq $i 12))] ${i}0s"
        sleep 5
    done
    echo ""

    # Start monitoring
    docker compose up -d prometheus grafana loki kafka-ui 2>&1 | tail -3
    log "Infrastructure stack started"

    cd "$AEGIS_DIR"
}

# ─────────────────────────────────────────────────────────────
# INITIALIZE KAFKA TOPICS
# ─────────────────────────────────────────────────────────────
init_kafka_topics() {
    info "Creating Kafka topics..."
    TOPICS=(
        "telemetry.assets:8"
        "telemetry.identities:8"
        "telemetry.vulnerabilities:4"
        "telemetry.configurations:4"
        "telemetry.network:4"
        "telemetry.controls:4"
        "genome.mutations:8"
        "genome.risk_updates:8"
        "knowledge.ingest:16"
        "knowledge.embed_queue:8"
        "soc.alerts:8"
        "soc.incidents:4"
        "agent.tasks:8"
        "agent.results:8"
    )
    for topic_config in "${TOPICS[@]}"; do
        TOPIC="${topic_config%%:*}"
        PARTS="${topic_config##*:}"
        docker exec aegis-kafka kafka-topics \
            --bootstrap-server localhost:29092 \
            --create --topic "$TOPIC" \
            --partitions "$PARTS" \
            --replication-factor 1 \
            --if-not-exists 2>/dev/null || true
    done
    log "Kafka topics created (${#TOPICS[@]} topics)"
}

# ─────────────────────────────────────────────────────────────
# INITIALIZE DATABASES
# ─────────────────────────────────────────────────────────────
init_databases() {
    info "Initializing databases..."

    # PostgreSQL schemas
    for schema_file in \
        "MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/database/schema.sql" \
        "MEGA-LAYER-2-SECURITY-GENOME/database/genome_schema.sql" \
        "MEGA-LAYER-3-KNOWLEDGE-UNIVERSE/database/knowledge_schema.sql"; do
        if [ -f "${AEGIS_DIR}/${schema_file}" ]; then
            docker cp "${AEGIS_DIR}/${schema_file}" aegis-postgres:/tmp/schema.sql 2>/dev/null
            docker exec aegis-postgres psql -U aegis -d aegis_omega \
                -f /tmp/schema.sql -q 2>/dev/null || true
        fi
    done

    # Neo4j constraints
    docker exec aegis-neo4j cypher-shell \
        -u neo4j -p AegisOmegaX2024! \
        "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE;
         CREATE CONSTRAINT asset_id  IF NOT EXISTS FOR (a:Asset)  REQUIRE a.asset_id  IS UNIQUE;
         CREATE CONSTRAINT genome_node_id IF NOT EXISTS FOR (n:GenomeNode) REQUIRE n.node_id IS UNIQUE;
         CREATE CONSTRAINT ku_node_id IF NOT EXISTS FOR (n:KnowledgeNode) REQUIRE n.node_id IS UNIQUE;" \
        2>/dev/null || true

    log "Databases initialized"
}

# ─────────────────────────────────────────────────────────────
# START AEGIS APIs
# ─────────────────────────────────────────────────────────────
start_apis() {
    info "Starting AEGIS API services..."
    source "${VENV_DIR}/bin/activate"

    # Set environment
    export NEO4J_URI="bolt://localhost:7687"
    export NEO4J_USER="neo4j"
    export NEO4J_PASS="AegisOmegaX2024!"
    export POSTGRES_URL="postgresql://aegis:AegisOmegaX2024!@localhost:5432/aegis_omega"
    export REDIS_URL="redis://localhost:6379"
    export KAFKA_BROKERS="localhost:9092"

    mkdir -p "${AEGIS_DIR}/logs"

    # Layer 1 — PDT API
    cd "${AEGIS_DIR}/MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/services"
    nohup uvicorn pdt_api:app \
        --host 0.0.0.0 --port 8001 \
        --log-level warning \
        > "${AEGIS_DIR}/logs/pdt-api.log" 2>&1 &
    echo $! > "${AEGIS_DIR}/logs/pdt-api.pid"

    # Layer 2 — Genome API
    cd "${AEGIS_DIR}/MEGA-LAYER-2-SECURITY-GENOME/services"
    nohup uvicorn genome_api:app \
        --host 0.0.0.0 --port 8002 \
        --log-level warning \
        > "${AEGIS_DIR}/logs/genome-api.log" 2>&1 &
    echo $! > "${AEGIS_DIR}/logs/genome-api.pid"

    # Layer 3 — Knowledge Universe API
    cd "${AEGIS_DIR}/MEGA-LAYER-3-KNOWLEDGE-UNIVERSE/services"
    nohup uvicorn knowledge_api:app \
        --host 0.0.0.0 --port 8003 \
        --log-level warning \
        > "${AEGIS_DIR}/logs/knowledge-api.log" 2>&1 &
    echo $! > "${AEGIS_DIR}/logs/knowledge-api.pid"

    # Layers 4-14 — Unified Gateway
    cd "${AEGIS_DIR}/MEGA-LAYERS-5-14"
    nohup uvicorn complete_implementation:gateway \
        --host 0.0.0.0 --port 8000 \
        --log-level warning \
        > "${AEGIS_DIR}/logs/gateway.log" 2>&1 &
    echo $! > "${AEGIS_DIR}/logs/gateway.pid"

    cd "$AEGIS_DIR"

    info "Waiting 10s for APIs to start..."
    sleep 10
    log "AEGIS APIs started"
}

# ─────────────────────────────────────────────────────────────
# START FRONTEND
# ─────────────────────────────────────────────────────────────
start_frontend() {
    if ! command -v node &>/dev/null; then
        warn "Node.js not available — skipping frontend"
        return 0
    fi

    info "Starting Next.js frontend..."
    cd "${AEGIS_DIR}/aegis-frontend"

    # Install deps if needed
    if [ ! -d "node_modules" ]; then
        info "Installing frontend dependencies (this takes 2-3 min first time)..."
        npm install --silent 2>&1 | tail -3
    fi

    # Write env file
    cat > .env.local << 'ENV_EOF'
NEXT_PUBLIC_PDT_API_URL=http://localhost:8001
NEXT_PUBLIC_GENOME_API_URL=http://localhost:8002
NEXT_PUBLIC_KNOWLEDGE_API_URL=http://localhost:8003
NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8001/ws
ENV_EOF

    nohup npm run dev -- --port 3001 \
        > "${AEGIS_DIR}/logs/frontend.log" 2>&1 &
    echo $! > "${AEGIS_DIR}/logs/frontend.pid"

    cd "$AEGIS_DIR"
    log "Frontend starting at http://localhost:3001"
}

# ─────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────
health_check() {
    info "Running health checks..."
    sleep 5
    echo ""

    check_service() {
        local name="$1" url="$2"
        local result
        if curl -sf --connect-timeout 3 "$url" > /dev/null 2>&1; then
            printf "  ${GREEN}✓${NC}  %-30s ${GREEN}ONLINE${NC}\n" "$name"
            return 0
        else
            printf "  ${RED}✗${NC}  %-30s ${RED}OFFLINE${NC}\n" "$name"
            return 1
        fi
    }

    echo ""
    banner "═══════════════════════════════════════════════════"
    banner "           SERVICE HEALTH STATUS"
    banner "═══════════════════════════════════════════════════"
    check_service "Neo4j Browser     :7474"  "http://localhost:7474"
    check_service "Kafka UI          :8080"  "http://localhost:8080"
    check_service "OpenSearch        :9200"  "http://localhost:9200"
    check_service "Prometheus        :9090"  "http://localhost:9090/-/healthy"
    check_service "Grafana           :3000"  "http://localhost:3000/api/health"
    check_service "PDT API     L1    :8001"  "http://localhost:8001/health"
    check_service "Genome API  L2    :8002"  "http://localhost:8002/health"
    check_service "KU API      L3    :8003"  "http://localhost:8003/health"
    check_service "Gateway     L4-14 :8000"  "http://localhost:8000/health"
    check_service "Frontend          :3001"  "http://localhost:3001"
    banner "═══════════════════════════════════════════════════"
    echo ""
}

# ─────────────────────────────────────────────────────────────
# PRINT ACCESS INFO
# ─────────────────────────────────────────────────────────────
print_access_info() {
    echo ""
    banner "╔══════════════════════════════════════════════════════════════╗"
    banner "║         AEGIS OMEGA X — READY                               ║"
    banner "╠══════════════════════════════════════════════════════════════╣"
    banner "║  DASHBOARDS                                                  ║"
    banner "║    Master Dashboard:  http://localhost:3001/master           ║"
    banner "║    PDT Dashboard:     http://localhost:3001/pdt              ║"
    banner "║    Genome Dashboard:  http://localhost:3001/genome           ║"
    banner "║    KU Dashboard:      http://localhost:3001/knowledge        ║"
    banner "║                                                              ║"
    banner "║  API DOCS (Swagger)                                          ║"
    banner "║    PDT API:       http://localhost:8001/docs                 ║"
    banner "║    Genome API:    http://localhost:8002/docs                 ║"
    banner "║    KU API:        http://localhost:8003/docs                 ║"
    banner "║    Gateway L4-14: http://localhost:8000/docs                 ║"
    banner "║                                                              ║"
    banner "║  MONITORING                                                  ║"
    banner "║    Grafana:    http://localhost:3000  admin/AegisOmegaX2024! ║"
    banner "║    Prometheus: http://localhost:9090                         ║"
    banner "║                                                              ║"
    banner "║  DATABASES                                                   ║"
    banner "║    Neo4j:      http://localhost:7474  neo4j/AegisOmegaX2024! ║"
    banner "║    Kafka UI:   http://localhost:8080                         ║"
    banner "║    OpenSearch: http://localhost:9200                         ║"
    banner "║                                                              ║"
    banner "║  MANAGEMENT                                                  ║"
    banner "║    Stop all:   ./stop.sh                                     ║"
    banner "║    View logs:  ./logs.sh                                     ║"
    banner "║    Run tests:  ./test.sh                                     ║"
    banner "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  Logs: ${AEGIS_DIR}/logs/"
    echo ""
}

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
main() {
    echo "" > "$LOG_FILE"
    echo "AEGIS OMEGA X Setup — $(date)" >> "$LOG_FILE"

    detect_os
    check_privileges
    install_system_deps
    install_docker
    install_nodejs
    install_rust
    setup_python_venv
    start_infrastructure
    init_kafka_topics
    init_databases
    start_apis
    start_frontend
    health_check
    print_access_info
}

main "$@"
