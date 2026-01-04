"""
Integration tests for explainability API endpoints.

Tests the full SHAP and PDP flow from API request to response.

References:
    - Analysis Router: src/synth_lab/api/routers/analysis.py
    - Explainability Service: src/synth_lab/services/simulation/explainability_service.py
"""

from unittest.mock import patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app
from synth_lab.domain.entities import SynthOutcome
from synth_lab.domain.entities.analysis_run import (
    AggregatedOutcomes,
    AnalysisConfig,
    AnalysisRun,
)
from synth_lab.domain.entities.experiment import (
    Experiment,
    ScorecardData,
    ScorecardDimension,
)
from synth_lab.domain.entities.simulation_attributes import (
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def experiment_id():
    """Sample experiment ID."""
    return "exp_12345678"


@pytest.fixture
def mock_completed_analysis(experiment_id):
    """Create a mock completed analysis."""
    return AnalysisRun(
        id="ana_12345678",
        experiment_id=experiment_id,
        config=AnalysisConfig(n_synths=50, n_executions=50),
        status="completed",
        total_synths=50,
        aggregated_outcomes=AggregatedOutcomes(
            did_not_try_rate=0.3,
            failed_rate=0.2,
            success_rate=0.5,
        ),
    )


@pytest.fixture
def mock_scorecard():
    """Create a mock scorecard for testing."""
    return ScorecardData(
        feature_name="Test Feature",
        scenario="Test scenario",
        description_text="Test feature description",
        perceived_risk=ScorecardDimension(score=0.5),
        initial_effort=ScorecardDimension(score=0.6),
        complexity=ScorecardDimension(score=0.4),
        time_to_value=ScorecardDimension(score=0.5),
    )


@pytest.fixture
def mock_experiment(experiment_id, mock_scorecard):
    """Create a mock experiment with scorecard."""
    return Experiment(
        id=experiment_id,
        name="Test Experiment",
        hypothesis="Test hypothesis for the experiment",
        scorecard_data=mock_scorecard,
    )


def create_synth_outcome(
    synth_id: str,
    success_rate: float,
    failed_rate: float,
    did_not_try_rate: float,
    capability_mean: float = 0.5,
    trust_mean: float = 0.5,
    friction_tolerance_mean: float = 0.5,
    exploration_prob: float = 0.5,
    outcome_id: str = "out_abcd1234",
) -> SynthOutcome:
    """Helper to create SynthOutcome with simulation attributes."""
    return SynthOutcome(
        id=outcome_id,
        synth_id=synth_id,
        analysis_id="ana_12345678",
        success_rate=success_rate,
        failed_rate=failed_rate,
        did_not_try_rate=did_not_try_rate,
        synth_attributes=SimulationAttributes(
            latent_traits=SimulationLatentTraits(
                capability_mean=capability_mean,
                trust_mean=trust_mean,
                friction_tolerance_mean=friction_tolerance_mean,
                exploration_prob=exploration_prob,
            ),
            observables=SimulationObservables(
                digital_literacy=0.3 + np.random.rand() * 0.5,
                similar_tool_experience=0.2 + np.random.rand() * 0.6,
                motor_ability=0.5 + np.random.rand() * 0.4,
                time_availability=0.3 + np.random.rand() * 0.5,
                domain_expertise=0.2 + np.random.rand() * 0.6,
            ),
        ),
    )


@pytest.fixture
def sample_outcomes():
    """Create sample synth outcomes for testing with realistic data (50 outcomes)."""
    np.random.seed(42)
    outcomes = []

    # Create 50 outcomes with attributes that correlate with success
    for i in range(50):
        # Higher capability and trust = higher success
        capability = 0.3 + np.random.rand() * 0.6
        trust = 0.2 + np.random.rand() * 0.7
        friction = 0.2 + np.random.rand() * 0.6
        exploration = 0.3 + np.random.rand() * 0.4

        # Success rate depends on capability and trust with some noise
        base_success = 0.3 * capability + 0.4 * trust + 0.2 * friction + 0.1 * exploration
        noise = np.random.randn() * 0.1
        success_rate = np.clip(base_success + noise, 0.05, 0.95)

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
            create_synth_outcome(
                f"synth_{i:03d}",
                success_rate,
                failed_rate,
                did_not_try_rate,
                capability,
                trust,
                friction,
                exploration,
            )
        )

    return outcomes


@pytest.fixture
def few_outcomes():
    """Create only 10 synth outcomes for testing minimum requirements."""
    return [
        create_synth_outcome(f"synth_{i:03d}", 0.5, 0.3, 0.2)
        for i in range(10)
    ]


class TestShapEndpoints:
    """Integration tests for SHAP endpoints."""

    def test_get_shap_explanation_basic(
        self,
        client,
        experiment_id,
        mock_completed_analysis,
        mock_experiment,
        sample_outcomes,
    ):
        """Test getting SHAP explanation for a specific synth."""
        with (
            patch("synth_lab.api.routers.analysis.get_analysis_service") as mock_analysis_svc,
            patch("synth_lab.api.routers.analysis.get_experiment_service") as mock_exp_svc,
            patch("synth_lab.api.routers.analysis.get_outcome_repository") as mock_outcome_repo,
        ):
            # Setup mocks
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (sample_outcomes, 50)

            # Make request
            response = client.get(f"/experiments/{experiment_id}/analysis/shap/synth_010")

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert data["experiment_id"] == experiment_id
            assert data["synth_id"] == "synth_010"
            assert "predicted_success_rate" in data
            assert "actual_success_rate" in data
            assert "baseline_prediction" in data
            assert "contributions" in data
            assert "explanation_text" in data
            assert len(data["contributions"]) > 0

    def test_shap_explanation_synth_not_found(
        self,
        client,
        experiment_id,
        mock_completed_analysis,
        mock_experiment,
        sample_outcomes,
    ):
        """Test error when synth not found."""
        with (
            patch("synth_lab.api.routers.analysis.get_analysis_service") as mock_analysis_svc,
            patch("synth_lab.api.routers.analysis.get_experiment_service") as mock_exp_svc,
            patch("synth_lab.api.routers.analysis.get_outcome_repository") as mock_outcome_repo,
        ):
            # Setup mocks
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (sample_outcomes, 50)

            # Make request with non-existent synth
            response = client.get(f"/experiments/{experiment_id}/analysis/shap/nonexistent_synth")

            # Should return 404
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_shap_requires_minimum_synths(
        self,
        client,
        experiment_id,
        mock_completed_analysis,
        mock_experiment,
        few_outcomes,
    ):
        """Test that SHAP requires at least 20 synths."""
        with (
            patch("synth_lab.api.routers.analysis.get_analysis_service") as mock_analysis_svc,
            patch("synth_lab.api.routers.analysis.get_experiment_service") as mock_exp_svc,
            patch("synth_lab.api.routers.analysis.get_outcome_repository") as mock_outcome_repo,
        ):
            # Setup mocks with only 10 synths
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (few_outcomes, 10)

            # Try to get SHAP
            response = client.get(f"/experiments/{experiment_id}/analysis/shap/synth_000")

            # Should return 400
            assert response.status_code == 400
            assert "at least 20 synths" in response.json()["detail"]


class TestPDPEndpoints:
    """Integration tests for PDP endpoints."""

    def test_get_pdp_basic(
        self,
        client,
        experiment_id,
        mock_completed_analysis,
        mock_experiment,
        sample_outcomes,
    ):
        """Test getting PDP for a feature."""
        with (
            patch("synth_lab.api.routers.analysis.get_analysis_service") as mock_analysis_svc,
            patch("synth_lab.api.routers.analysis.get_experiment_service") as mock_exp_svc,
            patch("synth_lab.api.routers.analysis.get_outcome_repository") as mock_outcome_repo,
        ):
            # Setup mocks
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (sample_outcomes, 50)

            # Make request
            response = client.get(f"/experiments/{experiment_id}/analysis/pdp?feature=trust_mean")

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert data["experiment_id"] == experiment_id
            assert data["feature_name"] == "trust_mean"
            assert "feature_display_name" in data
            assert "pdp_values" in data
            assert "effect_type" in data
            assert "effect_strength" in data
            assert len(data["pdp_values"]) > 0

    def test_pdp_invalid_feature(
        self,
        client,
        experiment_id,
        mock_completed_analysis,
        mock_experiment,
        sample_outcomes,
    ):
        """Test error for invalid feature."""
        with (
            patch("synth_lab.api.routers.analysis.get_analysis_service") as mock_analysis_svc,
            patch("synth_lab.api.routers.analysis.get_experiment_service") as mock_exp_svc,
            patch("synth_lab.api.routers.analysis.get_outcome_repository") as mock_outcome_repo,
        ):
            # Setup mocks
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (sample_outcomes, 50)

            # Make request with invalid feature
            response = client.get(f"/experiments/{experiment_id}/analysis/pdp?feature=invalid_feature")

            # Should return 400
            assert response.status_code == 400
            assert "not found" in response.json()["detail"]


class TestPDPComparisonEndpoint:
    """Integration tests for PDP comparison endpoint."""

    def test_pdp_comparison_basic(
        self,
        client,
        experiment_id,
        mock_completed_analysis,
        mock_experiment,
        sample_outcomes,
    ):
        """Test basic PDP comparison."""
        with (
            patch("synth_lab.api.routers.analysis.get_analysis_service") as mock_analysis_svc,
            patch("synth_lab.api.routers.analysis.get_experiment_service") as mock_exp_svc,
            patch("synth_lab.api.routers.analysis.get_outcome_repository") as mock_outcome_repo,
        ):
            # Setup mocks
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (sample_outcomes, 50)

            # Make request
            response = client.get(
                f"/experiments/{experiment_id}/analysis/pdp/comparison?features=trust_mean,capability_mean"
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert data["experiment_id"] == experiment_id
            assert len(data["pdp_results"]) == 2
            assert len(data["feature_ranking"]) == 2
            assert data["total_synths"] == 50

    def test_pdp_comparison_requires_two_features(
        self,
        client,
        experiment_id,
        mock_completed_analysis,
        mock_experiment,
        sample_outcomes,
    ):
        """Test that comparison requires at least 2 features."""
        with (
            patch("synth_lab.api.routers.analysis.get_analysis_service") as mock_analysis_svc,
            patch("synth_lab.api.routers.analysis.get_experiment_service") as mock_exp_svc,
            patch("synth_lab.api.routers.analysis.get_outcome_repository") as mock_outcome_repo,
        ):
            # Setup mocks
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (sample_outcomes, 50)

            # Make request with only 1 feature
            response = client.get(
                f"/experiments/{experiment_id}/analysis/pdp/comparison?features=trust_mean"
            )

            # Should return 400
            assert response.status_code == 400
            assert "At least 2 features" in response.json()["detail"]


if __name__ == "__main__":
    """Run integration tests."""
    pytest.main([__file__, "-v"])
