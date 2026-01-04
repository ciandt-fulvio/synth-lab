"""
Integration tests for outlier detection API endpoints.

Tests the full outlier detection flow from API request to response.

References:
    - Analysis Router: src/synth_lab/api/routers/analysis.py
    - Outlier Service: src/synth_lab/services/simulation/outlier_service.py
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
        config=AnalysisConfig(n_synths=50, n_executions=100),
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
                exploration_prob=0.5,
            ),
            observables=SimulationObservables(
                digital_literacy=0.5,
                similar_tool_experience=0.5,
                motor_ability=0.5,
                time_availability=0.5,
                domain_expertise=0.5,
            ),
        ),
    )


@pytest.fixture
def sample_outcomes():
    """Create sample synth outcomes with extreme cases and outliers (50 outcomes)."""
    outcomes = []
    np.random.seed(42)

    # Worst failures (10 synths) - high capability but failed
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
            create_synth_outcome(
                f"worst_{i:03d}",
                success_rate,
                failed_rate,
                did_not_try_rate,
                0.7 + np.random.rand() * 0.2,
                0.2 + np.random.rand() * 0.1,
                0.2 + np.random.rand() * 0.1,
            )
        )

    # Best successes (10 synths)
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
            create_synth_outcome(
                f"best_{i:03d}",
                success_rate,
                failed_rate,
                did_not_try_rate,
                0.8 + np.random.rand() * 0.15,
                0.8 + np.random.rand() * 0.15,
                0.8 + np.random.rand() * 0.15,
            )
        )

    # Normal performers (30 synths)
    for i in range(30):
        success_rate = 0.4 + np.random.rand() * 0.3
        failed_rate = 0.2 + np.random.rand() * 0.2
        did_not_try_rate = max(0.0, 1.0 - success_rate - failed_rate)
        # Normalize
        total = success_rate + failed_rate + did_not_try_rate
        success_rate /= total
        failed_rate /= total
        did_not_try_rate /= total

        outcomes.append(
            create_synth_outcome(
                f"normal_{i:03d}",
                success_rate,
                failed_rate,
                did_not_try_rate,
                0.5 + np.random.rand() * 0.2,
                0.5 + np.random.rand() * 0.2,
                0.5 + np.random.rand() * 0.2,
            )
        )

    return outcomes


@pytest.fixture
def few_outcomes():
    """Create only 5 synth outcomes for testing minimum requirements."""
    return [
        create_synth_outcome(f"synth_{i:03d}", 0.5, 0.3, 0.2)
        for i in range(5)
    ]


class TestExtremeCasesEndpoint:
    """Integration tests for extreme cases endpoint."""

    def test_get_extreme_cases(
        self,
        client,
        experiment_id,
        mock_completed_analysis,
        mock_experiment,
        sample_outcomes,
    ):
        """Test getting extreme cases."""
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
            response = client.get(f"/experiments/{experiment_id}/analysis/extreme-cases")

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert data["experiment_id"] == experiment_id
            assert data["total_synths"] == 50
            assert len(data["worst_failures"]) == 10
            assert len(data["best_successes"]) == 10
            assert len(data["unexpected_cases"]) >= 0

            # Check worst failures
            for synth in data["worst_failures"]:
                assert synth["category"] == "worst_failure"
                assert synth["failed_rate"] > 0.5
                assert synth["profile_summary"] != ""
                assert len(synth["interview_questions"]) >= 2

            # Check best successes
            for synth in data["best_successes"]:
                assert synth["category"] == "best_success"
                assert synth["success_rate"] > 0.7
                assert synth["profile_summary"] != ""

    def test_get_extreme_cases_with_custom_n(
        self,
        client,
        experiment_id,
        mock_completed_analysis,
        mock_experiment,
        sample_outcomes,
    ):
        """Test getting extreme cases with custom n_per_category."""
        with (
            patch("synth_lab.api.routers.analysis.get_analysis_service") as mock_analysis_svc,
            patch("synth_lab.api.routers.analysis.get_experiment_service") as mock_exp_svc,
            patch("synth_lab.api.routers.analysis.get_outcome_repository") as mock_outcome_repo,
        ):
            # Setup mocks
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (sample_outcomes, 50)

            # Make request with custom n
            response = client.get(f"/experiments/{experiment_id}/analysis/extreme-cases?n_per_category=5")

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert len(data["worst_failures"]) == 5
            assert len(data["best_successes"]) == 5

    def test_extreme_cases_requires_minimum_synths(
        self,
        client,
        experiment_id,
        mock_completed_analysis,
        mock_experiment,
        few_outcomes,
    ):
        """Test that extreme cases requires at least 10 synths."""
        with (
            patch("synth_lab.api.routers.analysis.get_analysis_service") as mock_analysis_svc,
            patch("synth_lab.api.routers.analysis.get_experiment_service") as mock_exp_svc,
            patch("synth_lab.api.routers.analysis.get_outcome_repository") as mock_outcome_repo,
        ):
            # Setup mocks with only 5 synths
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (few_outcomes, 5)

            # Try to get extreme cases
            response = client.get(f"/experiments/{experiment_id}/analysis/extreme-cases")

            # Should return 400
            assert response.status_code == 400
            assert "at least 10 synths" in response.json()["detail"]


class TestOutlierDetectionEndpoint:
    """Integration tests for outlier detection endpoint."""

    def test_detect_outliers(
        self,
        client,
        experiment_id,
        mock_completed_analysis,
        mock_experiment,
        sample_outcomes,
    ):
        """Test detecting outliers."""
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
            response = client.get(f"/experiments/{experiment_id}/analysis/outliers")

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert data["experiment_id"] == experiment_id
            assert data["method"] == "isolation_forest"
            assert data["contamination"] == 0.1
            assert data["total_synths"] == 50
            assert data["n_outliers"] > 0
            assert len(data["outliers"]) == data["n_outliers"]

            # Check outliers have required fields
            for outlier in data["outliers"]:
                assert outlier["outlier_type"] in [
                    "unexpected_failure",
                    "unexpected_success",
                    "atypical_profile",
                ]
                assert outlier["anomaly_score"] < 0  # Negative = outlier
                assert outlier["explanation"] != ""

    def test_detect_outliers_with_custom_contamination(
        self,
        client,
        experiment_id,
        mock_completed_analysis,
        mock_experiment,
        sample_outcomes,
    ):
        """Test detecting outliers with custom contamination."""
        with (
            patch("synth_lab.api.routers.analysis.get_analysis_service") as mock_analysis_svc,
            patch("synth_lab.api.routers.analysis.get_experiment_service") as mock_exp_svc,
            patch("synth_lab.api.routers.analysis.get_outcome_repository") as mock_outcome_repo,
        ):
            # Setup mocks
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (sample_outcomes, 50)

            # Make request with custom contamination
            response = client.get(f"/experiments/{experiment_id}/analysis/outliers?contamination=0.2")

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["contamination"] == 0.2
            # Should detect more outliers with higher contamination
            assert data["n_outliers"] > 5


if __name__ == "__main__":
    """Run integration tests."""
    pytest.main([__file__, "-v"])
