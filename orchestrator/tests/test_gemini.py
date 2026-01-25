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
    assert "Gemini CLI not found" in result.error
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


@pytest.mark.asyncio
async def test_cli_command_structure():
    """Test that CLI command uses correct syntax."""
    import os

    client = GeminiClient(model="gemini-flash")

    # Mock environment with API key
    test_env = os.environ.copy()
    test_env["GEMINI_API_KEY"] = "test-key-123"

    with patch("os.environ", test_env):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Test response",
                stderr=""
            )

            # Execute to trigger command building
            result = await client.execute("What is 2+2?")

            # Verify subprocess.run was called with correct command structure
            assert mock_run.called
            call_args = mock_run.call_args
            cmd = call_args[0][0]

            # Command should be: ["gemini", "prompt", "--model", "gemini-3-flash-preview", "-y"]
            assert cmd[0] == "gemini"
            assert cmd[1] == "What is 2+2?"  # Positional prompt
            assert "--model" in cmd
            assert "gemini-3-flash-preview" in cmd
            assert "-y" in cmd  # YOLO mode

            # Verify environment includes GEMINI_API_KEY
            kwargs = call_args[1]
            assert "env" in kwargs
            assert "GEMINI_API_KEY" in kwargs["env"]


@pytest.mark.asyncio
async def test_cli_output_parsing():
    """Test that CLI status messages are stripped from response."""
    client = GeminiClient(model="gemini-flash")

    # Mock result with CLI status prefixes
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = """YOLO mode is enabled.
When using Gemini API, you must accept the terms.
This is the actual response from the model.
It spans multiple lines."""
    mock_result.stderr = ""

    with patch.object(client, '_run_cli_command', return_value=mock_result):
        result = await client.execute("Test prompt")

    # Response should not contain CLI status messages
    assert "YOLO mode" not in result.response
    assert "When using Gemini" not in result.response
    assert "This is the actual response from the model." in result.response
    assert "It spans multiple lines." in result.response
    assert result.success is True


@pytest.mark.asyncio
async def test_api_key_error_handling():
    """Test specific error handling for missing API key."""
    client = GeminiClient(model="gemini-flash")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Error: GEMINI_API_KEY environment variable not set"

    with patch.object(client, '_run_cli_command', return_value=mock_result):
        result = await client.execute("Test prompt")

    assert result.success is False
    assert "GEMINI_API_KEY environment variable not set" in result.error
    assert "https://aistudio.google.com/apikey" in result.error
