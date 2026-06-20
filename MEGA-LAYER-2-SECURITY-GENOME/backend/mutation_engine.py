"""
AEGIS OMEGA X — MEGA LAYER 2
ENTERPRISE SECURITY GENOME — MUTATION ENGINE
Consumes telemetry events from Kafka, detects mutations,
propagates risk through dependency graph, emits MutationEvents.
"""

import asyncio
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from neo4j import AsyncGraphDatabase
import redis.asyncio as aioredis

from genome_models import (
    GenomeNode, GenomeEdge, MutationEvent, MutationType,
    RiskInheritanceCalculator, RiskInheritanceMode,
    AssetGenomeNode, IdentityGenomeNode, SecurityControlGenomeNode,
    DependencyGenomeNode, CVEGenomeNode
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("genome-mutation-engine")


# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────

KAFKA_BROKERS   = "kafka-0.kafka:9092,kafka-1.kafka:9092"
NEO4J_URI       = "bolt://neo4j:7687"
NEO4J_AUTH      = ("neo4j", "aegis-omega-x")
REDIS_URL       = "redis://redis:6379"

TOPICS_INBOUND  = [
    "telemetry.assets",
    "telemetry.identities",
    "telemetry.vulnerabilities",
    "telemetry.configurations",
    "telemetry.network",
    "telemetry.controls",
]
TOPIC_MUTATIONS  = "genome.mutations"
TOPIC_RISK       = "genome.risk_updates"
CONSUMER_GROUP   = "genome-mutation-engine"


# ──────────────────────────────────────────────
# TELEMETRY EVENT SCHEMAS
# ──────────────────────────────────────────────

ASSET_TELEMETRY_EXAMPLE = {
    "event_type":        "asset_scan",
    "source":            "aws_inspector",
    "entity_id":         "ent-001",
    "asset_id":          "ast-001",
    "name":              "payment-api-prod",
    "asset_type":        "server",
    "os":                "Ubuntu",
    "os_version":        "22.04",
    "is_internet_facing": True,
    "open_ports":        [443, 8080],
    "cve_ids":           ["CVE-2023-44487"],
    "timestamp":         "2024-01-15T12:00:00Z",
}

CVE_TELEMETRY_EXAMPLE = {
    "event_type":         "cve_detected",
    "source":             "nuclei",
    "entity_id":          "ent-001",
    "asset_id":           "ast-001",
    "cve_id":             "CVE-2023-44487",
    "cvss_score":         7.5,
    "severity":           "high",
    "exploited_in_wild":  True,
    "timestamp":          "2024-01-15T12:05:00Z",
}

IDENTITY_TELEMETRY_EXAMPLE = {
    "event_type":      "identity_change",
    "source":          "iam_scanner",
    "entity_id":       "ent-001",
    "identity_id":     "idn-001",
    "name":            "svc-payment",
    "identity_type":   "service",
    "privilege_level": "admin",      # was: standard → MUTATION: privilege_escalated
    "mfa_enabled":     False,
    "timestamp":       "2024-01-15T12:10:00Z",
}


# ──────────────────────────────────────────────
# MUTATION DETECTOR
# ──────────────────────────────────────────────

class MutationDetector:
    """
    Compares incoming telemetry against current genome state.
    Detects mutations and classifies them.
    """

    def __init__(self, redis_client):
        self.redis = redis_client

    async def get_current_state(self, node_id: str) -> Optional[Dict]:
        """Fetch current genome node state from Redis cache."""
        raw = await self.redis.get(f"genome:node:{node_id}")
        if raw:
            return json.loads(raw)
        return None

    async def store_state(self, node_id: str, state: Dict):
        """Update Redis cache with new node state."""
        await self.redis.setex(
            f"genome:node:{node_id}",
            86400,                      # 24hr TTL
            json.dumps(state, default=str)
        )

    def compute_fingerprint(self, state: Dict) -> str:
        clean = {k: v for k, v in state.items()
                 if k not in ("timestamp", "detected_at", "updated_at")}
        return hashlib.sha256(
            json.dumps(clean, sort_keys=True, default=str).encode()
        ).hexdigest()

    async def detect_asset_mutations(
        self, event: Dict
    ) -> List[MutationEvent]:
        mutations = []
        node_id = event.get("asset_id", "")
        current = await self.get_current_state(node_id)
        new_fp   = self.compute_fingerprint(event)
        old_fp   = current.get("fingerprint", "") if current else ""

        if not current:
            mutations.append(MutationEvent(
                entity_id    = event.get("entity_id", ""),
                node_id      = node_id,
                node_type    = "asset",
                mutation_type= MutationType.ASSET_ADDED,
                current_fp   = new_fp,
                current_state= event,
                risk_delta   = 0.1,
                severity     = "low",
                source       = event.get("source", "scanner"),
            ))
        elif new_fp != old_fp:
            delta = self._compute_delta(current, event)

            # Classify mutation type based on what changed
            if self._port_opened(current, event):
                mutations.append(self._make_mutation(
                    event, node_id, MutationType.PORT_OPENED,
                    old_fp, new_fp, delta, risk_delta=0.15, severity="medium"
                ))

            if self._cve_introduced(current, event):
                sev = "critical" if any(
                    c in event.get("cve_ids", [])
                    for c in ["CVE-2021-44228", "CVE-2023-44487"]  # Example critical CVEs
                ) else "high"
                mutations.append(self._make_mutation(
                    event, node_id, MutationType.CVE_INTRODUCED,
                    old_fp, new_fp, delta,
                    risk_delta=0.4 if sev == "critical" else 0.2,
                    severity=sev
                ))

            elif new_fp != old_fp:  # Generic modification
                mutations.append(self._make_mutation(
                    event, node_id, MutationType.ASSET_MODIFIED,
                    old_fp, new_fp, delta, risk_delta=0.05, severity="low"
                ))

        await self.store_state(node_id, {**event, "fingerprint": new_fp})
        return mutations

    async def detect_identity_mutations(
        self, event: Dict
    ) -> List[MutationEvent]:
        mutations = []
        node_id  = event.get("identity_id", "")
        current  = await self.get_current_state(f"idn:{node_id}")
        new_fp   = self.compute_fingerprint(event)
        old_fp   = current.get("fingerprint", "") if current else ""

        if current and new_fp != old_fp:
            delta = self._compute_delta(current, event)

            # Privilege escalation detection
            old_priv = current.get("privilege_level", "standard")
            new_priv = event.get("privilege_level", "standard")
            priv_order = {"standard": 0, "privileged": 1, "admin": 2, "superadmin": 3}
            if priv_order.get(new_priv, 0) > priv_order.get(old_priv, 0):
                mutations.append(self._make_mutation(
                    event, node_id, MutationType.PRIVILEGE_ESCALATED,
                    old_fp, new_fp, delta,
                    risk_delta=0.35, severity="critical"
                ))

            # MFA disabled
            if current.get("mfa_enabled") and not event.get("mfa_enabled"):
                mutations.append(self._make_mutation(
                    event, node_id, MutationType.MFA_DISABLED,
                    old_fp, new_fp, delta,
                    risk_delta=0.25, severity="high"
                ))

        elif not current:
            mutations.append(MutationEvent(
                entity_id     = event.get("entity_id", ""),
                node_id       = node_id,
                node_type     = "identity",
                mutation_type = MutationType.IDENTITY_CREATED,
                current_fp    = new_fp,
                current_state = event,
                severity      = "low",
            ))

        await self.store_state(f"idn:{node_id}", {**event, "fingerprint": new_fp})
        return mutations

    def _make_mutation(
        self, event, node_id, mut_type, old_fp, new_fp, delta,
        risk_delta=0.0, severity="low"
    ) -> MutationEvent:
        return MutationEvent(
            entity_id     = event.get("entity_id", ""),
            node_id       = node_id,
            node_type     = event.get("event_type", "").split("_")[0],
            mutation_type = mut_type,
            previous_fp   = old_fp,
            current_fp    = new_fp,
            delta         = delta,
            risk_delta    = risk_delta,
            severity      = severity,
            source        = event.get("source", "scanner"),
            occurred_at   = datetime.fromisoformat(
                event.get("timestamp", datetime.utcnow().isoformat())
            ),
        )

    def _compute_delta(self, old: Dict, new: Dict) -> Dict:
        delta = {}
        all_keys = set(old.keys()) | set(new.keys())
        for k in all_keys:
            ov, nv = old.get(k), new.get(k)
            if ov != nv:
                delta[k] = {"from": ov, "to": nv}
        return delta

    def _port_opened(self, old: Dict, new: Dict) -> bool:
        old_ports = set(old.get("open_ports", []))
        new_ports = set(new.get("open_ports", []))
        return bool(new_ports - old_ports)

    def _cve_introduced(self, old: Dict, new: Dict) -> bool:
        old_cves = set(old.get("cve_ids", []))
        new_cves = set(new.get("cve_ids", []))
        return bool(new_cves - old_cves)


# ──────────────────────────────────────────────
# RISK PROPAGATION SERVICE
# ──────────────────────────────────────────────

class GenomeRiskPropagator:
    """
    When a mutation occurs, propagates updated risk scores
    through the dependency graph in Neo4j.
    """

    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver

    async def propagate_from_mutation(self, mutation: MutationEvent):
        """
        Fetch the subgraph downstream of the mutated node,
        recompute effective risk scores, persist back.
        """
        async with self.driver.session() as session:
            # Get all downstream nodes (up to 5 hops)
            result = await session.run("""
                MATCH (origin:GenomeNode {node_id: $node_id})
                MATCH path = (origin)-[:DEPENDS_ON|HOSTS|EXPOSES|PROCESSES*1..5]->(downstream)
                RETURN downstream.node_id AS nid,
                       downstream.risk_score AS base_risk,
                       length(path) AS hops
                ORDER BY hops
            """, {"node_id": mutation.node_id})

            records = await result.data()

            for record in records:
                nid       = record["nid"]
                base      = record.get("base_risk") or 0.0
                hops      = record["hops"]
                damping   = 0.7 ** hops
                new_risk  = min(base + mutation.risk_delta * damping, 1.0)

                await session.run("""
                    MATCH (n:GenomeNode {node_id: $nid})
                    SET n.inherited_risk = $inherited,
                        n.effective_risk = $effective,
                        n.updated_at = datetime()
                """, {
                    "nid":       nid,
                    "inherited": round(mutation.risk_delta * damping, 4),
                    "effective": round(new_risk, 4),
                })

            log.info(
                f"[PROPAGATE] Mutation {mutation.mutation_type} on {mutation.node_id} "
                f"propagated to {len(records)} downstream nodes"
            )

    async def persist_mutation_to_neo4j(self, mutation: MutationEvent):
        """Persist mutation event as a node in Neo4j for audit trail."""
        async with self.driver.session() as session:
            await session.run("""
                CREATE (m:MutationEvent {
                    mutation_id:   $mutation_id,
                    entity_id:     $entity_id,
                    node_id:       $node_id,
                    mutation_type: $mutation_type,
                    risk_delta:    $risk_delta,
                    severity:      $severity,
                    occurred_at:   $occurred_at,
                    source:        $source
                })
                WITH m
                MATCH (n:GenomeNode {node_id: $node_id})
                CREATE (m)-[:MUTATED]->(n)
            """, {
                "mutation_id":   mutation.mutation_id,
                "entity_id":     mutation.entity_id,
                "node_id":       mutation.node_id,
                "mutation_type": mutation.mutation_type.value,
                "risk_delta":    mutation.risk_delta,
                "severity":      mutation.severity,
                "occurred_at":   mutation.occurred_at.isoformat(),
                "source":        mutation.source,
            })


# ──────────────────────────────────────────────
# MAIN MUTATION ENGINE
# ──────────────────────────────────────────────

class GenomeMutationEngine:

    def __init__(self):
        self.neo4j = AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        self.redis_client = None
        self.producer = None
        self.consumer = None
        self.detector = None
        self.propagator = None

    async def initialize(self):
        self.redis_client = await aioredis.from_url(REDIS_URL, decode_responses=True)
        self.detector     = MutationDetector(self.redis_client)
        self.propagator   = GenomeRiskPropagator(self.neo4j)

        self.consumer = AIOKafkaConsumer(
            *TOPICS_INBOUND,
            bootstrap_servers=KAFKA_BROKERS,
            group_id=CONSUMER_GROUP,
            auto_offset_reset="earliest",
            value_deserializer=lambda v: json.loads(v.decode()),
        )
        self.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BROKERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode(),
        )

        await self.consumer.start()
        await self.producer.start()
        log.info("[GENOME ENGINE] Initialized. Listening on topics: %s", TOPICS_INBOUND)

    async def run(self):
        await self.initialize()
        try:
            async for msg in self.consumer:
                await self.process_event(msg.topic, msg.value)
        finally:
            await self.shutdown()

    async def process_event(self, topic: str, event: Dict):
        mutations: List[MutationEvent] = []

        try:
            if topic == "telemetry.assets":
                mutations = await self.detector.detect_asset_mutations(event)
            elif topic == "telemetry.identities":
                mutations = await self.detector.detect_identity_mutations(event)
            elif topic == "telemetry.vulnerabilities":
                mutations = await self._handle_cve_event(event)
            elif topic == "telemetry.configurations":
                mutations = await self._handle_config_event(event)

            for mutation in mutations:
                log.info(
                    "[MUTATION] %s | node=%s | severity=%s | risk_delta=%+.3f",
                    mutation.mutation_type.value,
                    mutation.node_id,
                    mutation.severity,
                    mutation.risk_delta,
                )

                # Publish mutation event
                await self.producer.send(
                    TOPIC_MUTATIONS,
                    value=asdict(mutation),
                )

                # Propagate risk
                if mutation.risk_delta != 0.0:
                    await self.propagator.propagate_from_mutation(mutation)

                # Persist to Neo4j
                await self.propagator.persist_mutation_to_neo4j(mutation)

                # Publish risk update
                await self.producer.send(
                    TOPIC_RISK,
                    value={
                        "entity_id":  mutation.entity_id,
                        "node_id":    mutation.node_id,
                        "risk_delta": mutation.risk_delta,
                        "severity":   mutation.severity,
                        "timestamp":  datetime.utcnow().isoformat(),
                    }
                )

        except Exception as e:
            log.error("[ERROR] Processing event from %s: %s", topic, e, exc_info=True)

    async def _handle_cve_event(self, event: Dict) -> List[MutationEvent]:
        cve_id   = event.get("cve_id", "")
        cvss     = float(event.get("cvss_score", 0))
        risk_delta = min(cvss / 10.0 * 0.5, 0.5)
        severity = "critical" if cvss >= 9.0 else "high" if cvss >= 7.0 else "medium"
        return [MutationEvent(
            entity_id     = event.get("entity_id", ""),
            node_id       = event.get("asset_id", ""),
            node_type     = "asset",
            mutation_type = MutationType.CVE_INTRODUCED,
            current_state = event,
            risk_delta    = risk_delta,
            severity      = severity,
            source        = event.get("source", "scanner"),
            metadata      = {"cve_id": cve_id, "cvss": cvss},
        )]

    async def _handle_config_event(self, event: Dict) -> List[MutationEvent]:
        mut_type = (MutationType.SECRET_EXPOSED
                    if event.get("is_hardcoded_secret")
                    else MutationType.CONFIG_CHANGED)
        risk_delta = 0.4 if event.get("is_hardcoded_secret") else 0.05
        severity   = "critical" if event.get("is_hardcoded_secret") else "low"
        return [MutationEvent(
            entity_id     = event.get("entity_id", ""),
            node_id       = event.get("config_id", ""),
            node_type     = "configuration",
            mutation_type = mut_type,
            current_state = event,
            risk_delta    = risk_delta,
            severity      = severity,
            source        = event.get("source", "iac_scanner"),
        )]

    async def shutdown(self):
        await self.consumer.stop()
        await self.producer.stop()
        await self.neo4j.close()
        await self.redis_client.close()


# ──────────────────────────────────────────────
# ENTRYPOINT
# ──────────────────────────────────────────────

if __name__ == "__main__":
    engine = GenomeMutationEngine()
    asyncio.run(engine.run())
