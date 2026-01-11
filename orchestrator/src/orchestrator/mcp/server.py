"""MCP server exposing orchestrator tools for Claude Code integration."""

import asyncio
from typing import Optional

from ..scoring import ComplexityScorer
from ..registry import ModelRegistry, ModelTier
from ..executor import Executor
from ..models import Task
from .jsonrpc_handler import JSONRPCHandler


class OrchestratorMCPServer:
    """
    MCP server providing intelligent model routing and execution.

    Tools:
    - orchestrator_route: Get routing recommendation based on complexity
    - orchestrator_execute: Execute task on specified model
    - orchestrator_validate: Validate output using Sonnet
    """

    def __init__(self):
        """Initialize orchestrator MCP server."""
        self.scorer = ComplexityScorer()
        self.registry = ModelRegistry()
        self.executor = Executor()

    async def handle_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """
        Dispatch tool calls to appropriate handlers.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result dictionary
        """
        if tool_name == "orchestrator_route":
            return await self._route(arguments)
        elif tool_name == "orchestrator_execute":
            return await self._execute(arguments)
        elif tool_name == "orchestrator_validate":
            return await self._validate(arguments)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    async def _route(self, args: dict) -> dict:
        """
        Get routing recommendation for a task.

        Args:
            args: {task: str, context: dict (optional)}

        Returns:
            {
                model: str,
                complexity_score: float,
                complexity_factors: dict,
                reason: str,
                confidence: float,
                estimated_cost: dict
            }
        """
        task_description = args.get("task", "")
        context = args.get("context", {})

        # Create Task object
        task = Task(description=task_description, context=context)

        # Score complexity
        complexity = self.scorer.score_task(task)

        # Get model recommendation
        model_tier = self.registry.get_model_for_score(complexity.score)
        profile = self.registry.models[model_tier]

        # Format response
        return {
            "model": model_tier.value,
            "complexity_score": complexity.score,
            "complexity_factors": complexity.factors,
            "reason": (
                f"Task scored {complexity.score:.1f}/10. "
                f"Recommended: {profile.name} (${profile.cost_per_1m_input}/1M in, "
                f"${profile.cost_per_1m_output}/1M out)"
            ),
            "confidence": complexity.confidence,
            "estimated_cost": {
                "model": profile.name,
                "cost_per_1m_input": profile.cost_per_1m_input,
                "cost_per_1m_output": profile.cost_per_1m_output
            }
        }

    async def _execute(self, args: dict) -> dict:
        """
        Execute task on specified model.

        Args:
            args: {model: str, prompt: str, max_tokens: int}

        Returns:
            {
                success: bool,
                response: str,
                tokens: {input: int, output: int},
                latency_ms: int,
                error: str | None
            }
        """
        model_name = args.get("model")
        prompt = args.get("prompt", "")
        max_tokens = args.get("max_tokens", 4096)

        # Map model name to tier
        model_map = {
            "gemini-flash": ModelTier.FLASH,
            "gemini-pro": ModelTier.PRO,
            "haiku": ModelTier.HAIKU,
            "sonnet": ModelTier.SONNET,
            "opus": ModelTier.OPUS
        }

        model_tier = model_map.get(model_name)
        if not model_tier:
            return {
                "success": False,
                "response": "",
                "tokens": {"input": 0, "output": 0},
                "latency_ms": 0,
                "error": f"Unknown model: {model_name}"
            }

        # Execute with retry logic
        result = await self.executor.execute(model_tier, prompt, max_tokens)

        return {
            "success": result.success,
            "response": result.response,
            "tokens": {
                "input": result.tokens_input,
                "output": result.tokens_output
            },
            "latency_ms": result.latency_ms,
            "error": result.error
        }

    async def _validate(self, args: dict) -> dict:
        """
        Validate output against task requirements.

        Args:
            args: {task: str, output: str}

        Returns:
            {
                pass: bool,
                issues: List[str],
                confidence: float,
                escalate: bool
            }
        """
        task = args.get("task", "")
        output = args.get("output", "")

        # Validate using Sonnet (input-heavy, cost-effective)
        validation = await self.executor.validate_output(task, output)

        return {
            "pass": validation.get("pass", False),
            "issues": validation.get("issues", []),
            "confidence": validation.get("confidence", 0.0),
            "escalate": validation.get("escalate", False)
        }

    def run(self):
        """Run MCP server (stdio protocol)."""
        handler = JSONRPCHandler(self)
        handler.run()


def main():
    """Entry point for MCP server."""
    server = OrchestratorMCPServer()
    server.run()


if __name__ == "__main__":
    main()
