"""Tests for complexity scoring engine."""

import pytest
from orchestrator.models import Task, TaskComplexity
from orchestrator.scoring import ComplexityScorer


class TestComplexityScorer:
    """Test suite for ComplexityScorer."""

    @pytest.fixture
    def scorer(self):
        """Create a ComplexityScorer instance."""
        return ComplexityScorer()

    def test_simple_task_low_score(self, scorer):
        """Test that simple tasks get low complexity scores (Tier 0: Flash)."""
        task = Task(
            description="Add a comment to the function",
            context={}
        )
        result = scorer.score_task(task)

        assert isinstance(result, TaskComplexity)
        assert result.score < 3.0, f"Expected score < 3.0, got {result.score}"
        assert result.recommended_tier == 0
        assert 0.0 <= result.confidence <= 1.0

    def test_moderate_task_mid_score(self, scorer):
        """Test that moderate tasks get mid-range scores (Tier 1: Haiku)."""
        task = Task(
            description="Refactor the user service to improve code quality",
            context={"files_count": 3, "requires_tests": True}
        )
        result = scorer.score_task(task)

        assert 3.0 <= result.score < 5.0, f"Expected 3.0 <= score < 5.0, got {result.score}"
        assert result.recommended_tier == 1
        assert "high_complexity_keywords" in result.factors

    def test_complex_task_high_score(self, scorer):
        """Test that complex tasks get high scores (Tier 2: Sonnet)."""
        task = Task(
            description="Refactor the data processing pipeline to handle larger datasets "
                       "with improved performance and better error recovery",
            context={
                "files_count": 5,
                "requires_tests": True,
                "subsystems": ["data", "api"]
            }
        )
        result = scorer.score_task(task)

        assert 5.0 <= result.score < 8.0, f"Expected 5.0 <= score < 8.0, got {result.score}"
        assert result.recommended_tier == 2
        assert result.factors["high_complexity_keywords"] > 0

    def test_critical_task_max_score(self, scorer):
        """Test that critical tasks get maximum scores (Tier 3: Opus)."""
        task = Task(
            description="Architect and implement a complete payment processing "
                       "system with PCI compliance, encryption, fraud detection, "
                       "and multi-currency support across billing, auth, and "
                       "customer service subsystems",
            context={
                "files_count": 12,
                "requires_tests": True,
                "external_apis": ["Stripe", "PayPal", "Fraud.net"],
                "subsystems": ["payment", "billing", "auth", "customer"]
            }
        )
        result = scorer.score_task(task)

        assert result.score >= 8.0, f"Expected score >= 8.0, got {result.score}"
        assert result.recommended_tier == 3
        assert result.factors["critical_keywords"] > 0
        assert result.factors["high_complexity_keywords"] > 0

    def test_empty_task_minimal_score(self, scorer):
        """Test that empty/minimal tasks get very low scores."""
        task = Task(description="", context={})
        result = scorer.score_task(task)

        assert result.score < 1.0, f"Expected score < 1.0, got {result.score}"
        assert result.recommended_tier == 0

    def test_file_count_scoring(self, scorer):
        """Test that file count increases complexity appropriately."""
        # No files
        task1 = Task(description="Simple task", context={"files_count": 0})
        result1 = scorer.score_task(task1)

        # Many files
        task2 = Task(description="Simple task", context={"files_count": 6})
        result2 = scorer.score_task(task2)

        assert result2.score > result1.score
        assert result2.factors["file_count"] == 2.0

    def test_test_requirement_scoring(self, scorer):
        """Test that test requirements add complexity."""
        task1 = Task(
            description="Add feature",
            context={"requires_tests": False}
        )
        task2 = Task(
            description="Add feature",
            context={"requires_tests": True}
        )

        result1 = scorer.score_task(task1)
        result2 = scorer.score_task(task2)

        assert result2.score > result1.score
        assert result2.factors["requires_tests"] == 1.5
        assert result1.factors["requires_tests"] == 0.0

    def test_external_api_scoring(self, scorer):
        """Test that external API dependencies increase complexity."""
        task1 = Task(description="Task", context={"external_apis": []})
        task2 = Task(description="Task", context={"external_apis": ["API1", "API2"]})

        result1 = scorer.score_task(task1)
        result2 = scorer.score_task(task2)

        assert result2.score > result1.score
        assert result2.factors["external_apis"] == 1.5

    def test_subsystem_scoring(self, scorer):
        """Test that multi-subsystem work increases complexity."""
        task1 = Task(description="Task", context={"subsystems": ["auth"]})
        task2 = Task(
            description="Task",
            context={"subsystems": ["auth", "api", "db", "cache"]}
        )

        result1 = scorer.score_task(task1)
        result2 = scorer.score_task(task2)

        assert result2.score > result1.score
        assert result1.factors["multi_subsystem"] == 0.0  # Single subsystem
        assert result2.factors["multi_subsystem"] == 2.0  # 3+ subsystems

    def test_keyword_detection_high_complexity(self, scorer):
        """Test detection of high complexity keywords."""
        task = Task(
            description="Refactor and architect the system migration",
            context={}
        )
        result = scorer.score_task(task)

        assert result.factors["high_complexity_keywords"] >= 1.0

    def test_keyword_detection_critical(self, scorer):
        """Test detection of critical domain keywords."""
        task = Task(
            description="Implement authentication and payment security",
            context={}
        )
        result = scorer.score_task(task)

        assert result.factors["critical_keywords"] >= 1.0

    def test_task_length_scaling(self, scorer):
        """Test that longer descriptions increase complexity."""
        short = Task(description="Fix bug", context={})
        medium = Task(
            description="Fix bug in the authentication module " * 3,
            context={}
        )
        long = Task(
            description="Fix bug in the authentication module " * 10,
            context={}
        )

        result_short = scorer.score_task(short)
        result_medium = scorer.score_task(medium)
        result_long = scorer.score_task(long)

        assert result_short.factors["task_length"] < result_medium.factors["task_length"]
        assert result_medium.factors["task_length"] < result_long.factors["task_length"]

    def test_score_boundaries(self, scorer):
        """Test tier boundary conditions."""
        # Just below tier 1 threshold
        task1 = Task(description="Simple task with a bit more detail", context={})
        result1 = scorer.score_task(task1)

        # Just above tier 1 threshold
        task2 = Task(
            description="Refactor module",
            context={"files_count": 3}
        )
        result2 = scorer.score_task(task2)

        if result1.score < 3.0:
            assert result1.recommended_tier == 0
        if result2.score >= 3.0:
            assert result2.recommended_tier >= 1

    def test_confidence_calculation(self, scorer):
        """Test that confidence reflects factor coverage."""
        # Task with few factors
        task1 = Task(description="Simple", context={})
        result1 = scorer.score_task(task1)

        # Task with many factors
        task2 = Task(
            description="Refactor authentication with security audit",
            context={
                "files_count": 5,
                "requires_tests": True,
                "external_apis": ["Auth0"],
                "subsystems": ["auth", "api"]
            }
        )
        result2 = scorer.score_task(task2)

        # More factors should generally mean higher confidence
        assert result2.confidence >= result1.confidence

    def test_score_capped_at_ten(self, scorer):
        """Test that score never exceeds 10.0."""
        task = Task(
            description="Architect, refactor, and migrate the entire payment, "
                       "authentication, security, encryption, and billing system " * 5,
            context={
                "files_count": 100,
                "requires_tests": True,
                "external_apis": ["API1", "API2", "API3", "API4"],
                "subsystems": ["auth", "payment", "billing", "api", "db"]
            }
        )
        result = scorer.score_task(task)

        assert result.score <= 10.0, f"Score should be capped at 10.0, got {result.score}"
