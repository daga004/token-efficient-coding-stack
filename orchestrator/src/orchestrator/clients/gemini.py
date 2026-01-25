"""Gemini CLI wrapper for executing tasks via subprocess."""

import asyncio
import os
import subprocess
import time
from typing import Optional

from .base import ExecutionResult, ModelClient


class GeminiClient(ModelClient):
    """Client for executing prompts via Gemini CLI."""

    # Map internal model names to Gemini CLI model identifiers
    MODEL_MAPPING = {
        "gemini-flash": "gemini-3-flash-preview",
        "gemini-pro": "gemini-3-pro-preview",
    }

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

        Note:
            Token counts are estimated using 4-char/token approximation.
            The Gemini CLI does not expose actual token counts, so this
            limitation is inherent to the CLI-based approach.
        """
        start_time = time.time()

        try:
            # Run gemini CLI command as subprocess
            result = await self._run_cli_command(prompt, max_tokens)

            if result.returncode != 0:
                # Check for specific error cases
                error_msg = result.stderr
                if "GEMINI_API_KEY" in error_msg or "environment variable not set" in error_msg:
                    error_msg = (
                        "GEMINI_API_KEY environment variable not set. "
                        "Get your API key from: https://aistudio.google.com/apikey"
                    )
                return self._create_error_result(
                    error_msg=error_msg,
                    latency_ms=self._calculate_latency(start_time)
                )

            # Parse successful response (strip CLI status messages)
            response_text = result.stdout.strip()

            # Remove CLI status prefixes (YOLO mode, API key messages, etc.)
            lines = response_text.split('\n')
            # Skip lines that start with known CLI prefixes
            cli_prefixes = ['YOLO mode', 'When using Gemini', 'Update your environment']
            response_lines = [
                line for line in lines
                if not any(line.startswith(prefix) for prefix in cli_prefixes)
            ]
            response_text = '\n'.join(response_lines).strip()

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
                error_msg=(
                    "Gemini CLI not found. Install with: "
                    "npm install -g @google/gemini-cli OR brew install gemini-cli"
                ),
                latency_ms=0
            )
        except EnvironmentError as e:
            return self._create_error_result(
                error_msg=str(e),
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
            max_tokens: Maximum output tokens (not used - CLI handles server-side)

        Returns:
            CompletedProcess with stdout/stderr
        """
        # Map model name to CLI identifier
        cli_model = self.MODEL_MAPPING.get(self.model, "gemini-3-flash")

        # Gemini CLI syntax: gemini "prompt" --model <model> -y
        # Positional argument for prompt, not -p flag
        cmd = [
            "gemini",
            prompt,                  # Positional argument (not -p flag)
            "--model", cli_model,    # Specify model
            "-y",                    # YOLO mode (auto-approve all actions)
        ]

        # Ensure GEMINI_API_KEY is in environment
        env = os.environ.copy()
        if "GEMINI_API_KEY" not in env:
            # Check if API key is set in environment
            raise EnvironmentError(
                "GEMINI_API_KEY environment variable not set. "
                "Get your API key from: https://aistudio.google.com/apikey"
            )

        # Run subprocess in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env
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
