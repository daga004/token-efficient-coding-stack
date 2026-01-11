"""Claude Task tool client for executing tasks via Claude Code's internal routing."""

import time
from typing import Optional

from .base import ExecutionResult, ModelClient


class ClaudeTaskClient(ModelClient):
    """
    Client for executing prompts via Claude Code's Task tool with model routing.

    This client uses Claude Code's native Task spawning capability to route
    tasks to specific Claude models (Haiku, Sonnet, Opus) without direct API calls.

    Architecture:
        - NO direct Anthropic API usage
        - Uses Claude Code's Task tool with model parameter
        - Actual Task spawning happens in MCP server (Plan 02-03)
        - Standalone mode returns placeholder for testing
    """

    # Model name mapping from registry to Task tool
    MODEL_MAP = {
        "haiku": "haiku",
        "sonnet": "sonnet",
        "opus": "opus"
    }

    def __init__(self, model: str = "haiku"):
        """
        Initialize Claude Task client.

        Args:
            model: Model identifier (haiku, sonnet, or opus)
        """
        self.model = model
        self._validate_model()

    def _validate_model(self):
        """Validate that model is supported."""
        if self.model not in self.MODEL_MAP:
            raise ValueError(
                f"Invalid model: {self.model}. "
                f"Must be one of: {list(self.MODEL_MAP.keys())}"
            )

    async def execute(self, prompt: str, max_tokens: int = 4096) -> ExecutionResult:
        """
        Execute a prompt via Claude Code Task tool with specified model.

        This uses Claude Code's native Task spawning capability to run
        the prompt on a specific Claude model without direct API calls.

        Args:
            prompt: The input prompt/task to execute
            max_tokens: Maximum number of output tokens (hint for Task tool)

        Returns:
            ExecutionResult with response and metadata

        Note:
            In standalone mode (testing), returns placeholder response.
            In MCP server mode (Plan 02-03), integrates with Claude Code's
            Task API to actually spawn sub-agents with specified model.
        """
        start_time = time.time()
        model_id = self.MODEL_MAP.get(self.model, self.model)

        try:
            # Placeholder for Task tool integration
            # In MCP server (Plan 02-03), this will call Claude Code's
            # Task spawning API with model parameter

            # For now, return placeholder response for testing
            response_text = self._generate_placeholder_response(prompt, model_id)

            # Estimate tokens (rough: 4 chars = 1 token)
            tokens_input = len(prompt) // 4
            tokens_output = len(response_text) // 4

            return ExecutionResult(
                model=self.model,
                response=response_text,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                latency_ms=self._calculate_latency(start_time),
                success=True
            )

        except Exception as e:
            return self._create_error_result(
                error_msg=f"Task tool error: {str(e)}",
                latency_ms=self._calculate_latency(start_time)
            )

    def _generate_placeholder_response(self, prompt: str, model_id: str) -> str:
        """
        Generate placeholder response for testing.

        Args:
            prompt: Input prompt
            model_id: Model identifier

        Returns:
            Placeholder response text
        """
        return (
            f"[ClaudeTaskClient placeholder response]\n"
            f"Model: {model_id}\n"
            f"Prompt length: {len(prompt)} chars\n"
            f"Note: Actual Task tool integration happens in MCP server (Plan 02-03)"
        )

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
