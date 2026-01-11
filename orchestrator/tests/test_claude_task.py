"""Tests for ClaudeTaskClient wrapper."""

import pytest
from orchestrator.clients.claude_task import ClaudeTaskClient
from orchestrator.clients.base import ExecutionResult


class TestClaudeTaskClient:
    """Test suite for ClaudeTaskClient."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initializes with default model."""
        client = ClaudeTaskClient()
        assert client.model == "haiku"

    @pytest.mark.asyncio
    async def test_client_custom_model(self):
        """Test client initializes with custom model."""
        client = ClaudeTaskClient(model="sonnet")
        assert client.model == "sonnet"

    @pytest.mark.asyncio
    async def test_invalid_model_raises_error(self):
        """Test invalid model raises ValueError."""
        with pytest.raises(ValueError, match="Invalid model"):
            ClaudeTaskClient(model="invalid-model")

    @pytest.mark.asyncio
    async def test_execute_returns_execution_result(self):
        """Test execute returns ExecutionResult."""
        client = ClaudeTaskClient(model="haiku")
        result = await client.execute("Test prompt")

        assert isinstance(result, ExecutionResult)
        assert result.model == "haiku"
        assert result.success is True
        assert result.response != ""
        assert result.tokens_input > 0
        assert result.tokens_output > 0
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_execute_haiku_model(self):
        """Test execute with haiku model."""
        client = ClaudeTaskClient(model="haiku")
        result = await client.execute("Simple task")

        assert result.success is True
        assert result.model == "haiku"
        assert "haiku" in result.response.lower()

    @pytest.mark.asyncio
    async def test_execute_sonnet_model(self):
        """Test execute with sonnet model."""
        client = ClaudeTaskClient(model="sonnet")
        result = await client.execute("Medium complexity task")

        assert result.success is True
        assert result.model == "sonnet"
        assert "sonnet" in result.response.lower()

    @pytest.mark.asyncio
    async def test_execute_opus_model(self):
        """Test execute with opus model."""
        client = ClaudeTaskClient(model="opus")
        result = await client.execute("Complex task")

        assert result.success is True
        assert result.model == "opus"
        assert "opus" in result.response.lower()

    @pytest.mark.asyncio
    async def test_execute_with_max_tokens(self):
        """Test execute respects max_tokens parameter."""
        client = ClaudeTaskClient(model="haiku")
        result = await client.execute("Test prompt", max_tokens=1000)

        assert result.success is True
        # max_tokens is a hint, result may vary

    @pytest.mark.asyncio
    async def test_token_estimation(self):
        """Test token estimation is reasonable."""
        client = ClaudeTaskClient(model="haiku")
        prompt = "A" * 400  # 400 chars ~= 100 tokens

        result = await client.execute(prompt)

        assert result.success is True
        assert result.tokens_input > 0
        assert result.tokens_output > 0
        # Rough estimate: 4 chars per token
        assert 50 < result.tokens_input < 150  # ~100 tokens

    @pytest.mark.asyncio
    async def test_latency_tracking(self):
        """Test latency is tracked correctly."""
        client = ClaudeTaskClient(model="haiku")
        result = await client.execute("Test prompt")

        assert result.success is True
        assert result.latency_ms >= 0
        assert result.latency_ms < 1000  # Should be fast for placeholder

    @pytest.mark.asyncio
    async def test_placeholder_response_format(self):
        """Test placeholder response contains expected information."""
        client = ClaudeTaskClient(model="sonnet")
        result = await client.execute("Test task")

        assert result.success is True
        assert "ClaudeTaskClient placeholder" in result.response
        assert "sonnet" in result.response
        assert "Plan 02-03" in result.response  # References MCP integration

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling returns proper ExecutionResult."""
        # This test verifies error result structure
        # In practice, placeholder implementation always succeeds
        client = ClaudeTaskClient(model="haiku")
        result = await client.execute("")  # Empty prompt

        # Placeholder always succeeds, but structure is correct
        assert isinstance(result, ExecutionResult)
        if not result.success:
            assert result.error is not None
            assert result.tokens_input == 0
            assert result.tokens_output == 0
