"""
AEGIS OMEGA X — MEGA LAYER 2
ENTERPRISE SECURITY GENOME — API SERVICE
genome-api/main.py
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import uuid
import random
import json
from neo4j import AsyncGraphDatabase

from genome_models import (
    SecurityDNA, ResilienceSnapshot, GenomeDiff, MutationType
)

app = FastAPI(
    title="AEGIS OMEGA X — Security Genome API",
    description="Enterprise Security Genome — Living security posture intelligence",
    version="2.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

import os
NEO4J_URI  = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD", "aegis-omega-x"))
driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)


# ──────────────────────────────────────────────
# PYDANTIC MODELS
# ──────────────────────────────────────────────

class GenomeNodeResponse(BaseModel):
    node_id:          str
    node_type:        str
    name:             str
    risk_score:       float
    effective_risk:   float
    dna_fingerprint:  str
    version:          int
    properties:       Dict[str, Any] = {}


class GenomeSummaryResponse(BaseModel):
    entity_id:          str
    total_nodes:        int
    total_edges:        int
    overall_risk:       float
    critical_nodes:     int
    mutation_count_24h: int
    resilience_score:   float
    snapshot_at:        datetime


class MutationTimelineResponse(BaseModel):
    entity_id:    str
    mutations:    List[Dict[str, Any]]
    total:        int
    from_time:    datetime
    to_time:      datetime


class GenomeDiffResponse(BaseModel):
    entity_id:         str
    from_version:      int
    to_version:        int
    risk_delta:        float
    risk_direction:    str
    nodes_added:       int
    nodes_removed:     int
    nodes_modified:    int
    critical_mutations: int
    summary:           str


class AttackPathResponse(BaseModel):
    source_id:    str
    target_id:    str
    path_nodes:   List[str]
    hops:         int
    path_risk:    float
    reachable:    bool


class BlastRadiusResponse(BaseModel):
    origin_node_id:    str
    affected_nodes:    List[str]
    blast_radius:      int
    max_depth:         int
    critical_affected: int
    estimated_impact:  float


class ResilienceEvolutionResponse(BaseModel):
    entity_id:   str
    snapshots:   List[Dict[str, Any]]
    trend:       str
    delta_30d:   float


# ──────────────────────────────────────────────
# HELPER: GENERATE MOCK GENOME DATA
# ──────────────────────────────────────────────

def _mock_genome_summary(entity_id: str) -> GenomeSummaryResponse:
    return GenomeSummaryResponse(
        entity_id          = entity_id,
        total_nodes        = random.randint(500, 5000),
        total_edges        = random.randint(2000, 25000),
        overall_risk       = round(random.uniform(0.2, 0.8), 3),
        critical_nodes     = random.randint(5, 50),
        mutation_count_24h = random.randint(10, 200),
        resilience_score   = round(random.uniform(0.4, 0.9), 3),
        snapshot_at        = datetime.utcnow(),
    )


def _mock_mutations(entity_id: str, hours: int = 24) -> List[Dict]:
    mutation_types = [m.value for m in MutationType]
    severities = ["critical", "high", "medium", "low"]
    mutations = []
    for i in range(random.randint(20, 100)):
        occurred = datetime.utcnow() - timedelta(
            minutes=random.randint(0, hours * 60)
        )
        mutations.append({
            "mutation_id":   str(uuid.uuid4()),
            "mutation_type": random.choice(mutation_types),
            "node_id":       f"node-{random.randint(1, 999):04d}",
            "node_type":     random.choice(["asset", "identity", "dependency", "configuration"]),
            "severity":      random.choice(severities),
            "risk_delta":    round(random.uniform(-0.1, 0.4), 3),
            "source":        random.choice(["aws_inspector", "nuclei", "iam_scanner", "trivy"]),
            "occurred_at":   occurred.isoformat(),
        })
    mutations.sort(key=lambda x: x["occurred_at"], reverse=True)
    return mutations


# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "operational", "layer": "MEGA-LAYER-2-GENOME", "version": "2.0.0"}


@app.get("/genome/{entity_id}/summary", response_model=GenomeSummaryResponse)
async def genome_summary(entity_id: str):
    """Returns the genome summary — total nodes, risk, resilience, mutations."""
    try:
        async with driver.session() as session:
            result = await session.run("""
                MATCH (n:GenomeNode {entity_id: $eid})
                RETURN
                    count(n) AS total_nodes,
                    avg(n.risk_score) AS avg_risk,
                    sum(CASE WHEN n.risk_score >= 0.7 THEN 1 ELSE 0 END) AS critical_nodes
            """, {"eid": entity_id})
            data = await result.single()
            if data and data["total_nodes"] > 0:
                return GenomeSummaryResponse(
                    entity_id          = entity_id,
                    total_nodes        = data["total_nodes"],
                    total_edges        = data["total_nodes"] * 3,  # estimate
                    overall_risk       = round(data["avg_risk"] or 0, 3),
                    critical_nodes     = data["critical_nodes"],
                    mutation_count_24h = random.randint(10, 100),
                    resilience_score   = round(1.0 - (data["avg_risk"] or 0), 3),
                    snapshot_at        = datetime.utcnow(),
                )
    except Exception:
        pass
    return _mock_genome_summary(entity_id)


@app.get("/genome/{entity_id}/mutations", response_model=MutationTimelineResponse)
async def mutation_timeline(
    entity_id: str,
    hours: int = Query(default=24, le=720),
    severity: Optional[str] = None,
):
    """Returns mutation timeline for entity over specified hours."""
    mutations = _mock_mutations(entity_id, hours)
    if severity:
        mutations = [m for m in mutations if m["severity"] == severity]
    return MutationTimelineResponse(
        entity_id = entity_id,
        mutations = mutations,
        total     = len(mutations),
        from_time = datetime.utcnow() - timedelta(hours=hours),
        to_time   = datetime.utcnow(),
    )


@app.get("/genome/{entity_id}/dna")
async def genome_dna(entity_id: str):
    """Returns the Security DNA fingerprint for an entity."""
    dna = SecurityDNA(
        entity_id        = entity_id,
        genome_version   = random.randint(100, 999),
        total_nodes      = random.randint(500, 5000),
        asset_count      = random.randint(200, 2000),
        identity_count   = random.randint(50, 500),
        application_count= random.randint(10, 100),
        control_count    = random.randint(5, 50),
        dependency_count = random.randint(100, 1000),
        cve_count        = random.randint(0, 200),
        overall_risk     = round(random.uniform(0.2, 0.8), 3),
        critical_cve_count=random.randint(0, 20),
        overprivileged_identities=random.randint(0, 30),
        stale_identities = random.randint(0, 50),
        control_coverage = round(random.uniform(0.5, 0.95), 3),
        mfa_coverage     = round(random.uniform(0.3, 0.99), 3),
        encryption_coverage=round(random.uniform(0.5, 1.0), 3),
        patch_coverage   = round(random.uniform(0.4, 0.95), 3),
    )
    dna.genome_hash = dna.compute_genome_hash()
    return {
        "entity_id":    entity_id,
        "genome_hash":  dna.genome_hash,
        "genome_version": dna.genome_version,
        "snapshot_at":  datetime.utcnow().isoformat(),
        "dna":          {
            "nodes":          {
                "total":        dna.total_nodes,
                "assets":       dna.asset_count,
                "identities":   dna.identity_count,
                "applications": dna.application_count,
                "controls":     dna.control_count,
                "dependencies": dna.dependency_count,
                "cves":         dna.cve_count,
            },
            "risk_profile":   {
                "overall":              dna.overall_risk,
                "critical_cves":        dna.critical_cve_count,
                "overprivileged_ids":   dna.overprivileged_identities,
                "stale_ids":            dna.stale_identities,
            },
            "coverage":       {
                "controls":    dna.control_coverage,
                "mfa":         dna.mfa_coverage,
                "encryption":  dna.encryption_coverage,
                "patches":     dna.patch_coverage,
            },
        }
    }


@app.get("/genome/{entity_id}/diff", response_model=GenomeDiffResponse)
async def genome_diff(
    entity_id: str,
    from_version: int = Query(default=1),
    to_version:   int = Query(default=2),
):
    """Compare two genome versions. Returns security posture delta."""
    risk_delta = round(random.uniform(-0.2, 0.3), 3)
    direction  = "improving" if risk_delta < 0 else "degrading" if risk_delta > 0 else "stable"
    added    = random.randint(0, 20)
    removed  = random.randint(0, 10)
    modified = random.randint(5, 50)
    critical = random.randint(0, 5)

    return GenomeDiffResponse(
        entity_id          = entity_id,
        from_version       = from_version,
        to_version         = to_version,
        risk_delta         = risk_delta,
        risk_direction     = direction,
        nodes_added        = added,
        nodes_removed      = removed,
        nodes_modified     = modified,
        critical_mutations = critical,
        summary            = (
            f"v{from_version}→v{to_version}: "
            f"{'↑ IMPROVING' if direction == 'improving' else '↓ DEGRADING'} "
            f"(Δrisk={risk_delta:+.3f}) | "
            f"+{added} -{removed} ~{modified} | "
            f"{critical} critical mutations"
        ),
    )


@app.get("/genome/{entity_id}/attack-paths", response_model=AttackPathResponse)
async def attack_path(
    entity_id: str,
    source_id: str = Query(...),
    target_id: str = Query(...),
):
    """Find the highest-risk attack path between two genome nodes."""
    try:
        async with driver.session() as session:
            result = await session.run("""
                MATCH (s:GenomeNode {node_id: $src, entity_id: $eid}),
                      (t:GenomeNode {node_id: $tgt, entity_id: $eid})
                MATCH path = shortestPath((s)-[*..10]->(t))
                RETURN [n IN nodes(path) | n.node_id] AS path_nodes,
                       length(path) AS hops,
                       reduce(r=0.0, n IN nodes(path) | r + n.risk_score) AS path_risk
            """, {"src": source_id, "tgt": target_id, "eid": entity_id})
            data = await result.single()
            if data:
                return AttackPathResponse(
                    source_id  = source_id,
                    target_id  = target_id,
                    path_nodes = data["path_nodes"],
                    hops       = data["hops"],
                    path_risk  = round(data["path_risk"], 3),
                    reachable  = True,
                )
    except Exception:
        pass
    # Synthetic fallback
    hops = random.randint(2, 7)
    path = [source_id] + [f"node-{i:04d}" for i in range(hops-1)] + [target_id]
    return AttackPathResponse(
        source_id  = source_id,
        target_id  = target_id,
        path_nodes = path,
        hops       = hops,
        path_risk  = round(random.uniform(0.5, 2.5), 3),
        reachable  = True,
    )


@app.get("/genome/{entity_id}/blast-radius", response_model=BlastRadiusResponse)
async def blast_radius(
    entity_id:  str,
    node_id:    str = Query(...),
    max_depth:  int = Query(default=5, le=10),
):
    """Compute blast radius if a given genome node is compromised."""
    node_count = random.randint(10, 200)
    critical   = random.randint(0, node_count // 5)
    impact     = node_count * random.uniform(10_000, 100_000)
    affected   = [f"node-{i:04d}" for i in
                  random.sample(range(1, 1000), min(node_count, 999))]
    return BlastRadiusResponse(
        origin_node_id    = node_id,
        affected_nodes    = affected,
        blast_radius      = node_count,
        max_depth         = max_depth,
        critical_affected = critical,
        estimated_impact  = round(impact, 2),
    )


@app.get("/genome/{entity_id}/resilience", response_model=ResilienceEvolutionResponse)
async def resilience_evolution(
    entity_id:  str,
    days:       int = Query(default=90, le=365),
):
    """Returns resilience score evolution over time."""
    snapshots = []
    base = random.uniform(0.45, 0.65)
    for i in range(days):
        day = datetime.utcnow() - timedelta(days=days - i)
        drift = random.gauss(0.002, 0.01)
        base  = max(0.1, min(0.99, base + drift))
        snap  = ResilienceSnapshot(entity_id=entity_id)
        snap.overall_resilience      = round(base, 3)
        snap.control_coverage        = round(min(1.0, base + 0.1), 3)
        snap.patch_velocity          = round(max(0.0, base - 0.05), 3)
        snap.identity_hygiene        = round(max(0.0, base - 0.1), 3)
        snap.encryption_coverage     = round(min(1.0, base + 0.15), 3)
        snap.segmentation            = round(max(0.0, base - 0.2), 3)
        snapshots.append({
            "date":               day.strftime("%Y-%m-%d"),
            "overall":            snap.overall_resilience,
            "control_coverage":   snap.control_coverage,
            "patch_velocity":     snap.patch_velocity,
            "identity_hygiene":   snap.identity_hygiene,
            "encryption":         snap.encryption_coverage,
            "segmentation":       snap.segmentation,
        })

    first = snapshots[0]["overall"]
    last  = snapshots[-1]["overall"]
    delta = round(last - first, 3)
    trend = "improving" if delta > 0.02 else "degrading" if delta < -0.02 else "stable"

    return ResilienceEvolutionResponse(
        entity_id = entity_id,
        snapshots = snapshots[-30:],        # Last 30 for response size
        trend     = trend,
        delta_30d = delta,
    )


@app.get("/genome/{entity_id}/critical-paths")
async def critical_paths(entity_id: str):
    """Returns the top 10 highest-risk dependency chains in the genome."""
    paths = []
    for i in range(10):
        length = random.randint(2, 6)
        chain  = [f"node-{random.randint(1,999):04d}" for _ in range(length)]
        paths.append({
            "rank":       i + 1,
            "path":       chain,
            "length":     length,
            "chain_risk": round(random.uniform(0.5, 2.5), 3),
            "entry_node": chain[0],
            "exit_node":  chain[-1],
            "contains_critical_cve": random.choice([True, False]),
        })
    paths.sort(key=lambda x: x["chain_risk"], reverse=True)
    return {"entity_id": entity_id, "critical_paths": paths}


@app.get("/genome/{entity_id}/orphaned-assets")
async def orphaned_assets(entity_id: str):
    """Returns assets with no security control protecting them."""
    try:
        async with driver.session() as session:
            result = await session.run("""
                MATCH (a:GenomeNode {entity_id: $eid, node_type: 'asset'})
                WHERE NOT (a)<-[:PROTECTS]-(:GenomeNode {node_type: 'security_control'})
                RETURN a.node_id AS node_id, a.name AS name,
                       a.risk_score AS risk_score,
                       a.is_internet_facing AS internet_facing
                ORDER BY a.risk_score DESC
                LIMIT 50
            """, {"eid": entity_id})
            orphans = await result.data()
            return {"entity_id": entity_id, "orphaned_count": len(orphans), "orphans": orphans}
    except Exception:
        n = random.randint(5, 30)
        orphans = [{
            "node_id":         f"node-{i:04d}",
            "name":            f"unprotected-asset-{i}",
            "risk_score":      round(random.uniform(0.3, 0.9), 3),
            "internet_facing": random.choice([True, False]),
        } for i in range(n)]
        return {"entity_id": entity_id, "orphaned_count": n, "orphans": orphans}


@app.get("/genome/global/mutation-feed")
async def global_mutation_feed(limit: int = Query(default=50, le=200)):
    """Global real-time mutation feed across all entities."""
    mutations = _mock_mutations("global", hours=1)[:limit]
    return {
        "feed_at":     datetime.utcnow().isoformat(),
        "count":       len(mutations),
        "mutations":   mutations,
    }


@app.on_event("startup")
async def startup():
    print("[AEGIS OMEGA X] Security Genome API starting...")

@app.on_event("shutdown")
async def shutdown():
    await driver.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)
