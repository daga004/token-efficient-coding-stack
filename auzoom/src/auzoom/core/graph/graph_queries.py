"""Query operations for lazy code graph."""

from typing import Optional
from ...models import FetchLevel


class GraphQueries:
    """Handle graph query operations."""

    def __init__(self, graph):
        self.graph = graph

    def get_node(self, node_id: str, level: FetchLevel) -> dict:
        """Get single node, parsing file if needed."""
        # If not in memory, need to load the file
        if node_id not in self.graph.nodes:
            # Extract file path from node ID
            file_path = node_id.split("::")[0]
            self.graph.get_file(file_path, level)

        node = self.graph.nodes.get(node_id)
        if not node:
            raise KeyError(f"Node {node_id} not found")

        if level == FetchLevel.SKELETON:
            return node.to_skeleton()
        elif level == FetchLevel.SUMMARY:
            return node.to_summary()
        else:
            return node.to_full()

    def get_children(self, node_id: str, level: FetchLevel) -> list[dict]:
        """Get child nodes."""
        node = self.graph.nodes.get(node_id)
        if not node:
            return []
        return [self.get_node(cid, level) for cid in node.children]

    def get_dependencies(self, node_id: str, depth: int = 1) -> list[dict]:
        """Get dependency nodes, loading files as needed."""
        if depth < 1:
            return []

        visited = set()
        result = []

        def traverse(nid, d):
            if d > depth or nid in visited:
                return
            visited.add(nid)

            # Ensure node is loaded
            if nid not in self.graph.nodes:
                try:
                    self.get_node(nid, FetchLevel.SKELETON)
                except KeyError:
                    return

            node = self.graph.nodes.get(nid)
            if not node:
                return

            for dep_id in node.dependencies:
                if dep_id not in visited:
                    try:
                        result.append(self.get_node(dep_id, FetchLevel.SKELETON))
                        traverse(dep_id, d + 1)
                    except KeyError:
                        pass  # Dependency not found

        traverse(node_id, 1)
        return result

    def find_by_name(self, name_pattern: str) -> list[dict]:
        """Search across all loaded nodes."""
        matches = []
        for node in self.graph.nodes.values():
            if name_pattern.lower() in node.name.lower():
                matches.append(node.to_skeleton())
        return matches
