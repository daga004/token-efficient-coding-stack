"""MCP tool schemas for orchestrator."""


def get_tools_manifest():
    """Return MCP tools manifest with all orchestrator tool definitions."""
    return {
        "tools": [
            _orchestrator_route_schema(),
            _orchestrator_execute_schema(),
            _orchestrator_validate_schema(),
        ]
    }


def _orchestrator_route_schema():
    """Schema for orchestrator_route tool."""
    return {
        "name": "orchestrator_route",
        "description": (
            "Get routing recommendation for a task based on complexity scoring. "
            "Returns model suggestion, complexity breakdown, and cost estimates. "
            "Does NOT execute the task - use orchestrator_execute or Task tool for execution."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Task description to analyze and route"
                },
                "context": {
                    "type": "object",
                    "description": "Optional context for complexity scoring",
                    "properties": {
                        "files_count": {
                            "type": "integer",
                            "description": "Number of files involved"
                        },
                        "requires_tests": {
                            "type": "boolean",
                            "description": "Whether tests are required"
                        },
                        "subsystems": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of subsystems affected"
                        },
                        "external_apis": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of external APIs used"
                        }
                    }
                }
            },
            "required": ["task"]
        }
    }


def _orchestrator_execute_schema():
    """Schema for orchestrator_execute tool."""
    return {
        "name": "orchestrator_execute",
        "description": (
            "Execute task on specified model with retry logic. "
            "Supports Gemini (Flash, Pro) and Claude models (Haiku, Sonnet, Opus). "
            "Note: Claude models return placeholder responses - use Task tool for actual Claude execution."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "enum": ["gemini-flash", "gemini-pro", "haiku", "sonnet", "opus"],
                    "description": "Model to use for execution"
                },
                "prompt": {
                    "type": "string",
                    "description": "Task prompt to execute"
                },
                "max_tokens": {
                    "type": "integer",
                    "default": 4096,
                    "description": "Maximum output tokens (default: 4096)"
                }
            },
            "required": ["model", "prompt"]
        }
    }


def _orchestrator_validate_schema():
    """Schema for orchestrator_validate tool."""
    return {
        "name": "orchestrator_validate",
        "description": (
            "Validate output against task requirements using Sonnet. "
            "Input-heavy validation checkpoint - cost-effective for quality assurance. "
            "Returns pass/fail with up to 3 specific issues and escalation flag."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Original task description"
                },
                "output": {
                    "type": "string",
                    "description": "Output to validate against task"
                }
            },
            "required": ["task", "output"]
        }
    }
