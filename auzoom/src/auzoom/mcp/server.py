"""AuZoom MCP server for hierarchical file navigation."""

import json
from pathlib import Path
from typing import Optional
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
            return self._read_python_file(file_path, args.get("level", "skeleton"))
        else:
            return self._read_non_python_file(
                file_path,
                args.get("level", "skeleton"),
                args.get("offset"),
                args.get("limit")
            )

    def _read_python_file(self, file_path: Path, level_str: str) -> dict:
        """Read Python file using LazyCodeGraph."""
        level = FetchLevel[level_str.upper()]

        try:
            nodes = self.graph.get_file(str(file_path), level)
            return {
                "type": "python",
                "file_path": str(file_path),
                "level": level_str,
                "nodes": nodes,
                "node_count": len(nodes),
                "cached": str(file_path) in self.graph.file_index
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
        """Get dependency graph for a node."""
        node_id = args.get("node_id")
        if not node_id:
            return {"error": "node_id parameter required"}

        depth = args.get("depth", 1)
        deps = self.graph.get_dependencies(node_id, depth)

        return {
            "node_id": node_id,
            "dependencies": deps,
            "count": len(deps)
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
