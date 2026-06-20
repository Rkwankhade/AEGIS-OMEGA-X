"""
AEGIS OMEGA X — MEGA LAYER 3
GLOBAL SECURITY KNOWLEDGE UNIVERSE — DATA MODEL
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set, Tuple
from enum import Enum
from datetime import datetime
import uuid
import hashlib
import json


# ──────────────────────────────────────────────
# KNOWLEDGE NODE ENUMERATIONS
# ──────────────────────────────────────────────

class KnowledgeNodeType(str, Enum):
    # Threat Intelligence
    THREAT_ACTOR      = "threat_actor"
    CAMPAIGN          = "campaign"
    MALWARE           = "malware"
    TOOL              = "tool"
    INFRASTRUCTURE    = "infrastructure"
    # Vulnerability
    CVE               = "cve"
    CWE               = "cwe"
    CAPEC             = "capec"
    EXPLOIT           = "exploit"
    PATCH             = "patch"
    # Attack Knowledge
    TACTIC            = "tactic"
    TECHNIQUE         = "technique"
    SUB_TECHNIQUE     = "sub_technique"
    PROCEDURE         = "procedure"
    KILL_CHAIN        = "kill_chain"
    # Defense Knowledge
    SECURITY_CONTROL  = "security_control"
    DETECTION_RULE    = "detection_rule"
    MITIGATION        = "mitigation"
    ARCHITECTURE      = "architecture"
    # Compliance
    FRAMEWORK         = "framework"
    CONTROL_REQ       = "control_requirement"
    REQUIREMENT       = "requirement"
    EVIDENCE          = "evidence"
    # Incidents
    INCIDENT          = "incident"
    BREACH_RECORD     = "breach_record"
    LESSON_LEARNED    = "lesson_learned"
    # Research
    RESEARCH_PAPER    = "research_paper"
    ADVISORY          = "advisory"
    BLOG_POST         = "blog_post"
    # Indicators
    IOC               = "ioc"
    HASH              = "hash"
    DOMAIN            = "domain"
    IP_ADDRESS        = "ip_address"
    URL               = "url"
    # Organizations
    VICTIM_ORG        = "victim_org"
    VENDOR_ORG        = "vendor_org"
    RESEARCH_ORG      = "research_org"
    # Software/Hardware
    SOFTWARE          = "software"
    HARDWARE          = "hardware"
    PLATFORM          = "platform"
    PROTOCOL          = "protocol"


class ThreatActorType(str, Enum):
    NATION_STATE      = "nation_state"
    CRIMINAL_GROUP    = "criminal_group"
    HACKTIVIST        = "hacktivist"
    INSIDER           = "insider"
    RESEARCHER        = "researcher"
    UNKNOWN           = "unknown"


class MalwareType(str, Enum):
    RANSOMWARE        = "ransomware"
    TROJAN            = "trojan"
    ROOTKIT           = "rootkit"
    SPYWARE           = "spyware"
    WORM              = "worm"
    BACKDOOR          = "backdoor"
    LOADER            = "loader"
    DROPPER           = "dropper"
    RAT               = "rat"
    BOTNET            = "botnet"
    CRYPTOMINER       = "cryptominer"
    INFOSTEALER       = "infostealer"
    WIPER             = "wiper"


class ConfidenceLevel(str, Enum):
    CONFIRMED         = "confirmed"       # >90% confidence
    HIGH              = "high"            # 70-90%
    MEDIUM            = "medium"          # 50-70%
    LOW               = "low"             # 30-50%
    SPECULATIVE       = "speculative"     # <30%


class TLPMarking(str, Enum):
    WHITE   = "WHITE"     # Unlimited sharing
    GREEN   = "GREEN"     # Community sharing
    AMBER   = "AMBER"     # Limited sharing
    RED     = "RED"       # No sharing


class DetectionRuleType(str, Enum):
    SIGMA   = "sigma"
    YARA    = "yara"
    SNORT   = "snort"
    SURICATA = "suricata"
    KQL     = "kql"
    SPL     = "spl"       # Splunk
    ES_QL   = "es_ql"     # Elastic
    CUSTOM  = "custom"


# ──────────────────────────────────────────────
# BASE KNOWLEDGE NODE
# ──────────────────────────────────────────────

@dataclass
class KnowledgeNode:
    """
    Base class for all knowledge graph nodes.
    Every node has semantic embeddings, confidence, and provenance.
    """
    node_id:         str = field(default_factory=lambda: str(uuid.uuid4()))
    node_type:       KnowledgeNodeType = KnowledgeNodeType.TECHNIQUE
    name:            str = ""
    description:     str = ""
    aliases:         List[str] = field(default_factory=list)
    confidence:      ConfidenceLevel = ConfidenceLevel.HIGH
    tlp_marking:     TLPMarking = TLPMarking.WHITE
    sources:         List[str] = field(default_factory=list)
    stix_id:         Optional[str] = None
    external_refs:   Dict[str, str] = field(default_factory=dict)
    embedding:       Optional[List[float]] = None   # 1536-dim vector
    created_at:      datetime = field(default_factory=datetime.utcnow)
    updated_at:      datetime = field(default_factory=datetime.utcnow)
    deprecated:      bool = False
    tags:            List[str] = field(default_factory=list)
    metadata:        Dict[str, Any] = field(default_factory=dict)

    def knowledge_hash(self) -> str:
        payload = {
            "node_type": self.node_type,
            "name":      self.name,
            "stix_id":   self.stix_id,
        }
        return hashlib.md5(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()


# ──────────────────────────────────────────────
# THREAT INTELLIGENCE NODES
# ──────────────────────────────────────────────

@dataclass
class ThreatActorNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.THREAT_ACTOR
    actor_type:        ThreatActorType = ThreatActorType.UNKNOWN
    nation_state:      Optional[str] = None       # Attributed country
    motivation:        List[str] = field(default_factory=list)  # espionage | financial | ...
    sophistication:    str = "intermediate"        # minimal|intermediate|advanced|expert
    active_since:      Optional[datetime] = None
    last_seen:         Optional[datetime] = None
    target_sectors:    List[str] = field(default_factory=list)
    target_countries:  List[str] = field(default_factory=list)
    known_tools:       List[str] = field(default_factory=list)  # tool node_ids
    known_malware:     List[str] = field(default_factory=list)  # malware node_ids
    known_campaigns:   List[str] = field(default_factory=list)
    ioc_count:         int = 0
    technique_count:   int = 0
    incident_count:    int = 0
    threat_score:      float = 0.0              # 0.0–1.0 composite threat
    mitre_groups:      List[str] = field(default_factory=list)  # G0xxx IDs


@dataclass
class CampaignNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.CAMPAIGN
    attributed_to:     Optional[str] = None       # ThreatActor node_id
    objective:         str = ""
    start_date:        Optional[datetime] = None
    end_date:          Optional[datetime] = None
    ongoing:           bool = False
    target_sectors:    List[str] = field(default_factory=list)
    target_regions:    List[str] = field(default_factory=list)
    techniques_used:   List[str] = field(default_factory=list)
    malware_deployed:  List[str] = field(default_factory=list)
    ioc_count:         int = 0
    victim_count:      int = 0


@dataclass
class MalwareNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.MALWARE
    malware_type:      MalwareType = MalwareType.TROJAN
    families:          List[str] = field(default_factory=list)
    platforms:         List[str] = field(default_factory=list)
    first_seen:        Optional[datetime] = None
    last_seen:         Optional[datetime] = None
    capabilities:      List[str] = field(default_factory=list)
    c2_protocols:      List[str] = field(default_factory=list)
    obfuscation:       List[str] = field(default_factory=list)
    av_detection_rate: Optional[float] = None
    hashes:            List[str] = field(default_factory=list)
    mitre_software:    Optional[str] = None       # S0xxx ID


# ──────────────────────────────────────────────
# VULNERABILITY NODES
# ──────────────────────────────────────────────

@dataclass
class CVENode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.CVE
    cve_id:            str = ""
    cvss_v3_score:     float = 0.0
    cvss_v3_vector:    str = ""
    cvss_v2_score:     Optional[float] = None
    severity:          str = ""
    epss_score:        float = 0.0
    epss_percentile:   float = 0.0
    published:         Optional[datetime] = None
    last_modified:     Optional[datetime] = None
    cwe_ids:           List[str] = field(default_factory=list)
    affected_software: List[str] = field(default_factory=list)
    affected_versions: List[str] = field(default_factory=list)
    patch_available:   bool = False
    patch_ids:         List[str] = field(default_factory=list)
    exploited_in_wild: bool = False
    kev_listed:        bool = False               # CISA KEV
    exploit_code:      bool = False
    exploit_maturity:  str = "unproven"           # unproven|poc|functional|weaponized
    attack_vector:     str = ""
    attack_complexity: str = ""
    privileges_req:    str = ""
    user_interaction:  str = ""
    scope:             str = ""
    techniques_map:    List[str] = field(default_factory=list)  # ATT&CK tech IDs


@dataclass
class ExploitNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.EXPLOIT
    cve_id:            str = ""
    exploit_type:      str = ""             # poc | metasploit | weaponized | 0day
    reliability:       str = ""             # low | medium | high
    platform:          str = ""
    language:          str = ""
    source_url:        str = ""
    published:         Optional[datetime] = None
    verified:          bool = False


@dataclass
class CWENode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.CWE
    cwe_id:            str = ""
    weakness_type:     str = ""
    abstraction:       str = ""    # pillar | class | base | variant
    platform:          List[str] = field(default_factory=list)
    common_consequences: List[str] = field(default_factory=list)
    detection_methods: List[str] = field(default_factory=list)
    mitigations:       List[str] = field(default_factory=list)
    parent_cwe:        Optional[str] = None


# ──────────────────────────────────────────────
# ATTACK KNOWLEDGE NODES
# ──────────────────────────────────────────────

@dataclass
class TacticNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.TACTIC
    tactic_id:         str = ""       # TA0001-TA0040
    short_name:        str = ""
    kill_chain_phase:  int = 0        # 1–14
    technique_count:   int = 0


@dataclass
class TechniqueNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.TECHNIQUE
    technique_id:      str = ""       # T1xxx
    tactic_ids:        List[str] = field(default_factory=list)
    platforms:         List[str] = field(default_factory=list)
    permissions_req:   List[str] = field(default_factory=list)
    data_sources:      List[str] = field(default_factory=list)
    defenses_bypassed: List[str] = field(default_factory=list)
    sub_techniques:    List[str] = field(default_factory=list)
    detection_guidance: str = ""
    mitigation_ids:    List[str] = field(default_factory=list)
    exploit_count:     int = 0
    usage_in_wild:     bool = False
    prevalence_score:  float = 0.0    # 0.0–1.0, how commonly observed


@dataclass
class SubTechniqueNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.SUB_TECHNIQUE
    sub_technique_id:  str = ""       # T1xxx.xxx
    parent_technique:  str = ""       # T1xxx
    tactic_ids:        List[str] = field(default_factory=list)
    platforms:         List[str] = field(default_factory=list)
    detection_guidance: str = ""


# ──────────────────────────────────────────────
# DEFENSE KNOWLEDGE NODES
# ──────────────────────────────────────────────

@dataclass
class DetectionRuleNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.DETECTION_RULE
    rule_type:         DetectionRuleType = DetectionRuleType.SIGMA
    rule_id:           str = ""
    rule_content:      str = ""        # Full rule text
    techniques_covered: List[str] = field(default_factory=list)
    platforms:         List[str] = field(default_factory=list)
    log_sources:       List[str] = field(default_factory=list)
    false_positive_rate: float = 0.0
    true_positive_rate:  float = 0.0
    severity_level:    str = "medium"
    status:            str = "stable"  # experimental|test|stable|deprecated
    author:            str = ""
    license:           str = ""


@dataclass
class SecurityControlNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.SECURITY_CONTROL
    control_id:        str = ""
    framework:         str = ""         # NIST | ISO27001 | CIS | SOC2 | PCI-DSS
    category:          str = ""
    implementation_groups: List[str] = field(default_factory=list)
    techniques_mitigated: List[str] = field(default_factory=list)
    implementation_cost: str = ""       # low | medium | high
    effectiveness:     float = 0.0
    automation_level:  str = ""         # manual | partial | full
    mapped_controls:   Dict[str, str] = field(default_factory=dict)   # framework→control_id


@dataclass
class ArchitecturePatternNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.ARCHITECTURE
    pattern_type:      str = ""         # zero_trust | defense_in_depth | microsegmentation
    applicable_domains: List[str] = field(default_factory=list)
    components:        List[str] = field(default_factory=list)
    addresses_threats: List[str] = field(default_factory=list)
    maturity_level:    str = ""         # initial | managed | defined | optimized
    reference_implementations: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────
# COMPLIANCE NODES
# ──────────────────────────────────────────────

@dataclass
class ComplianceFrameworkNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.FRAMEWORK
    framework_id:      str = ""
    version:           str = ""
    issuing_body:      str = ""
    jurisdiction:      List[str] = field(default_factory=list)
    mandatory:         bool = False
    sector:            List[str] = field(default_factory=list)
    total_controls:    int = 0
    last_updated:      Optional[datetime] = None


@dataclass
class IncidentNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.INCIDENT
    incident_type:     str = ""
    victim_sector:     str = ""
    victim_country:    str = ""
    attack_vector:     str = ""
    techniques_used:   List[str] = field(default_factory=list)
    impact_type:       List[str] = field(default_factory=list)
    economic_loss_usd: Optional[float] = None
    records_exposed:   Optional[int] = None
    attributed_actor:  Optional[str] = None
    occurred_at:       Optional[datetime] = None
    disclosed_at:      Optional[datetime] = None
    contained_at:      Optional[datetime] = None
    dwell_time_days:   Optional[int] = None
    source_url:        str = ""


# ──────────────────────────────────────────────
# INDICATOR NODES
# ──────────────────────────────────────────────

@dataclass
class IOCNode(KnowledgeNode):
    node_type:         KnowledgeNodeType = KnowledgeNodeType.IOC
    ioc_type:          str = ""         # hash | ip | domain | url | email | cert
    value:             str = ""
    confidence:        ConfidenceLevel = ConfidenceLevel.MEDIUM
    first_seen:        Optional[datetime] = None
    last_seen:         Optional[datetime] = None
    active:            bool = True
    malware_family:    Optional[str] = None
    campaign:          Optional[str] = None
    threat_actor:      Optional[str] = None
    tlp:               TLPMarking = TLPMarking.AMBER
    sources:           List[str] = field(default_factory=list)
    kill_chain_phases: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────
# KNOWLEDGE EDGE
# ──────────────────────────────────────────────

@dataclass
class KnowledgeEdge:
    edge_id:     str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id:   str = ""
    target_id:   str = ""
    edge_type:   str = ""
    confidence:  ConfidenceLevel = ConfidenceLevel.HIGH
    weight:      float = 1.0
    sources:     List[str] = field(default_factory=list)
    stix_rel_id: Optional[str] = None
    created_at:  datetime = field(default_factory=datetime.utcnow)
    metadata:    Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────
# SEMANTIC SEARCH RESULT
# ──────────────────────────────────────────────

@dataclass
class SemanticSearchResult:
    node_id:       str = ""
    node_type:     str = ""
    name:          str = ""
    description:   str = ""
    similarity:    float = 0.0      # Cosine similarity 0.0–1.0
    graph_score:   float = 0.0      # Graph centrality score
    combined_score: float = 0.0     # Hybrid ranking score
    highlights:    List[str] = field(default_factory=list)
    related_ids:   List[str] = field(default_factory=list)


# ──────────────────────────────────────────────
# KNOWLEDGE MAP
# ──────────────────────────────────────────────

@dataclass
class KnowledgeMap:
    """
    A curated subgraph of the knowledge universe focused
    on a specific threat, actor, campaign, or security domain.
    """
    map_id:      str = field(default_factory=lambda: str(uuid.uuid4()))
    title:       str = ""
    description: str = ""
    focus_type:  str = ""        # threat_actor | campaign | technique | domain
    focus_id:    str = ""        # The central node_id
    nodes:       List[str] = field(default_factory=list)   # node_ids
    edges:       List[str] = field(default_factory=list)   # edge_ids
    depth:       int = 3
    node_count:  int = 0
    edge_count:  int = 0
    generated_at: datetime = field(default_factory=datetime.utcnow)
    metadata:    Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────
# INFERENCE RULE
# ──────────────────────────────────────────────

@dataclass
class InferenceRule:
    """
    Forward-chaining inference rule for the knowledge universe.
    Example: if ThreatActor uses Technique AND Technique exploits CVE
             THEN ThreatActor is likely to exploit CVE.
    """
    rule_id:         str = field(default_factory=lambda: str(uuid.uuid4()))
    name:            str = ""
    description:     str = ""
    premise_pattern: List[Dict[str, str]] = field(default_factory=list)
    conclusion:      Dict[str, str] = field(default_factory=dict)
    confidence:      float = 0.8
    enabled:         bool = True
    fire_count:      int = 0


# ──────────────────────────────────────────────
# ONTOLOGY CONCEPT (OWL-inspired)
# ──────────────────────────────────────────────

@dataclass
class OntologyConcept:
    concept_id:   str = field(default_factory=lambda: str(uuid.uuid4()))
    name:         str = ""
    parent:       Optional[str] = None
    properties:   List[str] = field(default_factory=list)
    restrictions: List[str] = field(default_factory=list)
    equivalent_to: List[str] = field(default_factory=list)
    disjoint_with: List[str] = field(default_factory=list)
    axioms:       List[str] = field(default_factory=list)


# ──────────────────────────────────────────────
# NEO4J SCHEMA FOR KNOWLEDGE UNIVERSE
# ──────────────────────────────────────────────
KNOWLEDGE_NEO4J_SCHEMA = """
// === CONSTRAINTS ===
CREATE CONSTRAINT ku_node_id     IF NOT EXISTS FOR (n:KnowledgeNode) REQUIRE n.node_id IS UNIQUE;
CREATE CONSTRAINT ku_cve_id      IF NOT EXISTS FOR (c:CVE)           REQUIRE c.cve_id IS UNIQUE;
CREATE CONSTRAINT ku_cwe_id      IF NOT EXISTS FOR (c:CWE)           REQUIRE c.cwe_id IS UNIQUE;
CREATE CONSTRAINT ku_technique   IF NOT EXISTS FOR (t:Technique)     REQUIRE t.technique_id IS UNIQUE;
CREATE CONSTRAINT ku_tactic      IF NOT EXISTS FOR (t:Tactic)        REQUIRE t.tactic_id IS UNIQUE;
CREATE CONSTRAINT ku_actor       IF NOT EXISTS FOR (a:ThreatActor)   REQUIRE a.node_id IS UNIQUE;
CREATE CONSTRAINT ku_rule        IF NOT EXISTS FOR (r:DetectionRule)  REQUIRE r.rule_id IS UNIQUE;
CREATE CONSTRAINT ku_framework   IF NOT EXISTS FOR (f:Framework)      REQUIRE f.framework_id IS UNIQUE;

// === INDEXES ===
CREATE INDEX ku_node_type    IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.node_type);
CREATE INDEX ku_cve_cvss     IF NOT EXISTS FOR (c:CVE)           ON (c.cvss_v3_score);
CREATE INDEX ku_cve_kev      IF NOT EXISTS FOR (c:CVE)           ON (c.kev_listed);
CREATE INDEX ku_cve_wild     IF NOT EXISTS FOR (c:CVE)           ON (c.exploited_in_wild);
CREATE INDEX ku_cve_epss     IF NOT EXISTS FOR (c:CVE)           ON (c.epss_score);
CREATE INDEX ku_technique_id IF NOT EXISTS FOR (t:Technique)     ON (t.technique_id);
CREATE INDEX ku_actor_type   IF NOT EXISTS FOR (a:ThreatActor)   ON (a.actor_type);
CREATE INDEX ku_actor_state  IF NOT EXISTS FOR (a:ThreatActor)   ON (a.nation_state);
CREATE INDEX ku_malware_type IF NOT EXISTS FOR (m:Malware)       ON (m.malware_type);
CREATE INDEX ku_ioc_type     IF NOT EXISTS FOR (i:IOC)           ON (i.ioc_type);
CREATE INDEX ku_rule_type    IF NOT EXISTS FOR (r:DetectionRule)  ON (r.rule_type);
CREATE VECTOR INDEX ku_embedding IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.embedding)
    OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}};

// === SAMPLE: MITRE ATT&CK SKELETON ===
CREATE (ta_recon:Tactic {
    tactic_id: 'TA0043', name: 'Reconnaissance',
    short_name: 'recon', kill_chain_phase: 1, technique_count: 10
});
CREATE (ta_init:Tactic {
    tactic_id: 'TA0001', name: 'Initial Access',
    short_name: 'initial-access', kill_chain_phase: 3, technique_count: 9
});
CREATE (t_phish:Technique {
    technique_id: 'T1566', name: 'Phishing',
    node_type: 'technique', usage_in_wild: true, prevalence_score: 0.92
});
CREATE (t_phish_sp:SubTechnique {
    sub_technique_id: 'T1566.001', name: 'Spearphishing Attachment',
    parent_technique: 'T1566'
});
CREATE (apt29:ThreatActor {
    node_id: 'ta-apt29', name: 'APT29',
    aliases: ['Cozy Bear', 'The Dukes', 'NOBELIUM'],
    actor_type: 'nation_state', nation_state: 'Russia',
    sophistication: 'expert', threat_score: 0.97
});
CREATE (cve_log4j:CVE {
    node_id: 'cve-cve-2021-44228',
    cve_id: 'CVE-2021-44228',
    cvss_v3_score: 10.0, severity: 'critical',
    exploited_in_wild: true, kev_listed: true,
    epss_score: 0.97614
});
CREATE (sigma_log4j:DetectionRule {
    rule_id: 'sigma-log4j-001',
    rule_type: 'sigma',
    name: 'Log4j JNDI Exploitation Attempt'
});
// Relationships
MATCH (ta:Tactic {tactic_id:'TA0001'}), (t:Technique {technique_id:'T1566'})
CREATE (t)-[:PART_OF]->(ta);
MATCH (t:Technique {technique_id:'T1566'}), (st:SubTechnique {sub_technique_id:'T1566.001'})
CREATE (st)-[:PART_OF]->(t);
MATCH (a:ThreatActor {node_id:'ta-apt29'}), (t:Technique {technique_id:'T1566'})
CREATE (a)-[:USES {confidence:'confirmed'}]->(t);
MATCH (r:DetectionRule {rule_id:'sigma-log4j-001'}), (c:CVE {cve_id:'CVE-2021-44228'})
CREATE (r)-[:DETECTS {coverage:'partial'}]->(c);
"""
