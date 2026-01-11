"""Orchestrator data models for task complexity and routing."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, Optional


class Task(BaseModel):
    """Represents a task to be routed to an appropriate model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Add authentication to the user API endpoint",
                "context": {
                    "files_count": 3,
                    "requires_tests": True,
                    "external_apis": ["Auth0"],
                }
            }
        }
    )

    description: str = Field(..., description="Task description text")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for complexity scoring"
    )


class TaskComplexity(BaseModel):
    """Result of complexity scoring analysis."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "score": 6.5,
                "factors": {
                    "task_length": 1.5,
                    "keywords": 2.0,
                    "file_count": 1.5,
                    "requires_tests": 1.5,
                },
                "recommended_tier": 2,
                "confidence": 0.85,
            }
        }
    )

    score: float = Field(..., ge=0.0, le=10.0, description="Complexity score 0-10")
    factors: Dict[str, float] = Field(
        ...,
        description="Breakdown of scoring factors"
    )
    recommended_tier: int = Field(
        ...,
        ge=0,
        le=3,
        description="Recommended model tier (0=Flash, 1=Haiku, 2=Sonnet, 3=Opus)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the scoring (0-1)"
    )
