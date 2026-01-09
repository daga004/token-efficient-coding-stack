"""Data models for AuZoom code navigation."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class FetchLevel(Enum):
    """Level of detail when fetching code nodes."""
    SKELETON = "skeleton"  # name + dependencies only (~15 tokens/node)
    SUMMARY = "summary"    # + docstring/signature (~75 tokens/node)
    FULL = "full"         # + complete source (~400 tokens/node)


class NodeType(Enum):
    """Type of code node."""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    IMPORT = "import"


class CodeNode(BaseModel):
    """Represents a code element at multiple resolution levels."""

    id: str                          # file_path::qualified_name
    name: str                        # Short name
    node_type: NodeType
    file_path: str
    line_start: int
    line_end: int
    dependencies: list[str] = []     # IDs of nodes this depends on
    children: list[str] = []         # IDs of child nodes
    docstring: Optional[str] = None  # For summary level
    signature: Optional[str] = None  # For functions/methods
    source: Optional[str] = None     # For full level

    def to_skeleton(self) -> dict:
        """Return minimal representation."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type.value,
            "dependencies": self.dependencies,
            "children": self.children,
        }

    def to_summary(self) -> dict:
        """Return summary representation with signatures."""
        result = self.to_skeleton()
        result.update({
            "file": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "docstring": self.docstring,
        })
        if self.signature:
            result["signature"] = self.signature
        return result

    def to_full(self) -> dict:
        """Return full representation with source code."""
        result = self.to_summary()
        result["source"] = self.source
        return result
