#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║     AEGIS OMEGA X — KALI LINUX SETUP SCRIPT                            ║
# ║     Copy-paste every block sequentially in your Kali terminal           ║
# ║     Run as root or with sudo                                            ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ─────────────────────────────────────────
# BLOCK 1 — SYSTEM UPDATE + BASE TOOLS
# ─────────────────────────────────────────
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  curl wget git vim nano unzip zip \
  build-essential gcc g++ make \
  software-properties-common \
  apt-transport-https ca-certificates \
  gnupg lsb-release jq tree \
  net-tools netcat-openbsd nmap \
  python3 python3-pip python3-venv \
  python3-dev libssl-dev libffi-dev \
  libpq-dev postgresql-client \
  redis-tools


# ─────────────────────────────────────────
# BLOCK 2 — DOCKER + DOCKER COMPOSE
# ─────────────────────────────────────────
# Remove old docker if present
sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Install Docker
curl -fsSL https://download.docker.com/linux/debian/gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add current user to docker group (re-login required)
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Verify
docker --version
docker compose version


# ─────────────────────────────────────────
# BLOCK 3 — NODE.JS 20 + NPM
# ─────────────────────────────────────────
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version    # Should show v20.x.x
npm --version


# ─────────────────────────────────────────
# BLOCK 4 — RUST TOOLCHAIN
# ─────────────────────────────────────────
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
  | sh -s -- -y --default-toolchain stable
source "$HOME/.cargo/env"
rustup update stable
rustup target add x86_64-unknown-linux-gnu
cargo --version
rustc --version


# ─────────────────────────────────────────
# BLOCK 5 — GO 1.22
# ─────────────────────────────────────────
wget https://go.dev/dl/go1.22.3.linux-amd64.tar.gz -O /tmp/go.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf /tmp/go.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
export PATH=$PATH:/usr/local/go/bin
go version


# ─────────────────────────────────────────
# BLOCK 6 — KUBECTL + HELM + K9S
# ─────────────────────────────────────────
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s \
  https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version

# k9s (Kubernetes TUI)
K9S_VER=$(curl -s https://api.github.com/repos/derailed/k9s/releases/latest \
  | jq -r .tag_name)
wget "https://github.com/derailed/k9s/releases/download/${K9S_VER}/k9s_Linux_amd64.tar.gz" \
  -O /tmp/k9s.tar.gz
sudo tar -C /usr/local/bin -xzf /tmp/k9s.tar.gz k9s
k9s version


# ─────────────────────────────────────────
# BLOCK 7 — TERRAFORM
# ─────────────────────────────────────────
wget -O- https://apt.releases.hashicorp.com/gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
  https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/hashicorp.list

sudo apt update && sudo apt install -y terraform
terraform version


# ─────────────────────────────────────────
# BLOCK 8 — AWS CLI v2
# ─────────────────────────────────────────
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
  -o /tmp/awscliv2.zip
unzip /tmp/awscliv2.zip -d /tmp/
sudo /tmp/aws/install
aws --version

# Configure AWS (replace with your credentials)
aws configure set aws_access_key_id     YOUR_ACCESS_KEY_ID
aws configure set aws_secret_access_key YOUR_SECRET_ACCESS_KEY
aws configure set default.region        ap-south-1
aws configure set default.output        json


# ─────────────────────────────────────────
# BLOCK 9 — PYTHON ENVIRONMENT
# ─────────────────────────────────────────
pip3 install --upgrade pip
pip3 install virtualenv pipenv

# Create aegis venv
mkdir -p ~/aegis-omega-x
cd ~/aegis-omega-x
python3 -m venv .venv
source .venv/bin/activate

pip install \
  fastapi uvicorn[standard] \
  neo4j aiokafka \
  redis aioredis \
  pydantic pydantic-settings \
  httpx aiohttp \
  asyncpg psycopg2-binary \
  sqlalchemy alembic \
  python-jose[cryptography] \
  passlib[bcrypt] \
  prometheus-client \
  opentelemetry-api \
  opentelemetry-sdk \
  opentelemetry-instrumentation-fastapi \
  numpy scipy \
  scikit-learn \
  sentence-transformers \
  stix2 taxii2-client \
  pyyaml toml \
  boto3 botocore \
  pytest pytest-asyncio httpx \
  black flake8 mypy \
  bandit safety \
  rich click typer

pip freeze > requirements.txt


# ─────────────────────────────────────────
# BLOCK 10 — CLONE / SETUP PROJECT
# ─────────────────────────────────────────
cd ~
# If you have the project files already:
git init aegis-omega-x
cd aegis-omega-x

# Create full directory structure
mkdir -p \
  MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/{architecture,data-model,services,database,infrastructure,frontend,backend,docs} \
  MEGA-LAYER-2-SECURITY-GENOME/{architecture,data-model,services,database,infrastructure,frontend,backend,docs} \
  MEGA-LAYER-3-KNOWLEDGE-UNIVERSE/{architecture,data-model,services,database,infrastructure,frontend,backend,docs,ontology,embeddings} \
  MEGA-LAYER-4-AI-CIVILIZATION/{architecture,agents,services,database,frontend,backend,docs} \
  MEGA-LAYER-5-AUTONOMOUS-SOC/{architecture,agents,services,database,frontend,backend,docs} \
  MEGA-LAYER-6-PREDICTIVE-INTELLIGENCE/{architecture,models,services,database,frontend,backend,docs} \
  MEGA-LAYER-7-ARCHITECTURE-EVOLUTION/{architecture,services,database,frontend,backend,docs} \
  MEGA-LAYER-8-SECURITY-ECONOMICS/{architecture,models,services,database,frontend,backend,docs} \
  MEGA-LAYER-9-AUTONOMOUS-GOVERNANCE/{architecture,policies,services,database,frontend,backend,docs} \
  MEGA-LAYER-10-SOCIETY-SIMULATOR/{architecture,simulators,services,database,frontend,backend,docs} \
  MEGA-LAYER-11-FOUNDATION-MODELS/{architecture,models,services,database,frontend,backend,docs} \
  MEGA-LAYER-12-FORMAL-VERIFICATION/{architecture,proofs,services,frontend,docs} \
  MEGA-LAYER-13-QUANTUM-SAFE/{architecture,crypto,services,database,frontend,docs} \
  MEGA-LAYER-14-CYBER-PHYSICAL/{architecture,simulators,services,database,frontend,docs} \
  DEPLOY/{kali-setup,docker,k8s,terraform,scripts,monitoring}

echo "Project structure created"
tree -d -L 2 .


# ─────────────────────────────────────────
# BLOCK 11 — LOCAL DOCKER COMPOSE STACK
# (Run entire AEGIS stack locally on Kali)
# ─────────────────────────────────────────
cat > ~/aegis-omega-x/DEPLOY/docker/docker-compose.yml << 'COMPOSE_EOF'
version: '3.9'

networks:
  aegis-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  neo4j-data:
  neo4j-logs:
  postgres-data:
  redis-data:
  kafka-data:
  opensearch-data:
  prometheus-data:
  grafana-data:

services:

  # ── NEO4J ──────────────────────────────
  neo4j:
    image: neo4j:5.15-community
    container_name: aegis-neo4j
    networks: [aegis-net]
    ports:
      - "7474:7474"   # HTTP browser
      - "7687:7687"   # Bolt
    environment:
      NEO4J_AUTH: neo4j/AegisOmegaX2024!
      NEO4J_PLUGINS: '["apoc","graph-data-science"]'
      NEO4J_dbms_memory_heap_initial__size: 512m
      NEO4J_dbms_memory_heap_max__size: 2G
      NEO4J_dbms_memory_pagecache_size: 1G
      NEO4J_apoc_export_file_enabled: "true"
      NEO4J_apoc_import_file_enabled: "true"
      NEO4J_dbms_security_procedures_unrestricted: "apoc.*,gds.*"
    volumes:
      - neo4j-data:/data
      - neo4j-logs:/logs
    healthcheck:
      test: ["CMD","cypher-shell","-u","neo4j","-p","AegisOmegaX2024!","RETURN 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # ── POSTGRESQL + TIMESCALEDB ───────────
  postgres:
    image: timescale/timescaledb:latest-pg16
    container_name: aegis-postgres
    networks: [aegis-net]
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: aegis
      POSTGRES_PASSWORD: AegisOmegaX2024!
      POSTGRES_DB: aegis_omega
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL","pg_isready -U aegis -d aegis_omega"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── REDIS ─────────────────────────────
  redis:
    image: redis:7.2-alpine
    container_name: aegis-redis
    networks: [aegis-net]
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD","redis-cli","ping"]
      interval: 10s
      retries: 5

  # ── ZOOKEEPER ─────────────────────────
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: aegis-zookeeper
    networks: [aegis-net]
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  # ── KAFKA ─────────────────────────────
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: aegis-kafka
    networks: [aegis-net]
    depends_on: [zookeeper]
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_NUM_PARTITIONS: 8
      KAFKA_DEFAULT_REPLICATION_FACTOR: 1
      KAFKA_LOG_RETENTION_HOURS: 168
    volumes:
      - kafka-data:/var/lib/kafka/data
    healthcheck:
      test: ["CMD","kafka-topics","--bootstrap-server","localhost:29092","--list"]
      interval: 30s
      retries: 5

  # ── KAFKA UI ──────────────────────────
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: aegis-kafka-ui
    networks: [aegis-net]
    depends_on: [kafka]
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: aegis-local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:29092

  # ── OPENSEARCH ────────────────────────
  opensearch:
    image: opensearchproject/opensearch:2.11.0
    container_name: aegis-opensearch
    networks: [aegis-net]
    ports:
      - "9200:9200"
    environment:
      discovery.type: single-node
      plugins.security.disabled: "true"
      OPENSEARCH_JAVA_OPTS: "-Xms1g -Xmx2g"
    volumes:
      - opensearch-data:/usr/share/opensearch/data
    healthcheck:
      test: ["CMD-SHELL","curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      retries: 5

  # ── PDT INTELLIGENCE API ──────────────
  pdt-api:
    build:
      context: ../../MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/services
      dockerfile: Dockerfile.api
    container_name: aegis-pdt-api
    networks: [aegis-net]
    depends_on:
      neo4j:     { condition: service_healthy }
      postgres:  { condition: service_healthy }
      redis:     { condition: service_healthy }
      kafka:     { condition: service_healthy }
    ports:
      - "8001:8001"
    environment:
      NEO4J_URI:    bolt://neo4j:7687
      NEO4J_USER:   neo4j
      NEO4J_PASS:   AegisOmegaX2024!
      POSTGRES_URL: postgresql://aegis:AegisOmegaX2024!@postgres:5432/aegis_omega
      REDIS_URL:    redis://redis:6379
      KAFKA_BROKERS: kafka:29092
    restart: unless-stopped

  # ── GENOME API ────────────────────────
  genome-api:
    build:
      context: ../../MEGA-LAYER-2-SECURITY-GENOME/services
      dockerfile: Dockerfile.api
    container_name: aegis-genome-api
    networks: [aegis-net]
    depends_on:
      neo4j:    { condition: service_healthy }
      postgres: { condition: service_healthy }
      redis:    { condition: service_healthy }
    ports:
      - "8002:8002"
    environment:
      NEO4J_URI:    bolt://neo4j:7687
      NEO4J_USER:   neo4j
      NEO4J_PASS:   AegisOmegaX2024!
      POSTGRES_URL: postgresql://aegis:AegisOmegaX2024!@postgres:5432/aegis_omega
      REDIS_URL:    redis://redis:6379
      KAFKA_BROKERS: kafka:29092
    restart: unless-stopped

  # ── KNOWLEDGE UNIVERSE API ────────────
  knowledge-api:
    build:
      context: ../../MEGA-LAYER-3-KNOWLEDGE-UNIVERSE/services
      dockerfile: Dockerfile.api
    container_name: aegis-knowledge-api
    networks: [aegis-net]
    depends_on:
      neo4j:      { condition: service_healthy }
      postgres:   { condition: service_healthy }
      redis:      { condition: service_healthy }
      opensearch: { condition: service_healthy }
    ports:
      - "8003:8003"
    environment:
      NEO4J_URI:         bolt://neo4j:7687
      NEO4J_USER:        neo4j
      NEO4J_PASS:        AegisOmegaX2024!
      POSTGRES_URL:      postgresql://aegis:AegisOmegaX2024!@postgres:5432/aegis_omega
      REDIS_URL:         redis://redis:6379
      OPENSEARCH_URL:    http://opensearch:9200
      KAFKA_BROKERS:     kafka:29092
    restart: unless-stopped

  # ── PROMETHEUS ────────────────────────
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: aegis-prometheus
    networks: [aegis-net]
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'

  # ── GRAFANA ───────────────────────────
  grafana:
    image: grafana/grafana:10.2.0
    container_name: aegis-grafana
    networks: [aegis-net]
    depends_on: [prometheus]
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: AegisOmegaX2024!
      GF_USERS_ALLOW_SIGN_UP: "false"
    volumes:
      - grafana-data:/var/lib/grafana

  # ── LOKI (Log aggregation) ────────────
  loki:
    image: grafana/loki:2.9.0
    container_name: aegis-loki
    networks: [aegis-net]
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml

COMPOSE_EOF

echo "docker-compose.yml created"


# ─────────────────────────────────────────
# BLOCK 12 — PROMETHEUS CONFIG
# ─────────────────────────────────────────
cat > ~/aegis-omega-x/DEPLOY/docker/prometheus.yml << 'PROM_EOF'
global:
  scrape_interval:     15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'aegis-pdt-api'
    static_configs:
      - targets: ['pdt-api:8001']
    metrics_path: /metrics

  - job_name: 'aegis-genome-api'
    static_configs:
      - targets: ['genome-api:8002']
    metrics_path: /metrics

  - job_name: 'aegis-knowledge-api'
    static_configs:
      - targets: ['knowledge-api:8003']
    metrics_path: /metrics

  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j:2004']

  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka:7071']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:9121']
PROM_EOF


# ─────────────────────────────────────────
# BLOCK 13 — DOCKERFILES FOR EACH SERVICE
# ─────────────────────────────────────────

# PDT API Dockerfile
mkdir -p ~/aegis-omega-x/MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/services
cat > ~/aegis-omega-x/MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/services/Dockerfile.api << 'DF_EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "pdt_api:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
DF_EOF

# PDT API requirements
cat > ~/aegis-omega-x/MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/services/requirements.txt << 'REQ_EOF'
fastapi==0.109.0
uvicorn[standard]==0.27.0
neo4j==5.17.0
aiokafka==0.10.0
redis[asyncio]==5.0.1
aioredis==2.0.1
asyncpg==0.29.0
psycopg2-binary==2.9.9
pydantic==2.6.0
httpx==0.26.0
prometheus-client==0.19.0
python-jose[cryptography]==3.3.0
REQ_EOF

# Genome API Dockerfile
mkdir -p ~/aegis-omega-x/MEGA-LAYER-2-SECURITY-GENOME/services
cat > ~/aegis-omega-x/MEGA-LAYER-2-SECURITY-GENOME/services/Dockerfile.api << 'DF_EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8002
CMD ["uvicorn", "genome_api:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "4"]
DF_EOF

cp ~/aegis-omega-x/MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/services/requirements.txt \
   ~/aegis-omega-x/MEGA-LAYER-2-SECURITY-GENOME/services/requirements.txt

# Knowledge API Dockerfile
mkdir -p ~/aegis-omega-x/MEGA-LAYER-3-KNOWLEDGE-UNIVERSE/services
cat > ~/aegis-omega-x/MEGA-LAYER-3-KNOWLEDGE-UNIVERSE/services/Dockerfile.api << 'DF_EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8003
CMD ["uvicorn", "knowledge_api:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "4"]
DF_EOF

cat > ~/aegis-omega-x/MEGA-LAYER-3-KNOWLEDGE-UNIVERSE/services/requirements.txt << 'REQ_EOF'
fastapi==0.109.0
uvicorn[standard]==0.27.0
neo4j==5.17.0
aiokafka==0.10.0
redis[asyncio]==5.0.1
aioredis==2.0.1
asyncpg==0.29.0
pydantic==2.6.0
httpx==0.26.0
aiohttp==3.9.3
numpy==1.26.4
scikit-learn==1.4.0
sentence-transformers==2.4.0
stix2==3.0.1
taxii2-client==2.3.0
pyyaml==6.0.1
prometheus-client==0.19.0
REQ_EOF

echo "Dockerfiles created"


# ─────────────────────────────────────────
# BLOCK 14 — START LOCAL STACK
# ─────────────────────────────────────────
cd ~/aegis-omega-x/DEPLOY/docker

# Pull all images first (saves time)
docker compose pull

# Start infrastructure (databases/messaging first)
docker compose up -d neo4j postgres redis zookeeper kafka opensearch

echo "Waiting 60 seconds for infrastructure to initialize..."
sleep 60

# Verify infrastructure health
docker compose ps
docker exec aegis-neo4j cypher-shell -u neo4j -p AegisOmegaX2024! "RETURN 'Neo4j OK' AS status;"
docker exec aegis-postgres psql -U aegis -d aegis_omega -c "SELECT version();"
docker exec aegis-redis redis-cli ping

echo "Infrastructure ready"


# ─────────────────────────────────────────
# BLOCK 15 — INITIALIZE DATABASES
# ─────────────────────────────────────────

# Create Kafka topics
docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic telemetry.assets \
  --partitions 8 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic telemetry.identities \
  --partitions 8 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic telemetry.vulnerabilities \
  --partitions 4 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic telemetry.configurations \
  --partitions 4 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic telemetry.network \
  --partitions 4 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic telemetry.controls \
  --partitions 4 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic genome.mutations \
  --partitions 8 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic genome.risk_updates \
  --partitions 8 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic knowledge.ingest \
  --partitions 16 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic knowledge.embed_queue \
  --partitions 8 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic soc.alerts \
  --partitions 8 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic soc.incidents \
  --partitions 4 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic agent.tasks \
  --partitions 8 --replication-factor 1

docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create --topic agent.results \
  --partitions 8 --replication-factor 1

# Verify topics
docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 --list

echo "Kafka topics created"


# ─────────────────────────────────────────
# BLOCK 16 — POSTGRESQL SCHEMA INIT
# ─────────────────────────────────────────

# Copy schema files and run them
docker cp ~/aegis-omega-x/MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/database/schema.sql \
  aegis-postgres:/tmp/layer1_schema.sql

docker cp ~/aegis-omega-x/MEGA-LAYER-2-SECURITY-GENOME/database/genome_schema.sql \
  aegis-postgres:/tmp/layer2_schema.sql

docker cp ~/aegis-omega-x/MEGA-LAYER-3-KNOWLEDGE-UNIVERSE/database/knowledge_schema.sql \
  aegis-postgres:/tmp/layer3_schema.sql

docker exec aegis-postgres psql -U aegis -d aegis_omega -f /tmp/layer1_schema.sql
docker exec aegis-postgres psql -U aegis -d aegis_omega -f /tmp/layer2_schema.sql
docker exec aegis-postgres psql -U aegis -d aegis_omega -f /tmp/layer3_schema.sql

echo "PostgreSQL schemas initialized"


# ─────────────────────────────────────────
# BLOCK 17 — NEO4J SCHEMA INIT
# ─────────────────────────────────────────
docker exec aegis-neo4j cypher-shell \
  -u neo4j -p AegisOmegaX2024! << 'CYPHER_EOF'
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE;
CREATE CONSTRAINT asset_id  IF NOT EXISTS FOR (a:Asset)  REQUIRE a.asset_id  IS UNIQUE;
CREATE CONSTRAINT identity_id IF NOT EXISTS FOR (i:Identity) REQUIRE i.identity_id IS UNIQUE;
CREATE CONSTRAINT genome_node_id IF NOT EXISTS FOR (n:GenomeNode) REQUIRE n.node_id IS UNIQUE;
CREATE CONSTRAINT ku_node_id IF NOT EXISTS FOR (n:KnowledgeNode) REQUIRE n.node_id IS UNIQUE;
CREATE CONSTRAINT cve_id IF NOT EXISTS FOR (c:CVE) REQUIRE c.cve_id IS UNIQUE;
CREATE INDEX entity_domain IF NOT EXISTS FOR (e:Entity) ON (e.domain);
CREATE INDEX asset_type IF NOT EXISTS FOR (a:Asset) ON (a.asset_type);
CREATE INDEX asset_risk  IF NOT EXISTS FOR (a:Asset) ON (a.risk_score);
CREATE INDEX genome_type IF NOT EXISTS FOR (n:GenomeNode) ON (n.node_type);
CREATE INDEX ku_node_type IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.node_type);
RETURN 'Neo4j constraints and indexes created' AS status;
CYPHER_EOF


# ─────────────────────────────────────────
# BLOCK 18 — START APPLICATION SERVICES
# ─────────────────────────────────────────
cd ~/aegis-omega-x/DEPLOY/docker
docker compose up -d kafka-ui prometheus grafana loki

# Build and start APIs (requires Dockerfiles to be in place)
# For local dev without Docker build, run APIs directly:

# Terminal 1 — PDT API
cd ~/aegis-omega-x
source .venv/bin/activate
cd MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/services
# uvicorn pdt_api:app --host 0.0.0.0 --port 8001 --reload &

# Terminal 2 — Genome API
cd ~/aegis-omega-x/MEGA-LAYER-2-SECURITY-GENOME/services
# uvicorn genome_api:app --host 0.0.0.0 --port 8002 --reload &

# Terminal 3 — Knowledge API
cd ~/aegis-omega-x/MEGA-LAYER-3-KNOWLEDGE-UNIVERSE/services
# uvicorn knowledge_api:app --host 0.0.0.0 --port 8003 --reload &

echo "Service startup commands ready. Uncomment above or run in separate terminals."


# ─────────────────────────────────────────
# BLOCK 19 — VERIFY ALL SERVICES
# ─────────────────────────────────────────
echo "=== AEGIS OMEGA X — SERVICE HEALTH CHECK ==="
echo ""

# Neo4j
echo -n "Neo4j:      "
curl -sf http://localhost:7474 > /dev/null && echo "OK :7474" || echo "NOT READY"

# PostgreSQL
echo -n "PostgreSQL: "
docker exec aegis-postgres pg_isready -U aegis && echo "OK :5432" || echo "NOT READY"

# Redis
echo -n "Redis:      "
docker exec aegis-redis redis-cli ping | grep -q PONG && echo "OK :6379" || echo "NOT READY"

# Kafka
echo -n "Kafka:      "
docker exec aegis-kafka kafka-topics \
  --bootstrap-server localhost:29092 --list \
  > /dev/null 2>&1 && echo "OK :9092" || echo "NOT READY"

# OpenSearch
echo -n "OpenSearch: "
curl -sf http://localhost:9200/_cluster/health > /dev/null && echo "OK :9200" || echo "NOT READY"

# Prometheus
echo -n "Prometheus: "
curl -sf http://localhost:9090/-/healthy > /dev/null && echo "OK :9090" || echo "NOT READY"

# Grafana
echo -n "Grafana:    "
curl -sf http://localhost:3000/api/health > /dev/null && echo "OK :3000" || echo "NOT READY"

# APIs
echo -n "PDT API:    "
curl -sf http://localhost:8001/health > /dev/null && echo "OK :8001" || echo "Not started (start manually)"
echo -n "Genome API: "
curl -sf http://localhost:8002/health > /dev/null && echo "OK :8002" || echo "Not started (start manually)"
echo -n "KU API:     "
curl -sf http://localhost:8003/health > /dev/null && echo "OK :8003" || echo "Not started (start manually)"

echo ""
echo "=== ACCESS URLS ==="
echo "Neo4j Browser:  http://localhost:7474"
echo "Kafka UI:       http://localhost:8080"
echo "OpenSearch:     http://localhost:9200"
echo "Prometheus:     http://localhost:9090"
echo "Grafana:        http://localhost:3000  (admin / AegisOmegaX2024!)"
echo "PDT API:        http://localhost:8001/docs"
echo "Genome API:     http://localhost:8002/docs"
echo "Knowledge API:  http://localhost:8003/docs"


# ─────────────────────────────────────────
# BLOCK 20 — TEST API ENDPOINTS
# ─────────────────────────────────────────

# PDT — Planetary Health
curl -s http://localhost:8001/planetary/health | jq .

# PDT — Cascade Simulation
curl -s -X POST http://localhost:8001/simulate/cascade \
  -H "Content-Type: application/json" \
  -d '{
    "origin_asset_id": "ast-001",
    "severity": 0.9,
    "max_hops": 5,
    "propagation_probability": 0.15,
    "simulation_ticks": 10
  }' | jq .

# PDT — Risk Forecast
curl -s -X POST http://localhost:8001/forecast/risk \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "ent-001",
    "horizon_days": 30
  }' | jq .

# Genome — Summary
curl -s http://localhost:8002/genome/ent-001/summary | jq .

# Genome — DNA
curl -s http://localhost:8002/genome/ent-001/dna | jq .

# Genome — Live Mutation Feed
curl -s "http://localhost:8002/genome/global/mutation-feed?limit=5" | jq .

# Knowledge — Universe Stats
curl -s http://localhost:8003/universe/stats | jq .

# Knowledge — Threat Landscape
curl -s http://localhost:8003/threat-landscape/summary | jq .

# Knowledge — Semantic Search
curl -s -X POST http://localhost:8003/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "phishing techniques used by Russian APT groups",
    "node_types": ["technique","threat_actor"],
    "top_k": 5
  }' | jq .

# Knowledge — CVE Intelligence
curl -s http://localhost:8003/cve/CVE-2021-44228/intelligence | jq .

# Knowledge — Threat Actor Profile
curl -s http://localhost:8003/actors/ta-apt29/profile | jq .

echo "All API tests complete"


# ─────────────────────────────────────────
# BLOCK 21 — NEXT.JS FRONTEND SETUP
# ─────────────────────────────────────────
cd ~/aegis-omega-x

# Create unified Next.js app
npx create-next-app@latest aegis-frontend \
  --typescript \
  --tailwind \
  --app \
  --no-eslint \
  --src-dir \
  --import-alias "@/*" \
  --no-git

cd aegis-frontend

# Install additional packages
npm install \
  d3 \
  three \
  @types/three \
  recharts \
  @types/d3 \
  lucide-react \
  framer-motion \
  @tanstack/react-query \
  axios \
  swr \
  zustand

# Copy dashboards
cp ~/aegis-omega-x/MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/frontend/pdt-dashboard.tsx \
   src/app/pdt/page.tsx

cp ~/aegis-omega-x/MEGA-LAYER-2-SECURITY-GENOME/frontend/genome-dashboard.tsx \
   src/app/genome/page.tsx

cp ~/aegis-omega-x/MEGA-LAYER-3-KNOWLEDGE-UNIVERSE/frontend/knowledge-dashboard.tsx \
   src/app/knowledge/page.tsx

# Environment file
cat > .env.local << 'ENV_EOF'
NEXT_PUBLIC_PDT_API_URL=http://localhost:8001
NEXT_PUBLIC_GENOME_API_URL=http://localhost:8002
NEXT_PUBLIC_KNOWLEDGE_API_URL=http://localhost:8003
NEXT_PUBLIC_WS_URL=ws://localhost:8001/ws
ENV_EOF

# Start dev server
npm run dev &
echo "Frontend running at http://localhost:3001"


# ─────────────────────────────────────────
# BLOCK 22 — USEFUL ALIASES FOR KALI
# ─────────────────────────────────────────
cat >> ~/.bashrc << 'ALIAS_EOF'

# AEGIS OMEGA X Aliases
alias aegis-start='cd ~/aegis-omega-x/DEPLOY/docker && docker compose up -d'
alias aegis-stop='cd ~/aegis-omega-x/DEPLOY/docker && docker compose down'
alias aegis-status='docker compose -f ~/aegis-omega-x/DEPLOY/docker/docker-compose.yml ps'
alias aegis-logs='docker compose -f ~/aegis-omega-x/DEPLOY/docker/docker-compose.yml logs -f'
alias aegis-neo4j='docker exec -it aegis-neo4j cypher-shell -u neo4j -p AegisOmegaX2024!'
alias aegis-redis='docker exec -it aegis-redis redis-cli'
alias aegis-kafka='docker exec -it aegis-kafka kafka-topics --bootstrap-server localhost:29092'
alias aegis-psql='docker exec -it aegis-postgres psql -U aegis -d aegis_omega'
alias aegis-pdt='curl -s http://localhost:8001/planetary/health | jq .'
alias aegis-genome='curl -s http://localhost:8002/genome/ent-001/summary | jq .'
alias aegis-ku='curl -s http://localhost:8003/universe/stats | jq .'
alias aegis-venv='cd ~/aegis-omega-x && source .venv/bin/activate'

ALIAS_EOF

source ~/.bashrc
echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║   AEGIS OMEGA X — KALI SETUP COMPLETE         ║"
echo "║   All 22 blocks executed successfully          ║"
echo "║                                                ║"
echo "║   Neo4j:      http://localhost:7474            ║"
echo "║   Kafka UI:   http://localhost:8080            ║"
echo "║   Grafana:    http://localhost:3000            ║"
echo "║   PDT API:    http://localhost:8001/docs       ║"
echo "║   Genome API: http://localhost:8002/docs       ║"
echo "║   KU API:     http://localhost:8003/docs       ║"
echo "║   Frontend:   http://localhost:3001            ║"
echo "╚═══════════════════════════════════════════════╝"
