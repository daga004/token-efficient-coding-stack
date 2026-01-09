"""MCP tool schema definitions for AuZoom."""


def get_tools_manifest() -> dict:
    """Return MCP tools manifest with all tool definitions."""
    return {
        "tools": [
            _auzoom_read_schema(),
            _auzoom_find_schema(),
            _auzoom_get_dependencies_schema(),
            _auzoom_stats_schema(),
            _auzoom_validate_schema()
        ]
    }


def _auzoom_read_schema() -> dict:
    """Schema for auzoom_read tool."""
    return {
        "name": "auzoom_read",
        "description": "Read file with hierarchical navigation. Python files return structure at requested level (skeleton/summary/full). Other files return cached summary or full content. All files indexed lazily on first access.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to read"
                },
                "level": {
                    "type": "string",
                    "enum": ["skeleton", "summary", "full"],
                    "default": "skeleton",
                    "description": "Detail level: skeleton (minimal), summary (with metadata), or full (complete content)"
                },
                "offset": {
                    "type": "integer",
                    "description": "Line offset for partial reads (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Line limit for partial reads (optional)"
                }
            },
            "required": ["path"]
        }
    }


def _auzoom_find_schema() -> dict:
    """Schema for auzoom_find tool."""
    return {
        "name": "auzoom_find",
        "description": "Search for code by name pattern across indexed files",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Name pattern to search for"
                }
            },
            "required": ["pattern"]
        }
    }


def _auzoom_get_dependencies_schema() -> dict:
    """Schema for auzoom_get_dependencies tool."""
    return {
        "name": "auzoom_get_dependencies",
        "description": "Get dependency graph for a node",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "string",
                    "description": "Node ID to analyze"
                },
                "depth": {
                    "type": "integer",
                    "default": 1,
                    "description": "Dependency depth to traverse"
                }
            },
            "required": ["node_id"]
        }
    }


def _auzoom_stats_schema() -> dict:
    """Schema for auzoom_stats tool."""
    return {
        "name": "auzoom_stats",
        "description": "Get cache performance statistics",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }


def _auzoom_validate_schema() -> dict:
    """Schema for auzoom_validate tool."""
    return {
        "name": "auzoom_validate",
        "description": "Validate code structure compliance with AuZoom guidelines (functions ≤50 lines, modules ≤250 lines, directories ≤7 files)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["file", "directory", "project"],
                    "default": "file",
                    "description": "Validation scope: single file, directory, or entire project"
                },
                "path": {
                    "type": "string",
                    "description": "Path to validate (defaults to project root)"
                }
            }
        }
    }
