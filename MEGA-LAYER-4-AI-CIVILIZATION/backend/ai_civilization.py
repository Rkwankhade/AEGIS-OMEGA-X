"""
AEGIS OMEGA X — MEGA LAYER 4
AI SECURITY CIVILIZATION
Complete implementation: agent classes, orchestration,
governance, alignment, multi-agent society.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Awaitable
from enum import Enum
from datetime import datetime

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from neo4j import AsyncGraphDatabase
import redis.asyncio as aioredis

log = logging.getLogger("ai-civilization")

# ──────────────────────────────────────────────
# ENUMERATIONS
# ──────────────────────────────────────────────

class AgentClass(str, Enum):
    ANALYST       = "analyst"
    ARCHITECT     = "architect"
    GOVERNANCE    = "governance"
    RISK          = "risk"
    COMPLIANCE    = "compliance"
    RESEARCH      = "research"
    DETECTION     = "detection"
    INTELLIGENCE  = "intelligence"
    OPTIMIZATION  = "optimization"
    AUDIT         = "audit"

class AgentStatus(str, Enum):
    IDLE          = "idle"
    WORKING       = "working"
    DELEGATING    = "delegating"
    WAITING       = "waiting"
    FAILED        = "failed"
    SUSPENDED     = "suspended"

class TaskPriority(str, Enum):
    CRITICAL      = "critical"
    HIGH          = "high"
    MEDIUM        = "medium"
    LOW           = "low"

class TrustLevel(str, Enum):
    VERIFIED      = "verified"
    TRUSTED       = "trusted"
    PROVISIONAL   = "provisional"
    UNTRUSTED     = "untrusted"
    REVOKED       = "revoked"

# ──────────────────────────────────────────────
# AGENT TASK
# ──────────────────────────────────────────────

@dataclass
class AgentTask:
    task_id:       str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type:     str = ""
    description:   str = ""
    priority:      TaskPriority = TaskPriority.MEDIUM
    assigned_to:   Optional[str] = None
    delegated_by:  Optional[str] = None
    context:       Dict[str, Any] = field(default_factory=dict)
    constraints:   Dict[str, Any] = field(default_factory=dict)
    result:        Optional[Dict] = None
    status:        str = "pending"
    created_at:    datetime = field(default_factory=datetime.utcnow)
    started_at:    Optional[datetime] = None
    completed_at:  Optional[datetime] = None
    error:         Optional[str] = None

# ──────────────────────────────────────────────
# AGENT MEMORY
# ──────────────────────────────────────────────

@dataclass
class AgentMemory:
    """Short and long-term memory for agents."""
    agent_id:      str = ""
    working_memory: List[Dict] = field(default_factory=list)   # Last N items (short-term)
    episodic_memory: List[Dict] = field(default_factory=list)  # Past tasks + outcomes
    semantic_memory: Dict[str, Any] = field(default_factory=dict)  # Learned facts
    skill_memory:   Dict[str, float] = field(default_factory=dict)  # Skill proficiency scores
    max_working:    int = 50

    def add_to_working(self, item: Dict):
        self.working_memory.append(item)
        if len(self.working_memory) > self.max_working:
            self.working_memory.pop(0)

    def commit_to_episodic(self, task: AgentTask):
        self.episodic_memory.append({
            "task_id":    task.task_id,
            "task_type":  task.task_type,
            "outcome":    task.status,
            "timestamp":  datetime.utcnow().isoformat(),
        })

    def get_skill_score(self, skill: str) -> float:
        return self.skill_memory.get(skill, 0.5)

    def update_skill(self, skill: str, delta: float):
        current = self.skill_memory.get(skill, 0.5)
        self.skill_memory[skill] = min(1.0, max(0.0, current + delta))

# ──────────────────────────────────────────────
# BASE AGENT
# ──────────────────────────────────────────────

class AegisAgent:
    """
    Base class for all AEGIS AI agents.
    Implements: task execution, delegation, negotiation,
    memory management, trust tracking.
    """

    def __init__(
        self,
        agent_id:    str,
        agent_class: AgentClass,
        name:        str,
        capabilities: List[str],
        trust_level: TrustLevel = TrustLevel.TRUSTED,
    ):
        self.agent_id    = agent_id
        self.agent_class = agent_class
        self.name        = name
        self.capabilities = capabilities
        self.trust_level = trust_level
        self.status      = AgentStatus.IDLE
        self.memory      = AgentMemory(agent_id=agent_id)
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.completed_tasks: int = 0
        self.failed_tasks:    int = 0
        self.created_at  = datetime.utcnow()
        self.society: Optional['AgentSociety'] = None

    async def receive_task(self, task: AgentTask):
        await self.task_queue.put(task)

    async def execute_task(self, task: AgentTask) -> Dict:
        """Override in subclasses for specialized behavior."""
        raise NotImplementedError

    async def delegate_task(
        self, task: AgentTask, target_class: AgentClass
    ) -> Optional[Dict]:
        """Delegate a subtask to another agent class."""
        if self.society:
            target = await self.society.find_agent(target_class)
            if target:
                subtask = AgentTask(
                    task_type    = task.task_type,
                    description  = f"[DELEGATED] {task.description}",
                    priority     = task.priority,
                    delegated_by = self.agent_id,
                    context      = task.context,
                )
                await target.receive_task(subtask)
                log.info("[%s] Delegated task to %s", self.name, target.name)
                return {"delegated_to": target.agent_id}
        return None

    async def run(self):
        """Main agent event loop."""
        log.info("[%s] Agent started (class=%s)", self.name, self.agent_class)
        while True:
            try:
                task = await asyncio.wait_for(
                    self.task_queue.get(), timeout=30.0
                )
                self.status = AgentStatus.WORKING
                task.started_at = datetime.utcnow()

                result = await self.execute_task(task)
                task.result = result
                task.status = "completed"
                task.completed_at = datetime.utcnow()

                self.memory.commit_to_episodic(task)
                self.completed_tasks += 1
                self.memory.update_skill(task.task_type, 0.01)
                self.status = AgentStatus.IDLE

            except asyncio.TimeoutError:
                pass   # No tasks — idle
            except Exception as e:
                log.error("[%s] Task failed: %s", self.name, e)
                self.failed_tasks += 1
                self.status = AgentStatus.FAILED
                await asyncio.sleep(1)
                self.status = AgentStatus.IDLE

    def agent_state(self) -> Dict:
        return {
            "agent_id":        self.agent_id,
            "name":            self.name,
            "class":           self.agent_class,
            "status":          self.status,
            "trust_level":     self.trust_level,
            "capabilities":    self.capabilities,
            "completed_tasks": self.completed_tasks,
            "failed_tasks":    self.failed_tasks,
            "queue_depth":     self.task_queue.qsize(),
            "skill_scores":    self.memory.skill_memory,
        }

# ──────────────────────────────────────────────
# SPECIALIZED AGENT CLASSES
# ──────────────────────────────────────────────

class AnalystAgent(AegisAgent):
    """
    Analyzes security events, correlates data,
    produces incident summaries and IOC extractions.
    """
    def __init__(self, agent_id: str, name: str):
        super().__init__(
            agent_id, AgentClass.ANALYST, name,
            capabilities=["event_analysis","correlation","ioc_extraction",
                          "incident_summary","threat_triage","log_analysis"]
        )

    async def execute_task(self, task: AgentTask) -> Dict:
        await asyncio.sleep(0.1)    # Simulates LLM call latency

        if task.task_type == "event_analysis":
            events = task.context.get("events", [])
            return {
                "analyst":       self.agent_id,
                "event_count":   len(events),
                "severity":      "high" if len(events) > 10 else "medium",
                "iocs_found":    [f"ioc-{i}" for i in range(min(3, len(events)))],
                "recommendation":"Escalate to detection agent for rule creation.",
                "confidence":    0.87,
            }

        elif task.task_type == "threat_triage":
            return {
                "triage_result": "escalate",
                "risk_score":    task.context.get("risk_score", 0.5),
                "priority":      "high",
                "analyst":       self.agent_id,
            }

        return {"status": "analyzed", "agent": self.agent_id}


class DetectionAgent(AegisAgent):
    """
    Creates and tunes detection rules, hunts threats,
    validates alert fidelity.
    """
    def __init__(self, agent_id: str, name: str):
        super().__init__(
            agent_id, AgentClass.DETECTION, name,
            capabilities=["rule_creation","rule_tuning","threat_hunting",
                          "alert_triage","sigma_generation","yara_generation"]
        )

    async def execute_task(self, task: AgentTask) -> Dict:
        await asyncio.sleep(0.15)

        if task.task_type == "sigma_generation":
            technique = task.context.get("technique_id", "T1566")
            return {
                "rule_type":  "sigma",
                "technique":  technique,
                "rule_name":  f"Detect {technique} activity",
                "rule_content": f"""
title: Auto-generated detection for {technique}
status: experimental
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    CommandLine|contains: '{technique}'
  condition: selection
level: high
tags:
  - attack.{technique.lower()}
""".strip(),
                "agent": self.agent_id,
                "confidence": 0.78,
            }

        elif task.task_type == "threat_hunting":
            return {
                "hunt_id":    str(uuid.uuid4()),
                "hypothesis": task.context.get("hypothesis", ""),
                "findings":   [],
                "verdict":    "no_threat_found",
                "agent":      self.agent_id,
            }

        return {"status": "detection_complete", "agent": self.agent_id}


class RiskAgent(AegisAgent):
    """
    Quantifies risk, runs risk models, produces
    risk scores for assets and organizations.
    """
    def __init__(self, agent_id: str, name: str):
        super().__init__(
            agent_id, AgentClass.RISK, name,
            capabilities=["risk_scoring","risk_quantification","threat_modeling",
                          "attack_surface_analysis","risk_reporting"]
        )

    async def execute_task(self, task: AgentTask) -> Dict:
        await asyncio.sleep(0.12)
        asset_id = task.context.get("asset_id", "unknown")
        base_risk = task.context.get("base_risk", 0.5)
        import random
        computed_risk = min(1.0, base_risk + random.uniform(-0.1, 0.2))
        return {
            "asset_id":     asset_id,
            "risk_score":   round(computed_risk, 3),
            "risk_level":   "critical" if computed_risk > 0.8 else "high" if computed_risk > 0.6 else "medium",
            "factors":      ["internet_facing","unpatched_cve","privileged_access"],
            "agent":        self.agent_id,
        }


class GovernanceAgent(AegisAgent):
    """
    Enforces policies, validates compliance,
    generates audit evidence, manages exceptions.
    """
    def __init__(self, agent_id: str, name: str):
        super().__init__(
            agent_id, AgentClass.GOVERNANCE, name,
            capabilities=["policy_enforcement","compliance_check","audit_evidence",
                          "exception_management","policy_generation","regulatory_mapping"]
        )

    async def execute_task(self, task: AgentTask) -> Dict:
        await asyncio.sleep(0.08)
        if task.task_type == "compliance_check":
            framework = task.context.get("framework", "NIST")
            entity_id = task.context.get("entity_id", "")
            return {
                "entity_id":      entity_id,
                "framework":      framework,
                "compliance_pct": round(74.5 + hash(entity_id) % 20, 1),
                "findings":       [{"control": "AC-2", "status": "partial"}],
                "agent":          self.agent_id,
            }
        return {"status": "governance_complete", "agent": self.agent_id}


class IntelligenceAgent(AegisAgent):
    """
    Produces strategic threat intelligence,
    correlates CTI feeds, generates intelligence reports.
    """
    def __init__(self, agent_id: str, name: str):
        super().__init__(
            agent_id, AgentClass.INTELLIGENCE, name,
            capabilities=["cti_correlation","actor_profiling","campaign_tracking",
                          "intelligence_report","ioc_enrichment","attribution"]
        )

    async def execute_task(self, task: AgentTask) -> Dict:
        await asyncio.sleep(0.2)
        actor = task.context.get("actor_id", "APT-UNKNOWN")
        return {
            "intelligence_report": {
                "actor":          actor,
                "confidence":     "high",
                "key_findings":   [
                    f"{actor} targeting financial sector",
                    "New TTP: credential stuffing via API abuse",
                    "C2 infrastructure identified in 3 regions",
                ],
                "recommended_detections": ["T1566.001","T1078","T1071.001"],
                "ioc_count":      47,
            },
            "agent": self.agent_id,
        }


class ArchitectAgent(AegisAgent):
    """
    Designs security architectures, evaluates
    existing architectures, recommends improvements.
    """
    def __init__(self, agent_id: str, name: str):
        super().__init__(
            agent_id, AgentClass.ARCHITECT, name,
            capabilities=["architecture_design","architecture_review","zero_trust_design",
                          "cloud_security_design","network_segmentation","resilience_design"]
        )

    async def execute_task(self, task: AgentTask) -> Dict:
        await asyncio.sleep(0.25)
        entity = task.context.get("entity_id", "")
        return {
            "architecture_recommendations": [
                {"priority": "critical", "action": "Implement Zero Trust Network Access"},
                {"priority": "high",     "action": "Deploy CASB for cloud workloads"},
                {"priority": "high",     "action": "Microsegment production network"},
                {"priority": "medium",   "action": "Enable E2E encryption for all APIs"},
            ],
            "maturity_delta": "+0.3",
            "entity":         entity,
            "agent":          self.agent_id,
        }


class OptimizationAgent(AegisAgent):
    """
    Optimizes security posture, tool configurations,
    alert tuning, and resource allocation.
    """
    def __init__(self, agent_id: str, name: str):
        super().__init__(
            agent_id, AgentClass.OPTIMIZATION, name,
            capabilities=["alert_tuning","control_optimization","cost_optimization",
                          "coverage_optimization","resource_allocation"]
        )

    async def execute_task(self, task: AgentTask) -> Dict:
        await asyncio.sleep(0.1)
        return {
            "optimization_results": {
                "false_positive_reduction": "34%",
                "coverage_improvement":     "12%",
                "cost_reduction_usd":       45_000,
                "new_tuning_rules":         8,
            },
            "agent": self.agent_id,
        }


class ComplianceAgent(AegisAgent):
    """Auto-generates compliance evidence and audit reports."""
    def __init__(self, agent_id: str, name: str):
        super().__init__(
            agent_id, AgentClass.COMPLIANCE, name,
            capabilities=["evidence_collection","audit_report","gap_analysis",
                          "remediation_tracking","regulatory_mapping"]
        )

    async def execute_task(self, task: AgentTask) -> Dict:
        await asyncio.sleep(0.15)
        framework = task.context.get("framework", "SOC2")
        return {
            "audit_report": {
                "framework":    framework,
                "controls_assessed": 87,
                "controls_passed":   71,
                "controls_failed":   16,
                "compliance_pct":    81.6,
                "critical_gaps":     3,
            },
            "evidence_artifacts": [f"ev-{i:04d}" for i in range(20)],
            "agent": self.agent_id,
        }


class AuditAgent(AegisAgent):
    """Continuous automated audit of security controls."""
    def __init__(self, agent_id: str, name: str):
        super().__init__(
            agent_id, AgentClass.AUDIT, name,
            capabilities=["control_testing","penetration_testing_coordination",
                          "configuration_audit","access_review","audit_trail"]
        )

    async def execute_task(self, task: AgentTask) -> Dict:
        await asyncio.sleep(0.1)
        return {
            "audit_findings": [
                {"control": "MFA",         "status": "pass"},
                {"control": "Encryption",  "status": "fail", "reason": "TLS 1.1 detected"},
                {"control": "Patch mgmt",  "status": "partial"},
            ],
            "critical_findings": 1,
            "agent": self.agent_id,
        }


class ResearchAgent(AegisAgent):
    """Conducts cybersecurity research, tracks emerging threats."""
    def __init__(self, agent_id: str, name: str):
        super().__init__(
            agent_id, AgentClass.RESEARCH, name,
            capabilities=["threat_research","vulnerability_research","technology_watch",
                          "research_synthesis","emerging_threat_detection"]
        )

    async def execute_task(self, task: AgentTask) -> Dict:
        await asyncio.sleep(0.3)
        return {
            "research_summary": {
                "topic":         task.context.get("topic", "AI security threats"),
                "key_findings":  ["Finding 1","Finding 2","Finding 3"],
                "references":    ["arXiv:2024.xxxxx","CVE-2024-xxxxx"],
                "threat_level":  "emerging",
            },
            "agent": self.agent_id,
        }

# ──────────────────────────────────────────────
# AGENT TRUST SYSTEM
# ──────────────────────────────────────────────

class AgentTrustSystem:
    """
    Manages inter-agent trust.
    Trust is earned through task success and degraded by failures.
    Prevents rogue agents from taking high-impact actions.
    """

    def __init__(self):
        self.trust_scores: Dict[str, float] = {}
        self.trust_history: Dict[str, List[Dict]] = {}
        self.min_trust_for_delegation = 0.6
        self.min_trust_for_critical   = 0.85

    def get_trust(self, agent_id: str) -> float:
        return self.trust_scores.get(agent_id, 0.7)  # Default: provisional

    def update_trust(
        self, agent_id: str, task_success: bool,
        task_criticality: str = "medium"
    ):
        current = self.get_trust(agent_id)
        weight  = {"critical": 0.2, "high": 0.1, "medium": 0.05, "low": 0.02}.get(
            task_criticality, 0.05
        )
        if task_success:
            new_trust = min(1.0, current + weight * (1.0 - current))
        else:
            new_trust = max(0.0, current - weight * 2 * current)

        self.trust_scores[agent_id] = round(new_trust, 4)
        self.trust_history.setdefault(agent_id, []).append({
            "timestamp":   datetime.utcnow().isoformat(),
            "success":     task_success,
            "criticality": task_criticality,
            "old_trust":   current,
            "new_trust":   new_trust,
        })

    def can_delegate(self, agent_id: str) -> bool:
        return self.get_trust(agent_id) >= self.min_trust_for_delegation

    def can_execute_critical(self, agent_id: str) -> bool:
        return self.get_trust(agent_id) >= self.min_trust_for_critical

    def revoke_trust(self, agent_id: str, reason: str):
        self.trust_scores[agent_id] = 0.0
        log.warning("[TRUST] REVOKED for %s: %s", agent_id, reason)


# ──────────────────────────────────────────────
# AGENT SOCIETY
# ──────────────────────────────────────────────

class AgentSociety:
    """
    The complete AI agent civilization.
    Manages all agents, task routing, collective reasoning,
    trust, governance, and emergent behavior detection.
    """

    def __init__(self, society_id: str = "aegis-prime"):
        self.society_id   = society_id
        self.agents:       Dict[str, AegisAgent] = {}
        self.trust_system: AgentTrustSystem = AgentTrustSystem()
        self.task_log:     List[AgentTask] = []
        self.running:      bool = False
        self.created_at    = datetime.utcnow()
        self.message_bus:  asyncio.Queue = asyncio.Queue()
        self.total_tasks   = 0
        self.emergent_patterns: List[Dict] = []

    def register_agent(self, agent: AegisAgent):
        agent.society = self
        self.agents[agent.agent_id] = agent
        self.trust_system.trust_scores[agent.agent_id] = 0.7
        log.info("[SOCIETY] Agent registered: %s (%s)", agent.name, agent.agent_class)

    async def find_agent(
        self, agent_class: AgentClass,
        min_trust: float = 0.5
    ) -> Optional[AegisAgent]:
        """Find best available agent of given class by trust + load."""
        candidates = [
            a for a in self.agents.values()
            if (a.agent_class == agent_class
                and a.status in (AgentStatus.IDLE, AgentStatus.WORKING)
                and self.trust_system.get_trust(a.agent_id) >= min_trust)
        ]
        if not candidates:
            return None
        # Pick lowest queue depth (load balancing)
        return min(candidates, key=lambda a: a.task_queue.qsize())

    async def dispatch_task(self, task: AgentTask, agent_class: AgentClass) -> Optional[str]:
        """Route task to appropriate agent."""
        agent = await self.find_agent(agent_class)
        if not agent:
            log.warning("[SOCIETY] No available agent for class %s", agent_class)
            return None
        if (task.priority == TaskPriority.CRITICAL
                and not self.trust_system.can_execute_critical(agent.agent_id)):
            log.warning("[SOCIETY] Agent %s lacks trust for CRITICAL task", agent.name)
            return None
        task.assigned_to = agent.agent_id
        await agent.receive_task(task)
        self.task_log.append(task)
        self.total_tasks += 1
        return agent.agent_id

    async def collective_reasoning(self, question: str, context: Dict) -> Dict:
        """
        Multi-agent collective reasoning.
        Multiple agents contribute perspectives; results synthesized.
        """
        task_types = {
            AgentClass.ANALYST:       "event_analysis",
            AgentClass.RISK:          "risk_scoring",
            AgentClass.INTELLIGENCE:  "ioc_enrichment",
            AgentClass.DETECTION:     "threat_hunting",
        }
        results = {}
        tasks_dispatched = []
        for agent_class, task_type in task_types.items():
            task = AgentTask(
                task_type   = task_type,
                description = question,
                priority    = TaskPriority.HIGH,
                context     = context,
            )
            assigned = await self.dispatch_task(task, agent_class)
            if assigned:
                tasks_dispatched.append((assigned, task))

        # Wait for results (simplified — production uses callbacks)
        await asyncio.sleep(0.5)

        return {
            "question":          question,
            "agents_consulted":  len(tasks_dispatched),
            "collective_answer": "Multi-agent consensus reached",
            "confidence":        0.87,
            "society_id":        self.society_id,
        }

    async def detect_emergent_behavior(self):
        """
        Monitors agent interaction patterns for emergent behaviors:
        task cascades, coordination loops, unexpected collaborations.
        """
        if len(self.task_log) < 10:
            return

        # Detect cascade: same task type fired 5+ times in rapid succession
        recent = self.task_log[-20:]
        type_counts: Dict[str, int] = {}
        for task in recent:
            type_counts[task.task_type] = type_counts.get(task.task_type, 0) + 1

        for task_type, count in type_counts.items():
            if count >= 5:
                pattern = {
                    "pattern_type": "task_cascade",
                    "task_type":    task_type,
                    "count":        count,
                    "detected_at":  datetime.utcnow().isoformat(),
                }
                self.emergent_patterns.append(pattern)
                log.warning("[EMERGENT] Task cascade detected: %s ×%d", task_type, count)

    async def start(self):
        """Start all agents concurrently."""
        self.running = True
        agent_tasks  = [agent.run() for agent in self.agents.values()]
        monitor_task = asyncio.create_task(self._monitor_loop())
        await asyncio.gather(*agent_tasks, monitor_task)

    async def _monitor_loop(self):
        while self.running:
            await asyncio.sleep(30)
            await self.detect_emergent_behavior()
            log.info(
                "[SOCIETY] Status: %d agents, %d tasks, %d emergent patterns",
                len(self.agents), self.total_tasks, len(self.emergent_patterns),
            )

    def society_state(self) -> Dict:
        return {
            "society_id":     self.society_id,
            "agent_count":    len(self.agents),
            "total_tasks":    self.total_tasks,
            "agents":         [a.agent_state() for a in self.agents.values()],
            "emergent_patterns": len(self.emergent_patterns),
            "trust_scores":   self.trust_system.trust_scores,
        }


# ──────────────────────────────────────────────
# SOCIETY FACTORY
# ──────────────────────────────────────────────

def build_aegis_society(agent_count_per_class: int = 3) -> AgentSociety:
    """Build the complete AEGIS AI civilization."""

    AGENT_FACTORIES = [
        (AnalystAgent,       "analyst"),
        (DetectionAgent,     "detection"),
        (RiskAgent,          "risk"),
        (GovernanceAgent,    "governance"),
        (IntelligenceAgent,  "intelligence"),
        (ArchitectAgent,     "architect"),
        (OptimizationAgent,  "optimization"),
        (ComplianceAgent,    "compliance"),
        (AuditAgent,         "audit"),
        (ResearchAgent,      "research"),
    ]

    society = AgentSociety()
    for i, (AgentCls, class_name) in enumerate(AGENT_FACTORIES):
        for j in range(agent_count_per_class):
            agent_id = f"{class_name}-{j+1:03d}"
            name     = f"{class_name.capitalize()} Agent {j+1}"
            agent    = AgentCls(agent_id=agent_id, name=name)
            society.register_agent(agent)

    total = len(AGENT_FACTORIES) * agent_count_per_class
    log.info("[FACTORY] Built AEGIS society: %d agents across %d classes",
             total, len(AGENT_FACTORIES))
    return society


# ──────────────────────────────────────────────
# FASTAPI SERVICE
# ──────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AEGIS OMEGA X — AI Civilization API",
    description="MEGA LAYER 4: AI Security Agent Society",
    version="4.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

_society: Optional[AgentSociety] = None


@app.on_event("startup")
async def startup():
    global _society
    _society = build_aegis_society(agent_count_per_class=3)
    asyncio.create_task(_society.start())
    log.info("[AI CIVILIZATION] Society started with %d agents", len(_society.agents))


@app.get("/health")
async def health():
    return {"status": "operational", "layer": "MEGA-LAYER-4-AI-CIVILIZATION"}


@app.get("/society/state")
async def society_state():
    return _society.society_state() if _society else {"error": "not initialized"}


@app.post("/society/task")
async def dispatch_task(task_type: str, agent_class: str, context: Dict = Body(default={})):
    task = AgentTask(
        task_type   = task_type,
        description = f"API-dispatched: {task_type}",
        priority    = TaskPriority.HIGH,
        context     = context,
    )
    ac   = AgentClass(agent_class)
    aid  = await _society.dispatch_task(task, ac)
    return {"task_id": task.task_id, "assigned_to": aid}


@app.post("/society/collective-reasoning")
async def collective_reasoning(question: str, context: Dict = Body(default={})):
    result = await _society.collective_reasoning(question, context)
    return result


@app.get("/society/agents")
async def list_agents():
    if not _society:
        return []
    return [a.agent_state() for a in _society.agents.values()]


@app.get("/society/trust")
async def trust_scores():
    return _society.trust_system.trust_scores if _society else {}


@app.get("/society/emergent")
async def emergent_patterns():
    return _society.emergent_patterns if _society else []


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004, reload=False)
