"""
Integration tests for explainability API endpoints.

Tests the full SHAP and PDP flow from API request to response.

References:
    - Simulation Router: src/synth_lab/api/routers/simulation.py
    - Explainability Service: src/synth_lab/services/simulation/explainability_service.py
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
        num_synths=100,
        simulations_per_synth=50,
        status="completed",
        seed=42,
    )


@pytest.fixture
def sample_outcomes():
    """Create sample synth outcomes for testing with realistic data."""
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


class TestShapEndpoints:
    """Integration tests for SHAP endpoints."""

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_get_shap_explanation_basic(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test getting SHAP explanation for a specific synth."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.get("/simulation/simulations/sim_12345678/shap/synth_010")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["simulation_id"] == "sim_12345678"
        assert data["synth_id"] == "synth_010"
        assert "predicted_success_rate" in data
        assert "actual_success_rate" in data
        assert "baseline_prediction" in data
        assert "contributions" in data
        assert "explanation_text" in data
        assert len(data["contributions"]) > 0

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_shap_explanation_contributions_sorted(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test that SHAP contributions are sorted by absolute value."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.get("/simulation/simulations/sim_12345678/shap/synth_025")

        assert response.status_code == 200
        data = response.json()

        # Contributions should be sorted by absolute SHAP value (descending)
        shap_values = [abs(c["shap_value"]) for c in data["contributions"]]
        assert shap_values == sorted(shap_values, reverse=True)

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_get_shap_summary_basic(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test getting global SHAP summary."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.get("/simulation/simulations/sim_12345678/shap/summary")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["simulation_id"] == "sim_12345678"
        assert "feature_importances" in data
        assert "top_features" in data
        assert "total_synths" in data
        assert "model_score" in data
        assert len(data["feature_importances"]) > 0
        assert len(data["top_features"]) > 0
        assert data["total_synths"] == len(sample_outcomes)
        assert 0 <= data["model_score"] <= 1.0

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_shap_summary_importances_positive(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test that feature importances are positive."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.get("/simulation/simulations/sim_12345678/shap/summary")

        assert response.status_code == 200
        data = response.json()

        for importance in data["feature_importances"].values():
            assert importance >= 0

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_shap_explanation_synth_not_found(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test error when synth not found."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request with non-existent synth
        response = client.get("/simulation/simulations/sim_12345678/shap/nonexistent_synth")

        # Should return 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestPDPEndpoints:
    """Integration tests for PDP endpoints."""

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_get_pdp_basic(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test getting PDP for a feature."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.get("/simulation/simulations/sim_12345678/pdp?feature=trust_mean")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["simulation_id"] == "sim_12345678"
        assert data["feature_name"] == "trust_mean"
        assert "feature_display_name" in data
        assert "pdp_values" in data
        assert "effect_type" in data
        assert "effect_strength" in data
        assert len(data["pdp_values"]) > 0

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_pdp_values_sorted(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test that PDP values are sorted by feature value."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.get("/simulation/simulations/sim_12345678/pdp?feature=capability_mean")

        assert response.status_code == 200
        data = response.json()

        feature_values = [p["feature_value"] for p in data["pdp_values"]]
        assert feature_values == sorted(feature_values)

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_pdp_grid_resolution(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test PDP with custom grid resolution."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request with custom resolution
        response = client.get(
            "/simulation/simulations/sim_12345678/pdp?feature=trust_mean&grid_resolution=10"
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["pdp_values"]) == 10

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_pdp_effect_type_valid(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test that PDP effect type is valid."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.get("/simulation/simulations/sim_12345678/pdp?feature=trust_mean")

        assert response.status_code == 200
        data = response.json()

        valid_effect_types = [
            "monotonic_increasing",
            "monotonic_decreasing",
            "non_linear",
            "flat",
        ]
        assert data["effect_type"] in valid_effect_types

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_pdp_invalid_feature(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test error for invalid feature."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request with invalid feature
        response = client.get("/simulation/simulations/sim_12345678/pdp?feature=invalid_feature")

        # Should return 400
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]


class TestPDPComparisonEndpoint:
    """Integration tests for PDP comparison endpoint."""

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_pdp_comparison_basic(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test basic PDP comparison."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.get(
            "/simulation/simulations/sim_12345678/pdp/comparison?features=trust_mean,capability_mean"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["simulation_id"] == "sim_12345678"
        assert len(data["pdp_results"]) == 2
        assert len(data["feature_ranking"]) == 2
        assert data["total_synths"] == len(sample_outcomes)

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_pdp_comparison_ranking(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test that features are ranked by effect strength."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.get(
            "/simulation/simulations/sim_12345678/pdp/comparison?features=trust_mean,capability_mean,friction_tolerance_mean"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify ranking matches effect strengths
        pdp_map = {pdp["feature_name"]: pdp["effect_strength"] for pdp in data["pdp_results"]}
        ranked_strengths = [pdp_map[f] for f in data["feature_ranking"]]
        assert ranked_strengths == sorted(ranked_strengths, reverse=True)

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_pdp_comparison_requires_two_features(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test that comparison requires at least 2 features."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request with only 1 feature
        response = client.get(
            "/simulation/simulations/sim_12345678/pdp/comparison?features=trust_mean"
        )

        # Should return 400
        assert response.status_code == 400
        assert "At least 2 features" in response.json()["detail"]


class TestExplainabilityEdgeCases:
    """Test edge cases and error handling."""

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    def test_shap_simulation_not_found(self, mock_get_service, client):
        """Test error when simulation not found."""
        # Setup mock with no simulation
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = None
        mock_get_service.return_value = mock_service

        # Try to get SHAP
        response = client.get("/simulation/simulations/sim_nonexistent/shap/synth_000")

        # Should return 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    def test_shap_requires_completed_simulation(self, mock_get_service, client):
        """Test that SHAP requires completed simulation."""
        # Setup mock with non-completed simulation
        incomplete_sim = SimulationRun(
            id="sim_abcd1234",
            scorecard_id="scorecard_001",
            scenario_id="baseline",
            num_synths=100,
            simulations_per_synth=50,
            status="running",  # Not completed
            seed=42,
        )

        mock_service = MagicMock()
        mock_service.get_simulation.return_value = incomplete_sim
        mock_get_service.return_value = mock_service

        # Try to get SHAP
        response = client.get("/simulation/simulations/sim_abcd1234/shap/synth_000")

        # Should return 400
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_shap_requires_minimum_synths(self, mock_get_outcomes, mock_get_service, client):
        """Test that SHAP requires at least 20 synths."""
        # Setup mocks with only 10 synths
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
            for i in range(10)
        ]

        sample_sim = SimulationRun(
            id="sim_12345678",
            scorecard_id="scorecard_001",
            scenario_id="baseline",
            num_synths=10,
            simulations_per_synth=50,
            status="completed",
            seed=42,
        )

        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_sim
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = few_outcomes

        # Try to get SHAP
        response = client.get("/simulation/simulations/sim_12345678/shap/synth_000")

        # Should return 400
        assert response.status_code == 400
        assert "at least 20 synths" in response.json()["detail"]


if __name__ == "__main__":
    """Run integration tests."""
    pytest.main([__file__, "-v"])
