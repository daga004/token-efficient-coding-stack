"""Tests for orchestrator MCP server."""

import pytest
from orchestrator.mcp.server import OrchestratorMCPServer


class TestOrchestratorMCPServer:
    """Test suite for OrchestratorMCPServer."""

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test server initializes correctly."""
        server = OrchestratorMCPServer()
        assert server.scorer is not None
        assert server.registry is not None
        assert server.executor is not None

    @pytest.mark.asyncio
    async def test_route_simple_task(self):
        """Test routing a simple task."""
        server = OrchestratorMCPServer()
        result = await server.handle_tool_call(
            "orchestrator_route",
            {"task": "Fix a typo in the README"}
        )

        assert "model" in result
        assert "complexity_score" in result
        assert "reason" in result
        assert "confidence" in result
        assert result["model"] in ["gemini-flash", "gemini-pro", "haiku", "sonnet", "opus"]

    @pytest.mark.asyncio
    async def test_route_complex_task(self):
        """Test routing a complex task."""
        server = OrchestratorMCPServer()
        result = await server.handle_tool_call(
            "orchestrator_route",
            {
                "task": "Implement a new authentication system with OAuth2 integration",
                "context": {
                    "files_count": 15,
                    "requires_tests": True,
                    "subsystems": ["auth", "api", "database"],
                    "external_apis": ["oauth2", "jwt"]
                }
            }
        )

        assert "model" in result
        assert "complexity_score" in result
        assert result["complexity_score"] > 5  # Should be complex
        assert result["model"] in ["sonnet", "opus"]  # Should route to high-tier

    @pytest.mark.asyncio
    async def test_route_with_context(self):
        """Test routing with context information."""
        server = OrchestratorMCPServer()
        result = await server.handle_tool_call(
            "orchestrator_route",
            {
                "task": "Add a new API endpoint",
                "context": {
                    "files_count": 3,
                    "requires_tests": True
                }
            }
        )

        assert "model" in result
        assert "complexity_factors" in result
        assert "estimated_cost" in result

    @pytest.mark.asyncio
    async def test_route_returns_proper_structure(self):
        """Test route returns all expected fields."""
        server = OrchestratorMCPServer()
        result = await server.handle_tool_call(
            "orchestrator_route",
            {"task": "Implement feature X"}
        )

        assert "model" in result
        assert "complexity_score" in result
        assert "complexity_factors" in result
        assert "reason" in result
        assert "confidence" in result
        assert "estimated_cost" in result

        # Check estimated_cost structure
        assert "model" in result["estimated_cost"]
        assert "cost_per_1m_input" in result["estimated_cost"]
        assert "cost_per_1m_output" in result["estimated_cost"]

    @pytest.mark.asyncio
    async def test_execute_with_valid_model(self):
        """Test execute with valid model."""
        server = OrchestratorMCPServer()
        result = await server.handle_tool_call(
            "orchestrator_execute",
            {
                "model": "haiku",
                "prompt": "Test prompt",
                "max_tokens": 100
            }
        )

        assert "success" in result
        assert "response" in result
        assert "tokens" in result
        assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_execute_with_invalid_model(self):
        """Test execute with invalid model returns error."""
        server = OrchestratorMCPServer()
        result = await server.handle_tool_call(
            "orchestrator_execute",
            {
                "model": "invalid-model",
                "prompt": "Test prompt"
            }
        )

        assert result["success"] is False
        assert "Unknown model" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_output(self):
        """Test validate output."""
        server = OrchestratorMCPServer()
        result = await server.handle_tool_call(
            "orchestrator_validate",
            {
                "task": "Fix bug in authentication",
                "output": "Fixed the auth bug by updating the token validation"
            }
        )

        assert "pass" in result
        assert "issues" in result
        assert "confidence" in result
        assert "escalate" in result
        assert isinstance(result["pass"], bool)
        assert isinstance(result["issues"], list)

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        """Test unknown tool returns error."""
        server = OrchestratorMCPServer()
        result = await server.handle_tool_call(
            "unknown_tool",
            {}
        )

        assert "error" in result
        assert "Unknown tool" in result["error"]

    @pytest.mark.asyncio
    async def test_route_empty_task(self):
        """Test routing empty task."""
        server = OrchestratorMCPServer()
        result = await server.handle_tool_call(
            "orchestrator_route",
            {"task": ""}
        )

        assert "model" in result
        assert "complexity_score" in result
        # Empty task should route to lowest tier
        assert result["model"] == "gemini-flash"

    @pytest.mark.asyncio
    async def test_execute_all_models(self):
        """Test execute works with all supported models."""
        server = OrchestratorMCPServer()
        models = ["gemini-flash", "gemini-pro", "haiku", "sonnet", "opus"]

        for model in models:
            result = await server.handle_tool_call(
                "orchestrator_execute",
                {
                    "model": model,
                    "prompt": "Test prompt"
                }
            )

            assert "success" in result
            assert "response" in result
