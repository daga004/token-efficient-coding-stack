from .models import CodeNode, FetchLevel, NodeType, estimate_tokens

class CodeGraph:
    """Container for navigating code structure at multiple resolutions."""

    def __init__(self):
        self.nodes: dict[str, CodeNode] = {}  # node_id -> CodeNode
        self.file_index: dict[str, list[str]] = {}  # file_path -> [node_ids]
        self.name_index: dict[str, list[str]] = {}  # name -> [node_ids] for search

    def add_node(self, node: CodeNode) -> None:
        """Add node and update indexes."""
        self.nodes[node.id] = node

        # Update file index
        if node.file_path not in self.file_index:
            self.file_index[node.file_path] = []
        self.file_index[node.file_path].append(node.id)

        # Update name index
        if node.name not in self.name_index:
            self.name_index[node.name] = []
        self.name_index[node.name].append(node.id)

    def get_node(self, node_id: str, level: FetchLevel) -> dict:
        """Get single node at requested resolution."""
        node = self.nodes.get(node_id)
        if not node:
            raise KeyError(f"Node {node_id} not found")

        if level == FetchLevel.SKELETON:
            return node.to_skeleton()
        elif level == FetchLevel.SUMMARY:
            return node.to_summary()
        else:  # FULL
            return node.to_full()

    def get_file(self, file_path: str, level: FetchLevel) -> list[dict]:
        """Get all nodes in a file at requested resolution."""
        node_ids = self.file_index.get(file_path, [])
        return [self.get_node(nid, level) for nid in node_ids]

    def get_children(self, node_id: str, level: FetchLevel) -> list[dict]:
        """Get child nodes (e.g., methods of a class)."""
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.get_node(cid, level) for cid in node.children]

    def get_dependencies(self, node_id: str, depth: int = 1) -> list[dict]:
        """Get dependency nodes (what this node depends on)."""
        if depth < 1:
            return []

        visited = set()
        result = []

        def traverse(nid, d):
            if d > depth or nid in visited:
                return
            visited.add(nid)

            node = self.nodes.get(nid)
            if not node:
                return

            for dep_id in node.dependencies:
                if dep_id not in visited:
                    result.append(self.get_node(dep_id, FetchLevel.SKELETON))
                    traverse(dep_id, d + 1)

        traverse(node_id, 1)
        return result

    def find_by_name(self, name_pattern: str) -> list[dict]:
        """Search for nodes by name (simple substring match)."""
        matches = []
        for name, node_ids in self.name_index.items():
            if name_pattern.lower() in name.lower():
                for nid in node_ids:
                    matches.append(self.get_node(nid, FetchLevel.SKELETON))
        return matches

    def get_token_stats(self, file_path: str) -> dict:
        """Compare token usage across fetch levels for a file."""
        node_ids = self.file_index.get(file_path, [])
        if not node_ids:
            return {"error": "File not found"}

        skeleton_tokens = 0
        summary_tokens = 0
        full_tokens = 0

        for nid in node_ids:
            node = self.nodes[nid]
            skeleton_tokens += estimate_tokens(str(node.to_skeleton()))
            summary_tokens += estimate_tokens(str(node.to_summary()))
            full_tokens += estimate_tokens(str(node.to_full()))

        return {
            "file": file_path,
            "nodes": len(node_ids),
            "tokens_skeleton": skeleton_tokens,
            "tokens_summary": summary_tokens,
            "tokens_full": full_tokens,
            "reduction_ratio": full_tokens / skeleton_tokens if skeleton_tokens > 0 else 0
        }
