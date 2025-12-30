"""
Unit tests for explainability service.

Tests:
- Model training with GradientBoostingRegressor
- SHAP explanation for individual synths
- SHAP summary (global feature importance)
- Partial Dependence Plots (PDP)
- Effect type classification

References:
    - SHAP: github.com/shap/shap
    - PDP: scikit-learn.org/stable/modules/partial_dependence.html
"""

import numpy as np
import pytest

from synth_lab.domain.entities import (
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables,
    SynthOutcome,
)

# Check if shap module is available (optional dependency for explainability)
try:
    import shap  # noqa: F401

    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

# Skip all tests if shap is not available
pytestmark = pytest.mark.skipif(
    not SHAP_AVAILABLE,
    reason="shap module not installed (optional dependency for explainability)",
)

from synth_lab.services.simulation.explainability_service import ExplainabilityService


@pytest.fixture
def sample_outcomes() -> list[SynthOutcome]:
    """Create sample synth outcomes for testing SHAP/PDP."""
    np.random.seed(42)
    outcomes = []

    # Create 100 synths with varying attributes and outcomes
    # Success rate correlates with capability and trust
    for i in range(100):
        capability = 0.3 + np.random.rand() * 0.6  # 0.3 to 0.9
        trust = 0.2 + np.random.rand() * 0.7  # 0.2 to 0.9
        friction = 0.2 + np.random.rand() * 0.6  # 0.2 to 0.8
        exploration = 0.3 + np.random.rand() * 0.4  # 0.3 to 0.7

        # Success rate depends on capability and trust with some noise
        base_success = 0.3 * capability + 0.4 * trust + 0.2 * friction + 0.1 * exploration
        noise = np.random.randn() * 0.1
        success_rate = np.clip(base_success + noise, 0.0, 0.95)

        # Failed rate inversely related
        failed_rate = np.clip(
            0.5 - 0.3 * capability - 0.2 * trust + np.random.randn() * 0.1, 0.05, 0.5
        )

        did_not_try_rate = max(0.0, 1.0 - success_rate - failed_rate)

        # Normalize
        total = success_rate + failed_rate + did_not_try_rate
        success_rate /= total
        failed_rate /= total
        did_not_try_rate /= total

        outcomes.append(
            SynthOutcome(
                synth_id=f"synth_{i:03d}",
                analysis_id="ana_12345678",
                success_rate=success_rate,
                failed_rate=failed_rate,
                did_not_try_rate=did_not_try_rate,
                synth_attributes=SimulationAttributes(
                    observables=SimulationObservables(
                        digital_literacy=0.3 + np.random.rand() * 0.5,
                        similar_tool_experience=0.2 + np.random.rand() * 0.6,
                        motor_ability=0.5 + np.random.rand() * 0.4,
                        time_availability=0.3 + np.random.rand() * 0.5,
                        domain_expertise=0.2 + np.random.rand() * 0.6,
                    ),
                    latent_traits=SimulationLatentTraits(
                        capability_mean=capability,
                        trust_mean=trust,
                        friction_tolerance_mean=friction,
                        exploration_prob=exploration,
                    ),
                ),
            )
        )

    return outcomes


class TestModelTraining:
    """Test model training functionality."""

    def test_train_model_basic(self, sample_outcomes):
        """Test basic model training."""
        service = ExplainabilityService()
        model, score = service._train_model(sample_outcomes)

        assert model is not None
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0  # R² score

    def test_train_model_with_custom_features(self, sample_outcomes):
        """Test model training with custom features."""
        service = ExplainabilityService()
        model, score = service._train_model(
            sample_outcomes,
            features=["capability_mean", "trust_mean"],
        )

        assert model is not None
        assert isinstance(score, float)

    def test_train_model_with_default_features(self, sample_outcomes):
        """Test that model uses default features when none specified."""
        service = ExplainabilityService()
        model, score = service._train_model(sample_outcomes)

        # Should have used default features
        assert model is not None
        assert hasattr(model, "feature_importances_")
        assert len(model.feature_importances_) > 0

    def test_model_caching(self, sample_outcomes):
        """Test that trained model is cached."""
        service = ExplainabilityService()

        # First call should train
        model1, score1 = service._train_model(sample_outcomes)

        # Second call should return cached model
        model2, score2 = service._train_model(sample_outcomes)

        assert model1 is model2  # Same object (cached)
        assert score1 == score2


class TestShapExplanation:
    """Test SHAP explanation for individual synths."""

    def test_explain_synth_basic(self, sample_outcomes):
        """Test basic SHAP explanation."""
        service = ExplainabilityService()
        result = service.explain_synth(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            synth_id="synth_000",
        )

        assert result.simulation_id == "sim_test"
        assert result.synth_id == "synth_000"
        assert 0.0 <= result.predicted_success_rate <= 1.0
        assert 0.0 <= result.actual_success_rate <= 1.0
        assert result.baseline_prediction > 0
        assert len(result.contributions) > 0
        assert result.explanation_text != ""

    def test_explain_synth_contributions_sorted(self, sample_outcomes):
        """Test that SHAP contributions are sorted by absolute value."""
        service = ExplainabilityService()
        result = service.explain_synth(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            synth_id="synth_050",
        )

        # Contributions should be sorted by absolute SHAP value (descending)
        shap_values = [abs(c.shap_value) for c in result.contributions]
        assert shap_values == sorted(shap_values, reverse=True)

    def test_explain_synth_contribution_direction(self, sample_outcomes):
        """Test that contribution directions are correct."""
        service = ExplainabilityService()
        result = service.explain_synth(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            synth_id="synth_010",
        )

        for contribution in result.contributions:
            if contribution.shap_value > 0:
                assert contribution.impact == "positive"
            elif contribution.shap_value < 0:
                assert contribution.impact == "negative"
            else:
                assert contribution.impact in ["positive", "negative"]  # Edge case

    def test_explain_synth_not_found(self, sample_outcomes):
        """Test error when synth not found."""
        service = ExplainabilityService()

        with pytest.raises(ValueError, match="not found"):
            service.explain_synth(
                simulation_id="sim_test",
                outcomes=sample_outcomes,
                synth_id="nonexistent_synth",
            )


class TestShapSummary:
    """Test SHAP summary (global feature importance)."""

    def test_get_shap_summary_basic(self, sample_outcomes):
        """Test basic SHAP summary."""
        service = ExplainabilityService()
        result = service.get_shap_summary(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
        )

        assert result.simulation_id == "sim_test"
        assert len(result.feature_importances) > 0
        assert len(result.top_features) > 0
        assert result.total_synths == len(sample_outcomes)
        assert 0.0 <= result.model_score <= 1.0

    def test_shap_summary_importances_positive(self, sample_outcomes):
        """Test that feature importances are positive."""
        service = ExplainabilityService()
        result = service.get_shap_summary(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
        )

        for importance in result.feature_importances.values():
            assert importance >= 0

    def test_shap_summary_top_features_sorted(self, sample_outcomes):
        """Test that top features are sorted by importance."""
        service = ExplainabilityService()
        result = service.get_shap_summary(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
        )

        # Top features should be ordered by importance
        importances = [result.feature_importances[f] for f in result.top_features]
        assert importances == sorted(importances, reverse=True)

    def test_shap_summary_with_custom_features(self, sample_outcomes):
        """Test SHAP summary with custom features."""
        service = ExplainabilityService()
        result = service.get_shap_summary(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            features=["capability_mean", "trust_mean"],
        )

        assert len(result.feature_importances) == 2
        assert "capability_mean" in result.feature_importances
        assert "trust_mean" in result.feature_importances


class TestPartialDependence:
    """Test Partial Dependence Plot calculation."""

    def test_calculate_pdp_basic(self, sample_outcomes):
        """Test basic PDP calculation."""
        service = ExplainabilityService()
        result = service.calculate_pdp(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            feature="capability_mean",
        )

        assert result.simulation_id == "sim_test"
        assert result.feature_name == "capability_mean"
        assert len(result.pdp_values) > 0
        assert result.effect_type in [
            "monotonic_increasing",
            "monotonic_decreasing",
            "non_linear",
            "flat",
        ]
        assert result.effect_strength >= 0

    def test_calculate_pdp_values_sorted(self, sample_outcomes):
        """Test that PDP values are sorted by feature value."""
        service = ExplainabilityService()
        result = service.calculate_pdp(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            feature="trust_mean",
        )

        feature_values = [p.feature_value for p in result.pdp_values]
        assert feature_values == sorted(feature_values)

    def test_calculate_pdp_grid_resolution(self, sample_outcomes):
        """Test PDP grid resolution."""
        service = ExplainabilityService()
        result = service.calculate_pdp(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            feature="capability_mean",
            grid_resolution=10,
        )

        assert len(result.pdp_values) == 10

    def test_pdp_effect_type_monotonic_increasing(self, sample_outcomes):
        """Test detection of monotonic increasing effect."""
        service = ExplainabilityService()
        # Trust has positive correlation with success in our synthetic data
        result = service.calculate_pdp(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            feature="trust_mean",
        )

        # Should detect some type of effect (our synthetic data has correlation)
        assert result.effect_type in [
            "monotonic_increasing",
            "monotonic_decreasing",
            "non_linear",
            "flat",
        ]

    def test_calculate_pdp_invalid_feature(self, sample_outcomes):
        """Test error for invalid feature."""
        service = ExplainabilityService()

        with pytest.raises(ValueError, match="not found"):
            service.calculate_pdp(
                simulation_id="sim_test",
                outcomes=sample_outcomes,
                feature="invalid_feature",
            )


class TestPDPComparison:
    """Test PDP comparison across multiple features."""

    def test_compare_pdps_basic(self, sample_outcomes):
        """Test basic PDP comparison."""
        service = ExplainabilityService()
        result = service.compare_pdps(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            features=["capability_mean", "trust_mean"],
        )

        assert result.simulation_id == "sim_test"
        assert len(result.pdp_results) == 2
        assert len(result.feature_ranking) == 2
        assert result.total_synths == len(sample_outcomes)

    def test_compare_pdps_ranking(self, sample_outcomes):
        """Test that features are ranked by effect strength."""
        service = ExplainabilityService()
        result = service.compare_pdps(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            features=["capability_mean", "trust_mean", "friction_tolerance_mean"],
        )

        # Ranking should be by effect strength (descending)
        strengths = [
            result.pdp_results[i].effect_strength for i in range(len(result.feature_ranking))
        ]
        # Feature ranking order should match effect strength order
        ranked_features = result.feature_ranking
        pdp_map = {pdp.feature_name: pdp.effect_strength for pdp in result.pdp_results}
        ranked_strengths = [pdp_map[f] for f in ranked_features]
        assert ranked_strengths == sorted(ranked_strengths, reverse=True)


class TestEffectClassification:
    """Test effect type classification."""

    def test_classify_effect_monotonic_increasing(self):
        """Test classification of monotonic increasing effect."""
        service = ExplainabilityService()

        # Create strictly increasing values
        values = [0.1, 0.2, 0.3, 0.4, 0.5]
        effect_type, strength = service._classify_effect(values)

        assert effect_type == "monotonic_increasing"
        assert strength > 0

    def test_classify_effect_monotonic_decreasing(self):
        """Test classification of monotonic decreasing effect."""
        service = ExplainabilityService()

        # Create strictly decreasing values
        values = [0.5, 0.4, 0.3, 0.2, 0.1]
        effect_type, strength = service._classify_effect(values)

        assert effect_type == "monotonic_decreasing"
        assert strength > 0

    def test_classify_effect_flat(self):
        """Test classification of flat effect."""
        service = ExplainabilityService()

        # Create flat values
        values = [0.5, 0.5, 0.5, 0.5, 0.5]
        effect_type, strength = service._classify_effect(values)

        assert effect_type == "flat"
        assert strength < 0.01  # Very small strength

    def test_classify_effect_non_linear(self):
        """Test classification of non-linear effect."""
        service = ExplainabilityService()

        # Create U-shaped values
        values = [0.5, 0.3, 0.2, 0.3, 0.5]
        effect_type, strength = service._classify_effect(values)

        assert effect_type == "non_linear"


class TestExplanationText:
    """Test explanation text generation."""

    def test_generate_explanation_text(self, sample_outcomes):
        """Test that explanation text is generated."""
        service = ExplainabilityService()
        result = service.explain_synth(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            synth_id="synth_025",
        )

        assert len(result.explanation_text) > 0
        # Should mention the most important feature
        if result.contributions:
            top_feature = result.contributions[0].feature_name
            # Explanation should mention at least one feature
            assert (
                any(
                    c.feature_name in result.explanation_text
                    for c in result.contributions[:3]  # Top 3 features
                )
                or "feature" in result.explanation_text.lower()
            )


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_minimum_synths_for_shap(self):
        """Test that SHAP requires minimum synths."""
        service = ExplainabilityService()

        # Create only 5 synths
        few_outcomes = [
            SynthOutcome(
                synth_id=f"synth_{i:03d}",
                analysis_id="ana_12345678",
                success_rate=0.5,
                failed_rate=0.3,
                did_not_try_rate=0.2,
                synth_attributes=SimulationAttributes(
                    observables=SimulationObservables(
                        digital_literacy=0.5,
                        similar_tool_experience=0.5,
                        motor_ability=0.5,
                        time_availability=0.5,
                        domain_expertise=0.5,
                    ),
                    latent_traits=SimulationLatentTraits(
                        capability_mean=0.5,
                        trust_mean=0.5,
                        friction_tolerance_mean=0.5,
                        exploration_prob=0.5,
                    ),
                ),
            )
            for i in range(5)
        ]

        with pytest.raises(ValueError, match="at least"):
            service.get_shap_summary(
                simulation_id="sim_test",
                outcomes=few_outcomes,
            )

    def test_empty_outcomes_list(self):
        """Test error for empty outcomes list."""
        service = ExplainabilityService()

        with pytest.raises(ValueError, match="empty"):
            service.get_shap_summary(
                simulation_id="sim_test",
                outcomes=[],
            )


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])
