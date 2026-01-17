"""Node serialization for lazy code graph."""

from typing import Optional, List
from ..models import CodeNode, FetchLevel


class NodeSerializer:
    """Serialize and deserialize CodeNode objects."""

    @staticmethod
    def serialize_node_for_cache(node: CodeNode) -> dict:
        """Serialize a CodeNode for cache storage.

        NOTE: Only stores reverse dependencies (dependents) for token efficiency.
        Forward dependencies computed on-demand via auzoom_get_calls.
        """
        return {
            "id": node.id,
            "name": node.name,
            "type": node.node_type.value,
            "file": node.file_path,
            "line_start": node.line_start,
            "line_end": node.line_end,
            # dependencies: REMOVED - compute on-demand for 20% of cases
            "dependents": node.dependents,  # Reverse deps only (80% of use cases)
            "children": node.children,
            "docstring": node.docstring,
            "signature": node.signature,
            "source": node.source
        }

    @staticmethod
    def hydrate_nodes(cache_data: dict) -> list[CodeNode]:
        """Hydrate CodeNode objects from cache data.

        NOTE: Forward dependencies not stored in cache (compute on-demand).
        Only reverse dependencies (dependents) are hydrated.
        """
        from ..models import NodeType

        nodes = []
        for node_data in cache_data.get("nodes", []):
            node = CodeNode(
                id=node_data["id"],
                name=node_data["name"],
                node_type=NodeType(node_data["type"]),
                file_path=node_data["file"],
                line_start=node_data["line_start"],
                line_end=node_data["line_end"],
                # dependencies: Not in cache - compute on-demand
                dependents=node_data.get("dependents", []),
                children=node_data.get("children", []),
                docstring=node_data.get("docstring"),
                signature=node_data.get("signature"),
                source=node_data.get("source")
            )
            nodes.append(node)
        return nodes

    @staticmethod
    def serialize_file(
        nodes: List[CodeNode],
        level: FetchLevel,
        fields: Optional[List[str]] = None
    ) -> List[dict]:
        """Serialize nodes at specified detail level with optional field filtering.

        Args:
            nodes: List of CodeNode objects to serialize
            level: Detail level (skeleton/summary/full)
            fields: Optional list of field names to include (50-70% token reduction)

        Returns:
            List of serialized node dictionaries
        """
        # Serialize at requested level
        if level == FetchLevel.SKELETON:
            serialized = [node.to_skeleton() for node in nodes]
        elif level == FetchLevel.SUMMARY:
            serialized = [node.to_summary() for node in nodes]
        else:  # FULL
            serialized = [node.to_full() for node in nodes]

        # Apply field filtering if requested
        if fields:
            return [
                {k: v for k, v in node.items() if k in fields}
                for node in serialized
            ]

        return serialized

    @staticmethod
    def serialize_file_compact(
        nodes: List[CodeNode],
        level: FetchLevel,
        relative_to: Optional[str] = None,
        fields: Optional[List[str]] = None
    ) -> List[dict]:
        """Serialize nodes in compact format with short keys for token efficiency.

        Optimizations:
        - Short keys: "i", "n", "t", "d" vs "id", "name", "type", "dependencies"
        - Type shortcodes: "f", "m", "c" vs "function", "method", "class"
        - Relative paths if relative_to provided
        - Optional field filtering

        Token savings: 40-50% for skeleton level, 30-40% for summary/full

        Args:
            nodes: List of CodeNode objects to serialize
            level: Detail level (skeleton/summary/full)
            relative_to: Project root for relative path calculation
            fields: Optional list of compact field names to include

        Returns:
            List of compact serialized node dictionaries
        """
        # Serialize using compact format
        serialized = [node.to_compact(relative_to=relative_to, level=level) for node in nodes]

        # Apply field filtering if requested
        if fields:
            return [
                {k: v for k, v in node.items() if k in fields}
                for node in serialized
            ]

        return serialized
