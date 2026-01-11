"""Tests for Anthropic API client."""

import json
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.clients.anthropic_client import AnthropicClient
from orchestrator.clients.base import ExecutionResult


@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client for testing."""
    with patch('orchestrator.clients.anthropic_client.Anthropic') as mock:
        yield mock


@pytest.mark.asyncio
async def test_anthropic_client_success(mock_anthropic):
    """Test successful execution via Anthropic API."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Here is the generated response.")]
    mock_response.usage = MagicMock(input_tokens=50, output_tokens=100)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    client = AnthropicClient(model="haiku")
    result = await client.execute("Test prompt")

    assert result.success is True
    assert result.model == "haiku"
    assert result.response == "Here is the generated response."
    assert result.tokens_input == 50
    assert result.tokens_output == 100
    assert result.latency_ms >= 0
    assert result.error is None


@pytest.mark.asyncio
async def test_anthropic_client_api_error(mock_anthropic):
    """Test handling of API errors."""
    mock_client = MagicMock()
    # Create a custom exception class that mimics APIError
    class APIError(Exception):
        pass
    api_error = APIError("Rate limit exceeded")
    mock_client.messages.create.side_effect = api_error
    mock_anthropic.return_value = mock_client

    client = AnthropicClient(model="sonnet")
    result = await client.execute("Test prompt")

    assert result.success is False
    assert "Rate limit exceeded" in result.error
    assert result.response == ""
    assert result.tokens_input == 0
    assert result.tokens_output == 0


@pytest.mark.asyncio
async def test_anthropic_client_unexpected_error(mock_anthropic):
    """Test handling of unexpected exceptions."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = RuntimeError("Network error")
    mock_anthropic.return_value = mock_client

    client = AnthropicClient(model="opus")
    result = await client.execute("Test prompt")

    assert result.success is False
    assert "Unexpected error" in result.error
    assert "Network error" in result.error


@pytest.mark.asyncio
async def test_anthropic_client_haiku_model(mock_anthropic):
    """Test using Haiku model."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Haiku response")]
    mock_response.usage = MagicMock(input_tokens=30, output_tokens=60)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    client = AnthropicClient(model="haiku")
    result = await client.execute("Test")

    # Verify correct model ID was used
    call_args = mock_client.messages.create.call_args
    assert call_args[1]["model"] == "claude-3-5-haiku-20241022"
    assert result.success is True
    assert result.model == "haiku"


@pytest.mark.asyncio
async def test_anthropic_client_sonnet_model(mock_anthropic):
    """Test using Sonnet model."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Sonnet response")]
    mock_response.usage = MagicMock(input_tokens=40, output_tokens=80)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    client = AnthropicClient(model="sonnet")
    result = await client.execute("Test")

    # Verify correct model ID was used
    call_args = mock_client.messages.create.call_args
    assert call_args[1]["model"] == "claude-3-5-sonnet-20241022"
    assert result.success is True
    assert result.model == "sonnet"


@pytest.mark.asyncio
async def test_anthropic_client_opus_model(mock_anthropic):
    """Test using Opus model."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Opus response")]
    mock_response.usage = MagicMock(input_tokens=50, output_tokens=100)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    client = AnthropicClient(model="opus")
    result = await client.execute("Test")

    # Verify correct model ID was used
    call_args = mock_client.messages.create.call_args
    assert call_args[1]["model"] == "claude-opus-4-20250514"
    assert result.success is True
    assert result.model == "opus"


@pytest.mark.asyncio
async def test_anthropic_client_custom_max_tokens(mock_anthropic):
    """Test execution with custom max_tokens."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Response")]
    mock_response.usage = MagicMock(input_tokens=25, output_tokens=75)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    client = AnthropicClient(model="haiku")
    result = await client.execute("Test", max_tokens=2048)

    # Verify max_tokens was passed correctly
    call_args = mock_client.messages.create.call_args
    assert call_args[1]["max_tokens"] == 2048
    assert result.success is True


@pytest.mark.asyncio
async def test_anthropic_client_validation_success(mock_anthropic):
    """Test validation method with valid JSON response."""
    mock_response = MagicMock()
    validation_result = {
        "pass": True,
        "issues": [],
        "confidence": 0.95,
        "escalate": False
    }
    mock_response.content = [MagicMock(text=json.dumps(validation_result))]
    mock_response.usage = MagicMock(input_tokens=80, output_tokens=20)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    client = AnthropicClient(model="sonnet")
    result = await client.validate("Create a function", "def foo(): pass")

    assert result["pass"] is True
    assert result["confidence"] == 0.95
    assert result["escalate"] is False


@pytest.mark.asyncio
async def test_anthropic_client_validation_failure(mock_anthropic):
    """Test validation method with failing validation."""
    mock_response = MagicMock()
    validation_result = {
        "pass": False,
        "issues": ["Missing docstring", "No type hints"],
        "confidence": 0.8,
        "escalate": False
    }
    mock_response.content = [MagicMock(text=json.dumps(validation_result))]
    mock_response.usage = MagicMock(input_tokens=80, output_tokens=30)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    client = AnthropicClient(model="sonnet")
    result = await client.validate("Create a function", "def foo(): pass")

    assert result["pass"] is False
    assert len(result["issues"]) == 2
    assert result["confidence"] == 0.8


@pytest.mark.asyncio
async def test_anthropic_client_validation_invalid_json(mock_anthropic):
    """Test validation with invalid JSON response."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Not valid JSON")]
    mock_response.usage = MagicMock(input_tokens=80, output_tokens=10)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    client = AnthropicClient(model="sonnet")
    result = await client.validate("Task", "Output")

    assert result["pass"] is False
    assert "Invalid JSON response" in result["issues"]
    assert result["escalate"] is True


@pytest.mark.asyncio
async def test_anthropic_client_validation_api_error(mock_anthropic):
    """Test validation when API call fails."""
    mock_client = MagicMock()
    # Create a custom exception class that mimics APIError
    class APIError(Exception):
        pass
    api_error = APIError("API error")
    mock_client.messages.create.side_effect = api_error
    mock_anthropic.return_value = mock_client

    client = AnthropicClient(model="sonnet")
    result = await client.validate("Task", "Output")

    assert result["pass"] is False
    assert result["escalate"] is True
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_anthropic_client_latency_tracking(mock_anthropic):
    """Test that latency is tracked correctly."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Response")]
    mock_response.usage = MagicMock(input_tokens=20, output_tokens=40)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    client = AnthropicClient(model="haiku")
    result = await client.execute("Test")

    # Latency should be non-negative and reasonable
    assert result.latency_ms >= 0
    assert result.latency_ms < 10000  # Should be < 10s for mocked call


@pytest.mark.asyncio
async def test_anthropic_client_model_mapping():
    """Test that model name mapping is correct."""
    assert AnthropicClient.MODEL_MAP["haiku"] == "claude-3-5-haiku-20241022"
    assert AnthropicClient.MODEL_MAP["sonnet"] == "claude-3-5-sonnet-20241022"
    assert AnthropicClient.MODEL_MAP["opus"] == "claude-opus-4-20250514"
