"""
AEGIS OMEGA X — MEGA LAYER 3
GLOBAL SECURITY KNOWLEDGE UNIVERSE
EMBEDDING SERVICE + SEMANTIC SEARCH + INFERENCE ENGINE
"""

import asyncio
import json
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from neo4j import AsyncGraphDatabase
import redis.asyncio as aioredis

from knowledge_models import (
    KnowledgeNode, KnowledgeEdge, SemanticSearchResult,
    InferenceRule, KnowledgeMap, ConfidenceLevel
)

log = logging.getLogger("ku-semantic-engine")
logging.basicConfig(level=logging.INFO)

NEO4J_URI    = "bolt://neo4j:7687"
NEO4J_AUTH   = ("neo4j", "aegis-omega-x")
REDIS_URL    = "redis://redis:6379"
KAFKA_BROKERS= "kafka-0.kafka:9092"

EMBEDDING_DIM = 1536     # OpenAI ada-002 / custom security model dims


# ──────────────────────────────────────────────
# SECURITY KNOWLEDGE EMBEDDING MODEL
# ──────────────────────────────────────────────

class SecurityKnowledgeEmbedder:
    """
    Generates semantic embeddings for knowledge nodes.
    Uses a fine-tuned security language model.
    In production: replace with actual model inference
    (sentence-transformers, OpenAI, or custom security-LM).
    """

    def __init__(self):
        self.model_name = "aegis-security-embed-v1"
        self.dim        = EMBEDDING_DIM
        self._vocab: Dict[str, np.ndarray] = {}

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for arbitrary text.
        Production: call embedding model API.
        """
        # Deterministic pseudo-embedding based on text hash
        # Replace with: openai.Embedding.create / sentence_transformers
        h = hash(text) % (2**32)
        rng = np.random.RandomState(h % (2**31))
        vec = rng.randn(self.dim).astype(np.float32)
        vec /= (np.linalg.norm(vec) + 1e-8)
        return vec.tolist()

    async def embed_node(self, node: KnowledgeNode) -> List[float]:
        """
        Generate embedding for a knowledge node.
        Combines name, description, and type semantics.
        """
        # Build rich text representation
        text_parts = [
            f"Type: {node.node_type}",
            f"Name: {node.name}",
        ]
        if node.description:
            text_parts.append(f"Description: {node.description[:500]}")
        if node.tags:
            text_parts.append(f"Tags: {', '.join(node.tags[:10])}")
        if hasattr(node, 'technique_id'):
            text_parts.append(f"MITRE: {node.technique_id}")
        if hasattr(node, 'cve_id'):
            text_parts.append(f"CVE: {node.cve_id}")

        text = " | ".join(text_parts)
        return await self.embed_text(text)

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        va = np.array(a, dtype=np.float32)
        vb = np.array(b, dtype=np.float32)
        dot = np.dot(va, vb)
        norm = np.linalg.norm(va) * np.linalg.norm(vb)
        if norm < 1e-8:
            return 0.0
        return float(dot / norm)


# ──────────────────────────────────────────────
# EMBEDDING WORKER (Kafka consumer)
# ──────────────────────────────────────────────

class EmbeddingWorker:
    """
    Consumes nodes from knowledge.embed_queue Kafka topic,
    generates embeddings, and writes them to Neo4j.
    """

    def __init__(self):
        self.embedder = SecurityKnowledgeEmbedder()
        self.driver   = AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        self.consumer = None
        self.processed = 0

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            "knowledge.embed_queue",
            bootstrap_servers=KAFKA_BROKERS,
            group_id="embedding-worker",
            auto_offset_reset="earliest",
            value_deserializer=lambda v: json.loads(v.decode()),
        )
        await self.consumer.start()

        try:
            async for msg in self.consumer:
                await self.process(msg.value)
        finally:
            await self.consumer.stop()
            await self.driver.close()

    async def process(self, node_data: Dict):
        node_id   = node_data.get("node_id", "")
        name      = node_data.get("name", "")
        node_type = node_data.get("node_type", "")
        desc      = node_data.get("description", "")
        tags      = node_data.get("tags", [])

        text = f"Type: {node_type} | Name: {name} | {desc[:500]} | Tags: {' '.join(tags)}"
        embedding = await self.embedder.embed_text(text)

        async with self.driver.session() as session:
            await session.run("""
                MATCH (n:KnowledgeNode {node_id: $node_id})
                SET n.embedding = $embedding,
                    n.embedded_at = datetime()
            """, {"node_id": node_id, "embedding": embedding})

        self.processed += 1
        if self.processed % 500 == 0:
            log.info("[EMBEDDING] Processed %d nodes", self.processed)


# ──────────────────────────────────────────────
# SEMANTIC SEARCH ENGINE
# ──────────────────────────────────────────────

class SemanticSearchEngine:
    """
    Hybrid search over the knowledge graph.
    Combines:
      1. Vector similarity (embedding-based)
      2. Keyword/fulltext match (Neo4j fulltext index)
      3. Graph centrality (PageRank-based importance)
    """

    def __init__(self, driver, embedder: SecurityKnowledgeEmbedder, redis_client):
        self.driver   = driver
        self.embedder = embedder
        self.redis    = redis_client

    async def search(
        self,
        query: str,
        node_types: Optional[List[str]] = None,
        top_k: int = 20,
        vector_weight: float = 0.6,
        keyword_weight: float = 0.3,
        graph_weight: float   = 0.1,
    ) -> List[SemanticSearchResult]:
        """
        Execute hybrid search.
        """
        cache_key = f"ku:search:{hash(query)}:{top_k}"
        cached    = await self.redis.get(cache_key)
        if cached:
            return [SemanticSearchResult(**r) for r in json.loads(cached)]

        # Generate query embedding
        query_embedding = await self.embedder.embed_text(query)

        # 1. Vector search via Neo4j vector index
        vector_results = await self._vector_search(query_embedding, node_types, top_k * 2)

        # 2. Keyword search via Neo4j fulltext
        keyword_results = await self._keyword_search(query, node_types, top_k * 2)

        # 3. Merge and re-rank
        merged = self._merge_results(
            vector_results, keyword_results,
            vector_weight, keyword_weight
        )

        # 4. Fetch graph centrality scores
        merged = await self._enrich_with_centrality(merged, graph_weight)

        # Sort by combined score
        merged.sort(key=lambda r: r.combined_score, reverse=True)
        top_results = merged[:top_k]

        # Cache for 5 minutes
        await self.redis.setex(
            cache_key, 300,
            json.dumps([asdict(r) for r in top_results])
        )
        return top_results

    async def _vector_search(
        self, embedding: List[float],
        node_types: Optional[List[str]], k: int
    ) -> List[Dict]:
        try:
            type_filter = ""
            if node_types:
                type_filter = "WHERE n.node_type IN $types"

            async with self.driver.session() as session:
                result = await session.run(f"""
                    CALL db.index.vector.queryNodes('ku_embedding', $k, $embedding)
                    YIELD node AS n, score
                    {type_filter}
                    RETURN n.node_id AS node_id,
                           n.node_type AS node_type,
                           n.name AS name,
                           n.description AS description,
                           score AS similarity
                    ORDER BY similarity DESC
                    LIMIT $k
                """, {
                    "k":         k,
                    "embedding": embedding,
                    "types":     node_types or [],
                })
                return await result.data()
        except Exception as e:
            log.debug("[VECTOR SEARCH] Error: %s", e)
            return []

    async def _keyword_search(
        self, query: str,
        node_types: Optional[List[str]], k: int
    ) -> List[Dict]:
        try:
            async with self.driver.session() as session:
                result = await session.run("""
                    CALL db.index.fulltext.queryNodes('ku_fulltext', $query)
                    YIELD node AS n, score
                    WHERE ($types IS NULL OR n.node_type IN $types)
                    RETURN n.node_id AS node_id,
                           n.node_type AS node_type,
                           n.name AS name,
                           n.description AS description,
                           score AS keyword_score
                    LIMIT $k
                """, {
                    "query": query,
                    "types": node_types,
                    "k":     k,
                })
                return await result.data()
        except Exception as e:
            log.debug("[KEYWORD SEARCH] Error: %s", e)
            return []

    def _merge_results(
        self, vector: List[Dict], keyword: List[Dict],
        vw: float, kw: float
    ) -> List[SemanticSearchResult]:
        scores: Dict[str, Dict] = {}

        for r in vector:
            nid = r["node_id"]
            scores[nid] = {
                "node_id":     nid,
                "node_type":   r.get("node_type", ""),
                "name":        r.get("name", ""),
                "description": r.get("description", ""),
                "vector_score":  float(r.get("similarity", 0)),
                "keyword_score": 0.0,
                "graph_score":   0.0,
            }

        for r in keyword:
            nid = r["node_id"]
            if nid in scores:
                scores[nid]["keyword_score"] = float(r.get("keyword_score", 0))
            else:
                scores[nid] = {
                    "node_id":      nid,
                    "node_type":    r.get("node_type", ""),
                    "name":         r.get("name", ""),
                    "description":  r.get("description", ""),
                    "vector_score": 0.0,
                    "keyword_score": float(r.get("keyword_score", 0)),
                    "graph_score":  0.0,
                }

        results = []
        for s in scores.values():
            combined = (
                vw * s["vector_score"] +
                kw * s["keyword_score"]
            )
            results.append(SemanticSearchResult(
                node_id       = s["node_id"],
                node_type     = s["node_type"],
                name          = s["name"],
                description   = s["description"][:200],
                similarity    = round(s["vector_score"], 4),
                graph_score   = 0.0,
                combined_score= round(combined, 4),
            ))
        return results

    async def _enrich_with_centrality(
        self, results: List[SemanticSearchResult], graph_weight: float
    ) -> List[SemanticSearchResult]:
        if not results:
            return results
        node_ids = [r.node_id for r in results]
        try:
            async with self.driver.session() as session:
                res = await session.run("""
                    UNWIND $ids AS nid
                    MATCH (n:KnowledgeNode {node_id: nid})
                    OPTIONAL MATCH (n)-[r]-()
                    RETURN nid, count(r) AS degree
                """, {"ids": node_ids})
                degrees = {row["nid"]: row["degree"] for row in await res.data()}
                max_deg = max(degrees.values(), default=1)

                for result in results:
                    deg   = degrees.get(result.node_id, 0)
                    norm  = deg / max(max_deg, 1)
                    result.graph_score   = round(norm, 4)
                    result.combined_score = round(
                        result.combined_score + graph_weight * norm, 4
                    )
        except Exception as e:
            log.debug("[CENTRALITY] Error: %s", e)
        return results


# ──────────────────────────────────────────────
# INFERENCE ENGINE
# ──────────────────────────────────────────────

class KnowledgeInferenceEngine:
    """
    Forward-chaining inference engine over the knowledge graph.
    Derives new relationships not explicitly stated in the data.

    Example inferences:
    - If ThreatActor USES Technique AND Technique EXPLOITS CVE
      → ThreatActor LIKELY_TARGETS Systems with CVE
    - If Campaign USES Malware AND Malware IMPLEMENTS SubTechnique
      → Campaign USES SubTechnique (inferred)
    - If Detection Rule DETECTS Technique AND ThreatActor USES Technique
      → Detection Rule RELEVANT_TO ThreatActor
    """

    BUILT_IN_RULES: List[Dict] = [
        {
            "rule_id":    "IR-001",
            "name":       "Actor → CVE via Technique",
            "description":"If Actor uses Technique AND Technique exploits CVE → Actor targets CVE",
            "cypher": """
                MATCH (actor:ThreatActor)-[:USES]->(technique:Technique)-[:EXPLOITS]->(cve:CVE)
                WHERE NOT (actor)-[:LIKELY_EXPLOITS]->(cve)
                CREATE (actor)-[:LIKELY_EXPLOITS {
                    inferred: true,
                    confidence: 0.75,
                    rule: 'IR-001',
                    inferred_at: datetime()
                }]->(cve)
                RETURN count(*) AS inferences_created
            """,
        },
        {
            "rule_id":    "IR-002",
            "name":       "Campaign Technique via Malware",
            "description":"If Campaign uses Malware AND Malware implements Technique → Campaign uses Technique",
            "cypher": """
                MATCH (campaign:Campaign)-[:USES]->(malware:Malware)
                      -[:IMPLEMENTS]->(technique:Technique)
                WHERE NOT (campaign)-[:USES]->(technique)
                CREATE (campaign)-[:USES {
                    inferred: true,
                    confidence: 0.85,
                    rule: 'IR-002',
                    inferred_at: datetime()
                }]->(technique)
                RETURN count(*) AS inferences_created
            """,
        },
        {
            "rule_id":    "IR-003",
            "name":       "Detection Rule relevance to Actor",
            "description":"If Rule detects Technique AND Actor uses Technique → Rule is relevant to Actor",
            "cypher": """
                MATCH (rule:DetectionRule)-[:DETECTS]->(technique:Technique)
                      <-[:USES]-(actor:ThreatActor)
                WHERE NOT (rule)-[:RELEVANT_TO]->(actor)
                CREATE (rule)-[:RELEVANT_TO {
                    inferred: true,
                    confidence: 0.80,
                    rule: 'IR-003',
                    inferred_at: datetime()
                }]->(actor)
                RETURN count(*) AS inferences_created
            """,
        },
        {
            "rule_id":    "IR-004",
            "name":       "High-EPSS CVE Prioritization",
            "description":"CVEs with EPSS > 0.5 are flagged as high_exploitation_risk",
            "cypher": """
                MATCH (c:CVE)
                WHERE c.epss_score > 0.5
                AND NOT 'high_exploitation_risk' IN c.tags
                SET c.tags = coalesce(c.tags, []) + ['high_exploitation_risk'],
                    c.prioritized = true
                RETURN count(*) AS flagged
            """,
        },
        {
            "rule_id":    "IR-005",
            "name":       "CVE → Malware family via Exploit",
            "description":"If Malware exploits CVE via known exploit → CVE linked to Malware",
            "cypher": """
                MATCH (malware:Malware)-[:USES]->(exploit:Exploit)-[:TARGETS]->(cve:CVE)
                WHERE NOT (malware)-[:EXPLOITS]->(cve)
                CREATE (malware)-[:EXPLOITS {
                    inferred: true,
                    confidence: 0.90,
                    rule: 'IR-005',
                    inferred_at: datetime()
                }]->(cve)
                RETURN count(*) AS inferences_created
            """,
        },
    ]

    def __init__(self, driver):
        self.driver = driver
        self.run_count = 0

    async def run_all_rules(self) -> Dict[str, int]:
        """Execute all inference rules. Returns dict of rule_id → inferences_created."""
        results = {}
        for rule in self.BUILT_IN_RULES:
            count = await self._execute_rule(rule)
            results[rule["rule_id"]] = count
            log.info("[INFERENCE] %s: %d inferences created", rule["rule_id"], count)
        self.run_count += 1
        return results

    async def _execute_rule(self, rule: Dict) -> int:
        try:
            async with self.driver.session() as session:
                result = await session.run(rule["cypher"])
                data   = await result.single()
                if data:
                    keys = list(data.keys())
                    return int(data[keys[0]] or 0)
        except Exception as e:
            log.error("[INFERENCE] Rule %s error: %s", rule["rule_id"], e)
        return 0

    async def schedule_periodic(self, interval_hours: int = 6):
        """Run inference engine every N hours."""
        while True:
            log.info("[INFERENCE] Starting inference run #%d", self.run_count + 1)
            results = await self.run_all_rules()
            total   = sum(results.values())
            log.info("[INFERENCE] Run complete: %d total inferences", total)
            await asyncio.sleep(interval_hours * 3600)


# ──────────────────────────────────────────────
# KNOWLEDGE MAP GENERATOR
# ──────────────────────────────────────────────

class KnowledgeMapGenerator:
    """
    Generates focused knowledge maps — curated subgraphs
    around a specific threat actor, campaign, technique, or domain.
    """

    def __init__(self, driver):
        self.driver = driver

    async def generate_actor_map(
        self, actor_id: str, depth: int = 3
    ) -> KnowledgeMap:
        """Generate a knowledge map centered on a threat actor."""
        async with self.driver.session() as session:
            result = await session.run(f"""
                MATCH (actor:ThreatActor {{node_id: $actor_id}})
                CALL apoc.path.subgraphAll(actor, {{
                    maxLevel: {depth},
                    relationshipFilter: 'USES>|ATTRIBUTED_TO>|TARGETS>|IMPLEMENTS>'
                }})
                YIELD nodes, relationships
                RETURN
                    [n IN nodes  | n.node_id] AS node_ids,
                    [r IN relationships | {{
                        src: startNode(r).node_id,
                        tgt: endNode(r).node_id,
                        type: type(r)
                    }}] AS edges
            """, {"actor_id": actor_id})
            data = await result.single()

            node_ids = data["node_ids"] if data else []
            edges    = data["edges"]    if data else []

            return KnowledgeMap(
                title       = f"Threat Actor Map: {actor_id}",
                description = f"Knowledge map centered on {actor_id} at depth {depth}",
                focus_type  = "threat_actor",
                focus_id    = actor_id,
                nodes       = node_ids,
                edges       = [f"{e['src']}-{e['type']}-{e['tgt']}" for e in edges],
                depth       = depth,
                node_count  = len(node_ids),
                edge_count  = len(edges),
            )

    async def generate_technique_map(
        self, technique_id: str, depth: int = 2
    ) -> KnowledgeMap:
        """Generate a knowledge map for a MITRE ATT&CK technique."""
        async with self.driver.session() as session:
            result = await session.run(f"""
                MATCH (tech:Technique {{technique_id: $tech_id}})
                CALL apoc.path.subgraphAll(tech, {{
                    maxLevel: {depth}
                }})
                YIELD nodes, relationships
                RETURN
                    [n IN nodes | n.node_id] AS node_ids,
                    size(relationships) AS edge_count
            """, {"tech_id": technique_id})
            data = await result.single()
            node_ids   = data["node_ids"]   if data else []
            edge_count = data["edge_count"] if data else 0

            return KnowledgeMap(
                title       = f"Technique Map: {technique_id}",
                focus_type  = "technique",
                focus_id    = technique_id,
                nodes       = node_ids,
                depth       = depth,
                node_count  = len(node_ids),
                edge_count  = edge_count,
            )

    async def generate_cve_context_map(self, cve_id: str) -> KnowledgeMap:
        """Full context map for a CVE: exploits, actors, mitigations, detections."""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (cve:CVE {cve_id: $cve_id})
                OPTIONAL MATCH (actor)-[:LIKELY_EXPLOITS|EXPLOITS]->(cve)
                OPTIONAL MATCH (technique)-[:EXPLOITS]->(cve)
                OPTIONAL MATCH (malware)-[:EXPLOITS]->(cve)
                OPTIONAL MATCH (ctrl:SecurityControl)-[:MITIGATES]->(cve)
                OPTIONAL MATCH (rule:DetectionRule)-[:DETECTS]->(cve)
                OPTIONAL MATCH (patch:Patch)-[:PATCHES]->(cve)
                WITH cve, collect(DISTINCT actor) AS actors,
                     collect(DISTINCT technique) AS techniques,
                     collect(DISTINCT malware) AS malwares,
                     collect(DISTINCT ctrl) AS controls,
                     collect(DISTINCT rule) AS rules,
                     collect(DISTINCT patch) AS patches
                RETURN
                    [n IN actors    | n.node_id] AS actor_ids,
                    [n IN techniques| n.node_id] AS technique_ids,
                    [n IN malwares  | n.node_id] AS malware_ids,
                    [n IN controls  | n.node_id] AS control_ids,
                    [n IN rules     | n.node_id] AS rule_ids,
                    [n IN patches   | n.node_id] AS patch_ids
            """, {"cve_id": cve_id})
            data = await result.single()
            if not data:
                return KnowledgeMap(focus_type="cve", focus_id=cve_id)

            all_nodes = (
                [f"cve-{cve_id.lower()}"] +
                data["actor_ids"] + data["technique_ids"] +
                data["malware_ids"] + data["control_ids"] +
                data["rule_ids"] + data["patch_ids"]
            )
            return KnowledgeMap(
                title       = f"CVE Context Map: {cve_id}",
                focus_type  = "cve",
                focus_id    = cve_id,
                nodes       = [n for n in all_nodes if n],
                node_count  = len(all_nodes),
                metadata    = {
                    "actors":     len(data["actor_ids"]),
                    "techniques": len(data["technique_ids"]),
                    "malwares":   len(data["malware_ids"]),
                    "controls":   len(data["control_ids"]),
                    "rules":      len(data["rule_ids"]),
                    "patches":    len(data["patch_ids"]),
                }
            )
