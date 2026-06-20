"""
AEGIS OMEGA X — MEGA LAYER 1
PLANETARY DIGITAL TWIN — PURE-PYTHON SIMULATION ENGINE

Provides the in-process, dependency-free simulation classes used by
unit tests and the FastAPI cascade endpoint.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class SimStatus(str, Enum):
    Nominal     = "nominal"
    Degraded    = "degraded"
    Compromised = "compromised"
    Failed      = "failed"
    Recovering  = "recovering"


@dataclass
class AssetState:
    asset_id:     str
    entity_id:    str
    status:       SimStatus = SimStatus.Nominal
    risk_score:   float     = 0.0
    last_updated: datetime  = field(default_factory=datetime.utcnow)


@dataclass
class CascadeEvent:
    event_id:         str           = field(default_factory=lambda: str(uuid.uuid4()))
    origin_asset_id:  str           = ""
    propagation_path: List[str]     = field(default_factory=list)
    affected_assets:  List[str]     = field(default_factory=list)
    severity:         float         = 1.0
    tick_started:     int           = 0
    tick_contained:   Optional[int] = None


@dataclass
class PlanetarySimulationState:
    assets:             Dict[str, AssetState] = field(default_factory=dict)
    relationship_graph: Dict[str, List[str]]  = field(default_factory=dict)
    active_cascades:    List[CascadeEvent]    = field(default_factory=list)
    tick:               int                   = 0


class CascadeEngine:
    @staticmethod
    def propagate(
        state: PlanetarySimulationState,
        cascade: CascadeEvent,
        propagation_probability: float = 0.3,
    ) -> None:
        newly_affected: List[str] = []

        for src_id in list(cascade.affected_assets):
            for nbr_id in state.relationship_graph.get(src_id, []):
                if nbr_id in cascade.affected_assets:
                    continue
                if random.random() < propagation_probability:
                    newly_affected.append(nbr_id)
                    if nbr_id in state.assets:
                        state.assets[nbr_id].status = SimStatus.Compromised
                        state.assets[nbr_id].risk_score = min(
                            1.0,
                            state.assets[nbr_id].risk_score + cascade.severity * 0.2,
                        )

        for aid in newly_affected:
            if aid not in cascade.affected_assets:
                cascade.affected_assets.append(aid)
            if aid not in cascade.propagation_path:
                cascade.propagation_path.append(aid)

        state.tick += 1


class RiskEngine:
    @staticmethod
    def recompute_all(state: PlanetarySimulationState) -> None:
        cascade_assets: Dict[str, float] = {}
        for ev in state.active_cascades:
            for aid in ev.affected_assets:
                cascade_assets[aid] = max(cascade_assets.get(aid, 0.0), ev.severity)

        for aid, asset in state.assets.items():
            if aid in cascade_assets:
                asset.risk_score = min(1.0, asset.risk_score + cascade_assets[aid] * 0.1)
            asset.risk_score = max(0.0, min(1.0, asset.risk_score))
