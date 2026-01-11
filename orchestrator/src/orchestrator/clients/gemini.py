"""Gemini CLI wrapper for executing tasks via subprocess."""

import asyncio
import subprocess
import time
from typing import Optional

from .base import ExecutionResult, ModelClient


class GeminiClient(ModelClient):
    """Client for executing prompts via Gemini CLI."""

    def __init__(self, model: str = "gemini-flash", timeout: int = 30):
        """
        Initialize Gemini CLI client.

        Args:
            model: Model identifier (gemini-flash or gemini-pro)
            timeout: Maximum execution time in seconds
        """
        self.model = model
        self.timeout = timeout

    async def execute(self, prompt: str, max_tokens: int = 8192) -> ExecutionResult:
        """
        Execute a prompt via Gemini CLI and return the result.

        Args:
            prompt: The input prompt/task to execute
            max_tokens: Maximum number of output tokens to generate

        Returns:
            ExecutionResult with response and metadata
        """
        start_time = time.time()

        try:
            # Run gemini CLI command as subprocess
            result = await self._run_cli_command(prompt, max_tokens)

            if result.returncode != 0:
                return self._create_error_result(
                    error_msg=result.stderr,
                    latency_ms=self._calculate_latency(start_time)
                )

            # Parse successful response
            response_text = result.stdout.strip()
            tokens_input = self._estimate_tokens(prompt)
            tokens_output = self._estimate_tokens(response_text)

            return ExecutionResult(
                model=self.model,
                response=response_text,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                latency_ms=self._calculate_latency(start_time),
                success=True
            )

        except asyncio.TimeoutError:
            return self._create_error_result(
                error_msg=f"Timeout after {self.timeout}s",
                latency_ms=self.timeout * 1000
            )
        except FileNotFoundError:
            return self._create_error_result(
                error_msg="Gemini CLI not installed. Run: pip install google-generativeai",
                latency_ms=0
            )
        except Exception as e:
            return self._create_error_result(
                error_msg=f"Unexpected error: {str(e)}",
                latency_ms=self._calculate_latency(start_time)
            )

    async def _run_cli_command(
        self, prompt: str, max_tokens: int
    ) -> subprocess.CompletedProcess:
        """
        Run gemini CLI command asynchronously.

        Args:
            prompt: Input prompt
            max_tokens: Maximum output tokens

        Returns:
            CompletedProcess with stdout/stderr
        """
        cmd = [
            "gemini",
            "generate",
            f"--model={self.model}",
            f"--max-tokens={max_tokens}",
            "--prompt",
            prompt,
        ]

        # Run subprocess in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
        )
        return result

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Rough estimate: 4 characters per token
        return max(1, len(text) // 4)

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
        self, error_msg: str, latency_ms: int
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
