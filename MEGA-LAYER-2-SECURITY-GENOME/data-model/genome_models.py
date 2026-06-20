"""
AEGIS OMEGA X — MEGA LAYER 2
ENTERPRISE SECURITY GENOME — DATA MODEL
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from enum import Enum
from datetime import datetime
import uuid
import hashlib
import json


# ──────────────────────────────────────────────
# ENUMERATIONS
# ──────────────────────────────────────────────

class GenomeNodeType(str, Enum):
    ASSET            = "asset"
    IDENTITY         = "identity"
    APPLICATION      = "application"
    CONTAINER        = "container"
    API_ENDPOINT     = "api_endpoint"
    DATA_STORE       = "data_store"
    CLOUD_SERVICE    = "cloud_service"
    SECURITY_CONTROL = "security_control"
    CONFIGURATION    = "configuration"
    DEPENDENCY       = "dependency"
    BUSINESS_PROCESS = "business_process"
    CVE              = "cve"
    PERMISSION       = "permission"
    NETWORK_SEGMENT  = "network_segment"
    CERTIFICATE      = "certificate"


class MutationType(str, Enum):
    # Asset mutations
    ASSET_ADDED          = "asset_added"
    ASSET_REMOVED        = "asset_removed"
    ASSET_MODIFIED       = "asset_modified"
    # Identity mutations
    IDENTITY_CREATED     = "identity_created"
    IDENTITY_DEACTIVATED = "identity_deactivated"
    PRIVILEGE_ESCALATED  = "privilege_escalated"
    PRIVILEGE_REVOKED    = "privilege_revoked"
    MFA_DISABLED         = "mfa_disabled"
    MFA_ENABLED          = "mfa_enabled"
    # Security control mutations
    CONTROL_ADDED        = "control_added"
    CONTROL_REMOVED      = "control_removed"
    CONTROL_DEGRADED     = "control_degraded"
    # Dependency mutations
    DEPENDENCY_ADDED     = "dependency_added"
    DEPENDENCY_UPDATED   = "dependency_updated"
    CVE_INTRODUCED       = "cve_introduced"
    CVE_PATCHED          = "cve_patched"
    # Configuration mutations
    CONFIG_CHANGED       = "config_changed"
    SECRET_ROTATED       = "secret_rotated"
    SECRET_EXPOSED       = "secret_exposed"
    # Network mutations
    PORT_OPENED          = "port_opened"
    PORT_CLOSED          = "port_closed"
    FIREWALL_RULE_ADDED  = "firewall_rule_added"
    FIREWALL_RULE_REMOVED= "firewall_rule_removed"
    # Relationship mutations
    TRUST_ADDED          = "trust_added"
    TRUST_REMOVED        = "trust_removed"
    DEPENDENCY_LINK      = "dependency_link"


class RiskInheritanceMode(str, Enum):
    DIRECT    = "direct"      # Inherits full risk of parent
    WEIGHTED  = "weighted"    # Partial risk based on relationship weight
    MAXIMUM   = "maximum"     # Takes max risk of all dependencies
    AVERAGE   = "average"     # Average of dependency risks


class ResilienceMetric(str, Enum):
    REDUNDANCY          = "redundancy"
    RECOVERY_TIME       = "recovery_time"
    BLAST_RADIUS        = "blast_radius"
    CONTROL_COVERAGE    = "control_coverage"
    PATCH_VELOCITY      = "patch_velocity"
    IDENTITY_HYGIENE    = "identity_hygiene"
    ENCRYPTION_COVERAGE = "encryption_coverage"
    SEGMENTATION        = "segmentation"


# ──────────────────────────────────────────────
# GENOME NODE MODELS
# ──────────────────────────────────────────────

@dataclass
class GenomeNode:
    """
    Base class for all genome nodes.
    Every node has a DNA fingerprint — a hash of its security-relevant properties.
    Changes to fingerprint = mutation event.
    """
    node_id:      str  = field(default_factory=lambda: str(uuid.uuid4()))
    node_type:    GenomeNodeType = GenomeNodeType.ASSET
    entity_id:    str  = ""
    name:         str  = ""
    label:        str  = ""
    risk_score:   float = 0.0
    inherited_risk: float = 0.0
    effective_risk: float = 0.0
    dna_fingerprint: str = ""
    created_at:   datetime = field(default_factory=datetime.utcnow)
    updated_at:   datetime = field(default_factory=datetime.utcnow)
    version:      int  = 1
    tags:         Dict[str, str] = field(default_factory=dict)
    properties:   Dict[str, Any] = field(default_factory=dict)

    def compute_fingerprint(self) -> str:
        """
        Computes a SHA-256 fingerprint of all security-relevant properties.
        If this changes between ticks → mutation event is emitted.
        """
        payload = {
            "node_id":    self.node_id,
            "node_type":  self.node_type,
            "name":       self.name,
            "risk_score": round(self.risk_score, 4),
            "properties": self.properties,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()

    def update_fingerprint(self) -> bool:
        """Returns True if fingerprint changed (mutation detected)."""
        new_fp = self.compute_fingerprint()
        if new_fp != self.dna_fingerprint:
            self.dna_fingerprint = new_fp
            self.version += 1
            self.updated_at = datetime.utcnow()
            return True
        return False


@dataclass
class AssetGenomeNode(GenomeNode):
    node_type:          GenomeNodeType = GenomeNodeType.ASSET
    asset_type:         str = ""
    os:                 Optional[str] = None
    os_version:         Optional[str] = None
    is_internet_facing: bool = False
    is_encrypted:       bool = False
    patched_at:         Optional[datetime] = None
    patch_lag_days:     int = 0
    open_ports:         List[int] = field(default_factory=list)
    running_services:   List[str] = field(default_factory=list)
    cve_count:          int = 0
    critical_cve_count: int = 0


@dataclass
class IdentityGenomeNode(GenomeNode):
    node_type:       GenomeNodeType = GenomeNodeType.IDENTITY
    identity_type:   str = "human"
    privilege_level: str = "standard"
    mfa_enabled:     bool = False
    active:          bool = True
    last_active:     Optional[datetime] = None
    anomaly_score:   float = 0.0
    stale:           bool = False             # No activity > 90 days
    overprivileged:  bool = False             # Has permissions not used in 90d


@dataclass
class ApplicationGenomeNode(GenomeNode):
    node_type:         GenomeNodeType = GenomeNodeType.APPLICATION
    language:          str = ""
    framework:         str = ""
    version:           str = ""
    auth_mechanism:    str = ""
    api_count:         int = 0
    dependency_count:  int = 0
    sast_score:        Optional[float] = None
    dast_score:        Optional[float] = None
    secret_count:      int = 0                 # secrets in codebase
    has_waf:           bool = False
    deployment_type:   str = "container"


@dataclass
class SecurityControlGenomeNode(GenomeNode):
    node_type:        GenomeNodeType = GenomeNodeType.SECURITY_CONTROL
    control_type:     str = ""               # firewall | waf | edr | siem | dlp | mfa | pam
    vendor:           str = ""
    version:          str = ""
    is_active:        bool = True
    coverage_scope:   List[str] = field(default_factory=list)   # asset_ids covered
    effectiveness:    float = 0.0            # 0.0–1.0
    last_audit:       Optional[datetime] = None
    configuration_ok: bool = True
    alerts_enabled:   bool = True


@dataclass
class DependencyGenomeNode(GenomeNode):
    node_type:    GenomeNodeType = GenomeNodeType.DEPENDENCY
    package_name: str = ""
    package_mgr:  str = ""       # npm | pip | maven | cargo | go | apt
    version:      str = ""
    cve_ids:      List[str] = field(default_factory=list)
    cvss_max:     float = 0.0
    is_direct:    bool = True    # vs transitive dependency
    is_outdated:  bool = False
    license:      str = ""
    supplier:     str = ""


@dataclass
class CVEGenomeNode(GenomeNode):
    node_type:   GenomeNodeType = GenomeNodeType.CVE
    cve_id:      str = ""
    cvss_score:  float = 0.0
    cvss_vector: str = ""
    severity:    str = ""        # critical | high | medium | low
    published:   Optional[datetime] = None
    patched:     bool = False
    exploited_in_wild: bool = False
    exploit_available: bool = False
    epss_score:  float = 0.0     # Exploit Prediction Scoring System


@dataclass
class ConfigurationGenomeNode(GenomeNode):
    node_type:      GenomeNodeType = GenomeNodeType.CONFIGURATION
    config_type:    str = ""     # iac | secret | policy | parameter | env
    source_path:    str = ""
    is_encrypted:   bool = False
    is_hardcoded_secret: bool = False
    compliance_violations: List[str] = field(default_factory=list)
    drift_detected: bool = False
    last_validated: Optional[datetime] = None


@dataclass
class BusinessProcessGenomeNode(GenomeNode):
    node_type:           GenomeNodeType = GenomeNodeType.BUSINESS_PROCESS
    process_type:        str = ""
    criticality:         float = 0.0
    data_classification: str = "internal"     # public | internal | confidential | secret
    regulatory_scope:    List[str] = field(default_factory=list)  # PCI | HIPAA | GDPR | SOX
    automation_level:    float = 0.0          # 0=manual, 1=fully automated
    human_in_loop:       bool = True


# ──────────────────────────────────────────────
# GENOME EDGE (RELATIONSHIP)
# ──────────────────────────────────────────────

@dataclass
class GenomeEdge:
    """
    A relationship between two genome nodes.
    Every edge carries risk weight and is versioned.
    """
    edge_id:          str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id:        str = ""
    target_id:        str = ""
    edge_type:        str = ""
    risk_weight:      float = 1.0            # How much risk transfers on this edge
    bidirectional:    bool = False
    encrypted:        bool = False
    authenticated:    bool = False
    authorized:       bool = True
    data_flow:        bool = False           # Does data flow on this edge?
    data_sensitivity: str = "low"
    discovered_at:    datetime = field(default_factory=datetime.utcnow)
    last_observed:    Optional[datetime] = None
    active:           bool = True
    version:          int = 1
    metadata:         Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────
# MUTATION EVENT
# ──────────────────────────────────────────────

@dataclass
class MutationEvent:
    """
    Every change to the security genome is a MutationEvent.
    Forms an immutable append-only audit log of the genome's evolution.
    """
    mutation_id:     str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_id:       str = ""
    node_id:         str = ""
    node_type:       str = ""
    mutation_type:   MutationType = MutationType.ASSET_MODIFIED
    previous_fp:     str = ""                # Previous DNA fingerprint
    current_fp:      str = ""                # New DNA fingerprint
    previous_state:  Dict[str, Any] = field(default_factory=dict)
    current_state:   Dict[str, Any] = field(default_factory=dict)
    delta:           Dict[str, Any] = field(default_factory=dict)   # Diff
    risk_delta:      float = 0.0             # Risk change (+/-) from this mutation
    severity:        str = "low"             # low | medium | high | critical
    auto_detected:   bool = True
    source:          str = ""                # scanner | api | iac | manual
    actor:           Optional[str] = None    # Who caused the mutation
    occurred_at:     datetime = field(default_factory=datetime.utcnow)
    detected_at:     datetime = field(default_factory=datetime.utcnow)
    metadata:        Dict[str, Any] = field(default_factory=dict)

    @property
    def detection_latency_seconds(self) -> float:
        return (self.detected_at - self.occurred_at).total_seconds()


# ──────────────────────────────────────────────
# SECURITY DNA FINGERPRINT
# ──────────────────────────────────────────────

@dataclass
class SecurityDNA:
    """
    The complete security DNA of an organization at a point in time.
    This is a snapshot of the entire genome that can be:
    - Compared across time (diff)
    - Compared across organizations (similarity)
    - Used to detect security posture regression
    """
    dna_id:              str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_id:           str = ""
    snapshot_at:         datetime = field(default_factory=datetime.utcnow)
    genome_version:      int = 1

    # Node counts
    total_nodes:         int = 0
    asset_count:         int = 0
    identity_count:      int = 0
    application_count:   int = 0
    control_count:       int = 0
    dependency_count:    int = 0
    cve_count:           int = 0

    # Risk profile
    overall_risk:        float = 0.0
    asset_risk_avg:      float = 0.0
    identity_risk_avg:   float = 0.0
    critical_cve_count:  int = 0
    unpatched_critical:  int = 0
    overprivileged_identities: int = 0
    stale_identities:    int = 0
    orphaned_assets:     int = 0             # Assets with no security control

    # Control coverage
    control_coverage:    float = 0.0         # % assets with at least 1 control
    mfa_coverage:        float = 0.0         # % identities with MFA
    encryption_coverage: float = 0.0         # % data stores encrypted
    patch_coverage:      float = 0.0         # % assets up to date

    # Complexity metrics
    total_edges:         int = 0
    avg_dependencies:    float = 0.0
    max_blast_radius:    int = 0

    # Composite fingerprint of entire genome
    genome_hash:         str = ""

    # Resilience dimensions
    resilience_scores:   Dict[str, float] = field(default_factory=dict)

    def compute_genome_hash(self) -> str:
        payload = {
            "entity_id":         self.entity_id,
            "genome_version":    self.genome_version,
            "total_nodes":       self.total_nodes,
            "overall_risk":      round(self.overall_risk, 4),
            "control_coverage":  round(self.control_coverage, 4),
            "critical_cve_count": self.critical_cve_count,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()


# ──────────────────────────────────────────────
# RISK INHERITANCE CALCULATOR
# ──────────────────────────────────────────────

class RiskInheritanceCalculator:
    """
    Propagates risk scores through the genome dependency graph.
    Uses configurable inheritance modes.
    """

    @staticmethod
    def propagate(
        nodes: Dict[str, GenomeNode],
        edges: List[GenomeEdge],
        mode: RiskInheritanceMode = RiskInheritanceMode.WEIGHTED,
        damping: float = 0.7,
        max_iterations: int = 10,
    ) -> Dict[str, float]:
        """
        Iterative risk propagation. Each node's inherited risk
        is computed from its upstream dependencies.

        damping: Controls how much risk decays over each hop (0.7 = 70% transfer).
        """
        inherited = {nid: 0.0 for nid in nodes}
        effective = {nid: nodes[nid].risk_score for nid in nodes}

        # Build adjacency: target → list of (source, weight)
        incoming: Dict[str, List[tuple]] = {nid: [] for nid in nodes}
        for edge in edges:
            if edge.active and edge.source_id in nodes and edge.target_id in nodes:
                incoming[edge.target_id].append(
                    (edge.source_id, edge.risk_weight)
                )

        for iteration in range(max_iterations):
            prev_effective = dict(effective)

            for node_id in nodes:
                if not incoming[node_id]:
                    continue

                upstream_risks = []
                for (src_id, weight) in incoming[node_id]:
                    upstream_risk = effective[src_id] * weight * damping
                    upstream_risks.append(upstream_risk)

                if mode == RiskInheritanceMode.MAXIMUM:
                    inh = max(upstream_risks)
                elif mode == RiskInheritanceMode.AVERAGE:
                    inh = sum(upstream_risks) / len(upstream_risks)
                elif mode == RiskInheritanceMode.WEIGHTED:
                    total_weight = sum(w for (_, w) in incoming[node_id])
                    inh = sum(upstream_risks) / max(total_weight, 1.0)
                else:  # DIRECT
                    inh = upstream_risks[0] if upstream_risks else 0.0

                inherited[node_id] = min(inh, 1.0)
                effective[node_id] = min(
                    nodes[node_id].risk_score + inherited[node_id] * 0.5,
                    1.0
                )

            # Check convergence
            delta = sum(abs(effective[nid] - prev_effective[nid]) for nid in nodes)
            if delta < 1e-6:
                break

        return effective


# ──────────────────────────────────────────────
# GENOME DIFF ENGINE
# ──────────────────────────────────────────────

@dataclass
class GenomeDiff:
    """
    Represents the difference between two genome snapshots.
    Like a git diff but for security posture.
    """
    diff_id:          str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_id:        str = ""
    from_version:     int = 0
    to_version:       int = 0
    from_snapshot_at: Optional[datetime] = None
    to_snapshot_at:   Optional[datetime] = None

    # Changes
    nodes_added:      List[str] = field(default_factory=list)
    nodes_removed:    List[str] = field(default_factory=list)
    nodes_modified:   List[str] = field(default_factory=list)
    edges_added:      List[str] = field(default_factory=list)
    edges_removed:    List[str] = field(default_factory=list)
    mutations:        List[MutationEvent] = field(default_factory=list)

    # Risk delta
    risk_delta:       float = 0.0
    risk_direction:   str = "stable"        # improving | degrading | stable

    # Summary
    security_posture_change: str = "neutral"
    mutation_count:   int = 0
    critical_mutations: int = 0

    def summarize(self) -> str:
        direction = "↑ IMPROVED" if self.risk_delta < 0 else "↓ DEGRADED" if self.risk_delta > 0 else "→ STABLE"
        return (
            f"Genome diff v{self.from_version}→v{self.to_version}: "
            f"{direction} ({self.risk_delta:+.3f} risk) | "
            f"+{len(self.nodes_added)} nodes "
            f"-{len(self.nodes_removed)} nodes "
            f"~{len(self.nodes_modified)} modified | "
            f"{self.critical_mutations} critical mutations"
        )


# ──────────────────────────────────────────────
# RESILIENCE EVOLUTION MODEL
# ──────────────────────────────────────────────

@dataclass
class ResilienceSnapshot:
    """
    Point-in-time resilience measurement for an entity.
    Tracking these over time reveals resilience trajectories.
    """
    snapshot_id:        str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_id:          str = ""
    measured_at:        datetime = field(default_factory=datetime.utcnow)

    # Resilience dimensions (0.0–1.0, higher = more resilient)
    redundancy:          float = 0.0
    recovery_speed:      float = 0.0     # Based on RTO/RPO estimates
    blast_radius_score:  float = 0.0     # Lower blast radius = higher score
    control_coverage:    float = 0.0
    patch_velocity:      float = 0.0     # Speed of patching critical CVEs
    identity_hygiene:    float = 0.0
    encryption_coverage: float = 0.0
    segmentation:        float = 0.0     # Network segmentation quality

    # Composite score
    overall_resilience:  float = 0.0

    def compute_overall(self):
        weights = {
            "redundancy":          0.15,
            "recovery_speed":      0.15,
            "blast_radius_score":  0.15,
            "control_coverage":    0.20,
            "patch_velocity":      0.15,
            "identity_hygiene":    0.10,
            "encryption_coverage": 0.05,
            "segmentation":        0.05,
        }
        self.overall_resilience = sum(
            getattr(self, k) * v for k, v in weights.items()
        )
        return self.overall_resilience


# ──────────────────────────────────────────────
# NEO4J SCHEMA FOR GENOME
# ──────────────────────────────────────────────
GENOME_NEO4J_SCHEMA = """
// CONSTRAINTS
CREATE CONSTRAINT genome_node_id IF NOT EXISTS FOR (n:GenomeNode) REQUIRE n.node_id IS UNIQUE;
CREATE CONSTRAINT cve_id         IF NOT EXISTS FOR (c:CVE)        REQUIRE c.cve_id IS UNIQUE;
CREATE CONSTRAINT dep_id         IF NOT EXISTS FOR (d:Dependency)  REQUIRE d.node_id IS UNIQUE;

// NODE LABEL INDEXES
CREATE INDEX idx_genome_entity   IF NOT EXISTS FOR (n:GenomeNode) ON (n.entity_id);
CREATE INDEX idx_genome_type     IF NOT EXISTS FOR (n:GenomeNode) ON (n.node_type);
CREATE INDEX idx_genome_risk     IF NOT EXISTS FOR (n:GenomeNode) ON (n.risk_score);
CREATE INDEX idx_genome_version  IF NOT EXISTS FOR (n:GenomeNode) ON (n.version);
CREATE INDEX idx_cve_score       IF NOT EXISTS FOR (c:CVE) ON (c.cvss_score);
CREATE INDEX idx_cve_exploited   IF NOT EXISTS FOR (c:CVE) ON (c.exploited_in_wild);

// GENOME EDGE TYPES (stored as relationships in Neo4j)
// DEPENDS_ON | EXPOSES | PROCESSES | STORES | HOSTS | RUNS_AS
// ACCESSES | GRANTS | BELONGS_TO | PROTECTS | APPLIES_TO
// CONTAINS | USED_IN | ROUTES_TO | SIGNED_BY | TRUSTS

// EXAMPLE: Full genome subgraph for one application
CREATE (app:GenomeNode:Application {
    node_id: 'app-001',
    entity_id: 'ent-001',
    node_type: 'application',
    name: 'payment-service',
    risk_score: 0.72,
    dna_fingerprint: '',
    version: 1
});

CREATE (dep:GenomeNode:Dependency {
    node_id: 'dep-001',
    package_name: 'log4j-core',
    version: '2.14.1',
    package_mgr: 'maven',
    is_outdated: true
});

CREATE (cve:GenomeNode:CVE {
    node_id: 'cve-001',
    cve_id: 'CVE-2021-44228',
    cvss_score: 10.0,
    severity: 'critical',
    exploited_in_wild: true,
    exploit_available: true
});

CREATE (ctrl:GenomeNode:SecurityControl {
    node_id: 'ctrl-001',
    control_type: 'waf',
    vendor: 'Cloudflare',
    is_active: true,
    effectiveness: 0.85
});

MATCH (app:GenomeNode {node_id: 'app-001'}),
      (dep:GenomeNode {node_id: 'dep-001'})
CREATE (app)-[:DEPENDS_ON {risk_weight: 0.9, is_direct: true}]->(dep);

MATCH (dep:GenomeNode {node_id: 'dep-001'}),
      (cve:GenomeNode {node_id: 'cve-001'})
CREATE (dep)-[:CONTAINS {cvss: 10.0}]->(cve);

MATCH (ctrl:GenomeNode {node_id: 'ctrl-001'}),
      (app:GenomeNode  {node_id: 'app-001'})
CREATE (ctrl)-[:PROTECTS {coverage: 0.85}]->(app);
"""
