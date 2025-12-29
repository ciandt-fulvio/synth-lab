"""
Unit tests for outlier detection service.

Tests:
- Extreme cases identification (worst failures, best successes, unexpected)
- Outlier detection via Isolation Forest
- Outlier type classification
- Profile summaries and interview questions
"""

import pytest
import numpy as np

from synth_lab.domain.entities import (
    SynthOutcome,
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables,
)
from synth_lab.services.simulation.outlier_service import OutlierService


@pytest.fixture
def sample_outcomes() -> list[SynthOutcome]:
    """Create sample synth outcomes with extreme cases and outliers."""
    outcomes = []
    np.random.seed(42)

    # Cluster 1: Worst failures (10 synths) - high capability but failed
    for i in range(10):
        success_rate = 0.05 + np.random.rand() * 0.05
        failed_rate = 0.8 + np.random.rand() * 0.15
        did_not_try_rate = max(0.0, 1.0 - success_rate - failed_rate)
        # Normalize
        total = success_rate + failed_rate + did_not_try_rate
        success_rate /= total
        failed_rate /= total
        did_not_try_rate /= total

        outcomes.append(
            SynthOutcome(
                synth_id=f"worst_{i:03d}",
                analysis_id="ana_12345678",
                success_rate=success_rate,
                failed_rate=failed_rate,
                did_not_try_rate=did_not_try_rate,
                synth_attributes=SimulationAttributes(
                    observables=SimulationObservables(
                        digital_literacy=0.2,
                        similar_tool_experience=0.2,
                        motor_ability=0.3,
                        time_availability=0.2,
                        domain_expertise=0.2,
                    ),
                    latent_traits=SimulationLatentTraits(
                        capability_mean=0.7 + np.random.rand() * 0.2,  # High capability
                        trust_mean=0.2 + np.random.rand() * 0.1,  # Low trust
                        friction_tolerance_mean=0.2 + np.random.rand() * 0.1,
                        exploration_prob=0.2,
                    ),
                ),
            )
        )

    # Cluster 2: Best successes (10 synths)
    for i in range(10):
        success_rate = 0.85 + np.random.rand() * 0.1
        failed_rate = 0.05 + np.random.rand() * 0.05
        did_not_try_rate = max(0.0, 1.0 - success_rate - failed_rate)
        # Normalize
        total = success_rate + failed_rate + did_not_try_rate
        success_rate /= total
        failed_rate /= total
        did_not_try_rate /= total

        outcomes.append(
            SynthOutcome(
                synth_id=f"best_{i:03d}",
                analysis_id="ana_12345678",
                success_rate=success_rate,
                failed_rate=failed_rate,
                did_not_try_rate=did_not_try_rate,
                synth_attributes=SimulationAttributes(
                    observables=SimulationObservables(
                        digital_literacy=0.8,
                        similar_tool_experience=0.8,
                        motor_ability=0.9,
                        time_availability=0.8,
                        domain_expertise=0.8,
                    ),
                    latent_traits=SimulationLatentTraits(
                        capability_mean=0.8 + np.random.rand() * 0.15,
                        trust_mean=0.8 + np.random.rand() * 0.15,
                        friction_tolerance_mean=0.8 + np.random.rand() * 0.15,
                        exploration_prob=0.8,
                    ),
                ),
            )
        )

    # Cluster 3: Unexpected outlier - low capability but high success
    outcomes.append(
        SynthOutcome(
            synth_id="outlier_success",
            analysis_id="ana_12345678",
            success_rate=0.92,
            failed_rate=0.05,
            did_not_try_rate=0.03,
            synth_attributes=SimulationAttributes(
                observables=SimulationObservables(
                    digital_literacy=0.2,
                    similar_tool_experience=0.2,
                    motor_ability=0.2,
                    time_availability=0.2,
                    domain_expertise=0.2,
                ),
                latent_traits=SimulationLatentTraits(
                    capability_mean=0.2,  # Low capability but high success - OUTLIER
                    trust_mean=0.9,
                    friction_tolerance_mean=0.9,
                    exploration_prob=0.9,
                ),
            ),
        )
    )

    # Cluster 4: Normal performers (29 synths)
    for i in range(29):
        success_rate = 0.4 + np.random.rand() * 0.3
        failed_rate = 0.2 + np.random.rand() * 0.2
        did_not_try_rate = max(0.0, 1.0 - success_rate - failed_rate)
        # Normalize
        total = success_rate + failed_rate + did_not_try_rate
        success_rate /= total
        failed_rate /= total
        did_not_try_rate /= total

        outcomes.append(
            SynthOutcome(
                synth_id=f"normal_{i:03d}",
                analysis_id="ana_12345678",
                success_rate=success_rate,
                failed_rate=failed_rate,
                did_not_try_rate=did_not_try_rate,
                synth_attributes=SimulationAttributes(
                    observables=SimulationObservables(
                        digital_literacy=0.5,
                        similar_tool_experience=0.5,
                        motor_ability=0.5,
                        time_availability=0.5,
                        domain_expertise=0.5,
                    ),
                    latent_traits=SimulationLatentTraits(
                        capability_mean=0.5 + np.random.rand() * 0.2,
                        trust_mean=0.5 + np.random.rand() * 0.2,
                        friction_tolerance_mean=0.5 + np.random.rand() * 0.2,
                        exploration_prob=0.5,
                    ),
                ),
            )
        )

    return outcomes


class TestExtremeCases:
    """Test extreme cases identification."""

    def test_get_extreme_cases_basic(self, sample_outcomes):
        """Test identifying extreme cases."""
        service = OutlierService()
        result = service.get_extreme_cases(
            simulation_id="sim_test_001",
            outcomes=sample_outcomes,
            n_per_category=5,
        )

        assert result.simulation_id == "sim_test_001"
        assert len(result.worst_failures) == 5
        assert len(result.best_successes) == 5
        assert len(result.unexpected_cases) >= 1
        assert result.total_synths == 50

    def test_worst_failures_have_highest_failure_rate(self, sample_outcomes):
        """Test that worst failures are correctly ranked by lowest success rate."""
        service = OutlierService()
        result = service.get_extreme_cases(
            simulation_id="sim_test_001",
            outcomes=sample_outcomes,
            n_per_category=10,
        )

        # Check that failures are sorted by success rate (ascending)
        success_rates = [synth.success_rate for synth in result.worst_failures]
        assert success_rates == sorted(success_rates, reverse=False)

        # All should have low success rates
        for synth in result.worst_failures:
            assert synth.success_rate < 0.5
            assert synth.category == "worst_failure"

    def test_best_successes_have_highest_success_rate(self, sample_outcomes):
        """Test that best successes are correctly ranked."""
        service = OutlierService()
        result = service.get_extreme_cases(
            simulation_id="sim_test_001",
            outcomes=sample_outcomes,
            n_per_category=10,
        )

        # Check that successes are sorted by success rate (descending)
        success_rates = [synth.success_rate for synth in result.best_successes]
        assert success_rates == sorted(success_rates, reverse=True)

        # All should have high success rates
        for synth in result.best_successes:
            assert synth.success_rate > 0.7
            assert synth.category == "best_success"

    def test_profile_summary_is_generated(self, sample_outcomes):
        """Test that profile summaries are generated."""
        service = OutlierService()
        result = service.get_extreme_cases(
            simulation_id="sim_test_001",
            outcomes=sample_outcomes,
        )

        # Check that all extreme cases have summaries
        for synth in result.worst_failures + result.best_successes:
            assert synth.profile_summary != ""
            assert len(synth.profile_summary) > 10

    def test_interview_questions_are_generated(self, sample_outcomes):
        """Test that interview questions are generated."""
        service = OutlierService()
        result = service.get_extreme_cases(
            simulation_id="sim_test_001",
            outcomes=sample_outcomes,
        )

        # Check that all extreme cases have questions
        for synth in result.worst_failures[:3]:  # Check first 3
            assert len(synth.interview_questions) >= 2
            assert all(q.endswith("?") for q in synth.interview_questions)


class TestOutlierDetection:
    """Test outlier detection via Isolation Forest."""

    def test_detect_outliers_basic(self, sample_outcomes):
        """Test basic outlier detection."""
        service = OutlierService()
        result = service.detect_outliers(
            simulation_id="sim_test_001",
            outcomes=sample_outcomes,
            contamination=0.1,
        )

        assert result.simulation_id == "sim_test_001"
        assert result.method == "isolation_forest"
        assert result.contamination == 0.1
        assert result.total_synths == 50
        assert result.n_outliers > 0
        assert len(result.outliers) == result.n_outliers

    def test_outliers_have_anomaly_scores(self, sample_outcomes):
        """Test that outliers have anomaly scores."""
        service = OutlierService()
        result = service.detect_outliers(
            simulation_id="sim_test_001",
            outcomes=sample_outcomes,
        )

        for outlier in result.outliers:
            assert hasattr(outlier, "anomaly_score")
            assert outlier.anomaly_score < 0  # Negative scores = outliers

    def test_outliers_are_classified(self, sample_outcomes):
        """Test that outliers are classified by type."""
        service = OutlierService()
        result = service.detect_outliers(
            simulation_id="sim_test_001",
            outcomes=sample_outcomes,
        )

        # Check that outliers have types
        for outlier in result.outliers:
            assert outlier.outlier_type in [
                "unexpected_failure",
                "unexpected_success",
                "atypical_profile",
            ]

    def test_contamination_parameter(self, sample_outcomes):
        """Test that contamination affects number of outliers."""
        service = OutlierService()

        # Low contamination = fewer outliers
        result_low = service.detect_outliers(
            simulation_id="sim_test_001",
            outcomes=sample_outcomes,
            contamination=0.05,
        )

        # High contamination = more outliers
        result_high = service.detect_outliers(
            simulation_id="sim_test_001",
            outcomes=sample_outcomes,
            contamination=0.2,
        )

        assert result_high.n_outliers > result_low.n_outliers

    def test_outlier_has_explanation(self, sample_outcomes):
        """Test that outliers have explanations."""
        service = OutlierService()
        result = service.detect_outliers(
            simulation_id="sim_test_001",
            outcomes=sample_outcomes,
        )

        for outlier in result.outliers:
            assert outlier.explanation != ""
            assert len(outlier.explanation) > 10


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_minimum_synths_for_outliers(self):
        """Test that outlier detection requires minimum synths."""
        service = OutlierService()

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

        with pytest.raises(ValueError, match="at least 10"):
            service.detect_outliers(
                simulation_id="sim_test_001",
                outcomes=few_outcomes,
            )

    def test_n_per_category_larger_than_available(self, sample_outcomes):
        """Test handling when n_per_category > available synths."""
        service = OutlierService()

        # Request more than available
        result = service.get_extreme_cases(
            simulation_id="sim_test_001",
            outcomes=sample_outcomes,
            n_per_category=100,  # More than total synths
        )

        # Should return all available without error
        assert len(result.worst_failures) <= 50
        assert len(result.best_successes) <= 50


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])
