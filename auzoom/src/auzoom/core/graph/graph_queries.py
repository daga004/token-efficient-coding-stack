"""Query operations for lazy code graph."""

from typing import Optional
from ...models import FetchLevel, TraversalStrategy, TraversalDirection, NodeType
from .graph_traversal import SelectiveGraphTraversal


class GraphQueries:
    """Handle graph query operations."""

    def __init__(self, graph):
        self.graph = graph
        self.traversal = SelectiveGraphTraversal(graph)

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

    def get_dependencies(
        self,
        node_id: str,
        depth: int = 1,
        strategy: Optional[TraversalStrategy] = None,
        direction: Optional[TraversalDirection] = None,
        node_type_filter: Optional[list[NodeType]] = None
    ) -> list[dict]:
        """Get dependency nodes with advanced traversal options.

        Args:
            node_id: Starting node ID
            depth: Maximum traversal depth (1 = immediate neighbors)
            strategy: BFS (breadth-first) or DFS (depth-first), default: BFS
            direction: FORWARD (calls), REVERSE (callers), or BOTH, default: REVERSE
            node_type_filter: Optional list of NodeTypes to include

        Returns:
            List of dependency nodes with depth annotation

        Examples:
            # Impact analysis (default): Who depends on this?
            get_dependencies("utils.py::validate_email", depth=2)
            → Returns all callers (reverse dependencies)

            # Call chain analysis: What does this call?
            get_dependencies("api.py::create_user", depth=5, direction=FORWARD)
            → Returns all called functions (forward dependencies, computed on-demand)

            # Filter to functions only
            get_dependencies("service.py::login", depth=3, node_type_filter=[NodeType.FUNCTION])
        """
        if depth < 1:
            return []

        # Default to BFS + REVERSE (80% use case: impact analysis)
        if strategy is None:
            strategy = TraversalStrategy.BFS
        if direction is None:
            direction = TraversalDirection.REVERSE

        # Ensure starting node is loaded
        if node_id not in self.graph.nodes:
            try:
                self.get_node(node_id, FetchLevel.SKELETON)
            except KeyError:
                return []

        # Use advanced traversal
        result = self.traversal.traverse(
            start_node_id=node_id,
            depth=depth,
            strategy=strategy,
            direction=direction,
            node_type_filter=node_type_filter,
            batch_load=True  # Enable BFS optimization
        )

        return result

    def find_by_name(self, name_pattern: str) -> list[dict]:
        """Search across all loaded nodes."""
        matches = []
        for node in self.graph.nodes.values():
            if name_pattern.lower() in node.name.lower():
                matches.append(node.to_skeleton())
        return matches
