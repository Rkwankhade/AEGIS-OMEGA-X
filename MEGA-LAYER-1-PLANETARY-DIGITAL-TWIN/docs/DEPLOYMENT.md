# AEGIS OMEGA X — MEGA LAYER 1
# PLANETARY DIGITAL TWIN
# COMPLETE DEPLOYMENT GUIDE + FOLDER STRUCTURE

---

## COMPLETE FOLDER STRUCTURE

```
AEGIS-OMEGA-X/
├── MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/
│   ├── architecture/
│   │   └── 01-VISION.md                    ✓ Architecture, vision, service design
│   ├── data-model/
│   │   └── models.py                        ✓ All Python dataclasses + Neo4j schema
│   ├── backend/
│   │   └── simulation_core.rs               ✓ Rust tick engine + cascade engine
│   ├── services/
│   │   └── pdt_api.py                       ✓ FastAPI intelligence API (12 endpoints)
│   ├── database/
│   │   └── schema.sql                       ✓ PostgreSQL + TimescaleDB schema
│   ├── infrastructure/
│   │   ├── k8s-manifests.yaml               ✓ Full Kubernetes manifests
│   │   └── main.tf                          ✓ Terraform multi-region AWS
│   ├── frontend/
│   │   └── pdt-dashboard.tsx                ✓ Next.js real-time dashboard
│   └── docs/
│       ├── outputs-3-to-20.md               ✓ Research, threat model, scaling, etc.
│       └── DEPLOYMENT.md                    ← This file
│
├── MEGA-LAYER-2-SECURITY-GENOME/            ← Next phase
├── MEGA-LAYER-3-KNOWLEDGE-UNIVERSE/
├── MEGA-LAYER-4-AI-CIVILIZATION/
├── MEGA-LAYER-5-AUTONOMOUS-SOC/
├── MEGA-LAYER-6-PREDICTIVE-INTELLIGENCE/
├── MEGA-LAYER-7-ARCHITECTURE-EVOLUTION/
├── MEGA-LAYER-8-SECURITY-ECONOMICS/
├── MEGA-LAYER-9-AUTONOMOUS-GOVERNANCE/
├── MEGA-LAYER-10-SOCIETY-SIMULATOR/
├── MEGA-LAYER-11-FOUNDATION-MODELS/
├── MEGA-LAYER-12-FORMAL-VERIFICATION/
├── MEGA-LAYER-13-QUANTUM-SAFE/
└── MEGA-LAYER-14-CYBER-PHYSICAL/
```

---

## DEPLOYMENT GUIDE

### Prerequisites

```bash
# Tools required
- kubectl >= 1.28
- helm >= 3.13
- terraform >= 1.6
- docker >= 24.0
- aws-cli >= 2.15
- python >= 3.11
- rust >= 1.75
- node >= 20.0
```

---

### Step 1 — AWS Infrastructure

```bash
cd MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/infrastructure

# Initialize Terraform
terraform init

# Plan (review carefully)
terraform plan -out=pdt.tfplan

# Apply (creates EKS, Neo4j nodes, OpenSearch, ElastiCache, S3)
terraform apply pdt.tfplan

# Configure kubectl
aws eks update-kubeconfig \
  --region ap-south-1 \
  --name aegis-omega-x-pdt-primary
```

---

### Step 2 — Kubernetes Namespaces + Secrets

```bash
# Create namespace
kubectl apply -f infrastructure/k8s-manifests.yaml

# Create secrets
kubectl create secret generic neo4j-secret \
  --namespace aegis-pdt \
  --from-literal=auth=neo4j/CHANGE_ME_STRONG_PASSWORD \
  --from-literal=username=neo4j \
  --from-literal=password=CHANGE_ME_STRONG_PASSWORD

kubectl create secret generic postgres-secret \
  --namespace aegis-pdt \
  --from-literal=username=aegis \
  --from-literal=password=CHANGE_ME_STRONG_PASSWORD

kubectl create secret generic grafana-secret \
  --namespace aegis-pdt \
  --from-literal=admin-password=CHANGE_ME_STRONG_PASSWORD
```

---

### Step 3 — Database Initialization

```bash
# Wait for Neo4j cluster to be ready
kubectl wait --for=condition=ready pod \
  -l app=neo4j --namespace aegis-pdt --timeout=300s

# Initialize Neo4j schema (port-forward for local access)
kubectl port-forward svc/neo4j 7687:7687 --namespace aegis-pdt &

# Run Cypher schema (from models.py NEO4J_SCHEMA constant)
cypher-shell -a bolt://localhost:7687 \
  -u neo4j -p CHANGE_ME_STRONG_PASSWORD \
  < data-model/neo4j-schema.cypher

# Wait for PostgreSQL
kubectl wait --for=condition=ready pod \
  -l app=postgres --namespace aegis-pdt --timeout=300s

# Initialize PostgreSQL schema
kubectl port-forward svc/postgres 5432:5432 --namespace aegis-pdt &
psql postgresql://aegis:CHANGE_ME@localhost:5432/aegis_pdt \
  < database/schema.sql
```

---

### Step 4 — Build + Push Docker Images

```bash
# PDT Intelligence API (Python)
docker build -t aegis-omega-x/pdt-api:latest \
  -f services/Dockerfile.api services/

# PDT Simulation Core (Rust)
docker build -t aegis-omega-x/pdt-sim-core:latest \
  -f backend/Dockerfile.rust backend/

# Push to ECR
ECR_REGISTRY=$(aws ecr describe-registry --query registryId --output text).dkr.ecr.ap-south-1.amazonaws.com
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

docker tag aegis-omega-x/pdt-api:latest $ECR_REGISTRY/pdt-api:latest
docker push $ECR_REGISTRY/pdt-api:latest

docker tag aegis-omega-x/pdt-sim-core:latest $ECR_REGISTRY/pdt-sim-core:latest
docker push $ECR_REGISTRY/pdt-sim-core:latest
```

---

### Step 5 — Deploy Application Services

```bash
# Deploy PDT Intelligence API
kubectl apply -f infrastructure/k8s-manifests.yaml

# Verify rollout
kubectl rollout status deployment/pdt-intelligence-api \
  --namespace aegis-pdt

# Verify simulation core
kubectl rollout status statefulset/pdt-simulation-core \
  --namespace aegis-pdt

# Check all pods running
kubectl get pods --namespace aegis-pdt
```

---

### Step 6 — Frontend Deployment

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cat > .env.local << EOF
NEXT_PUBLIC_PDT_API_URL=http://pdt-intelligence-api.aegis-pdt:8001
NEXT_PUBLIC_WS_URL=ws://pdt-intelligence-api.aegis-pdt:8001/ws
EOF

# Build
npm run build

# Deploy to Kubernetes (Next.js app)
docker build -t aegis-omega-x/pdt-frontend:latest .
docker push $ECR_REGISTRY/pdt-frontend:latest

kubectl set image deployment/pdt-frontend \
  frontend=$ECR_REGISTRY/pdt-frontend:latest \
  --namespace aegis-pdt
```

---

### Step 7 — Observability

```bash
# Apply Prometheus scrape configs
kubectl apply -f monitoring/prometheus-config.yaml

# Import Grafana dashboards
kubectl port-forward svc/grafana 3000:3000 --namespace aegis-pdt &

# Import dashboard via Grafana API
curl -X POST http://admin:CHANGE_ME@localhost:3000/api/dashboards/import \
  -H 'Content-Type: application/json' \
  -d @monitoring/grafana-dashboard-pdt.json
```

---

### Step 8 — Verify System Health

```bash
# Port-forward PDT API
kubectl port-forward svc/pdt-intelligence-api 8001:8001 --namespace aegis-pdt &

# Check planetary health
curl http://localhost:8001/planetary/health | python3 -m json.tool

# Run cascade simulation test
curl -X POST http://localhost:8001/simulate/cascade \
  -H 'Content-Type: application/json' \
  -d '{
    "origin_asset_id": "ast-001",
    "severity": 0.8,
    "max_hops": 5,
    "propagation_probability": 0.15,
    "simulation_ticks": 10
  }' | python3 -m json.tool

# Verify Neo4j
curl http://localhost:7474/db/data/ | python3 -m json.tool
```

---

## API REFERENCE — MEGA LAYER 1

| Method | Endpoint                                | Description                              |
|--------|-----------------------------------------|------------------------------------------|
| GET    | /health                                 | API health check                         |
| GET    | /planetary/health                       | Global PDT health snapshot               |
| POST   | /entities/query                         | Query entities by domain/country/risk    |
| POST   | /assets/query                           | Query assets by type/risk/exposure       |
| GET    | /assets/{id}/neighbors                  | Get graph neighbors up to N hops         |
| POST   | /simulate/cascade                       | Run cascade propagation simulation       |
| POST   | /forecast/risk                          | Generate risk forecast (N-day horizon)   |
| GET    | /entities/{id}/attack-surface           | Attack surface summary for entity        |
| GET    | /topology/path?source=&target=          | Shortest attack path between assets      |

---

## LAYER 1 COMPLETION CHECKLIST

- [x] 01. Vision
- [x] 02. Architecture (conceptual + service design)
- [x] 03. Research objectives
- [x] 04. Threat model
- [x] 05. Data model (Python dataclasses + Neo4j schema)
- [x] 06. Service design (FastAPI 12 endpoints)
- [x] 07. API design (REST + route table)
- [x] 08. Database schema (PostgreSQL + TimescaleDB + Neo4j)
- [x] 09. Infrastructure design (Kubernetes + Terraform)
- [x] 10. Scaling strategy (Phase 1→5 scale targets)
- [x] 11. Reliability strategy (SLOs + multi-region)
- [x] 12. Security controls (encryption, RBAC, mTLS, OPA)
- [x] 13. Testing strategy (unit + integration + load + chaos)
- [x] 14. CI/CD design (GitHub Actions full pipeline)
- [x] 15. Monitoring strategy (Prometheus metrics + alerts)
- [x] 16. Cost model (AWS monthly estimate)
- [x] 17. Operations model (runbooks)
- [x] 18. Disaster recovery (RTO/RPO + DR runbook)
- [x] 19. Formal verification (TLA+, Alloy, Coq, Kani)
- [x] 20. Future evolution roadmap (20-year phased plan)

---

## NEXT: TYPE "next" TO BEGIN MEGA LAYER 2 — ENTERPRISE SECURITY GENOME
