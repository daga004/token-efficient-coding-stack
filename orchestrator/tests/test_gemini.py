"""Tests for Gemini CLI client."""

import asyncio
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orchestrator.clients.gemini import GeminiClient
from orchestrator.clients.base import ExecutionResult


@pytest.mark.asyncio
async def test_gemini_client_success():
    """Test successful execution via Gemini CLI."""
    client = GeminiClient(model="gemini-flash")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Here is the generated code for your task."
    mock_result.stderr = ""

    with patch.object(client, '_run_cli_command', return_value=mock_result):
        result = await client.execute("Write a hello world function")

    assert result.success is True
    assert result.model == "gemini-flash"
    assert result.response == "Here is the generated code for your task."
    assert result.tokens_input > 0
    assert result.tokens_output > 0
    assert result.latency_ms >= 0
    assert result.error is None


@pytest.mark.asyncio
async def test_gemini_client_cli_error():
    """Test handling of CLI execution errors."""
    client = GeminiClient(model="gemini-flash")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "API key not configured"

    with patch.object(client, '_run_cli_command', return_value=mock_result):
        result = await client.execute("Test prompt")

    assert result.success is False
    assert result.error == "API key not configured"
    assert result.response == ""
    assert result.tokens_input == 0
    assert result.tokens_output == 0


@pytest.mark.asyncio
async def test_gemini_client_timeout():
    """Test timeout handling."""
    client = GeminiClient(model="gemini-flash", timeout=1)

    async def mock_timeout(*args, **kwargs):
        raise asyncio.TimeoutError()

    with patch.object(client, '_run_cli_command', side_effect=mock_timeout):
        result = await client.execute("Test prompt")

    assert result.success is False
    assert "Timeout after 1s" in result.error
    assert result.latency_ms == 1000


@pytest.mark.asyncio
async def test_gemini_client_missing_cli():
    """Test handling when Gemini CLI is not installed."""
    client = GeminiClient(model="gemini-flash")

    async def mock_file_not_found(*args, **kwargs):
        raise FileNotFoundError()

    with patch.object(client, '_run_cli_command', side_effect=mock_file_not_found):
        result = await client.execute("Test prompt")

    assert result.success is False
    assert "not installed" in result.error
    assert "pip install google-generativeai" in result.error
    assert result.latency_ms == 0


@pytest.mark.asyncio
async def test_gemini_client_unexpected_error():
    """Test handling of unexpected exceptions."""
    client = GeminiClient(model="gemini-flash")

    async def mock_exception(*args, **kwargs):
        raise RuntimeError("Unexpected runtime error")

    with patch.object(client, '_run_cli_command', side_effect=mock_exception):
        result = await client.execute("Test prompt")

    assert result.success is False
    assert "Unexpected error" in result.error
    assert "Unexpected runtime error" in result.error


@pytest.mark.asyncio
async def test_gemini_client_token_estimation():
    """Test token estimation logic."""
    client = GeminiClient()

    # Test with known text lengths
    short_text = "Hello"
    assert client._estimate_tokens(short_text) == max(1, len(short_text) // 4)

    long_text = "A" * 1000
    assert client._estimate_tokens(long_text) == max(1, len(long_text) // 4)

    # Empty string should return at least 1
    assert client._estimate_tokens("") == 1


@pytest.mark.asyncio
async def test_gemini_client_with_max_tokens():
    """Test execution with custom max_tokens parameter."""
    client = GeminiClient(model="gemini-pro")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Response with custom token limit"
    mock_result.stderr = ""

    with patch.object(client, '_run_cli_command', return_value=mock_result):
        result = await client.execute("Test prompt", max_tokens=4096)

    assert result.success is True
    assert result.model == "gemini-pro"


@pytest.mark.asyncio
async def test_gemini_client_latency_calculation():
    """Test latency calculation is reasonable."""
    client = GeminiClient()

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Quick response"
    mock_result.stderr = ""

    with patch.object(client, '_run_cli_command', return_value=mock_result):
        result = await client.execute("Test")

    # Latency should be non-negative and reasonable (< 10s for mocked call)
    assert result.latency_ms >= 0
    assert result.latency_ms < 10000


@pytest.mark.asyncio
async def test_execution_result_model():
    """Test ExecutionResult model validation."""
    result = ExecutionResult(
        model="test-model",
        response="test response",
        tokens_input=100,
        tokens_output=200,
        latency_ms=500,
        success=True,
        error=None
    )

    assert result.model == "test-model"
    assert result.response == "test response"
    assert result.tokens_input == 100
    assert result.tokens_output == 200
    assert result.latency_ms == 500
    assert result.success is True
    assert result.error is None


@pytest.mark.asyncio
async def test_execution_result_with_error():
    """Test ExecutionResult with error condition."""
    result = ExecutionResult(
        model="test-model",
        response="",
        tokens_input=0,
        tokens_output=0,
        latency_ms=100,
        success=False,
        error="Some error occurred"
    )

    assert result.success is False
    assert result.error == "Some error occurred"
    assert result.response == ""
