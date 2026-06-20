from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MutationType(str, Enum):
    VULNERABILITY_INTRODUCED = "vulnerability_introduced"
    VULNERABILITY_PATCHED = "vulnerability_patched"
    CONFIGURATION_CHANGED = "configuration_changed"
    IDENTITY_MODIFIED = "identity_modified"
    NETWORK_TOPOLOGY_CHANGED = "network_topology_changed"
    CONTROL_ADDED = "control_added"
    CONTROL_REMOVED = "control_removed"
    THREAT_DETECTED = "threat_detected"
    RISK_SCORE_CHANGED = "risk_score_changed"
    ASSET_ADDED = "asset_added"
    ASSET_REMOVED = "asset_removed"

class SecurityDNA(BaseModel):
    entity_id: str
    entity_type: str
    domain: Optional[str] = None
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    vulnerability_count: int = Field(default=0, ge=0)
    critical_vulns: int = Field(default=0, ge=0)
    control_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    identity_risk: float = Field(default=0.0, ge=0.0, le=100.0)
    network_exposure: float = Field(default=0.0, ge=0.0, le=1.0)
    patch_compliance: float = Field(default=0.0, ge=0.0, le=1.0)
    threat_intelligence_hits: int = Field(default=0, ge=0)
    mutation_rate: float = Field(default=0.0, ge=0.0)
    genome_hash: Optional[str] = None
    last_sequenced: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ResilienceSnapshot(BaseModel):
    entity_id: str
    snapshot_time: Optional[datetime] = None
    overall_resilience: float = Field(default=0.0, ge=0.0, le=100.0)
    detection_capability: float = Field(default=0.0, ge=0.0, le=1.0)
    response_capability: float = Field(default=0.0, ge=0.0, le=1.0)
    recovery_capability: float = Field(default=0.0, ge=0.0, le=1.0)
    prevention_capability: float = Field(default=0.0, ge=0.0, le=1.0)
    threat_landscape_score: float = Field(default=0.0, ge=0.0, le=100.0)
    business_impact_score: float = Field(default=0.0, ge=0.0, le=100.0)
    trend: Optional[str] = None
    contributing_factors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class GenomeDiff(BaseModel):
    diff_id: Optional[str] = None
    entity_id: str
    from_snapshot: Optional[str] = None
    to_snapshot: Optional[str] = None
    diff_time: Optional[datetime] = None
    mutation_type: MutationType
    field_changed: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    delta: Optional[float] = None
    severity: Optional[str] = None
    triggered_by: Optional[str] = None
    auto_remediated: bool = False
    notes: Optional[str] = None
