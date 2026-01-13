"""
Real Claude API execution harness for validation testing.

Makes actual API calls (not simulations) to verify token/cost savings claims.
"""

import os
import time
from pathlib import Path
from typing import Any, Optional

from anthropic import Anthropic

from audit.harness import AuditTest
from audit.models import EvidenceType, TestStatus


class RealAPIExecutor(AuditTest):
    """Executes tasks with real Claude API calls and measures actual usage."""

    # Model pricing per million input tokens (as of Jan 2024)
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
        "claude-3-5-flash-20250107": {"input": 0.01, "output": 0.05},
        "claude-opus-4-5-20251101": {"input": 15.00, "output": 75.00},
    }

    def __init__(self, name: str, category: str, api_key: Optional[str] = None):
        """
        Initialize real API executor.

        Args:
            name: Test name
            category: Test category
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        super().__init__(name, category)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set and no api_key provided"
            )
        self.client = Anthropic(api_key=self.api_key)

    def execute_task(
        self,
        task_description: str,
        model: str,
        context_files: Optional[list[str]] = None,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Execute a task with real Claude API call.

        Args:
            task_description: Task prompt/description
            model: Claude model to use (e.g., claude-3-5-sonnet-20241022)
            context_files: Optional list of file paths to include as context
            max_tokens: Maximum output tokens

        Returns:
            Dict with:
                - input_tokens: Actual input tokens from API
                - output_tokens: Actual output tokens from API
                - cost: Actual cost in dollars
                - time_ms: Execution time in milliseconds
                - output: Response text
                - quality_score: 100 (success) or 0 (error)
        """
        # Build context from files
        context = ""
        if context_files:
            for file_path in context_files:
                path = Path(file_path)
                if path.exists():
                    context += f"\n\n# File: {file_path}\n\n{path.read_text()}"

        # Build full prompt
        full_prompt = task_description
        if context:
            full_prompt = f"Context files:\n{context}\n\nTask:\n{task_description}"

        # Execute with retries for rate limits
        max_retries = 3
        retry_delay = 1.0
        last_error = None

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                # Make actual API call
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": full_prompt}],
                )

                end_time = time.time()

                # Extract actual usage from API response
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens

                # Calculate actual cost
                pricing = self.PRICING.get(model)
                if not pricing:
                    raise ValueError(f"Unknown model pricing: {model}")

                cost = (
                    input_tokens * pricing["input"] / 1_000_000
                    + output_tokens * pricing["output"] / 1_000_000
                )

                # Extract response text
                output_text = ""
                for block in response.content:
                    if block.type == "text":
                        output_text += block.text

                result = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": cost,
                    "time_ms": (end_time - start_time) * 1000,
                    "output": output_text,
                    "quality_score": 100,  # API succeeded
                    "model": model,
                }

                # Log evidence
                self.evidence.log(
                    EvidenceType.API,
                    result,
                    metadata={
                        "task": task_description[:100],  # Truncate long descriptions
                        "context_files": context_files or [],
                    },
                )

                return result

            except Exception as e:
                last_error = e
                if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                    # Exponential backoff for rate limits
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    # Log error and return failure result
                    self.evidence.log(
                        EvidenceType.ERROR,
                        {"error": str(e), "attempt": attempt + 1},
                        metadata={"task": task_description[:100]},
                    )

                    return {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cost": 0.0,
                        "time_ms": 0.0,
                        "output": "",
                        "quality_score": 0,  # API failed
                        "model": model,
                        "error": str(e),
                    }

        # All retries exhausted
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "cost": 0.0,
            "time_ms": 0.0,
            "output": "",
            "quality_score": 0,
            "model": model,
            "error": str(last_error),
        }

    def execute(self) -> TestStatus:
        """
        Execute the test (implemented by subclasses).

        Base implementation just returns PASS. Override in specific test classes.
        """
        return TestStatus.PASS

    def verify(self) -> bool:
        """Verify that API key is configured."""
        return self.api_key is not None
