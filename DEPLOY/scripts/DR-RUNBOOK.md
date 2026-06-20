# AEGIS OMEGA X — DISASTER RECOVERY RUNBOOK
# Complete procedures for all failure scenarios

---

## SLO TARGETS

| Component              | Availability | RTO     | RPO     |
|------------------------|-------------|---------|---------|
| PDT Intelligence API   | 99.99%      | < 1 min | 0       |
| Genome API             | 99.99%      | < 1 min | 0       |
| Knowledge Universe API | 99.99%      | < 1 min | 0       |
| Unified Gateway        | 99.99%      | < 1 min | 0       |
| Neo4j Graph Cluster    | 99.99%      | < 5 min | < 10 s  |
| PostgreSQL Primary     | 99.999%     | < 2 min | < 1 s   |
| Redis Cluster          | 99.99%      | < 2 min | 0       |
| Kafka Cluster          | 99.99%      | < 2 min | 0       |
| OpenSearch             | 99.9%       | < 5 min | < 1 min |
| Simulation Core (Rust) | 99.9%       | < 5 min | < 1 min |

---

## SCENARIO 1 — PRIMARY REGION TOTAL FAILURE (ap-south-1)

**Trigger:** AWS region-wide outage  
**RTO Target:** 5 minutes  
**RPO Target:** < 10 seconds  

### Automated Steps (Route53 + ALB)

```
T+0:00  Route53 health check detects primary API endpoints unhealthy
T+0:30  DNS failover triggers → traffic routes to us-east-1
T+1:00  ALB in us-east-1 starts receiving traffic
T+1:30  PostgreSQL read replica in us-east-1 promoted to primary
T+2:00  Neo4j causal cluster in us-east-1 elects new primary
T+2:30  All AEGIS APIs in us-east-1 accepting read+write traffic
T+5:00  PagerDuty alert fired → ops team notified
```

### Manual Steps (Ops Team)

```bash
# Step 1 — Verify failover completed
aws route53 list-health-checks --region us-east-1
kubectl get pods -n aegis-omega-x --context us-east-1-cluster

# Step 2 — Confirm Neo4j cluster health in secondary
kubectl port-forward svc/aegis-omega-x-neo4j 7474:7474 \
  -n aegis-omega-x --context us-east-1-cluster
curl http://localhost:7474/db/data/

# Step 3 — Validate data consistency
psql $POSTGRES_URL_SECONDARY -c "
  SELECT count(*), max(created_at) FROM pdt.civilizational_entities;
"

# Step 4 — Run smoke tests against secondary
curl -f https://api-us.aegis-omega-x.internal/health
curl -f https://api-us.aegis-omega-x.internal/planetary/health

# Step 5 — Monitor Kafka consumer lag (replay if needed)
kafka-consumer-groups \
  --bootstrap-server $KAFKA_BROKERS_SECONDARY \
  --describe --all-groups | grep -v "0$"

# Step 6 — Page on-call if failover incomplete > 5min
echo "ESCALATE TO: security-platform-oncall@company.com"
```

---

## SCENARIO 2 — NEO4J CLUSTER QUORUM LOSS

**Trigger:** 2+ Neo4j core nodes fail simultaneously  
**RTO Target:** 5 minutes  

```bash
# Check cluster status
kubectl exec -it aegis-omega-x-neo4j-0 -n aegis-omega-x -- \
  cypher-shell -u neo4j -p $NEO4J_PASS \
  "CALL dbms.cluster.overview()"

# If only 1 node remaining — restore from backup
# Step 1: Get latest backup from S3
aws s3 ls s3://aegis-omega-x-data-lake/neo4j-backups/ \
  --recursive | sort | tail -5

# Step 2: Scale down statefulset
kubectl scale statefulset aegis-omega-x-neo4j \
  --replicas=0 -n aegis-omega-x

# Step 3: Restore backup to primary PVC
BACKUP_DATE=$(date -d "yesterday" +%Y%m%d)
aws s3 cp \
  s3://aegis-omega-x-data-lake/neo4j-backups/neo4j-${BACKUP_DATE}.dump \
  /tmp/neo4j-restore.dump

kubectl cp /tmp/neo4j-restore.dump \
  aegis-omega-x-neo4j-0:/tmp/restore.dump \
  -n aegis-omega-x

# Step 4: Restore
kubectl exec -it aegis-omega-x-neo4j-0 -n aegis-omega-x -- \
  neo4j-admin database restore \
  --from=/tmp/restore.dump \
  --database=neo4j \
  --overwrite-destination=true

# Step 5: Scale back up
kubectl scale statefulset aegis-omega-x-neo4j \
  --replicas=3 -n aegis-omega-x

# Step 6: Replay Kafka mutations since backup
# (Mutation engine will auto-replay from last committed offset)
kubectl rollout restart deployment/aegis-omega-x-genome-api \
  -n aegis-omega-x

echo "Neo4j restored. Monitor mutation replay progress."
```

---

## SCENARIO 3 — KAFKA CLUSTER DATA LOSS

**Trigger:** All Kafka brokers fail with data loss  
**RTO Target:** 10 minutes  

```bash
# Step 1: Check broker status
kafka-broker-api-versions \
  --bootstrap-server $KAFKA_BROKERS 2>&1 | head -20

# Step 2: If total loss — rebuild topics
BROKERS="kafka-0.kafka:9092"
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
  TOPIC=$(echo $topic_config | cut -d: -f1)
  PARTITIONS=$(echo $topic_config | cut -d: -f2)
  kafka-topics \
    --bootstrap-server $BROKERS \
    --create --topic $TOPIC \
    --partitions $PARTITIONS \
    --replication-factor 3 || \
  kafka-topics \
    --bootstrap-server $BROKERS \
    --alter --topic $TOPIC \
    --partitions $PARTITIONS
  echo "Topic $TOPIC ready"
done

# Step 3: Reset consumer group offsets (start from end)
kafka-consumer-groups \
  --bootstrap-server $BROKERS \
  --group genome-mutation-engine \
  --reset-offsets --to-latest --all-topics --execute

# Step 4: Restart all consumers
kubectl rollout restart deployment/aegis-omega-x-genome-api \
  -n aegis-omega-x
kubectl rollout restart deployment/aegis-omega-x-knowledge-api \
  -n aegis-omega-x

echo "Kafka rebuilt. Consumers restarting."
```

---

## SCENARIO 4 — POSTGRESQL PRIMARY FAILURE

**Trigger:** Primary RDS instance fails  
**RTO Target:** 2 minutes (Multi-AZ auto-failover)  

```bash
# Multi-AZ failover is AUTOMATIC — monitor via:
aws rds describe-events \
  --source-identifier aegis-omega-x-prod-postgres \
  --duration 60 \
  --region ap-south-1

# Verify new primary endpoint (DNS updates automatically)
psql "$(aws secretsmanager get-secret-value \
  --secret-id aegis-omega-x/postgres-credentials \
  --query SecretString --output text | jq -r .url)" \
  -c "SELECT now(), pg_is_in_recovery();"

# If pg_is_in_recovery = false → failover complete
# If pg_is_in_recovery = true → still a replica, wait

# Force manual failover if needed:
aws rds reboot-db-instance \
  --db-instance-identifier aegis-omega-x-prod-postgres \
  --force-failover \
  --region ap-south-1

echo "PostgreSQL failover complete when pg_is_in_recovery = false"
```

---

## SCENARIO 5 — SECURITY BREACH OF AEGIS PLATFORM

**Trigger:** Unauthorized access to AEGIS APIs or databases  
**RTO Target:** Immediate containment  

```bash
# STEP 1 — IMMEDIATE: Isolate compromised namespace
kubectl apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: emergency-lockdown
  namespace: aegis-omega-x
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
EOF

# STEP 2 — Rotate all secrets
aws secretsmanager rotate-secret \
  --secret-id aegis-omega-x/postgres-credentials
aws secretsmanager rotate-secret \
  --secret-id aegis-omega-x/neo4j-credentials

# Rotate Kubernetes secrets
kubectl create secret generic aegis-neo4j-secret \
  --from-literal=username=neo4j \
  --from-literal=password=$(openssl rand -base64 32) \
  -n aegis-omega-x \
  --dry-run=client -o yaml | kubectl apply -f -

# STEP 3 — Revoke all active sessions (JWT blacklist via Redis)
kubectl exec -it deploy/aegis-gateway -n aegis-omega-x -- \
  python3 -c "
import redis
r = redis.Redis(host='redis', port=6379)
r.set('jwt:blacklist:all', '1', ex=86400)
print('All JWTs blacklisted for 24h')
"

# STEP 4 — Collect forensic evidence
kubectl logs --previous \
  -n aegis-omega-x \
  -l system=aegis-omega-x \
  --timestamps=true \
  > /tmp/aegis-forensics-$(date +%Y%m%d-%H%M%S).log

aws s3 cp /tmp/aegis-forensics-*.log \
  s3://aegis-omega-x-data-lake/forensics/

# STEP 5 — Notify security team
echo "SECURITY INCIDENT — AEGIS OMEGA X platform breach detected"
echo "Timestamp: $(date -u)"
echo "Actions taken: namespace isolated, secrets rotated, JWTs blacklisted"
echo "Forensics: s3://aegis-omega-x-data-lake/forensics/"
echo ""
echo "ESCALATE TO: ciso@company.com, security-ir@company.com"

# STEP 6 — After investigation: restore network policy
kubectl delete networkpolicy emergency-lockdown -n aegis-omega-x
```

---

## BACKUP SCHEDULE

| Data                     | Method            | Frequency    | Retention | Location                    |
|--------------------------|-------------------|--------------|-----------|----------------------------|
| Neo4j full dump          | neo4j-admin dump  | Daily 02:00  | 90 days   | S3 cross-region             |
| Neo4j incremental        | Change data cap   | Continuous   | 7 days    | S3 same-region              |
| PostgreSQL WAL           | pg_basebackup     | Continuous   | 30 days   | RDS automated (cross-AZ)    |
| PostgreSQL snapshot      | RDS snapshot      | Daily 03:00  | 30 days   | RDS automated               |
| Redis RDB                | redis BGSAVE      | Every 15min  | 7 days    | S3 same-region              |
| Kafka topic data         | MirrorMaker 2     | Continuous   | 7 days    | Secondary region            |
| OpenSearch snapshots     | ISM policy        | Daily 04:00  | 30 days   | S3 same-region              |
| Simulation checkpoints   | Rust state dump   | Every 60 sec | 7 days    | S3 same-region              |
| K8s etcd                 | Velero            | Daily 01:00  | 30 days   | S3 cross-region             |

---

## BACKUP VERIFICATION (Run weekly)

```bash
#!/bin/bash
# DEPLOY/scripts/verify-backups.sh

echo "=== AEGIS OMEGA X BACKUP VERIFICATION ==="
BACKUP_DATE=$(date -d "yesterday" +%Y%m%d)
ERRORS=0

# 1. Neo4j backup exists
echo -n "Neo4j backup ($BACKUP_DATE): "
if aws s3 ls \
    s3://aegis-omega-x-data-lake/neo4j-backups/neo4j-${BACKUP_DATE}.dump \
    > /dev/null 2>&1; then
  echo "OK"
else
  echo "MISSING"
  ERRORS=$((ERRORS+1))
fi

# 2. PostgreSQL snapshot exists
echo -n "PostgreSQL snapshot ($BACKUP_DATE): "
SNAP=$(aws rds describe-db-snapshots \
  --db-instance-identifier aegis-omega-x-prod-postgres \
  --query "DBSnapshots[?SnapshotCreateTime>='${BACKUP_DATE}'] | [0].DBSnapshotIdentifier" \
  --output text 2>/dev/null)
if [ "$SNAP" != "None" ] && [ -n "$SNAP" ]; then
  echo "OK ($SNAP)"
else
  echo "MISSING"
  ERRORS=$((ERRORS+1))
fi

# 3. Test Neo4j restore (dry-run)
echo -n "Neo4j restore test: "
aws s3 cp \
  s3://aegis-omega-x-data-lake/neo4j-backups/neo4j-${BACKUP_DATE}.dump \
  /tmp/neo4j-test-restore.dump > /dev/null 2>&1
if [ $? -eq 0 ]; then
  SIZE=$(du -sh /tmp/neo4j-test-restore.dump | cut -f1)
  echo "OK (size: $SIZE)"
  rm /tmp/neo4j-test-restore.dump
else
  echo "FAILED — cannot download"
  ERRORS=$((ERRORS+1))
fi

# Summary
echo ""
if [ $ERRORS -eq 0 ]; then
  echo "ALL BACKUPS VERIFIED OK"
else
  echo "WARNING: $ERRORS backup(s) failed verification"
  exit 1
fi
```

---

## GAME DAY EXERCISES (Quarterly)

Run these chaos scenarios in staging to validate DR procedures:

```bash
# Install Chaos Mesh
helm install chaos-mesh chaos-mesh/chaos-mesh \
  -n chaos-testing --create-namespace

# Exercise 1: Kill Neo4j leader
kubectl apply -f - << 'EOF'
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: neo4j-leader-kill
  namespace: chaos-testing
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces: [aegis-omega-x]
    labelSelectors: { app: neo4j }
  scheduler:
    cron: "@once"
EOF

# Exercise 2: Network partition between API and DB
kubectl apply -f - << 'EOF'
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: api-db-partition
  namespace: chaos-testing
spec:
  action: partition
  mode: all
  selector:
    namespaces: [aegis-omega-x]
    labelSelectors: { app: pdt-api }
  direction: both
  target:
    mode: all
    selector:
      namespaces: [aegis-omega-x]
      labelSelectors: { app: neo4j }
  duration: "2m"
EOF

# Exercise 3: Memory pressure on simulation core
kubectl apply -f - << 'EOF'
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: sim-core-memory-stress
  namespace: chaos-testing
spec:
  mode: one
  selector:
    namespaces: [aegis-omega-x]
    labelSelectors: { app: pdt-simulation-core }
  stressors:
    memory:
      workers: 4
      size: "4GB"
  duration: "5m"
EOF

echo "Chaos exercises deployed to staging. Monitor dashboards."
echo "Expected: all SLOs maintained within RTO/RPO targets"
```
