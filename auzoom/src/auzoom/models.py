"""AuZoom Data Models - Tiered node structure for multi-resolution navigation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union


class NodeType(Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    CONSTANT = "constant"
    VARIABLE = "variable"
    IMPORT = "import"

    @property
    def shortcode(self) -> str:
        """Get compact single-character shortcode for token efficiency."""
        shortcodes = {
            "module": "M",
            "class": "c",
            "function": "f",
            "method": "m",
            "constant": "C",
            "variable": "v",
            "import": "i",
        }
        return shortcodes.get(self.value, self.value)


class EdgeType(Enum):
    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    USES = "uses"


class FetchLevel(Enum):
    SKELETON = "skeleton"  # ~15 tokens/node
    SUMMARY = "summary"    # ~75 tokens/node
    FULL = "full"          # ~400 tokens/node


class TraversalStrategy(Enum):
    """Graph traversal strategy for dependency analysis."""
    DFS = "dfs"  # Depth-first: follow call chains deep
    BFS = "bfs"  # Breadth-first: show immediate impacts first


class TraversalDirection(Enum):
    """Direction for dependency traversal."""
    FORWARD = "forward"      # What does this depend on?
    REVERSE = "reverse"      # What depends on this?
    BIDIRECTIONAL = "both"   # Both directions


@dataclass
class EdgeSkeleton:
    """Dependency edge between nodes."""
    target_id: str
    target_name: str
    edge_type: EdgeType
    location_line: Optional[int] = None


@dataclass
class NodeSkeleton:
    """Layer 0: Names and dependencies only (~15 tokens)."""
    id: str                 # "src/auth/service.py::AuthService.login"
    name: str               # "login"
    qualified_name: str     # "auth.service.AuthService.login"
    node_type: NodeType
    level: int              # 0=root, 1=module, 2=class, 3=method
    parent_id: Optional[str]
    children_ids: list[str] = field(default_factory=list)
    depends_on: list[EdgeSkeleton] = field(default_factory=list)
    depended_by: list[EdgeSkeleton] = field(default_factory=list)
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0


@dataclass
class NodeSummary(NodeSkeleton):
    """Layer 1: + docstrings and signatures (~75 tokens)."""
    signature: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    args: Optional[list[dict]] = None
    returns: Optional[str] = None
    raises: Optional[list[str]] = None
    compliance: Optional["ComplianceStatus"] = None


@dataclass
class NodeFull(NodeSummary):
    """Layer 2: + source code (~400 tokens)."""
    source: Optional[str] = None


@dataclass
class ComplianceStatus:
    is_compliant: bool
    violations: list["Violation"] = field(default_factory=list)


@dataclass
class Violation:
    rule: str
    severity: str  # "error" | "warning"
    message: str
    suggestion: Optional[str] = None


@dataclass
class SnapshotInfo:
    id: str
    timestamp: str
    trigger: str  # "file_change" | "manual"
    files_changed: list[str] = field(default_factory=list)
    nodes_added: int = 0
    nodes_removed: int = 0
    nodes_modified: int = 0
    git_commit: Optional[str] = None
    git_message: Optional[str] = None


Node = Union[NodeSkeleton, NodeSummary, NodeFull]


def estimate_tokens(text: str) -> int:
    """Rough token estimate using character count / 4."""
    if not text:
        return 0
    return len(text) // 4


@dataclass
class CodeNode:
    """Simplified code node for parser output with multi-level serialization.

    NOTE: Only stores reverse dependencies (dependents) for token efficiency.
    Forward dependencies (what this calls) can be computed on-demand via auzoom_get_calls.

    Rationale: 80% of use cases need reverse deps (impact analysis: "what breaks if I change this?")
              Only 20% need forward deps (call chain analysis: "what does this ultimately call?")
              Storing reverse-only saves 30% tokens in skeleton responses.
    """
    id: str  # format: "file_path::qualified_name"
    name: str
    node_type: NodeType
    file_path: str
    line_start: int
    line_end: int
    # dependencies: REMOVED - compute on-demand with auzoom_get_calls for 20% of cases that need it
    dependents: list[str] = field(default_factory=list)  # node IDs that depend on this (reverse deps) - 80% of use cases
    children: list[str] = field(default_factory=list)  # child node IDs
    docstring: Optional[str] = None
    signature: Optional[str] = None  # for functions/methods
    source: Optional[str] = None  # full source code

    def to_skeleton(self) -> dict:
        """Return skeleton representation (~15 tokens): id, name, type, dependents.

        NOTE: Only includes reverse dependencies (dependents).
        For forward dependencies, use auzoom_get_calls(node_id) on-demand.
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type.value,
            "dependents": self.dependents,  # Reverse deps: who depends on me (80% of use cases)
        }

    def to_summary(self) -> dict:
        """Return summary representation (~75 tokens): skeleton + docstring + signature."""
        result = self.to_skeleton()

        # Add signature if available
        if self.signature:
            result["signature"] = self.signature

        # Add truncated docstring if available
        if self.docstring:
            truncated = self.docstring[:100]
            if len(self.docstring) > 100:
                truncated += "..."
            result["docstring"] = truncated

        # Add line range for context
        result["line_start"] = self.line_start
        result["line_end"] = self.line_end

        return result

    def to_full(self) -> dict:
        """Return full representation (~400 tokens): everything including source."""
        result = self.to_summary()

        # Replace truncated docstring with full version
        if self.docstring:
            result["docstring"] = self.docstring

        # Add children
        result["children"] = self.children

        # Add file path
        result["file_path"] = self.file_path

        # Add full source
        if self.source:
            result["source"] = self.source

        return result

    def to_compact(self, relative_to: Optional[str] = None, level: FetchLevel = FetchLevel.SKELETON) -> dict:
        """Return compact representation with short keys and minimal tokens.

        Optimizations:
        - Short keys: "i" (id), "n" (name), "t" (type), "r" (dependents/reverse), "c" (children)
        - Type shortcodes: "f" (function), "m" (method), "c" (class), etc.
        - Relative paths if relative_to provided
        - Level-dependent fields (skeleton/summary/full)
        - Reverse-only deps: stores "r" (dependents), not forward deps (30% token savings)

        Args:
            relative_to: Project root for relative path calculation
            level: Detail level (skeleton/summary/full)

        Returns:
            Compact dict representation (40-50% token reduction)
        """
        # Calculate relative ID if base path provided
        node_id = self.id
        if relative_to and self.id.startswith(relative_to):
            node_id = self.id[len(relative_to):].lstrip("/")

        # Base compact format (skeleton level)
        result = {
            "i": node_id,
            "n": self.name,
            "t": self.node_type.shortcode,
            "r": self.dependents,  # Reverse deps only (was "d": dependencies)
        }

        # Summary level additions
        if level in (FetchLevel.SUMMARY, FetchLevel.FULL):
            if self.signature:
                result["s"] = self.signature
            if self.docstring:
                truncated = self.docstring[:100]
                if len(self.docstring) > 100:
                    truncated += "..."
                result["doc"] = truncated
            result["ls"] = self.line_start
            result["le"] = self.line_end

        # Full level additions
        if level == FetchLevel.FULL:
            if self.docstring:
                result["doc"] = self.docstring  # Replace with full docstring
            result["c"] = self.children
            result["fp"] = self.file_path
            if self.source:
                result["src"] = self.source

        return result
