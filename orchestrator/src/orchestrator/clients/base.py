"""Base classes and shared interfaces for model clients."""

from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict, Field


class ExecutionResult(BaseModel):
    """Unified result format for all model client executions."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "gemini-flash",
                "response": "Here is the generated code...",
                "tokens_input": 150,
                "tokens_output": 400,
                "latency_ms": 1250,
                "success": True,
                "error": None,
            }
        }
    )

    model: str = Field(..., description="Model identifier used for execution")
    response: str = Field(..., description="Generated response text")
    tokens_input: int = Field(..., ge=0, description="Number of input tokens consumed")
    tokens_output: int = Field(..., ge=0, description="Number of output tokens generated")
    latency_ms: int = Field(..., ge=0, description="Execution latency in milliseconds")
    success: bool = Field(..., description="Whether execution succeeded")
    error: str | None = Field(default=None, description="Error message if execution failed")


class ModelClient(ABC):
    """Abstract base class for model clients."""

    @abstractmethod
    async def execute(self, prompt: str, max_tokens: int = 4096) -> ExecutionResult:
        """
        Execute a prompt on the model and return the result.

        Args:
            prompt: The input prompt/task to execute
            max_tokens: Maximum number of output tokens to generate

        Returns:
            ExecutionResult with response and metadata
        """
        pass
