"""AuZoom MCP Tool Schemas - Parameters and responses for all tools."""

from dataclasses import dataclass, field
from typing import Literal, Optional
from .models import FetchLevel, Node, NodeSkeleton, NodeType, SnapshotInfo


# === Navigation ===

@dataclass
class GetGraphParams:
    node_id: str                                    # or "root"
    depth_up: int = 0                               # levels toward root
    depth_down: int = 1                             # levels toward leaves
    fetch_level: FetchLevel = FetchLevel.SKELETON
    include_private: bool = False
    type_filter: Optional[list[NodeType]] = None
    name_pattern: Optional[str] = None


@dataclass
class GetGraphResponse:
    center: Node
    ancestors: list[Node] = field(default_factory=list)
    descendants: list[Node] = field(default_factory=list)
    edges: list = field(default_factory=list)
    total_nodes: int = 0
    truncated: bool = False
    snapshot_id: str = "latest"


@dataclass
class GetDependenciesParams:
    node_id: str
    direction: Literal["incoming", "outgoing", "both"] = "both"
    depth: int = 1
    fetch_level: FetchLevel = FetchLevel.SKELETON


@dataclass
class DependencyChain:
    node: Node
    edge_type: str
    distance: int
    path: list[str] = field(default_factory=list)


@dataclass
class GetDependenciesResponse:
    center: NodeSkeleton
    outgoing: list[DependencyChain] = field(default_factory=list)
    incoming: list[DependencyChain] = field(default_factory=list)


@dataclass
class FindParams:
    query: str
    scope: Optional[str] = None
    type_filter: Optional[list[NodeType]] = None
    fetch_level: FetchLevel = FetchLevel.SKELETON
    limit: int = 20


@dataclass
class FindResponse:
    matches: list[Node]
    total_count: int


# === Visualization ===

@dataclass
class VisualizeParams:
    node_id: str
    depth_up: int = 0
    depth_down: int = 2
    format: Literal["mermaid", "ascii", "svg", "dot"] = "mermaid"
    layout: Literal["hierarchical", "force", "radial"] = "hierarchical"
    show_docstrings: bool = False
    show_signatures: bool = True
    highlight_violations: bool = True
    group_by_module: bool = True


@dataclass
class VisualizeResponse:
    format: str
    content: str
    node_positions: Optional[dict[str, dict[str, float]]] = None


@dataclass
class VisualizeDiffParams:
    from_snapshot: str
    to_snapshot: str = "latest"
    format: Literal["mermaid", "ascii", "svg"] = "mermaid"
    show_added: bool = True
    show_removed: bool = True
    show_modified: bool = True


@dataclass
class VisualizeDiffResponse:
    format: str
    content: str
    summary: dict = field(default_factory=lambda: {
        "nodes_added": 0, "nodes_removed": 0, "nodes_modified": 0,
        "edges_added": 0, "edges_removed": 0
    })


# === History ===

@dataclass
class ListSnapshotsParams:
    limit: int = 10
    before: Optional[str] = None
    since: Optional[str] = None


@dataclass
class ListSnapshotsResponse:
    snapshots: list[SnapshotInfo]
    has_more: bool


@dataclass
class GetSnapshotParams:
    snapshot_id: str
    node_id: str
    fetch_level: FetchLevel = FetchLevel.SKELETON


@dataclass
class GetSnapshotResponse:
    snapshot_id: str
    timestamp: str
    node: Optional[Node]
    exists: bool


@dataclass
class DiffSnapshotsParams:
    from_snapshot: str
    to_snapshot: str
    scope: Optional[str] = None


@dataclass
class NodeChange:
    node_id: str
    change_type: Literal["added", "removed", "modified"]
    old_state: Optional[NodeSkeleton] = None
    new_state: Optional[NodeSkeleton] = None
    changes: Optional[dict] = None


@dataclass
class DiffSnapshotsResponse:
    from_id: str
    to_id: str
    changes: list[NodeChange] = field(default_factory=list)


# === Indexing ===

@dataclass
class IndexParams:
    path: str
    recursive: bool = True
    force: bool = False


@dataclass
class IndexResponse:
    files_indexed: int
    nodes_created: int
    errors: list[dict] = field(default_factory=list)


# === Validation ===

@dataclass
class ValidateParams:
    scope: str = "all"
    rules: Optional[list[str]] = None


@dataclass
class ViolationDetail:
    node_id: str
    node_name: str
    rule: str
    severity: str
    message: str
    suggestion: Optional[str]
    location: dict  # {"file": str, "line": int}


@dataclass
class ValidateResponse:
    summary: dict = field(default_factory=lambda: {"passed": 0, "warnings": 0, "errors": 0})
    violations: list[ViolationDetail] = field(default_factory=list)
