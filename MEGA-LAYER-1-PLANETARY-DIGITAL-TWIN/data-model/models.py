"""
AEGIS OMEGA X — MEGA LAYER 1
PLANETARY DIGITAL TWIN — DATA MODEL
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


# ──────────────────────────────────────────────
# ENUMERATIONS
# ──────────────────────────────────────────────

class DomainType(str, Enum):
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"
    HEALTHCARE = "healthcare"
    FINANCIAL = "financial"
    TELECOM = "telecom"
    TRANSPORT = "transport"
    ENERGY = "energy"
    MANUFACTURING = "manufacturing"
    SMART_CITY = "smart_city"
    UNIVERSITY = "university"
    SUPPLY_CHAIN = "supply_chain"
    CLOUD_PROVIDER = "cloud_provider"
    AI_ECOSYSTEM = "ai_ecosystem"


class AssetType(str, Enum):
    SERVER = "server"
    ENDPOINT = "endpoint"
    NETWORK_DEVICE = "network_device"
    CLOUD_RESOURCE = "cloud_resource"
    CONTAINER = "container"
    KUBERNETES_POD = "kubernetes_pod"
    SERVERLESS = "serverless"
    DATABASE = "database"
    API_ENDPOINT = "api_endpoint"
    IOT_DEVICE = "iot_device"
    OT_DEVICE = "ot_device"
    AI_MODEL = "ai_model"
    AI_AGENT = "ai_agent"
    DATA_PIPELINE = "data_pipeline"
    IDENTITY = "identity"
    APPLICATION = "application"
    CERTIFICATE = "certificate"
    SECRET = "secret"
    FIRMWARE = "firmware"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class RelationshipType(str, Enum):
    DEPENDS_ON = "depends_on"
    COMMUNICATES_WITH = "communicates_with"
    AUTHENTICATES_TO = "authenticates_to"
    HOSTS = "hosts"
    MANAGES = "manages"
    INHERITS_FROM = "inherits_from"
    SUPPLIES = "supplies"
    ROUTES_THROUGH = "routes_through"
    CONTAINS = "contains"
    TRUSTS = "trusts"
    EXPOSES = "exposes"
    PROCESSES = "processes"
    STORES = "stores"
    REPLICATES_TO = "replicates_to"


class SimulationStatus(str, Enum):
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    COMPROMISED = "compromised"
    FAILED = "failed"
    RECOVERING = "recovering"
    UNKNOWN = "unknown"


# ──────────────────────────────────────────────
# CORE NODE MODELS
# ──────────────────────────────────────────────

@dataclass
class CivilizationalEntity:
    """
    Top-level entity. Represents any real-world organization
    that has a digital presence worth modeling.
    """
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    domain: DomainType = DomainType.ENTERPRISE
    country: str = ""
    region: str = ""
    sector: str = ""
    employee_count: int = 0
    revenue_usd: float = 0.0
    criticality_score: float = 0.0       # 0.0–1.0
    interconnectedness: float = 0.0      # 0.0–1.0
    security_maturity: float = 0.0       # 0.0–1.0
    digital_surface_area: int = 0        # total asset count
    simulation_status: SimulationStatus = SimulationStatus.NOMINAL
    last_sync: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DigitalAsset:
    """
    Any digital asset within a CivilizationalEntity.
    Maps to a node in the planetary graph.
    """
    asset_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str = ""
    name: str = ""
    asset_type: AssetType = AssetType.SERVER
    hostname: Optional[str] = None
    ip_addresses: List[str] = field(default_factory=list)
    cloud_provider: Optional[str] = None
    cloud_region: Optional[str] = None
    cloud_account: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    software_stack: List[str] = field(default_factory=list)
    cve_ids: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    exposure_score: float = 0.0
    criticality: float = 0.0
    is_internet_facing: bool = False
    is_in_dmz: bool = False
    is_air_gapped: bool = False
    contains_pii: bool = False
    contains_phi: bool = False
    contains_pci: bool = False
    security_controls: List[str] = field(default_factory=list)
    simulation_status: SimulationStatus = SimulationStatus.NOMINAL
    last_seen: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Identity:
    """
    Human or machine identity within a CivilizationalEntity.
    """
    identity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str = ""
    name: str = ""
    email: Optional[str] = None
    identity_type: str = "human"          # human | service | machine | api_key | certificate
    department: Optional[str] = None
    role: Optional[str] = None
    privilege_level: str = "standard"     # standard | privileged | admin | superadmin
    mfa_enabled: bool = False
    federated: bool = False
    active: bool = True
    last_activity: Optional[datetime] = None
    risk_score: float = 0.0
    behavioral_baseline: Dict[str, Any] = field(default_factory=dict)
    access_map: List[str] = field(default_factory=list)  # asset_ids accessible
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AssetRelationship:
    """
    Edge in the planetary graph. Connects two DigitalAssets
    or a DigitalAsset to an Identity.
    """
    relationship_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    relationship_type: RelationshipType = RelationshipType.COMMUNICATES_WITH
    protocol: Optional[str] = None
    port: Optional[int] = None
    encrypted: bool = False
    authenticated: bool = False
    data_sensitivity: str = "low"          # low | medium | high | critical
    bandwidth_mbps: Optional[float] = None
    latency_ms: Optional[float] = None
    risk_score: float = 0.0
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_observed: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CascadeEvent:
    """
    Represents a simulated or real cascade failure event
    propagating through the planetary graph.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    origin_asset_id: str = ""
    origin_entity_id: str = ""
    event_type: str = ""                   # breach | outage | ransomware | supply_chain | etc.
    blast_radius: List[str] = field(default_factory=list)   # affected asset_ids
    affected_entities: List[str] = field(default_factory=list)
    propagation_path: List[str] = field(default_factory=list)
    severity: RiskLevel = RiskLevel.HIGH
    economic_impact_usd: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)
    contained_at: Optional[datetime] = None
    recovered_at: Optional[datetime] = None
    simulated: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CloudRegionModel:
    """
    Models a cloud provider region as a first-class entity.
    """
    region_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider: str = ""                     # aws | gcp | azure | oci | alibaba
    region_code: str = ""                  # e.g. ap-south-1
    geography: str = ""
    availability_zones: List[str] = field(default_factory=list)
    services_hosted: List[str] = field(default_factory=list)
    tenant_count: int = 0
    data_sovereignty_laws: List[str] = field(default_factory=list)
    interconnects: List[str] = field(default_factory=list)  # peered regions
    status: SimulationStatus = SimulationStatus.NOMINAL
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIEcosystemNode:
    """
    Models an AI model, agent, or training pipeline in the twin.
    """
    ai_node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str = ""
    name: str = ""
    model_type: str = ""                   # llm | diffusion | classifier | rl_agent | etc.
    provider: Optional[str] = None
    version: Optional[str] = None
    hosting: str = "cloud"                 # cloud | on-prem | edge | hybrid
    training_data_sources: List[str] = field(default_factory=list)
    inference_endpoints: List[str] = field(default_factory=list)
    access_controls: List[str] = field(default_factory=list)
    data_processed: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    alignment_score: Optional[float] = None
    audit_trail: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationTick:
    """
    Represents one tick of the planetary simulation.
    Captures global state delta at each simulation step.
    """
    tick_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tick_number: int = 0
    tick_timestamp: datetime = field(default_factory=datetime.utcnow)
    global_risk_score: float = 0.0
    active_threats: int = 0
    compromised_assets: int = 0
    degraded_entities: int = 0
    cascade_events_active: int = 0
    simulation_lag_ms: float = 0.0
    state_delta: Dict[str, Any] = field(default_factory=dict)  # compressed diff


# ──────────────────────────────────────────────
# NEO4J SCHEMA (Cypher)
# ──────────────────────────────────────────────
NEO4J_SCHEMA = """
// CONSTRAINTS
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE;
CREATE CONSTRAINT asset_id  IF NOT EXISTS FOR (a:Asset)  REQUIRE a.asset_id  IS UNIQUE;
CREATE CONSTRAINT identity_id IF NOT EXISTS FOR (i:Identity) REQUIRE i.identity_id IS UNIQUE;
CREATE CONSTRAINT region_id IF NOT EXISTS FOR (r:CloudRegion) REQUIRE r.region_id IS UNIQUE;
CREATE CONSTRAINT ai_node_id IF NOT EXISTS FOR (n:AINode) REQUIRE n.ai_node_id IS UNIQUE;

// INDEXES
CREATE INDEX entity_domain  IF NOT EXISTS FOR (e:Entity)  ON (e.domain);
CREATE INDEX asset_type     IF NOT EXISTS FOR (a:Asset)   ON (a.asset_type);
CREATE INDEX asset_risk     IF NOT EXISTS FOR (a:Asset)   ON (a.risk_score);
CREATE INDEX asset_entity   IF NOT EXISTS FOR (a:Asset)   ON (a.entity_id);
CREATE INDEX identity_type  IF NOT EXISTS FOR (i:Identity) ON (i.identity_type);
CREATE INDEX identity_priv  IF NOT EXISTS FOR (i:Identity) ON (i.privilege_level);

// EXAMPLE NODES
CREATE (e:Entity {
    entity_id: 'ent-001',
    name: 'GlobalBank Corp',
    domain: 'financial',
    country: 'US',
    sector: 'banking',
    criticality_score: 0.95,
    security_maturity: 0.72
});

CREATE (a:Asset {
    asset_id: 'ast-001',
    entity_id: 'ent-001',
    name: 'core-banking-api',
    asset_type: 'api_endpoint',
    is_internet_facing: true,
    risk_score: 0.87,
    risk_level: 'critical'
});

CREATE (i:Identity {
    identity_id: 'idn-001',
    entity_id: 'ent-001',
    name: 'svc-payment-processor',
    identity_type: 'service',
    privilege_level: 'privileged',
    mfa_enabled: false
});

// EXAMPLE RELATIONSHIPS
MATCH (e:Entity {entity_id: 'ent-001'}), (a:Asset {asset_id: 'ast-001'})
CREATE (e)-[:CONTAINS {created_at: datetime()}]->(a);

MATCH (i:Identity {identity_id: 'idn-001'}), (a:Asset {asset_id: 'ast-001'})
CREATE (i)-[:AUTHENTICATES_TO {protocol: 'mTLS', encrypted: true}]->(a);
"""
