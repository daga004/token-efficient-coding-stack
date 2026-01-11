"""Model registry with tier profiles and cost estimation."""

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, List


class ModelTier(str, Enum):
    """Available model tiers for task routing."""

    FLASH = "gemini-flash"
    PRO = "gemini-pro"
    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


class ModelProfile(BaseModel):
    """Profile for a specific model including cost and capability info."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Gemini Flash",
                "tier": 0,
                "cost_per_1m_input": 0.01,
                "cost_per_1m_output": 0.04,
                "max_tokens": 8192,
                "best_for": ["simple_code", "tests", "docs"],
            }
        }
    )

    name: str = Field(..., description="Human-readable model name")
    tier: int = Field(..., ge=0, le=3, description="Tier level (0-3)")
    cost_per_1m_input: float = Field(..., description="Cost per 1M input tokens in USD")
    cost_per_1m_output: float = Field(..., description="Cost per 1M output tokens in USD")
    max_tokens: int = Field(..., description="Maximum context window size")
    best_for: List[str] = Field(
        default_factory=list,
        description="Task types this model excels at"
    )


class ModelRegistry:
    """Registry of available models with tier-based routing and cost estimation."""

    def __init__(self):
        """Initialize model registry with predefined model profiles."""
        self.models: Dict[ModelTier, ModelProfile] = {
            ModelTier.FLASH: ModelProfile(
                name="Gemini Flash",
                tier=0,
                cost_per_1m_input=0.01,
                cost_per_1m_output=0.04,
                max_tokens=8192,
                best_for=["simple_code", "tests", "docs", "comments"],
            ),
            ModelTier.PRO: ModelProfile(
                name="Gemini Pro",
                tier=0,
                cost_per_1m_input=0.125,
                cost_per_1m_output=0.50,
                max_tokens=32768,
                best_for=["simple_code", "tests", "basic_refactor"],
            ),
            ModelTier.HAIKU: ModelProfile(
                name="Claude Haiku",
                tier=1,
                cost_per_1m_input=0.80,
                cost_per_1m_output=4.00,
                max_tokens=200000,
                best_for=["moderate_code", "refactoring", "api_endpoints"],
            ),
            ModelTier.SONNET: ModelProfile(
                name="Claude Sonnet",
                tier=2,
                cost_per_1m_input=3.00,
                cost_per_1m_output=15.00,
                max_tokens=200000,
                best_for=["complex_logic", "validation", "architecture_review"],
            ),
            ModelTier.OPUS: ModelProfile(
                name="Claude Opus",
                tier=3,
                cost_per_1m_input=15.00,
                cost_per_1m_output=75.00,
                max_tokens=200000,
                best_for=["critical_decisions", "system_design", "security_audit"],
            ),
        }

    def get_model_for_score(self, complexity_score: float) -> ModelTier:
        """
        Map complexity score to appropriate model tier.

        Args:
            complexity_score: Score from 0-10

        Returns:
            ModelTier enum representing the recommended model
        """
        if complexity_score < 3.0:
            return ModelTier.FLASH
        elif complexity_score < 5.0:
            return ModelTier.HAIKU
        elif complexity_score < 8.0:
            return ModelTier.SONNET
        else:
            return ModelTier.OPUS

    def get_model_for_tier(self, tier: int) -> ModelTier:
        """
        Get primary model for a specific tier number.

        Args:
            tier: Tier number (0-3)

        Returns:
            ModelTier enum for the specified tier
        """
        tier_map = {
            0: ModelTier.FLASH,
            1: ModelTier.HAIKU,
            2: ModelTier.SONNET,
            3: ModelTier.OPUS,
        }
        return tier_map.get(tier, ModelTier.FLASH)

    def get_profile(self, model: ModelTier) -> ModelProfile:
        """
        Get profile for a specific model.

        Args:
            model: ModelTier enum

        Returns:
            ModelProfile with cost and capability info
        """
        return self.models[model]

    def estimate_cost(
        self, model: ModelTier, input_tokens: int, output_tokens: int
    ) -> float:
        """
        Calculate estimated cost for a task with given token counts.

        Args:
            model: ModelTier to use
            input_tokens: Estimated input token count
            output_tokens: Estimated output token count

        Returns:
            Estimated cost in USD
        """
        profile = self.models[model]
        input_cost = (input_tokens * profile.cost_per_1m_input) / 1_000_000
        output_cost = (output_tokens * profile.cost_per_1m_output) / 1_000_000
        return input_cost + output_cost

    def compare_costs(
        self, input_tokens: int, output_tokens: int
    ) -> Dict[str, float]:
        """
        Compare costs across all models for given token counts.

        Args:
            input_tokens: Estimated input token count
            output_tokens: Estimated output token count

        Returns:
            Dictionary mapping model names to costs
        """
        return {
            model.value: self.estimate_cost(model, input_tokens, output_tokens)
            for model in ModelTier
        }
