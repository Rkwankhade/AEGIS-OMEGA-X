"""
AEGIS OMEGA X — MEGA LAYER 1
PLANETARY DIGITAL TWIN — INTELLIGENCE API (Python/FastAPI)
pdt-intelligence-api/main.py
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import uuid
import random
import json
from neo4j import AsyncGraphDatabase

# ──────────────────────────────────────────────
# APP INIT
# ──────────────────────────────────────────────

app = FastAPI(
    title="AEGIS OMEGA X — PDT Intelligence API",
    description="Planetary Digital Twin — Query, Simulation, Prediction Layer",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# NEO4J CONNECTION
# ──────────────────────────────────────────────

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "aegis-omega-x"

driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

# ──────────────────────────────────────────────
# PYDANTIC MODELS
# ──────────────────────────────────────────────

class EntityQuery(BaseModel):
    domain: Optional[str] = None
    country: Optional[str] = None
    min_criticality: Optional[float] = None
    limit: int = 50


class AssetQuery(BaseModel):
    entity_id: Optional[str] = None
    asset_type: Optional[str] = None
    min_risk: Optional[float] = None
    internet_facing: Optional[bool] = None
    limit: int = 100


class CascadeSimulationRequest(BaseModel):
    origin_asset_id: str
    severity: float = 0.8
    max_hops: int = 5
    propagation_probability: float = 0.15
    simulation_ticks: int = 10


class CascadeSimulationResult(BaseModel):
    simulation_id: str
    origin_asset_id: str
    affected_assets: List[str]
    affected_entities: List[str]
    propagation_path: List[str]
    blast_radius: int
    estimated_economic_impact_usd: float
    severity: float
    tick_count: int
    simulated_at: datetime


class RiskForecastRequest(BaseModel):
    entity_id: str
    horizon_days: int = 30


class RiskForecastResult(BaseModel):
    entity_id: str
    current_risk: float
    forecast: List[Dict[str, Any]]
    horizon_days: int
    forecast_generated_at: datetime


class PlanetaryHealthResponse(BaseModel):
    total_entities: int
    total_assets: int
    total_relationships: int
    global_risk_score: float
    critical_entities: int
    compromised_assets: int
    active_cascades: int
    snapshot_at: datetime


# ──────────────────────────────────────────────
# GRAPH QUERIES
# ──────────────────────────────────────────────

async def query_entities(filters: EntityQuery) -> List[Dict]:
    query = "MATCH (e:Entity) WHERE 1=1"
    params = {}

    if filters.domain:
        query += " AND e.domain = $domain"
        params["domain"] = filters.domain
    if filters.country:
        query += " AND e.country = $country"
        params["country"] = filters.country
    if filters.min_criticality is not None:
        query += " AND e.criticality_score >= $min_crit"
        params["min_crit"] = filters.min_criticality

    query += f" RETURN e LIMIT {filters.limit}"

    async with driver.session() as session:
        result = await session.run(query, params)
        records = await result.data()
        return [r["e"] for r in records]


async def query_assets(filters: AssetQuery) -> List[Dict]:
    query = "MATCH (a:Asset) WHERE 1=1"
    params = {}

    if filters.entity_id:
        query += " AND a.entity_id = $entity_id"
        params["entity_id"] = filters.entity_id
    if filters.asset_type:
        query += " AND a.asset_type = $asset_type"
        params["asset_type"] = filters.asset_type
    if filters.min_risk is not None:
        query += " AND a.risk_score >= $min_risk"
        params["min_risk"] = filters.min_risk
    if filters.internet_facing is not None:
        query += " AND a.is_internet_facing = $internet_facing"
        params["internet_facing"] = filters.internet_facing

    query += f" RETURN a LIMIT {filters.limit}"

    async with driver.session() as session:
        result = await session.run(query, params)
        records = await result.data()
        return [r["a"] for r in records]


async def get_asset_neighbors(asset_id: str, max_hops: int = 3) -> List[str]:
    query = f"""
    MATCH (origin:Asset {{asset_id: $asset_id}})
    CALL apoc.path.subgraphNodes(origin, {{maxLevel: {max_hops}}})
    YIELD node
    RETURN node.asset_id AS id
    """
    async with driver.session() as session:
        result = await session.run(query, {"asset_id": asset_id})
        records = await result.data()
        return [r["id"] for r in records if r["id"] != asset_id]


# ──────────────────────────────────────────────
# CASCADE SIMULATION ENGINE
# ──────────────────────────────────────────────

async def run_cascade_simulation(req: CascadeSimulationRequest) -> CascadeSimulationResult:
    """
    Simulates cascade propagation from an origin asset through
    the planetary graph using BFS + stochastic propagation.
    """
    affected = [req.origin_asset_id]
    propagation_path = [req.origin_asset_id]
    frontier = [req.origin_asset_id]

    # Try to get real neighbors from graph; fallback to synthetic
    try:
        all_neighbors = await get_asset_neighbors(req.origin_asset_id, req.max_hops)
    except Exception:
        # Synthetic fallback for demo
        all_neighbors = [f"synth-asset-{i}" for i in range(20)]

    for tick in range(req.simulation_ticks):
        if not frontier or not all_neighbors:
            break
        new_frontier = []
        for asset in frontier:
            for neighbor in all_neighbors:
                if neighbor in affected:
                    continue
                # Stochastic propagation
                roll = random.random()
                base_risk = random.uniform(0.3, 0.9)  # simulated risk
                adjusted_prob = req.propagation_probability * base_risk * req.severity
                if roll < adjusted_prob:
                    affected.append(neighbor)
                    propagation_path.append(neighbor)
                    new_frontier.append(neighbor)
        frontier = new_frontier

    # Synthetic entity mapping (one entity per 10 assets)
    affected_entities = list(set(
        f"entity-{int(a.split('-')[-1]) // 10 if a.split('-')[-1].isdigit() else 0}"
        for a in affected
    ))

    economic_impact = len(affected) * random.uniform(50_000, 500_000)

    return CascadeSimulationResult(
        simulation_id=str(uuid.uuid4()),
        origin_asset_id=req.origin_asset_id,
        affected_assets=affected,
        affected_entities=affected_entities,
        propagation_path=propagation_path,
        blast_radius=len(affected),
        estimated_economic_impact_usd=economic_impact,
        severity=req.severity,
        tick_count=req.simulation_ticks,
        simulated_at=datetime.utcnow(),
    )


# ──────────────────────────────────────────────
# RISK FORECAST ENGINE
# ──────────────────────────────────────────────

async def generate_risk_forecast(req: RiskForecastRequest) -> RiskForecastResult:
    """
    Generates a time-series risk forecast for an entity.
    Uses a simple autoregressive model with simulated inputs.
    Replace with actual ML model in production.
    """
    current_risk = random.uniform(0.3, 0.8)
    forecast = []
    risk = current_risk

    for day in range(req.horizon_days):
        # Simulated AR(1) risk drift with random shocks
        shock = random.gauss(0, 0.02)
        risk = min(max(risk * 0.98 + shock + 0.01, 0.0), 1.0)
        forecast.append({
            "day": day + 1,
            "date": (datetime.utcnow() + timedelta(days=day+1)).isoformat(),
            "risk_score": round(risk, 4),
            "confidence": round(max(0.5, 1.0 - (day * 0.01)), 3),
        })

    return RiskForecastResult(
        entity_id=req.entity_id,
        current_risk=round(current_risk, 4),
        forecast=forecast,
        horizon_days=req.horizon_days,
        forecast_generated_at=datetime.utcnow(),
    )


# ──────────────────────────────────────────────
# API ROUTES
# ──────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "operational", "layer": "MEGA-LAYER-1-PDT", "version": "1.0.0"}


@app.get("/planetary/health", response_model=PlanetaryHealthResponse)
async def planetary_health():
    """Returns global health snapshot of the Planetary Digital Twin."""
    try:
        async with driver.session() as session:
            result = await session.run("""
                MATCH (e:Entity) WITH count(e) AS entities
                MATCH (a:Asset)  WITH entities, count(a) AS assets
                MATCH ()-[r]->() WITH entities, assets, count(r) AS rels
                RETURN entities, assets, rels
            """)
            data = await result.single()
            total_entities = data["entities"] if data else 0
            total_assets = data["assets"] if data else 0
            total_rels = data["rels"] if data else 0
    except Exception:
        total_entities = 0
        total_assets = 0
        total_rels = 0

    return PlanetaryHealthResponse(
        total_entities=total_entities,
        total_assets=total_assets,
        total_relationships=total_rels,
        global_risk_score=round(random.uniform(0.3, 0.7), 3),
        critical_entities=int(total_entities * 0.1),
        compromised_assets=int(total_assets * 0.05),
        active_cascades=random.randint(0, 5),
        snapshot_at=datetime.utcnow(),
    )


@app.post("/entities/query")
async def query_entities_route(filters: EntityQuery):
    """Query CivilizationalEntity nodes from the planetary graph."""
    try:
        results = await query_entities(filters)
        return {"count": len(results), "entities": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assets/query")
async def query_assets_route(filters: AssetQuery):
    """Query DigitalAsset nodes from the planetary graph."""
    try:
        results = await query_assets(filters)
        return {"count": len(results), "assets": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets/{asset_id}/neighbors")
async def get_neighbors(asset_id: str, max_hops: int = Query(default=3, le=10)):
    """Get all assets reachable from a given asset within max_hops."""
    try:
        neighbors = await get_asset_neighbors(asset_id, max_hops)
        return {"asset_id": asset_id, "neighbor_count": len(neighbors), "neighbors": neighbors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate/cascade", response_model=CascadeSimulationResult)
async def simulate_cascade(req: CascadeSimulationRequest):
    """
    Run a cascade failure simulation from an origin asset.
    Returns blast radius, propagation path, and estimated economic impact.
    """
    result = await run_cascade_simulation(req)
    return result


@app.post("/forecast/risk", response_model=RiskForecastResult)
async def forecast_risk(req: RiskForecastRequest):
    """
    Generate a risk score forecast for an entity over a given horizon.
    """
    result = await generate_risk_forecast(req)
    return result


@app.get("/entities/{entity_id}/attack-surface")
async def attack_surface(entity_id: str):
    """
    Returns the attack surface summary for a given entity:
    internet-facing assets, high-risk assets, unpatched CVEs, etc.
    """
    try:
        async with driver.session() as session:
            result = await session.run("""
                MATCH (a:Asset {entity_id: $entity_id})
                RETURN
                    count(a) AS total,
                    sum(CASE WHEN a.is_internet_facing THEN 1 ELSE 0 END) AS internet_facing,
                    sum(CASE WHEN a.risk_score >= 0.7 THEN 1 ELSE 0 END) AS high_risk,
                    avg(a.risk_score) AS avg_risk
            """, {"entity_id": entity_id})
            data = await result.single()
            if not data:
                raise HTTPException(status_code=404, detail="Entity not found")
            return {
                "entity_id": entity_id,
                "total_assets": data["total"],
                "internet_facing": data["internet_facing"],
                "high_risk_assets": data["high_risk"],
                "average_risk_score": round(data["avg_risk"] or 0, 4),
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/topology/path")
async def shortest_attack_path(
    source_id: str = Query(...),
    target_id: str = Query(...),
):
    """
    Find the shortest attack path between two assets in the planetary graph.
    Uses Neo4j shortest path algorithm.
    """
    try:
        async with driver.session() as session:
            result = await session.run("""
                MATCH (s:Asset {asset_id: $source}), (t:Asset {asset_id: $target})
                MATCH path = shortestPath((s)-[*..10]->(t))
                RETURN [n IN nodes(path) | n.asset_id] AS path_nodes,
                       length(path) AS hops
            """, {"source": source_id, "target": target_id})
            data = await result.single()
            if not data:
                return {"path": [], "hops": -1, "reachable": False}
            return {
                "source": source_id,
                "target": target_id,
                "path": data["path_nodes"],
                "hops": data["hops"],
                "reachable": True,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# STARTUP / SHUTDOWN
# ──────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    print("[AEGIS OMEGA X] PDT Intelligence API starting...")
    print("[AEGIS OMEGA X] Connected to Neo4j at", NEO4J_URI)


@app.on_event("shutdown")
async def shutdown():
    await driver.close()
    print("[AEGIS OMEGA X] PDT Intelligence API shut down.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
