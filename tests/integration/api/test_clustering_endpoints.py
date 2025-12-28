"""
Integration tests for clustering API endpoints.

Tests the full clustering flow from API request to response.

References:
    - Clustering Router: src/synth_lab/api/routers/simulation.py
    - Clustering Service: src/synth_lab/services/simulation/clustering_service.py
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
        num_synths=100,
        simulations_per_synth=50,
        status="completed",
        seed=42,
    )


@pytest.fixture
def sample_outcomes():
    """Create sample synth outcomes for testing."""
    outcomes = []

    # Create 100 outcomes with varying attributes
    for i in range(100):
        # Vary attributes to create distinct clusters
        if i < 30:  # Cluster 1: High performers
            cap = 0.7 + np.random.rand() * 0.2
            trust = 0.7 + np.random.rand() * 0.2
            success_base = 0.7
        elif i < 60:  # Cluster 2: Low performers
            cap = 0.2 + np.random.rand() * 0.2
            trust = 0.2 + np.random.rand() * 0.2
            success_base = 0.2
        else:  # Cluster 3: Medium performers
            cap = 0.4 + np.random.rand() * 0.2
            trust = 0.5 + np.random.rand() * 0.2
            success_base = 0.5

        success_rate = success_base + np.random.rand() * 0.15
        failed_rate = 0.2 + np.random.rand() * 0.1
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
                        digital_literacy=0.5,
                        similar_tool_experience=0.5,
                        motor_ability=0.5,
                        time_availability=0.5,
                        domain_expertise=0.5,
                    ),
                    latent_traits=SimulationLatentTraits(
                        capability_mean=cap,
                        trust_mean=trust,
                        friction_tolerance_mean=0.5,
                        exploration_prob=0.4,
                    ),
                ),
            )
        )

    return outcomes


@pytest.fixture
def mock_get_simulation_outcomes(sample_outcomes):
    """Mock get_simulation_outcomes_as_entities function."""
    def mock_func(service, simulation_id):
        return sample_outcomes

    return mock_func


class TestClusteringEndpoints:
    """Integration tests for clustering endpoints."""

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_create_kmeans_clustering(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test creating K-Means clustering."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.post(
            "/simulation/simulations/sim_12345678/clusters",
            json={"method": "kmeans", "n_clusters": 3},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["simulation_id"] == "sim_12345678"
        assert data["n_clusters"] == 3
        assert data["method"] == "kmeans"
        assert len(data["clusters"]) == 3
        assert "silhouette_score" in data
        assert "inertia" in data
        assert "elbow_data" in data
        assert data["silhouette_score"] > 0

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_create_hierarchical_clustering(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test creating Hierarchical clustering."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Make request
        response = client.post(
            "/simulation/simulations/sim_12345678/clusters",
            json={"method": "hierarchical", "linkage": "ward"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["simulation_id"] == "sim_12345678"
        assert data["method"] == "hierarchical"
        assert data["linkage_method"] == "ward"
        assert "nodes" in data
        assert "linkage_matrix" in data
        assert "suggested_cuts" in data
        assert len(data["nodes"]) > 0

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_get_clustering_after_creation(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test getting clustering after creation."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Create clustering first
        create_response = client.post(
            "/simulation/simulations/sim_12345678/clusters",
            json={"method": "kmeans", "n_clusters": 3},
        )
        assert create_response.status_code == 200

        # Get clustering
        get_response = client.get("/simulation/simulations/sim_12345678/clusters")

        # Assertions
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["simulation_id"] == "sim_12345678"
        assert data["method"] == "kmeans"

    def test_get_clustering_without_creation(self, client):
        """Test getting clustering without creating it first."""
        # Clear cache
        from synth_lab.api.routers.simulation import _clustering_cache

        _clustering_cache.clear()

        # Try to get non-existent clustering
        response = client.get("/simulation/simulations/sim_nonexistent/clusters")

        # Should return 404
        assert response.status_code == 404
        assert "No clustering found" in response.json()["detail"]

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_get_elbow_data(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test getting elbow method data."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Create K-Means clustering first
        client.post(
            "/simulation/simulations/sim_12345678/clusters",
            json={"method": "kmeans", "n_clusters": 3},
        )

        # Get elbow data
        response = client.get("/simulation/simulations/sim_12345678/clusters/elbow")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("k" in point and "inertia" in point for point in data)

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_get_radar_comparison(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test getting radar chart comparison."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Create K-Means clustering first
        client.post(
            "/simulation/simulations/sim_12345678/clusters",
            json={"method": "kmeans", "n_clusters": 3},
        )

        # Get radar comparison
        response = client.get(
            "/simulation/simulations/sim_12345678/clusters/radar-comparison"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["simulation_id"] == "sim_12345678"
        assert "clusters" in data
        assert len(data["clusters"]) == 3
        assert "axis_labels" in data
        assert "baseline" in data

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_get_cluster_radar(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test getting radar chart for specific cluster."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Create K-Means clustering first
        client.post(
            "/simulation/simulations/sim_12345678/clusters",
            json={"method": "kmeans", "n_clusters": 3},
        )

        # Get radar for cluster 0
        response = client.get(
            "/simulation/simulations/sim_12345678/clusters/0/radar"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["clusters"]) == 1
        assert data["clusters"][0]["cluster_id"] == 0

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_cut_dendrogram(
        self,
        mock_get_outcomes,
        mock_get_service,
        client,
        sample_simulation,
        sample_outcomes,
    ):
        """Test cutting hierarchical dendrogram."""
        # Setup mocks
        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = sample_outcomes

        # Create hierarchical clustering first
        client.post(
            "/simulation/simulations/sim_12345678/clusters",
            json={"method": "hierarchical"},
        )

        # Cut dendrogram
        response = client.post(
            "/simulation/simulations/sim_12345678/clusters/cut",
            json={"n_clusters": 4},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["n_clusters"] == 4
        assert data["cluster_assignments"] is not None
        assert len(data["cluster_assignments"]) == 100

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    def test_clustering_requires_completed_simulation(
        self, mock_get_service, client
    ):
        """Test that clustering requires completed simulation."""
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

        # Try to create clustering
        response = client.post(
            "/simulation/simulations/sim_abcd1234/clusters",
            json={"method": "kmeans", "n_clusters": 3},
        )

        # Should return 400
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]

    @patch("synth_lab.api.routers.simulation.get_simulation_service")
    @patch("synth_lab.api.routers.simulation.get_simulation_outcomes_as_entities")
    def test_clustering_requires_minimum_synths(
        self, mock_get_outcomes, mock_get_service, client, sample_simulation
    ):
        """Test that clustering requires at least 10 synths."""
        # Setup mocks with only 5 synths
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

        mock_service = MagicMock()
        mock_service.get_simulation.return_value = sample_simulation
        mock_get_service.return_value = mock_service
        mock_get_outcomes.return_value = few_outcomes

        # Try to create clustering
        response = client.post(
            "/simulation/simulations/sim_12345678/clusters",
            json={"method": "kmeans", "n_clusters": 3},
        )

        # Should return 400
        assert response.status_code == 400
        assert "at least 10 synths" in response.json()["detail"]


if __name__ == "__main__":
    """Run integration tests."""
    pytest.main([__file__, "-v"])
