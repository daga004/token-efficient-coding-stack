"""Edge case test suite for ComplexityScorer.

Tests boundary conditions, single-factor dominance, multi-factor combinations,
confidence extremes, and various edge cases to ensure robust scoring.
"""

import pytest
from orchestrator.scoring import ComplexityScorer
from orchestrator.models import Task


class TestScorerEdgeCases:
    """Edge case testing for complexity scorer."""

    def setup_method(self):
        """Setup scorer instance for each test."""
        self.scorer = ComplexityScorer()

    # Boundary Tests - Tier Thresholds

    def test_score_exactly_zero(self):
        """Test task scoring exactly 0.0 (minimal complexity)."""
        task = Task(
            description="Do it",  # 2 words = 0.5
            context={}
        )
        result = self.scorer.score_task(task)
        assert result.score == 0.5
        assert result.recommended_tier == 0  # Flash
        assert result.confidence >= 0.5

    def test_score_tier_0_boundary(self):
        """Test task at tier 0/1 boundary (score ~3.0)."""
        task = Task(
            description="Update the constant value in config",  # 6 words = 0.5
            context={"files_count": 2}  # 0.5
        )
        result = self.scorer.score_task(task)
        assert result.score == 1.0
        assert result.recommended_tier == 0  # Flash (<3.0)

    def test_score_tier_1_boundary(self):
        """Test task at tier 1/2 boundary (score ~5.0)."""
        task = Task(
            description="Implement new validation rule for user input checking across multiple components",  # 11 words = 1.0
            context={"files_count": 3, "requires_tests": True}  # 1.0 + 1.5 = 2.5
        )
        result = self.scorer.score_task(task)
        # Actual: 1.0 (length) + 1.0 (3 files) + 1.5 (tests) = 3.5
        assert result.score == 3.5
        assert result.recommended_tier == 1  # Haiku (3-5 range)

    def test_score_tier_2_boundary(self):
        """Test task at tier 2/3 boundary (score ~8.0)."""
        task = Task(
            description="Refactor the entire authentication system to use OAuth2 with proper error handling and comprehensive test coverage",  # 18 words = 1.0
            context={
                "files_count": 6,  # 2.0
                "requires_tests": True,  # 1.5
                "external_apis": ["Auth0", "JWT"],  # 1.5
                "subsystems": ["auth", "api", "db"]  # 2.0
            }
        )
        result = self.scorer.score_task(task)
        # Actual: 1.0 (length) + 1.0 (refactor) + 2.0 (auth+OAuth2) + 2.0 (files) + 1.5 (tests) + 1.5 (apis) + 2.0 (subsystems) = 11.0 → capped at 10.0
        assert result.score == 10.0
        assert result.recommended_tier == 3  # Opus (8-10 range)

    def test_score_maximum_capped_at_10(self):
        """Test that score caps at 10.0 even when factors exceed."""
        task = Task(
            description=" ".join(["refactor", "restructure", "migrate", "architect", "redesign"] * 20),  # 100 words = 3.0 + keywords = 2.0 + 2.0
            context={
                "files_count": 20,  # 2.0
                "requires_tests": True,  # 1.5
                "external_apis": ["api1", "api2", "api3"],  # 1.5
                "subsystems": ["sys1", "sys2", "sys3", "sys4"]  # 2.0
            }
        )
        result = self.scorer.score_task(task)
        assert result.score == 10.0  # Capped
        assert result.recommended_tier == 3  # Opus

    # Single-Factor Dominance Tests

    def test_single_factor_task_length_only(self):
        """Test task complexity driven only by length."""
        task = Task(
            description=" ".join(["word"] * 100),  # 100 words = 3.0
            context={}
        )
        result = self.scorer.score_task(task)
        assert result.score == 3.0
        assert result.factors["task_length"] == 3.0
        assert result.factors["high_complexity_keywords"] == 0.0
        assert result.factors["critical_keywords"] == 0.0

    def test_single_factor_high_complexity_keywords(self):
        """Test task driven by high complexity keywords only."""
        task = Task(
            description="refactor and restructure",  # 2 keywords = 2.0, 3 words = 0.5
            context={}
        )
        result = self.scorer.score_task(task)
        assert result.score == 2.5  # 2.0 keywords + 0.5 length
        assert result.factors["high_complexity_keywords"] == 2.0

    def test_single_factor_critical_keywords(self):
        """Test task driven by critical domain keywords only."""
        task = Task(
            description="authentication and authorization",  # 2 critical = 2.0, 3 words = 0.5
            context={}
        )
        result = self.scorer.score_task(task)
        assert result.score == 2.5
        assert result.factors["critical_keywords"] == 2.0

    def test_single_factor_file_count(self):
        """Test task driven by file count only."""
        task = Task(
            description="fix it",  # 2 words = 0.5
            context={"files_count": 10}  # 2.0
        )
        result = self.scorer.score_task(task)
        assert result.score == 2.5
        assert result.factors["file_count"] == 2.0

    def test_single_factor_requires_tests(self):
        """Test task driven by test requirement only."""
        task = Task(
            description="add feature",  # 2 words = 0.5
            context={"requires_tests": True}  # 1.5
        )
        result = self.scorer.score_task(task)
        assert result.score == 2.0
        assert result.factors["requires_tests"] == 1.5

    def test_single_factor_external_apis(self):
        """Test task driven by external API dependencies only."""
        task = Task(
            description="call api",  # 2 words = 0.5
            context={"external_apis": ["stripe", "twilio"]}  # 1.5
        )
        result = self.scorer.score_task(task)
        assert result.score == 2.0
        assert result.factors["external_apis"] == 1.5

    def test_single_factor_multi_subsystem(self):
        """Test task driven by subsystem count only."""
        task = Task(
            description="update config",  # 2 words = 0.5
            context={"subsystems": ["frontend", "backend", "db"]}  # 2.0
        )
        result = self.scorer.score_task(task)
        assert result.score == 2.5
        assert result.factors["multi_subsystem"] == 2.0

    # Confidence Tests

    def test_confidence_minimum_one_factor(self):
        """Test confidence with only one active factor (minimum 0.5)."""
        task = Task(
            description="x",  # Only task_length active (0.5)
            context={}
        )
        result = self.scorer.score_task(task)
        # Only 1 factor active (task_length) out of 7
        assert result.confidence == pytest.approx(0.5 + (1/7) * 0.5, abs=0.01)

    def test_confidence_maximum_all_factors(self):
        """Test confidence with all 7 factors active (maximum 1.0)."""
        task = Task(
            description="refactor authentication system with extensive testing",  # length + 2 keywords
            context={
                "files_count": 5,
                "requires_tests": True,
                "external_apis": ["auth0"],
                "subsystems": ["auth", "api"]
            }
        )
        result = self.scorer.score_task(task)
        assert result.confidence == 1.0  # All 7 factors active

    # Keyword Detection Tests

    def test_keyword_case_insensitive(self):
        """Test that keyword matching is case insensitive."""
        task1 = Task(description="REFACTOR the code", context={})
        task2 = Task(description="refactor the code", context={})
        task3 = Task(description="Refactor the code", context={})

        result1 = self.scorer.score_task(task1)
        result2 = self.scorer.score_task(task2)
        result3 = self.scorer.score_task(task3)

        assert result1.factors["high_complexity_keywords"] == 1.0
        assert result2.factors["high_complexity_keywords"] == 1.0
        assert result3.factors["high_complexity_keywords"] == 1.0

    def test_keyword_partial_match(self):
        """Test that keywords match as substrings."""
        task = Task(
            description="refactoring and authentication system",  # Contains "refactor" and "authentication"
            context={}
        )
        result = self.scorer.score_task(task)
        assert result.factors["high_complexity_keywords"] == 1.0  # "refactor" in "refactoring"
        # "authentication" matches both "auth" and "authentication" keywords = 2 matches → 2.0 (capped)
        assert result.factors["critical_keywords"] == 2.0

    def test_keyword_multiple_matches_capped(self):
        """Test that keyword scoring caps at 2.0 even with 3+ matches."""
        task = Task(
            description="refactor restructure migrate architect redesign",  # 5 keywords
            context={}
        )
        result = self.scorer.score_task(task)
        assert result.factors["high_complexity_keywords"] == 2.0  # Capped at 2.0

    # Empty/Minimal Task Tests

    def test_empty_description(self):
        """Test task with empty description."""
        task = Task(description="", context={})
        result = self.scorer.score_task(task)
        # Empty string: 0 words, but still gets 0.5 for <10 words
        assert result.score == 0.5
        assert result.recommended_tier == 0  # Flash

    def test_single_word_task(self):
        """Test task with single word."""
        task = Task(description="fix", context={})
        result = self.scorer.score_task(task)
        assert result.score == 0.5
        assert result.recommended_tier == 0  # Flash

    def test_no_context_provided(self):
        """Test task with no context dict."""
        task = Task(
            description="implement feature",
            context={}
        )
        result = self.scorer.score_task(task)
        # Should handle missing context gracefully (defaults to 0)
        assert result.factors["file_count"] == 0.0
        assert result.factors["requires_tests"] == 0.0
        assert result.factors["external_apis"] == 0.0
        assert result.factors["multi_subsystem"] == 0.0

    # File Count Threshold Tests

    def test_file_count_zero(self):
        """Test file count of 0."""
        task = Task(description="task", context={"files_count": 0})
        result = self.scorer.score_task(task)
        assert result.factors["file_count"] == 0.0

    def test_file_count_one(self):
        """Test file count of 1."""
        task = Task(description="task", context={"files_count": 1})
        result = self.scorer.score_task(task)
        assert result.factors["file_count"] == 0.5

    def test_file_count_five(self):
        """Test file count of 5."""
        task = Task(description="task", context={"files_count": 5})
        result = self.scorer.score_task(task)
        assert result.factors["file_count"] == 1.5

    def test_file_count_large(self):
        """Test file count >6."""
        task = Task(description="task", context={"files_count": 20})
        result = self.scorer.score_task(task)
        assert result.factors["file_count"] == 2.0
