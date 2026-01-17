"""AuZoom MCP server for hierarchical file navigation."""

import json
import os
from pathlib import Path
from typing import Optional, List
from ..core.graph.lazy_graph import LazyCodeGraph
from ..models import FetchLevel
from .file_summarizer import FileSummarizer
from .jsonrpc_handler import JSONRPCHandler


class AuZoomMCPServer:
    """MCP server that replaces Read with hierarchical file navigation.

    Tool: auzoom_read(path, level="skeleton")
    - Python files: Return parsed structure at requested level
    - Other files: Return cached summary or full content (lazy indexing)
    """

    def __init__(self, project_root: str, auto_warm: bool = True):
        self.project_root = Path(project_root).resolve()
        self.graph = LazyCodeGraph(str(self.project_root), auto_warm=auto_warm)

        # Summary cache for non-Python files
        summary_cache_dir = self.project_root / ".auzoom" / "summaries"
        self.summarizer = FileSummarizer(summary_cache_dir)

    def handle_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """Dispatch tool calls to appropriate handlers."""
        handlers = {
            "auzoom_read": self._tool_read,
            "auzoom_find": self._tool_find,
            "auzoom_get_dependencies": self._tool_get_dependencies,
            "auzoom_get_calls": self._tool_get_calls,
            "auzoom_stats": self._tool_stats,
            "auzoom_validate": self._tool_validate
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            return handler(arguments)
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}

    def _tool_read(self, args: dict) -> dict:
        """Handle auzoom_read - the main file reading tool."""
        path = args.get("path")
        if not path:
            return {"error": "path parameter required"}

        # Resolve path relative to project root
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self.project_root / path
        file_path = file_path.resolve()

        if not file_path.exists():
            return {"error": f"File not found: {path}"}

        if file_path.suffix == ".py":
            return self._read_python_file(
                file_path,
                args.get("level", "skeleton"),
                format=args.get("format", "standard"),
                fields=args.get("fields")
            )
        else:
            return self._read_non_python_file(
                file_path,
                args.get("level", "skeleton"),
                args.get("offset"),
                args.get("limit")
            )

    def _read_python_file(
        self,
        file_path: Path,
        level_str: str,
        format: str = "standard",
        fields: Optional[List[str]] = None
    ) -> dict:
        """Read Python file using LazyCodeGraph with optimization support.

        Args:
            file_path: Path to Python file
            level_str: Detail level ("skeleton", "summary", "full")
            format: Serialization format ("standard" or "compact")
            fields: Optional list of fields to include (field filtering)

        Returns:
            Dict with file data and metadata
        """
        # Check file size threshold bypass (default: 300 tokens)
        threshold = int(os.environ.get("AUZOOM_SMALL_FILE_THRESHOLD", "300"))
        line_count = sum(1 for _ in open(file_path))
        estimated_tokens = line_count * 4  # ~4 tokens per line

        if estimated_tokens < threshold:
            # Small file bypass: return full content directly (no parsing)
            return {
                "type": "small_file_bypass",
                "file_path": str(file_path),
                "content": file_path.read_text(),
                "note": f"File below {threshold} token threshold ({estimated_tokens} estimated)",
                "level": "full"
            }

        # Normal progressive disclosure path
        level = FetchLevel[level_str.upper()]

        try:
            imports, nodes = self.graph.get_file(
                str(file_path),
                level,
                format=format,
                fields=fields
            )
            return {
                "type": "python",
                "file_path": str(file_path),
                "level": level_str,
                "format": format,
                "imports": imports,  # Collapsed import nodes (simple string array)
                "nodes": nodes,      # Non-import nodes (functions, classes, methods)
                "node_count": len(nodes),
                "import_count": len(imports),
                "cached": str(file_path) in self.graph.file_index,
                "token_estimate": len(json.dumps({"imports": imports, "nodes": nodes})) // 4
            }
        except Exception as e:
            return {
                "type": "python_fallback",
                "file_path": str(file_path),
                "error": f"Parse failed: {e}",
                "content": file_path.read_text(),
                "level": "full"
            }

    def _read_non_python_file(
        self,
        file_path: Path,
        level_str: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None
    ) -> dict:
        """Read non-Python file with lazy summary generation."""
        cached_summary = self.summarizer.load_cached_summary(file_path)

        # Return full content if requested
        if level_str == "full":
            content = file_path.read_text()
            lines = content.splitlines()
            if offset is not None or limit is not None:
                offset = offset or 0
                limit = limit or len(lines)
                lines = lines[offset:offset + limit]
                content = '\n'.join(lines)
            if not cached_summary:
                self.summarizer.schedule_summarization(file_path, content)
            return {
                "type": "full_content",
                "file_path": str(file_path),
                "content": content,
                "line_count": len(lines),
                "level": "full"
            }

        # Return cached summary if available
        if cached_summary:
            return {
                "type": "cached_summary",
                "file_path": str(file_path),
                "level": level_str,
                "summary": cached_summary["summary"],
                "file_type": cached_summary.get("file_type", file_path.suffix),
                "line_count": cached_summary.get("line_count", 0),
                "size_bytes": cached_summary.get("size_bytes", 0),
                "cached": True,
                "note": "Use level='full' for complete content"
            }

        # First access - return full and schedule summarization
        content = file_path.read_text()
        lines = content.splitlines()
        self.summarizer.schedule_summarization(file_path, content)
        return {
            "type": "full_content_first_access",
            "file_path": str(file_path),
            "content": content,
            "line_count": len(lines),
            "level": "full",
            "cached": False,
            "note": "First access - summary will be cached for future reads"
        }

    def _tool_find(self, args: dict) -> dict:
        """Search for code by name pattern."""
        pattern = args.get("pattern", "")
        matches = self.graph.find_by_name(pattern)
        return {"matches": matches, "count": len(matches)}

    def _tool_get_dependencies(self, args: dict) -> dict:
        """Get dependency graph for a node with advanced traversal options.

        Supports:
        - BFS vs DFS strategies
        - Forward/Reverse/Bidirectional directions
        - Node type filtering
        - Batch loading optimization

        Args:
            node_id: Starting node ID (required)
            depth: Maximum traversal depth (default: 1)
            strategy: "bfs" (breadth-first) or "dfs" (depth-first), default: "bfs"
            direction: "forward" (calls), "reverse" (callers), or "both", default: "reverse"
            node_types: List of node types to include (e.g., ["function", "method"])

        Returns:
            Dict with:
            - node_id: The starting node
            - dependencies: List of nodes with depth annotation
            - count: Number of dependencies found
            - strategy: Traversal strategy used
            - direction: Traversal direction used

        Examples:
            # Impact analysis (default): Who depends on this?
            {"node_id": "utils.py::validate_email", "depth": 2}
            → BFS traversal of reverse dependencies (callers)

            # Call chain analysis: What does this call?
            {"node_id": "api.py::create_user", "depth": 5, "direction": "forward"}
            → DFS traversal of forward dependencies (calls)

            # Filter to functions only
            {"node_id": "service.py::login", "depth": 3, "node_types": ["function", "method"]}
        """
        from ..models import TraversalStrategy, TraversalDirection, NodeType

        node_id = args.get("node_id")
        if not node_id:
            return {"error": "node_id parameter required"}

        depth = args.get("depth", 1)

        # Parse strategy
        strategy_str = args.get("strategy", "bfs").lower()
        strategy = TraversalStrategy.BFS if strategy_str == "bfs" else TraversalStrategy.DFS

        # Parse direction
        direction_str = args.get("direction", "reverse").lower()
        direction_map = {
            "forward": TraversalDirection.FORWARD,
            "reverse": TraversalDirection.REVERSE,
            "both": TraversalDirection.BIDIRECTIONAL
        }
        direction = direction_map.get(direction_str, TraversalDirection.REVERSE)

        # Parse node type filter
        node_type_filter = None
        if "node_types" in args:
            type_strs = args["node_types"]
            if isinstance(type_strs, list):
                type_map = {
                    "function": NodeType.FUNCTION,
                    "method": NodeType.METHOD,
                    "class": NodeType.CLASS,
                    "module": NodeType.MODULE,
                    "import": NodeType.IMPORT
                }
                node_type_filter = [type_map[t] for t in type_strs if t in type_map]

        # Execute traversal
        deps = self.graph.get_dependencies(
            node_id,
            depth,
            strategy=strategy,
            direction=direction,
            node_type_filter=node_type_filter
        )

        return {
            "node_id": node_id,
            "dependencies": deps,
            "count": len(deps),
            "strategy": strategy.value,
            "direction": direction.value,
            "note": "Use strategy='bfs' for impact analysis (show all callers level-by-level). "
                    "Use strategy='dfs' direction='forward' for call chain analysis (follow execution deep)."
        }

    def _tool_get_calls(self, args: dict) -> dict:
        """Get forward dependencies (what this node calls) on-demand.

        This computes forward dependencies by parsing the node's source code,
        since we only store reverse dependencies for token efficiency.

        Use cases (20% of dependency queries):
        - Call chain analysis: "What does this function ultimately call?"
        - Execution path tracing: "Show me the full call chain"
        - Circular dependency detection: "Does A → B → A exist?"

        Args:
            node_id: Node ID to analyze

        Returns:
            Dict with:
            - node_id: The requested node ID
            - calls: List of node IDs called by this node
            - count: Number of calls
            - cost: Token cost estimate (~150 tokens)
            - note: Explanation that this is computed on-demand
        """
        node_id = args.get("node_id")
        if not node_id:
            return {"error": "node_id parameter required"}

        # Get the node with full source code
        try:
            node = self.graph.get_node(node_id)
            if not node:
                return {"error": f"Node not found: {node_id}"}

            # Parse the source code to extract function calls
            from ..core.parsing.parser import PythonParser

            calls = []
            if node.get("source"):
                # Create a temporary file with the source
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(node["source"])
                    temp_path = f.name

                try:
                    # Parse to extract calls
                    parser = PythonParser()
                    # We'll use the parser's call extraction directly
                    from tree_sitter import Language, Parser as TSParser
                    import tree_sitter_python as tspython

                    PY_LANGUAGE = Language(tspython.language())
                    ts_parser = TSParser(PY_LANGUAGE)
                    tree = ts_parser.parse(node["source"].encode())

                    # Extract calls from the AST
                    call_names = parser._extract_function_calls_from_node(tree.root_node)
                    calls = list(call_names)
                finally:
                    import os
                    os.unlink(temp_path)

            return {
                "node_id": node_id,
                "calls": calls,
                "count": len(calls),
                "cost_estimate_tokens": 150,
                "note": "Computed on-demand from source code (not cached). Use sparingly - most cases only need reverse deps from auzoom_get_dependencies."
            }

        except Exception as e:
            return {
                "error": f"Failed to extract calls: {str(e)}",
                "node_id": node_id
            }

    def _tool_stats(self, args: dict) -> dict:
        """Get cache performance statistics."""
        stats = self.graph.get_stats()
        summary_files = list(self.summarizer.cache_dir.glob("*.json"))
        stats["non_python_summaries_cached"] = len(summary_files)
        return stats

    def _tool_validate(self, args: dict) -> dict:
        """Validate code structure compliance."""
        from ..core.validator import CodeValidator

        scope = args.get("scope", "file")
        path = args.get("path", str(self.project_root))

        validator = CodeValidator()

        if scope == "file":
            violations = validator.validate_file(path)
        elif scope == "directory":
            violations = validator.validate_directory(path)
        else:
            violations = validator.validate_project(path)

        return {
            "violations": [
                {
                    "file": v.file,
                    "line": v.line,
                    "type": v.type,
                    "severity": v.severity,
                    "message": v.message,
                    "current": v.current,
                    "limit": v.limit
                }
                for v in violations
            ],
            "compliant": len(violations) == 0,
            "report": validator.format_report(violations)
        }

    def run(self):
        """Run MCP server (stdio protocol)."""
        handler = JSONRPCHandler(self)
        handler.run()


def main():
    """Entry point for MCP server."""
    import os
    project_root = os.getcwd()
    server = AuZoomMCPServer(project_root)
    server.run()


if __name__ == "__main__":
    main()
