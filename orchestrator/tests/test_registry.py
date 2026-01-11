"""Tests for model registry and tier selection."""

import pytest
from orchestrator.registry import ModelRegistry, ModelTier, ModelProfile


class TestModelRegistry:
    """Test suite for ModelRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a ModelRegistry instance."""
        return ModelRegistry()

    def test_registry_initialization(self, registry):
        """Test that registry initializes with all model tiers."""
        assert len(registry.models) == 5
        assert ModelTier.FLASH in registry.models
        assert ModelTier.PRO in registry.models
        assert ModelTier.HAIKU in registry.models
        assert ModelTier.SONNET in registry.models
        assert ModelTier.OPUS in registry.models

    def test_model_profiles_have_required_fields(self, registry):
        """Test that all model profiles have required fields."""
        for model_tier, profile in registry.models.items():
            assert isinstance(profile, ModelProfile)
            assert profile.name
            assert isinstance(profile.tier, int)
            assert 0 <= profile.tier <= 3
            assert profile.cost_per_1m_input >= 0
            assert profile.cost_per_1m_output >= 0
            assert profile.max_tokens > 0
            assert isinstance(profile.best_for, list)

    def test_flash_tier_mapping(self, registry):
        """Test that low scores (0-2.9) map to Flash."""
        assert registry.get_model_for_score(0.0) == ModelTier.FLASH
        assert registry.get_model_for_score(1.5) == ModelTier.FLASH
        assert registry.get_model_for_score(2.9) == ModelTier.FLASH

    def test_haiku_tier_mapping(self, registry):
        """Test that mid-low scores (3.0-4.9) map to Haiku."""
        assert registry.get_model_for_score(3.0) == ModelTier.HAIKU
        assert registry.get_model_for_score(4.0) == ModelTier.HAIKU
        assert registry.get_model_for_score(4.9) == ModelTier.HAIKU

    def test_sonnet_tier_mapping(self, registry):
        """Test that mid-high scores (5.0-7.9) map to Sonnet."""
        assert registry.get_model_for_score(5.0) == ModelTier.SONNET
        assert registry.get_model_for_score(6.5) == ModelTier.SONNET
        assert registry.get_model_for_score(7.9) == ModelTier.SONNET

    def test_opus_tier_mapping(self, registry):
        """Test that high scores (8.0-10.0) map to Opus."""
        assert registry.get_model_for_score(8.0) == ModelTier.OPUS
        assert registry.get_model_for_score(9.0) == ModelTier.OPUS
        assert registry.get_model_for_score(10.0) == ModelTier.OPUS

    def test_boundary_conditions(self, registry):
        """Test exact boundary values for tier transitions."""
        # Just below Haiku threshold
        assert registry.get_model_for_score(2.99) == ModelTier.FLASH
        # Exactly at Haiku threshold
        assert registry.get_model_for_score(3.0) == ModelTier.HAIKU

        # Just below Sonnet threshold
        assert registry.get_model_for_score(4.99) == ModelTier.HAIKU
        # Exactly at Sonnet threshold
        assert registry.get_model_for_score(5.0) == ModelTier.SONNET

        # Just below Opus threshold
        assert registry.get_model_for_score(7.99) == ModelTier.SONNET
        # Exactly at Opus threshold
        assert registry.get_model_for_score(8.0) == ModelTier.OPUS

    def test_get_model_for_tier(self, registry):
        """Test tier number to model mapping."""
        assert registry.get_model_for_tier(0) == ModelTier.FLASH
        assert registry.get_model_for_tier(1) == ModelTier.HAIKU
        assert registry.get_model_for_tier(2) == ModelTier.SONNET
        assert registry.get_model_for_tier(3) == ModelTier.OPUS

    def test_get_model_for_invalid_tier(self, registry):
        """Test that invalid tier numbers default to Flash."""
        assert registry.get_model_for_tier(99) == ModelTier.FLASH
        assert registry.get_model_for_tier(-1) == ModelTier.FLASH

    def test_get_profile(self, registry):
        """Test retrieving model profiles."""
        flash_profile = registry.get_profile(ModelTier.FLASH)
        assert flash_profile.name == "Gemini Flash"
        assert flash_profile.tier == 0

        opus_profile = registry.get_profile(ModelTier.OPUS)
        assert opus_profile.name == "Claude Opus"
        assert opus_profile.tier == 3

    def test_cost_estimation_flash(self, registry):
        """Test cost estimation for Flash model."""
        # 100K input, 10K output tokens
        cost = registry.estimate_cost(ModelTier.FLASH, 100_000, 10_000)

        expected_input = (100_000 * 0.01) / 1_000_000
        expected_output = (10_000 * 0.04) / 1_000_000
        expected_total = expected_input + expected_output

        assert abs(cost - expected_total) < 0.0001

    def test_cost_estimation_opus(self, registry):
        """Test cost estimation for Opus model (most expensive)."""
        # 100K input, 50K output tokens
        cost = registry.estimate_cost(ModelTier.OPUS, 100_000, 50_000)

        expected_input = (100_000 * 15.00) / 1_000_000
        expected_output = (50_000 * 75.00) / 1_000_000
        expected_total = expected_input + expected_output

        assert abs(cost - expected_total) < 0.0001

    def test_cost_comparison(self, registry):
        """Test that cost comparison returns all models."""
        comparison = registry.compare_costs(100_000, 10_000)

        assert len(comparison) == 5
        assert "gemini-flash" in comparison
        assert "gemini-pro" in comparison
        assert "haiku" in comparison
        assert "sonnet" in comparison
        assert "opus" in comparison

    def test_cost_ordering(self, registry):
        """Test that models are ordered correctly by cost."""
        comparison = registry.compare_costs(100_000, 10_000)

        # Flash should be cheapest
        assert comparison["gemini-flash"] < comparison["gemini-pro"]
        assert comparison["gemini-flash"] < comparison["haiku"]
        assert comparison["gemini-flash"] < comparison["sonnet"]
        assert comparison["gemini-flash"] < comparison["opus"]

        # Opus should be most expensive
        assert comparison["opus"] > comparison["sonnet"]
        assert comparison["opus"] > comparison["haiku"]
        assert comparison["opus"] > comparison["gemini-pro"]

    def test_zero_tokens_cost(self, registry):
        """Test cost estimation with zero tokens."""
        cost = registry.estimate_cost(ModelTier.FLASH, 0, 0)
        assert cost == 0.0

    def test_flash_cost_optimization(self, registry):
        """Test that Flash is significantly cheaper for simple tasks."""
        tokens_in = 10_000
        tokens_out = 1_000

        flash_cost = registry.estimate_cost(ModelTier.FLASH, tokens_in, tokens_out)
        opus_cost = registry.estimate_cost(ModelTier.OPUS, tokens_in, tokens_out)

        # Flash should be at least 100x cheaper than Opus
        assert opus_cost > flash_cost * 100

    def test_model_tier_costs_accurate(self, registry):
        """Test that model costs match documented pricing."""
        flash = registry.get_profile(ModelTier.FLASH)
        assert flash.cost_per_1m_input == 0.01
        assert flash.cost_per_1m_output == 0.04

        haiku = registry.get_profile(ModelTier.HAIKU)
        assert haiku.cost_per_1m_input == 0.80
        assert haiku.cost_per_1m_output == 4.00

        sonnet = registry.get_profile(ModelTier.SONNET)
        assert sonnet.cost_per_1m_input == 3.00
        assert sonnet.cost_per_1m_output == 15.00

        opus = registry.get_profile(ModelTier.OPUS)
        assert opus.cost_per_1m_input == 15.00
        assert opus.cost_per_1m_output == 75.00
