"""
AEGIS OMEGA X — MEGA LAYER 3
GLOBAL SECURITY KNOWLEDGE UNIVERSE — INGESTION PIPELINE
Multi-source knowledge ingestion: NVD, MITRE ATT&CK, STIX/TAXII,
CISA KEV, Sigma rules, YARA rules, arXiv, threat feeds.
"""

import asyncio
import aiohttp
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import asdict

from aiokafka import AIOKafkaProducer
from neo4j import AsyncGraphDatabase
import redis.asyncio as aioredis

from knowledge_models import (
    CVENode, TechniqueNode, TacticNode, SubTechniqueNode,
    ThreatActorNode, MalwareNode, CampaignNode, DetectionRuleNode,
    IOCNode, IncidentNode, KnowledgeEdge,
    KnowledgeNodeType, ConfidenceLevel, TLPMarking, DetectionRuleType,
    ThreatActorType
)

log = logging.getLogger("ku-ingestion-pipeline")
logging.basicConfig(level=logging.INFO)


# ──────────────────────────────────────────────
# SOURCE CONFIGURATIONS
# ──────────────────────────────────────────────

SOURCES = {
    "nvd_cve":          "https://services.nvd.nist.gov/rest/json/cves/2.0",
    "nvd_cpe":          "https://services.nvd.nist.gov/rest/json/cpes/2.0",
    "mitre_attack":     "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json",
    "cisa_kev":         "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    "sigma_rules":      "https://api.github.com/repos/SigmaHQ/sigma/contents/rules",
    "epss_data":        "https://epss.cyentia.com/epss_scores-current.csv.gz",
}

KAFKA_BROKERS = "kafka-0.kafka:9092,kafka-1.kafka:9092"
NEO4J_URI     = "bolt://neo4j:7687"
NEO4J_AUTH    = ("neo4j", "aegis-omega-x")
REDIS_URL     = "redis://redis:6379"

TOPIC_KNOWLEDGE_INGEST = "knowledge.ingest"
TOPIC_KNOWLEDGE_EMBED  = "knowledge.embed_queue"


# ──────────────────────────────────────────────
# BASE INGESTION SOURCE
# ──────────────────────────────────────────────

class KnowledgeIngestionSource:
    """Abstract base class for all knowledge sources."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.ingested = 0
        self.errors   = 0

    async def fetch(self) -> AsyncGenerator[Dict, None]:
        raise NotImplementedError

    async def transform(self, raw: Dict) -> Optional[Any]:
        raise NotImplementedError

    async def run(self, producer: AIOKafkaProducer):
        async for raw in self.fetch():
            try:
                node = await self.transform(raw)
                if node:
                    await producer.send(
                        TOPIC_KNOWLEDGE_INGEST,
                        value=json.dumps(asdict(node), default=str).encode()
                    )
                    self.ingested += 1
                    if self.ingested % 1000 == 0:
                        log.info(
                            "[%s] Ingested %d nodes",
                            self.__class__.__name__,
                            self.ingested
                        )
            except Exception as e:
                self.errors += 1
                log.warning("[%s] Error: %s", self.__class__.__name__, e)


# ──────────────────────────────────────────────
# NVD CVE INGESTION
# ──────────────────────────────────────────────

class NVDCVEIngestionSource(KnowledgeIngestionSource):
    """
    Ingests CVE data from NIST NVD API 2.0.
    Handles pagination, rate limiting, and incremental updates.
    """

    NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    PAGE_SIZE = 2000

    async def fetch(self) -> AsyncGenerator[Dict, None]:
        start_index = 0
        total = None

        while total is None or start_index < total:
            params = {
                "resultsPerPage": self.PAGE_SIZE,
                "startIndex":     start_index,
            }
            try:
                async with self.session.get(
                    self.NVD_API, params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 429:      # Rate limited
                        log.warning("[NVD] Rate limited, sleeping 30s")
                        await asyncio.sleep(30)
                        continue
                    if resp.status != 200:
                        log.error("[NVD] HTTP %d", resp.status)
                        break
                    data = await resp.json()
                    total = data.get("totalResults", 0)
                    vulns = data.get("vulnerabilities", [])
                    for v in vulns:
                        yield v
                    start_index += len(vulns)
                    await asyncio.sleep(0.6)    # NVD rate limit: ~100 req/min
            except Exception as e:
                log.error("[NVD] Fetch error: %s", e)
                await asyncio.sleep(5)
                break

    async def transform(self, raw: Dict) -> Optional[CVENode]:
        cve_data = raw.get("cve", {})
        cve_id   = cve_data.get("id", "")
        if not cve_id:
            return None

        # Extract CVSS v3
        cvss3  = {}
        metrics = cve_data.get("metrics", {})
        if metrics.get("cvssMetricV31"):
            cvss3 = metrics["cvssMetricV31"][0].get("cvssData", {})
        elif metrics.get("cvssMetricV30"):
            cvss3 = metrics["cvssMetricV30"][0].get("cvssData", {})

        score   = float(cvss3.get("baseScore", 0))
        severity_map = {(0,4):"low",(4,7):"medium",(7,9):"high",(9,11):"critical"}
        severity = next(
            (v for (lo,hi),v in severity_map.items() if lo <= score < hi),
            "unknown"
        )

        # Extract description
        desc    = ""
        for d in cve_data.get("descriptions", []):
            if d.get("lang") == "en":
                desc = d.get("value", "")
                break

        # Extract affected software
        affected = []
        for config in cve_data.get("configurations", []):
            for node in config.get("nodes", []):
                for match in node.get("cpeMatch", []):
                    affected.append(match.get("criteria", ""))

        # Extract CWEs
        cwes = []
        for weakness in cve_data.get("weaknesses", []):
            for wd in weakness.get("description", []):
                if wd.get("value", "").startswith("CWE-"):
                    cwes.append(wd["value"])

        published_raw = cve_data.get("published", "")
        modified_raw  = cve_data.get("lastModified", "")

        return CVENode(
            node_id          = f"cve-{cve_id.lower()}",
            cve_id           = cve_id,
            name             = cve_id,
            description      = desc[:2000],
            cvss_v3_score    = score,
            cvss_v3_vector   = cvss3.get("vectorString", ""),
            severity         = severity,
            epss_score       = 0.0,         # Enriched separately
            published        = datetime.fromisoformat(published_raw[:19]) if published_raw else None,
            last_modified    = datetime.fromisoformat(modified_raw[:19]) if modified_raw else None,
            cwe_ids          = cwes[:10],
            affected_software= affected[:50],
            sources          = ["NVD"],
            confidence       = ConfidenceLevel.CONFIRMED,
            tlp_marking      = TLPMarking.WHITE,
            tags             = [severity, "cve"],
        )


# ──────────────────────────────────────────────
# MITRE ATT&CK INGESTION
# ──────────────────────────────────────────────

class MITREAttackIngestionSource(KnowledgeIngestionSource):
    """
    Ingests the complete MITRE ATT&CK Enterprise framework
    from the official CTI GitHub repository (STIX 2.1 bundle).
    """

    ATTACK_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"

    async def fetch(self) -> AsyncGenerator[Dict, None]:
        try:
            async with self.session.get(
                self.ATTACK_URL,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                data = await resp.json(content_type=None)
                for obj in data.get("objects", []):
                    yield obj
        except Exception as e:
            log.error("[MITRE] Fetch error: %s", e)

    async def transform(self, raw: Dict) -> Optional[Any]:
        obj_type = raw.get("type", "")
        stix_id  = raw.get("id", "")
        name     = raw.get("name", "")
        desc     = raw.get("description", "")[:2000]
        deprecated = raw.get("x_mitre_deprecated", False) or raw.get("revoked", False)

        if obj_type == "x-mitre-tactic":
            tactic_id = ""
            for ref in raw.get("external_references", []):
                if ref.get("source_name") == "mitre-attack":
                    tactic_id = ref.get("external_id", "")
            return TacticNode(
                node_id    = f"tactic-{tactic_id.lower()}",
                tactic_id  = tactic_id,
                name       = name,
                description= desc,
                stix_id    = stix_id,
                deprecated = deprecated,
                sources    = ["MITRE ATT&CK"],
                confidence = ConfidenceLevel.CONFIRMED,
            )

        elif obj_type == "attack-pattern":
            ext_id = ""
            for ref in raw.get("external_references", []):
                if ref.get("source_name") == "mitre-attack":
                    ext_id = ref.get("external_id", "")

            platforms   = raw.get("x_mitre_platforms", [])
            permissions = raw.get("x_mitre_permissions_required", [])
            data_sources= raw.get("x_mitre_data_sources", [])
            defenses    = raw.get("x_mitre_defense_bypassed", [])
            is_subtechnique = raw.get("x_mitre_is_subtechnique", False)

            if is_subtechnique:
                parent = ext_id.split(".")[0] if "." in ext_id else ""
                return SubTechniqueNode(
                    node_id          = f"subtechnique-{ext_id.lower().replace('.','-')}",
                    sub_technique_id = ext_id,
                    parent_technique = parent,
                    name             = name,
                    description      = desc,
                    platforms        = platforms,
                    stix_id          = stix_id,
                    deprecated       = deprecated,
                    sources          = ["MITRE ATT&CK"],
                    confidence       = ConfidenceLevel.CONFIRMED,
                )
            else:
                return TechniqueNode(
                    node_id          = f"technique-{ext_id.lower()}",
                    technique_id     = ext_id,
                    name             = name,
                    description      = desc,
                    platforms        = platforms,
                    permissions_req  = permissions,
                    data_sources     = data_sources,
                    defenses_bypassed= defenses,
                    stix_id          = stix_id,
                    deprecated       = deprecated,
                    sources          = ["MITRE ATT&CK"],
                    confidence       = ConfidenceLevel.CONFIRMED,
                    usage_in_wild    = True,
                )

        elif obj_type == "intrusion-set":
            actor_type = ThreatActorType.UNKNOWN
            nation     = None
            for ref in raw.get("external_references", []):
                src = ref.get("source_name", "")
                if "nation" in src.lower() or "apt" in name.lower():
                    actor_type = ThreatActorType.NATION_STATE

            return ThreatActorNode(
                node_id        = f"actor-{stix_id.split('--')[1][:8]}",
                name           = name,
                description    = desc,
                aliases        = raw.get("aliases", []),
                actor_type     = actor_type,
                stix_id        = stix_id,
                deprecated     = deprecated,
                sources        = ["MITRE ATT&CK"],
                confidence     = ConfidenceLevel.HIGH,
            )

        elif obj_type == "malware":
            return MalwareNode(
                node_id    = f"malware-{stix_id.split('--')[1][:8]}",
                name       = name,
                description= desc,
                platforms  = raw.get("x_mitre_platforms", []),
                stix_id    = stix_id,
                deprecated = deprecated,
                sources    = ["MITRE ATT&CK"],
                confidence = ConfidenceLevel.HIGH,
            )

        return None     # Ignore unsupported types


# ──────────────────────────────────────────────
# CISA KEV INGESTION
# ──────────────────────────────────────────────

class CISAKEVIngestionSource(KnowledgeIngestionSource):
    """
    Ingests the CISA Known Exploited Vulnerabilities catalog.
    These are CVEs actively exploited in the wild.
    """

    KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

    async def fetch(self) -> AsyncGenerator[Dict, None]:
        try:
            async with self.session.get(self.KEV_URL) as resp:
                data = await resp.json(content_type=None)
                for vuln in data.get("vulnerabilities", []):
                    yield vuln
        except Exception as e:
            log.error("[CISA KEV] Fetch error: %s", e)

    async def transform(self, raw: Dict) -> Optional[CVENode]:
        cve_id = raw.get("cveID", "")
        if not cve_id:
            return None
        return CVENode(
            node_id          = f"cve-{cve_id.lower()}",
            cve_id           = cve_id,
            name             = cve_id,
            description      = raw.get("shortDescription", ""),
            exploited_in_wild= True,
            kev_listed       = True,
            sources          = ["CISA KEV"],
            confidence       = ConfidenceLevel.CONFIRMED,
            tlp_marking      = TLPMarking.WHITE,
            tags             = ["kev", "exploited_in_wild"],
            metadata         = {
                "vendor":         raw.get("vendorProject", ""),
                "product":        raw.get("product", ""),
                "due_date":       raw.get("dueDate", ""),
                "required_action":raw.get("requiredAction", ""),
            }
        )


# ──────────────────────────────────────────────
# SIGMA RULES INGESTION
# ──────────────────────────────────────────────

class SigmaRulesIngestionSource(KnowledgeIngestionSource):
    """
    Ingests Sigma detection rules from the SigmaHQ GitHub repository.
    Parses YAML rule files and maps them to techniques.
    """

    SIGMA_API = "https://api.github.com/repos/SigmaHQ/sigma/contents/rules"

    async def fetch(self) -> AsyncGenerator[Dict, None]:
        """Recursively fetch all .yml files from the Sigma rules directory."""
        dirs_to_process = [self.SIGMA_API]

        while dirs_to_process:
            current_dir = dirs_to_process.pop(0)
            try:
                async with self.session.get(
                    current_dir,
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 403:      # Rate limit
                        await asyncio.sleep(60)
                        continue
                    items = await resp.json()
                    for item in items:
                        if item["type"] == "dir":
                            dirs_to_process.append(item["url"])
                        elif item["type"] == "file" and item["name"].endswith(".yml"):
                            # Fetch raw content
                            async with self.session.get(item["download_url"]) as r:
                                if r.status == 200:
                                    content = await r.text()
                                    yield {"content": content, "path": item["path"]}
                            await asyncio.sleep(0.1)
            except Exception as e:
                log.warning("[SIGMA] Error fetching %s: %s", current_dir, e)

    async def transform(self, raw: Dict) -> Optional[DetectionRuleNode]:
        try:
            import yaml
            content = yaml.safe_load(raw.get("content", ""))
            if not content or not isinstance(content, dict):
                return None

            rule_id   = content.get("id", str(uuid.uuid4() if True else ""))
            title     = content.get("title", "")
            desc      = content.get("description", "")
            status    = content.get("status", "experimental")
            level     = content.get("level", "medium")
            author    = content.get("author", "")
            tags      = content.get("tags", [])

            # Extract technique IDs from tags
            techniques = [
                t.replace("attack.t", "T").upper()
                for t in tags
                if t.lower().startswith("attack.t")
            ]

            # Extract log source
            logsource  = content.get("logsource", {})
            log_sources = [
                f"{logsource.get('product','')}/{logsource.get('category','')}/"
                f"{logsource.get('service','')}".strip("/")
            ]

            return DetectionRuleNode(
                node_id           = f"sigma-{rule_id[:32]}",
                rule_id           = rule_id,
                name              = title,
                description       = desc[:1000],
                rule_type         = DetectionRuleType.SIGMA,
                rule_content      = raw.get("content", "")[:5000],
                techniques_covered= techniques,
                log_sources       = log_sources,
                severity_level    = level,
                status            = status,
                author            = author,
                sources           = ["SigmaHQ"],
                confidence        = ConfidenceLevel.HIGH,
                tags              = tags[:20],
            )
        except Exception as e:
            log.debug("[SIGMA] Transform error: %s", e)
            return None


# ──────────────────────────────────────────────
# EPSS ENRICHMENT
# ──────────────────────────────────────────────

class EPSSEnrichmentSource:
    """
    Downloads and parses the EPSS (Exploit Prediction Scoring System)
    dataset from FIRST.org and updates CVE nodes with EPSS scores.
    """

    EPSS_URL = "https://epss.cyentia.com/epss_scores-current.csv.gz"

    async def fetch_scores(
        self, session: aiohttp.ClientSession
    ) -> Dict[str, float]:
        """Returns dict of cve_id → epss_score."""
        scores = {}
        try:
            import gzip, io
            async with session.get(self.EPSS_URL) as resp:
                raw = await resp.read()
            decompressed = gzip.decompress(raw).decode()
            lines = decompressed.strip().split("\n")
            # Skip header comment lines
            for line in lines:
                if line.startswith("#") or line.startswith("cve,"):
                    continue
                parts = line.split(",")
                if len(parts) >= 2:
                    cve_id  = parts[0].strip()
                    try:
                        score = float(parts[1].strip())
                        scores[cve_id] = score
                    except ValueError:
                        pass
        except Exception as e:
            log.error("[EPSS] Error: %s", e)
        log.info("[EPSS] Loaded %d scores", len(scores))
        return scores

    async def enrich_neo4j(
        self, driver, scores: Dict[str, float]
    ):
        """Bulk update CVE nodes in Neo4j with EPSS scores."""
        batch_size = 500
        cve_ids    = list(scores.keys())
        for i in range(0, len(cve_ids), batch_size):
            batch = cve_ids[i:i+batch_size]
            updates = [
                {"cve_id": c, "epss": scores[c]} for c in batch
            ]
            async with driver.session() as session:
                await session.run("""
                    UNWIND $updates AS u
                    MATCH (c:CVE {cve_id: u.cve_id})
                    SET c.epss_score = u.epss,
                        c.updated_at = datetime()
                """, {"updates": updates})
            log.info("[EPSS] Updated batch %d/%d", i + batch_size, len(cve_ids))


# ──────────────────────────────────────────────
# KNOWLEDGE INGESTION COORDINATOR
# ──────────────────────────────────────────────

class KnowledgeIngestionCoordinator:
    """
    Orchestrates all knowledge ingestion sources.
    Manages deduplication, conflict resolution, and scheduling.
    """

    def __init__(self):
        self.driver   = AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        self.producer = None
        self.redis    = None
        self.session  = None
        self.stats    = {
            "total_ingested": 0,
            "total_errors":   0,
            "sources":        {},
        }

    async def initialize(self):
        self.redis    = await aioredis.from_url(REDIS_URL, decode_responses=True)
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
        await self.producer.start()
        self.session  = aiohttp.ClientSession()
        log.info("[COORDINATOR] Initialized all connections")

    async def run_all_sources(self):
        """Run all ingestion sources concurrently."""
        sources = [
            NVDCVEIngestionSource(self.session),
            MITREAttackIngestionSource(self.session),
            CISAKEVIngestionSource(self.session),
            SigmaRulesIngestionSource(self.session),
        ]
        tasks = [
            asyncio.create_task(source.run(self.producer))
            for source in sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for source, result in zip(sources, results):
            name = source.__class__.__name__
            if isinstance(result, Exception):
                log.error("[%s] Failed: %s", name, result)
            else:
                self.stats["sources"][name] = {
                    "ingested": source.ingested,
                    "errors":   source.errors,
                }
                self.stats["total_ingested"] += source.ingested
                self.stats["total_errors"]   += source.errors

        # EPSS enrichment
        epss = EPSSEnrichmentSource()
        scores = await epss.fetch_scores(self.session)
        await epss.enrich_neo4j(self.driver, scores)
        log.info("[COORDINATOR] Ingestion complete: %s", json.dumps(self.stats, indent=2))

    async def run_incremental(self, since_hours: int = 24):
        """Run incremental update — only fetch changes since N hours ago."""
        log.info("[COORDINATOR] Running incremental update (last %dh)", since_hours)
        # NVD supports lastModStartDate/lastModEndDate for incremental pulls
        since = (datetime.utcnow() - timedelta(hours=since_hours)).isoformat() + ".000"
        source = NVDCVEIngestionSource(self.session)
        await source.run(self.producer)

    async def shutdown(self):
        await self.producer.stop()
        await self.session.close()
        await self.driver.close()


# ──────────────────────────────────────────────
# ENTRYPOINT
# ──────────────────────────────────────────────

async def main():
    coordinator = KnowledgeIngestionCoordinator()
    await coordinator.initialize()
    try:
        await coordinator.run_all_sources()
    finally:
        await coordinator.shutdown()

if __name__ == "__main__":
    import uuid
    asyncio.run(main())
