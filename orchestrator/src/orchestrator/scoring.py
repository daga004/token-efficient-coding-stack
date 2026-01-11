"""Rule-based complexity scoring engine for task routing."""

import re
from typing import Dict
from orchestrator.models import Task, TaskComplexity


class ComplexityScorer:
    """Rule-based complexity scorer that analyzes tasks and assigns 0-10 scores."""

    # Keyword categories with point values
    HIGH_COMPLEXITY_KEYWORDS = {
        "refactor", "architect", "migrate", "redesign", "restructure"
    }
    CRITICAL_KEYWORDS = {
        "auth", "authentication", "payment", "security", "encryption",
        "authorization", "privacy", "billing"
    }

    def __init__(self):
        """Initialize complexity scorer."""
        pass

    def score_task(self, task: Task) -> TaskComplexity:
        """
        Score task complexity on 0-10 scale using rule-based factors.

        Args:
            task: Task to score

        Returns:
            TaskComplexity with score, factor breakdown, tier, and confidence
        """
        factors = {}

        # Factor 1: Task length (0-3 points based on word count)
        factors["task_length"] = self._score_task_length(task.description)

        # Factor 2: High complexity keywords (0-2 points)
        factors["high_complexity_keywords"] = self._score_keywords(
            task.description, self.HIGH_COMPLEXITY_KEYWORDS
        )

        # Factor 3: Critical domain keywords (0-2 points)
        factors["critical_keywords"] = self._score_keywords(
            task.description, self.CRITICAL_KEYWORDS
        )

        # Factor 4: File count from context (0-2 points)
        factors["file_count"] = self._score_file_count(
            task.context.get("files_count", 0)
        )

        # Factor 5: Test requirement (0-1.5 points)
        factors["requires_tests"] = self._score_tests(
            task.context.get("requires_tests", False)
        )

        # Factor 6: External API dependencies (0-1.5 points)
        factors["external_apis"] = self._score_external_apis(
            task.context.get("external_apis", [])
        )

        # Factor 7: Multi-subsystem work (0-2 points)
        factors["multi_subsystem"] = self._score_subsystems(
            task.context.get("subsystems", [])
        )

        # Calculate total score
        total_score = sum(factors.values())
        total_score = min(10.0, total_score)  # Cap at 10

        # Determine tier and confidence
        tier = self._score_to_tier(total_score)
        confidence = self._calculate_confidence(factors)

        return TaskComplexity(
            score=round(total_score, 2),
            factors=factors,
            recommended_tier=tier,
            confidence=round(confidence, 2),
        )

    def _score_task_length(self, description: str) -> float:
        """Score based on task description length (0-3 points)."""
        words = len(description.split())
        if words < 10:
            return 0.5
        elif words < 20:
            return 1.0
        elif words < 40:
            return 1.5
        elif words < 60:
            return 2.0
        else:
            return 3.0

    def _score_keywords(self, description: str, keywords: set) -> float:
        """Score based on keyword presence (0-2 points)."""
        desc_lower = description.lower()
        matches = sum(1 for kw in keywords if kw in desc_lower)
        return min(2.0, matches * 1.0)

    def _score_file_count(self, file_count: int) -> float:
        """Score based on number of files involved (0-2 points)."""
        if file_count == 0:
            return 0.0
        elif file_count <= 2:
            return 0.5
        elif file_count <= 3:
            return 1.0
        elif file_count <= 5:
            return 1.5
        else:
            return 2.0

    def _score_tests(self, requires_tests: bool) -> float:
        """Score based on test requirement (0-1.5 points)."""
        return 1.5 if requires_tests else 0.0

    def _score_external_apis(self, external_apis: list) -> float:
        """Score based on external API dependencies (0-1.5 points)."""
        if not external_apis:
            return 0.0
        return min(1.5, len(external_apis) * 0.75)

    def _score_subsystems(self, subsystems: list) -> float:
        """Score based on multi-subsystem involvement (0-2 points)."""
        if not subsystems:
            return 0.0
        elif len(subsystems) == 1:
            return 0.0
        elif len(subsystems) == 2:
            return 1.0
        else:
            return 2.0

    def _score_to_tier(self, score: float) -> int:
        """Map complexity score to model tier (0-3)."""
        if score < 3.0:
            return 0  # Flash
        elif score < 5.0:
            return 1  # Haiku
        elif score < 8.0:
            return 2  # Sonnet
        else:
            return 3  # Opus

    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        """Calculate confidence based on factor distribution."""
        # Higher confidence when multiple factors contribute
        active_factors = sum(1 for v in factors.values() if v > 0)
        total_factors = len(factors)

        # Base confidence from factor coverage
        coverage = active_factors / total_factors
        return 0.5 + (coverage * 0.5)  # Range: 0.5-1.0
