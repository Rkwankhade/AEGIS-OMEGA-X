from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class SemanticSearchResult(BaseModel):
    node_id: str
    node_type: str
    title: str
    summary: Optional[str] = None
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    semantic_distance: Optional[float] = None
    source: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class KnowledgeMapNode(BaseModel):
    node_id: str
    node_type: str
    label: str
    weight: float = Field(default=1.0, ge=0.0)
    cluster: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeMapEdge(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str
    weight: float = Field(default=1.0, ge=0.0)
    directed: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeMap(BaseModel):
    map_id: Optional[str] = None
    query: Optional[str] = None
    generated_at: Optional[datetime] = None
    nodes: List[KnowledgeMapNode] = Field(default_factory=list)
    edges: List[KnowledgeMapEdge] = Field(default_factory=list)
    clusters: Dict[str, List[str]] = Field(default_factory=dict)
    total_nodes: int = 0
    total_edges: int = 0
    coverage_score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
