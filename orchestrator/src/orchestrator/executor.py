"""Unified executor with retry logic and intelligent tier-based routing."""

import asyncio
import json
from typing import Optional

from .clients.base import ExecutionResult
from .clients.gemini import GeminiClient
from .clients.claude_task import ClaudeTaskClient
from .registry import ModelRegistry, ModelTier


class Executor:
    """
    Unified executor that routes tasks to appropriate models with retry and fallback.

    Architecture:
    - Tier 0 (Flash, Pro): External Gemini CLI
    - Tier 1-3 (Haiku, Sonnet, Opus): Claude Code Task tool (internal)

    Features:
    - Automatic model selection based on tier
    - Exponential backoff retry logic
    - Fallback to higher tiers on persistent failure
    - Validation via Task tool
    """

    def __init__(self):
        """Initialize executor with clients and registry."""
        self.gemini = GeminiClient()
        self.claude_task = ClaudeTaskClient()
        self.registry = ModelRegistry()

    async def execute(
        self,
        model_tier: ModelTier,
        prompt: str,
        max_tokens: int = 4096,
        retry_count: int = 2
    ) -> ExecutionResult:
        """
        Execute task on specified model tier with retry and fallback logic.

        Args:
            model_tier: Target model tier for execution
            prompt: Input prompt/task to execute
            max_tokens: Maximum output tokens to generate
            retry_count: Number of retries on failure (default: 2)

        Returns:
            ExecutionResult with response and metadata

        Routing:
            - Tier 0 (Flash, Pro): Gemini CLI (external)
            - Tier 1 (Haiku): Claude Task tool (internal)
            - Tier 2 (Sonnet): Claude Task tool (internal)
            - Tier 3 (Opus): Claude Task tool (internal)

        Behavior:
            - Retries with exponential backoff (2^attempt seconds)
            - Falls back to next higher tier on persistent failure
            - Flash → Haiku fallback only (prevents infinite escalation)
        """
        # Get client and model for this tier
        client, model = self._get_client_for_tier(model_tier)

        # Retry loop with exponential backoff
        last_result = None
        for attempt in range(retry_count + 1):
            result = await client.execute(prompt, max_tokens)

            if result.success:
                return result

            last_result = result

            # If not last attempt, wait and retry
            if attempt < retry_count:
                backoff_seconds = 2 ** attempt
                await asyncio.sleep(backoff_seconds)

        # All retries failed - attempt fallback to next tier up
        if model_tier == ModelTier.FLASH:
            # Fallback Flash → Haiku (prevent endless escalation)
            return await self.execute(
                ModelTier.HAIKU,
                prompt,
                max_tokens,
                retry_count=0  # No retries on fallback
            )

        # No fallback available - return final failure
        return last_result

    async def validate_output(self, task: str, output: str) -> dict:
        """
        Validate output against task requirements using Sonnet.

        Validation is always input-heavy (large task context, small output),
        making Sonnet cost-effective despite higher base cost.

        Args:
            task: Original task description
            output: Output to validate

        Returns:
            Dictionary with validation results:
            - pass: bool - Whether output meets requirements
            - issues: List[str] - Up to 3 specific issues found
            - confidence: float - Validation confidence (0-1)
            - escalate: bool - Whether to escalate for manual review
        """
        validation_prompt = f"""<context>{task}</context>
<output_to_validate>{output}</output_to_validate>

Validate the output against the task requirements.
Respond ONLY with JSON:
{{"pass": bool, "issues": ["max 3 items"], "confidence": 0-1, "escalate": bool}}"""

        # Always use Sonnet for validation (input-heavy mode)
        validator = ClaudeTaskClient(model="sonnet")
        result = await validator.execute(validation_prompt, max_tokens=100)

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

    def _get_client_for_tier(self, tier: ModelTier) -> tuple:
        """
        Get appropriate client and model name for a given tier.

        Args:
            tier: ModelTier enum value

        Returns:
            Tuple of (client, model_name)

        Routing:
            - Tier 0 (Flash, Pro): Gemini CLI
            - Tier 1-3 (Haiku, Sonnet, Opus): Claude Task tool
        """
        if tier in [ModelTier.FLASH, ModelTier.PRO]:
            # External: Gemini CLI
            model = "gemini-flash" if tier == ModelTier.FLASH else "gemini-pro"
            return (self.gemini, model)
        else:
            # Internal: Claude Code Task tool
            model_map = {
                ModelTier.HAIKU: "haiku",
                ModelTier.SONNET: "sonnet",
                ModelTier.OPUS: "opus"
            }
            model = model_map[tier]
            return (self.claude_task, model)

    async def execute_with_validation(
        self,
        model_tier: ModelTier,
        task: str,
        max_tokens: int = 4096,
        retry_count: int = 2
    ) -> tuple[ExecutionResult, Optional[dict]]:
        """
        Execute task and automatically validate output.

        Args:
            model_tier: Target model tier
            task: Task description (used as prompt and for validation)
            max_tokens: Maximum output tokens
            retry_count: Retry count for execution

        Returns:
            Tuple of (ExecutionResult, validation_dict or None)
            validation_dict is None if execution failed
        """
        result = await self.execute(model_tier, task, max_tokens, retry_count)

        if not result.success:
            return (result, None)

        validation = await self.validate_output(task, result.response)
        return (result, validation)
