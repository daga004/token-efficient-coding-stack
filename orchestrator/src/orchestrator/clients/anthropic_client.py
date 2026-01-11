"""Anthropic API client for executing tasks via official SDK."""

import json
import os
import time
from typing import Dict, Optional

from .base import ExecutionResult, ModelClient

try:
    from anthropic import Anthropic, APIError
except ImportError:
    # Allow import even if anthropic not installed (for testing)
    Anthropic = None
    APIError = Exception


class AnthropicClient(ModelClient):
    """Client for executing prompts via Anthropic API."""

    # Model name mapping from short names to full IDs
    MODEL_MAP = {
        "haiku": "claude-3-5-haiku-20241022",
        "sonnet": "claude-3-5-sonnet-20241022",
        "opus": "claude-opus-4-20250514",
    }

    def __init__(
        self,
        model: str = "haiku",
        api_key: Optional[str] = None
    ):
        """
        Initialize Anthropic API client.

        Args:
            model: Model identifier (haiku, sonnet, or opus)
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        if Anthropic is None:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )

        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key)

    async def execute(self, prompt: str, max_tokens: int = 4096) -> ExecutionResult:
        """
        Execute a prompt via Anthropic API and return the result.

        Args:
            prompt: The input prompt/task to execute
            max_tokens: Maximum number of output tokens to generate

        Returns:
            ExecutionResult with response and metadata
        """
        start_time = time.time()
        model_id = self.MODEL_MAP.get(self.model, self.model)

        try:
            # Make API call (synchronous SDK, but in async context)
            response = self.client.messages.create(
                model=model_id,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract response text
            response_text = response.content[0].text

            return ExecutionResult(
                model=self.model,
                response=response_text,
                tokens_input=response.usage.input_tokens,
                tokens_output=response.usage.output_tokens,
                latency_ms=self._calculate_latency(start_time),
                success=True
            )

        except Exception as e:
            # Handle both APIError and other exceptions uniformly
            return self._create_error_result(
                error_msg=f"Unexpected error: {str(e)}",
                latency_ms=self._calculate_latency(start_time)
            )

    async def validate(
        self,
        task: str,
        output: str,
        max_tokens: int = 100
    ) -> Dict:
        """
        Validate output against task requirements using Sonnet.

        Args:
            task: Original task description
            output: Output to validate
            max_tokens: Maximum tokens for validation response

        Returns:
            Dictionary with validation results
        """
        validation_prompt = f"""<context>{task}</context>
<output_to_validate>{output}</output_to_validate>

Validate the output against the task requirements.
Respond ONLY with JSON (max {max_tokens} tokens):
{{"pass": bool, "issues": ["max 3 items"], "confidence": 0-1, "escalate": bool}}"""

        result = await self.execute(validation_prompt, max_tokens=max_tokens)

        if not result.success:
            return {
                "pass": False,
                "issues": [result.error],
                "confidence": 0.0,
                "escalate": True
            }

        try:
            return json.loads(result.response)
        except json.JSONDecodeError:
            return {
                "pass": False,
                "issues": ["Invalid JSON response"],
                "confidence": 0.0,
                "escalate": True
            }

    def _calculate_latency(self, start_time: float) -> int:
        """
        Calculate latency in milliseconds.

        Args:
            start_time: Start time from time.time()

        Returns:
            Latency in milliseconds
        """
        return int((time.time() - start_time) * 1000)

    def _create_error_result(
        self,
        error_msg: str,
        latency_ms: int
    ) -> ExecutionResult:
        """
        Create an error ExecutionResult.

        Args:
            error_msg: Error message
            latency_ms: Execution latency

        Returns:
            ExecutionResult with success=False
        """
        return ExecutionResult(
            model=self.model,
            response="",
            tokens_input=0,
            tokens_output=0,
            latency_ms=latency_ms,
            success=False,
            error=error_msg
        )
