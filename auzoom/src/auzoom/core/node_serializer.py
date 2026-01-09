"""Node serialization for lazy code graph."""

from ..models import CodeNode, FetchLevel


class NodeSerializer:
    """Serialize and deserialize CodeNode objects."""

    @staticmethod
    def serialize_node_for_cache(node: CodeNode) -> dict:
        """Serialize a CodeNode for cache storage."""
        return {
            "id": node.id,
            "name": node.name,
            "type": node.node_type.value,
            "file": node.file_path,
            "line_start": node.line_start,
            "line_end": node.line_end,
            "dependencies": node.dependencies,
            "children": node.children,
            "docstring": node.docstring,
            "signature": node.signature,
            "source": node.source
        }

    @staticmethod
    def hydrate_nodes(cache_data: dict) -> list[CodeNode]:
        """Hydrate CodeNode objects from cache data."""
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
                dependencies=node_data.get("dependencies", []),
                children=node_data.get("children", []),
                docstring=node_data.get("docstring"),
                signature=node_data.get("signature"),
                source=node_data.get("source")
            )
            nodes.append(node)
        return nodes

    @staticmethod
    def serialize_file(nodes: list[CodeNode], level: FetchLevel) -> list[dict]:
        """Serialize nodes at specified detail level."""
        if level == FetchLevel.SKELETON:
            return [node.to_skeleton() for node in nodes]
        elif level == FetchLevel.SUMMARY:
            return [node.to_summary() for node in nodes]
        else:  # FULL
            return [node.to_full() for node in nodes]
