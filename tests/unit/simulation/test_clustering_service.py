"""
Unit tests for clustering service.

Tests:
- K-Means clustering with elbow method
- Hierarchical clustering with dendrogram
- Cluster profile generation
- Radar chart visualization
- Label suggestions for clusters
"""

import pytest
import numpy as np

from synth_lab.domain.entities import (
    SynthOutcome,
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables,
)
from synth_lab.services.simulation.clustering_service import ClusteringService


@pytest.fixture
def sample_outcomes() -> list[SynthOutcome]:
    """Create sample synth outcomes for testing."""
    outcomes = []

    # Cluster 1: High capability, high trust (Power Users)
    for i in range(30):
        success_rate = 0.7 + np.random.rand() * 0.2
        failed_rate = 0.1 + np.random.rand() * 0.1
        did_not_try_rate = max(0.0, 1.0 - success_rate - failed_rate)
        # Normalize to ensure sum = 1.0
        total = success_rate + failed_rate + did_not_try_rate
        success_rate = success_rate / total
        failed_rate = failed_rate / total
        did_not_try_rate = did_not_try_rate / total
        outcomes.append(
            SynthOutcome(
                synth_id=f"synth_{i:03d}",
                analysis_id="ana_12345678",
                success_rate=success_rate,
                failed_rate=failed_rate,
                did_not_try_rate=did_not_try_rate,
                synth_attributes=SimulationAttributes(
                    observables=SimulationObservables(
                        digital_literacy=0.7,
                        similar_tool_experience=0.7,
                        motor_ability=0.8,
                        time_availability=0.6,
                        domain_expertise=0.7,
                    ),
                    latent_traits=SimulationLatentTraits(
                        capability_mean=0.7 + np.random.rand() * 0.2,
                        trust_mean=0.7 + np.random.rand() * 0.2,
                        friction_tolerance_mean=0.6 + np.random.rand() * 0.2,
                        exploration_prob=0.6,
                    ),
                ),
            )
        )

    # Cluster 2: Low capability, low trust (Strugglers)
    for i in range(30, 60):
        success_rate = 0.1 + np.random.rand() * 0.1
        failed_rate = 0.5 + np.random.rand() * 0.2
        did_not_try_rate = max(0.0, 1.0 - success_rate - failed_rate)
        # Normalize to ensure sum = 1.0
        total = success_rate + failed_rate + did_not_try_rate
        success_rate = success_rate / total
        failed_rate = failed_rate / total
        did_not_try_rate = did_not_try_rate / total
        outcomes.append(
            SynthOutcome(
                synth_id=f"synth_{i:03d}",
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
                        capability_mean=0.2 + np.random.rand() * 0.2,
                        trust_mean=0.2 + np.random.rand() * 0.2,
                        friction_tolerance_mean=0.2 + np.random.rand() * 0.2,
                        exploration_prob=0.2,
                    ),
                ),
            )
        )

    # Cluster 3: Medium capability, high trust (Engaged Users)
    for i in range(60, 90):
        success_rate = 0.4 + np.random.rand() * 0.2
        failed_rate = 0.2 + np.random.rand() * 0.15
        did_not_try_rate = max(0.0, 1.0 - success_rate - failed_rate)
        # Normalize to ensure sum = 1.0
        total = success_rate + failed_rate + did_not_try_rate
        success_rate = success_rate / total
        failed_rate = failed_rate / total
        did_not_try_rate = did_not_try_rate / total
        outcomes.append(
            SynthOutcome(
                synth_id=f"synth_{i:03d}",
                analysis_id="ana_12345678",
                success_rate=success_rate,
                failed_rate=failed_rate,
                did_not_try_rate=did_not_try_rate,
                synth_attributes=SimulationAttributes(
                    observables=SimulationObservables(
                        digital_literacy=0.4,
                        similar_tool_experience=0.5,
                        motor_ability=0.6,
                        time_availability=0.5,
                        domain_expertise=0.5,
                    ),
                    latent_traits=SimulationLatentTraits(
                        capability_mean=0.4 + np.random.rand() * 0.2,
                        trust_mean=0.6 + np.random.rand() * 0.2,
                        friction_tolerance_mean=0.5 + np.random.rand() * 0.2,
                        exploration_prob=0.4,
                    ),
                ),
            )
        )

    return outcomes


class TestKMeansClustering:
    """Test K-Means clustering functionality."""

    def test_cluster_kmeans_basic(self, sample_outcomes):
        """Test basic K-Means clustering with 3 clusters."""
        service = ClusteringService()
        result = service.cluster_kmeans(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            n_clusters=3,
            features=["capability_mean", "trust_mean", "friction_tolerance_mean"],
        )

        assert result.simulation_id == "sim_test"
        assert result.n_clusters == 3
        assert result.method == "kmeans"
        assert len(result.clusters) == 3
        assert len(result.synth_assignments) == 90
        assert result.silhouette_score > 0.0  # Should have positive silhouette
        assert result.inertia > 0.0

        # Check that all clusters have reasonable size
        for cluster in result.clusters:
            assert cluster.size > 0
            assert cluster.percentage > 0
            assert 0 <= cluster.avg_success_rate <= 1.0
            assert 0 <= cluster.avg_failed_rate <= 1.0
            assert 0 <= cluster.avg_did_not_try_rate <= 1.0

    def test_cluster_kmeans_with_elbow_data(self, sample_outcomes):
        """Test that elbow method data is generated."""
        service = ClusteringService()
        result = service.cluster_kmeans(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            n_clusters=3,
        )

        assert len(result.elbow_data) > 0
        assert all(2 <= point.k <= 10 for point in result.elbow_data)
        assert all(point.inertia > 0 for point in result.elbow_data)
        assert all(-1 <= point.silhouette <= 1 for point in result.elbow_data)

    def test_cluster_kmeans_default_features(self, sample_outcomes):
        """Test clustering with default features."""
        service = ClusteringService()
        result = service.cluster_kmeans(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            n_clusters=3,
        )

        # Should use default features
        assert len(result.features_used) > 0
        assert "capability_mean" in result.features_used
        assert "trust_mean" in result.features_used

    def test_cluster_profiles_have_labels(self, sample_outcomes):
        """Test that cluster profiles have suggested labels."""
        service = ClusteringService()
        result = service.cluster_kmeans(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            n_clusters=3,
        )

        for cluster in result.clusters:
            assert cluster.suggested_label != ""
            assert len(cluster.suggested_label) > 0
            assert cluster.cluster_id >= 0
            assert len(cluster.synth_ids) == cluster.size

    def test_cluster_traits_identification(self, sample_outcomes):
        """Test that high/low traits are identified correctly."""
        service = ClusteringService()
        result = service.cluster_kmeans(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            n_clusters=3,
        )

        # Each cluster should have either high or low traits
        for cluster in result.clusters:
            assert isinstance(cluster.high_traits, list)
            assert isinstance(cluster.low_traits, list)


class TestHierarchicalClustering:
    """Test hierarchical clustering functionality."""

    def test_cluster_hierarchical_basic(self, sample_outcomes):
        """Test basic hierarchical clustering."""
        service = ClusteringService()
        result = service.cluster_hierarchical(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            features=["capability_mean", "trust_mean"],
            linkage_method="ward",
        )

        assert result.simulation_id == "sim_test"
        assert result.method == "hierarchical"
        assert result.linkage_method == "ward"
        assert len(result.nodes) > 0
        assert len(result.linkage_matrix) > 0
        assert len(result.suggested_cuts) > 0

    def test_hierarchical_linkage_matrix_format(self, sample_outcomes):
        """Test that linkage matrix has correct scipy format."""
        service = ClusteringService()
        result = service.cluster_hierarchical(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
        )

        # Scipy linkage matrix has shape (n-1, 4) for n samples
        n_outcomes = len(sample_outcomes)
        assert len(result.linkage_matrix) == n_outcomes - 1
        for row in result.linkage_matrix:
            assert len(row) == 4  # [idx1, idx2, distance, count]

    def test_suggested_cuts(self, sample_outcomes):
        """Test that suggested cuts are reasonable."""
        service = ClusteringService()
        result = service.cluster_hierarchical(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
        )

        for cut in result.suggested_cuts:
            assert 2 <= cut.n_clusters <= 10
            assert cut.distance > 0
            assert -1 <= cut.silhouette_estimate <= 1

    def test_cut_dendrogram(self, sample_outcomes):
        """Test cutting dendrogram into N clusters."""
        service = ClusteringService()

        # First create hierarchical result
        hierarchical = service.cluster_hierarchical(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
        )

        # Then cut it
        result = service.cut_dendrogram(
            hierarchical_result=hierarchical,
            n_clusters=3,
        )

        assert result.n_clusters == 3
        assert result.cluster_assignments is not None
        assert len(result.cluster_assignments) == len(sample_outcomes)
        # All cluster IDs should be 0 to n_clusters-1
        cluster_ids = set(result.cluster_assignments.values())
        assert cluster_ids == {0, 1, 2}


class TestRadarChart:
    """Test radar chart generation."""

    def test_get_radar_chart(self, sample_outcomes):
        """Test radar chart generation from clustering result."""
        service = ClusteringService()

        # First create clusters
        kmeans = service.cluster_kmeans(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            n_clusters=3,
        )

        # Then generate radar chart
        radar = service.get_radar_chart(
            simulation_id="sim_test",
            kmeans_result=kmeans,
        )

        assert radar.simulation_id == "sim_test"
        assert len(radar.clusters) == 3
        assert len(radar.axis_labels) > 0
        assert len(radar.baseline) == len(radar.axis_labels)

        # Check each cluster radar
        for cluster_radar in radar.clusters:
            assert cluster_radar.cluster_id >= 0
            assert cluster_radar.label != ""
            assert cluster_radar.color != ""
            assert len(cluster_radar.axes) == len(radar.axis_labels)
            assert 0 <= cluster_radar.success_rate <= 1.0

            # Check axes normalization
            for axis in cluster_radar.axes:
                assert 0 <= axis.normalized <= 1.0
                assert axis.value >= 0

    def test_radar_chart_axis_consistency(self, sample_outcomes):
        """Test that all clusters have same axes."""
        service = ClusteringService()
        kmeans = service.cluster_kmeans(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            n_clusters=3,
        )
        radar = service.get_radar_chart(
            simulation_id="sim_test",
            kmeans_result=kmeans,
        )

        # All clusters should have same number and order of axes
        first_cluster_axes = [axis.name for axis in radar.clusters[0].axes]
        for cluster_radar in radar.clusters[1:]:
            cluster_axes = [axis.name for axis in cluster_radar.axes]
            assert cluster_axes == first_cluster_axes


class TestElbowMethod:
    """Test elbow method calculation."""

    def test_calculate_elbow_range(self, sample_outcomes):
        """Test that elbow method tests k from 2 to 10."""
        service = ClusteringService()
        result = service.cluster_kmeans(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            n_clusters=3,
        )

        k_values = [point.k for point in result.elbow_data]
        assert min(k_values) >= 2
        assert max(k_values) <= 10

        # Should be sequential
        k_values_sorted = sorted(k_values)
        assert k_values_sorted == list(range(min(k_values), max(k_values) + 1))

    def test_elbow_inertia_decreases(self, sample_outcomes):
        """Test that inertia generally decreases as k increases."""
        service = ClusteringService()
        result = service.cluster_kmeans(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            n_clusters=3,
        )

        # Sort by k
        elbow_sorted = sorted(result.elbow_data, key=lambda x: x.k)

        # Inertia should generally decrease
        # (may not be strictly decreasing due to random initialization)
        inertias = [point.inertia for point in elbow_sorted]
        assert inertias[0] > inertias[-1]  # First > last


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_minimum_synths_for_clustering(self):
        """Test that clustering requires minimum 10 synths."""
        service = ClusteringService()

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
            service.cluster_kmeans(
                simulation_id="sim_test",
                outcomes=few_outcomes,
                n_clusters=2,
            )

    def test_n_clusters_less_than_synths(self, sample_outcomes):
        """Test that n_clusters must be less than number of synths."""
        service = ClusteringService()

        with pytest.raises(ValueError, match="n_clusters"):
            service.cluster_kmeans(
                simulation_id="sim_test",
                outcomes=sample_outcomes,
                n_clusters=100,  # More than 90 synths
            )

    def test_empty_features_list(self, sample_outcomes):
        """Test that empty features list uses defaults."""
        service = ClusteringService()
        result = service.cluster_kmeans(
            simulation_id="sim_test",
            outcomes=sample_outcomes,
            n_clusters=3,
            features=[],  # Empty list
        )

        # Should fallback to default features
        assert len(result.features_used) > 0


if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v"])
