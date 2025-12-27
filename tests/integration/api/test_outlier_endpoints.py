"""
Integration tests for outlier detection API endpoints.

Tests the full outlier detection flow from API request to response.

References:
    - Outlier Router: src/synth_lab/api/routers/simulation.py
    - Outlier Service: src/synth_lab/services/simulation/outlier_service.py
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app
from synth_lab.domain.entities import (
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables,
    SimulationRun,
    SynthOutcome,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_simulation():
    """Create a mock simulation run."""
    return SimulationRun(
        id="sim_12345678",
        scorecard_id="scorecard_001",
        scenario_id="baseline",
        num_synths=50,
        simulations_per_synth=100,
        status="completed",
        seed=42,
    )


@pytest.fixture
def sample_outcomes():
    """Create sample synth outcomes with extreme cases and outliers."""
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
            SynthOutcome(
                synth_id=f"worst_{i:03d}",
                simulation_id="sim_12345678",
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
                        capability_mean=0.7 + np.random.rand() * 0.2,
                        trust_mean=0.2 + np.random.rand() * 0.1,
                        friction_tolerance_mean=0.2 + np.random.rand() * 0.1,
                        exploration_prob=0.2,
                    ),
                ),
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
            SynthOutcome(
                synth_id=f"best_{i:03d}",
                simulation_id="sim_12345678",
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
            SynthOutcome(
                synth_id=f"normal_{i:03d}",
                simulation_id="sim_12345678",
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


class TestExtremeCasesEndpoint:
    """Integration tests for extreme cases endpoint."""

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_get_extreme_cases(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test getting extreme cases."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.get("/simulation/simulations/sim_12345678/extreme-cases")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["simulation_id"] == "sim_12345678"
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

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_get_extreme_cases_with_custom_n(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test getting extreme cases with custom n_per_category."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request with custom n
        response = client.get(
            "/simulation/simulations/sim_12345678/extreme-cases?n_per_category=5"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["worst_failures"]) == 5
        assert len(data["best_successes"]) == 5

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    def test_extreme_cases_requires_completed_simulation(
        self, mock_get_service, client
    ):
        """Test that extreme cases requires completed simulation."""
        # Setup mock with non-completed simulation
        incomplete_sim = SimulationRun(
            id="sim_abcd1234",
            scorecard_id="scorecard_001",
            scenario_id="baseline",
            num_synths=50,
            simulations_per_synth=100,
            status="running",
            seed=42,
        )

        mock_service = MagicMock()
        mock_service.get_simulation.return_value = incomplete_sim
        mock_get_service.return_value = mock_service

        # Try to get extreme cases
        response = client.get("/simulation/simulations/sim_abcd1234/extreme-cases")

        # Should return 400
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_extreme_cases_requires_minimum_synths(
        self, mock_get_outcomes, mock_get_service, client, sample_simulation
    ):
        """Test that extreme cases requires at least 10 synths."""
        # Setup mocks with only 5 synths
        few_outcomes = [
            SynthOutcome(
                synth_id=f"synth_{i:03d}",
                simulation_id="sim_12345678",
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

        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = few_outcomes

        # Try to get extreme cases
        response = client.get("/simulation/simulations/sim_12345678/extreme-cases")

        # Should return 400
        assert response.status_code == 400
        assert "at least 10 synths" in response.json()["detail"]


class TestOutlierDetectionEndpoint:
    """Integration tests for outlier detection endpoint."""

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_detect_outliers(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test detecting outliers."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.get("/simulation/simulations/sim_12345678/outliers")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["simulation_id"] == "sim_12345678"
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

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_detect_outliers_with_custom_contamination(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test detecting outliers with custom contamination."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request with custom contamination
        response = client.get(
            "/simulation/simulations/sim_12345678/outliers?contamination=0.2"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["contamination"] == 0.2
        # Should detect more outliers with higher contamination
        assert data["n_outliers"] > 5

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    def test_outliers_requires_completed_simulation(self, mock_get_service, client):
        """Test that outlier detection requires completed simulation."""
        # Setup mock with non-completed simulation
        incomplete_sim = SimulationRun(
            id="sim_abcd1234",
            scorecard_id="scorecard_001",
            scenario_id="baseline",
            num_synths=50,
            simulations_per_synth=100,
            status="running",
            seed=42,
        )

        mock_service = MagicMock()
        mock_service.get_simulation.return_value = incomplete_sim
        mock_get_service.return_value = mock_service

        # Try to detect outliers
        response = client.get("/simulation/simulations/sim_abcd1234/outliers")

        # Should return 400
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]


if __name__ == "__main__":
    """Run integration tests."""
    pytest.main([__file__, "-v"])
