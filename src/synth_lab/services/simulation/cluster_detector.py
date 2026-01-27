"""
Cluster Detector for causal simulation system.

Identifies behavioral clusters in simulated worlds using k-means clustering
with automatic k selection via elbow method.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - scikit-learn KMeans: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html
    - kneed: https://kneed.readthedocs.io/en/stable/
"""

import numpy as np
from kneed import KneeLocator
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from synth_lab.domain.entities.simulated_world import (
    BehavioralCluster,
    ClusterOutcomeStats,
)


class ClusterDetector:
    """
    Detector for behavioral clusters in simulated worlds.

    Uses k-means clustering with automatic determination of optimal k via
    elbow method. Standardizes features before clustering.
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize cluster detector.

        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        self.scaler = StandardScaler()

    def detect_clusters(
        self,
        variable_matrix: np.ndarray,
        outcome_matrix: np.ndarray,
        variable_names: list[str],
        outcome_names: list[str],
        world_ids: list[str],
        evidence_id: str,
        k_range: tuple[int, int] = (2, 10),
    ) -> list[BehavioralCluster]:
        """
        Detect behavioral clusters in simulated worlds.

        Automatically determines optimal number of clusters using elbow method,
        then performs k-means clustering on standardized variable values.

        Args:
            variable_matrix: World variable values (shape: (n_worlds, n_vars))
            outcome_matrix: World outcome values (shape: (n_worlds, n_outcomes))
            variable_names: Names of variables (length: n_vars)
            outcome_names: Names of outcomes (length: n_outcomes)
            world_ids: IDs of worlds (length: n_worlds)
            evidence_id: Parent evidence ID
            k_range: Range of k values to test (min_k, max_k)

        Returns:
            List of BehavioralCluster entities

        Example:
            >>> detector = ClusterDetector(random_state=42)
            >>> clusters = detector.detect_clusters(
            ...     var_matrix, outcome_matrix, var_names, outcome_names, world_ids, evd_id
            ... )
            >>> print(f"Found {len(clusters)} clusters")
        """
        n_worlds = len(world_ids)

        # Standardize features
        variable_matrix_scaled = self.scaler.fit_transform(variable_matrix)

        # Find optimal k using elbow method
        optimal_k = self._find_optimal_k(
            variable_matrix_scaled, k_range[0], k_range[1]
        )

        # Perform k-means clustering
        kmeans = KMeans(
            n_clusters=optimal_k, random_state=self.random_state, n_init=10
        )
        cluster_labels = kmeans.fit_predict(variable_matrix_scaled)

        # Build BehavioralCluster entities
        clusters = []
        for cluster_num in range(optimal_k):
            # Get indices of worlds in this cluster
            cluster_mask = cluster_labels == cluster_num
            cluster_world_ids = [
                world_ids[i] for i in range(n_worlds) if cluster_mask[i]
            ]
            cluster_size = len(cluster_world_ids)

            # Calculate centroid (in original space, not scaled)
            centroid = {}
            for i, var_name in enumerate(variable_names):
                centroid[var_name] = float(
                    np.mean(variable_matrix[cluster_mask, i])
                )

            # Calculate outcome stats for this cluster
            outcome_stats = {}
            for i, outcome_name in enumerate(outcome_names):
                cluster_outcome_values = outcome_matrix[cluster_mask, i]
                outcome_stats[outcome_name] = ClusterOutcomeStats(
                    mean=float(np.mean(cluster_outcome_values)),
                    std=float(np.std(cluster_outcome_values)),
                    p50=float(np.median(cluster_outcome_values)),
                )

            # Generate cluster label
            label = self._generate_cluster_label(
                centroid, variable_names, cluster_num
            )

            clusters.append(
                BehavioralCluster(
                    evidence_id=evidence_id,
                    cluster_number=cluster_num + 1,  # 1-indexed
                    world_ids=cluster_world_ids,
                    centroid=centroid,
                    outcome_stats=outcome_stats,
                    size=cluster_size,
                    percentage=float(cluster_size / n_worlds),
                    label=label,
                )
            )

        # Sort clusters by size (descending)
        clusters.sort(key=lambda x: x.size, reverse=True)

        return clusters

    def _find_optimal_k(
        self, variable_matrix_scaled: np.ndarray, min_k: int, max_k: int
    ) -> int:
        """
        Find optimal number of clusters using elbow method.

        Args:
            variable_matrix_scaled: Standardized variable matrix
            min_k: Minimum number of clusters to test
            max_k: Maximum number of clusters to test

        Returns:
            Optimal number of clusters
        """
        # Compute inertia for different k values
        inertias = []
        k_values = range(min_k, max_k + 1)

        for k in k_values:
            kmeans = KMeans(
                n_clusters=k, random_state=self.random_state, n_init=10
            )
            kmeans.fit(variable_matrix_scaled)
            inertias.append(kmeans.inertia_)

        # Find elbow point
        try:
            knee_locator = KneeLocator(
                k_values,
                inertias,
                curve="convex",
                direction="decreasing",
            )
            optimal_k = knee_locator.elbow

            # If no clear elbow, default to middle of range
            if optimal_k is None:
                optimal_k = (min_k + max_k) // 2

        except Exception:
            # Fallback if kneed fails
            optimal_k = (min_k + max_k) // 2

        return optimal_k

    def _generate_cluster_label(
        self,
        centroid: dict[str, float],
        variable_names: list[str],
        cluster_num: int,
    ) -> str:
        """
        Generate human-readable label for cluster based on centroid.

        Identifies top 2 variables with highest absolute centroid values.

        Args:
            centroid: Cluster centroid (variable_name: mean_value)
            variable_names: Names of variables
            cluster_num: Cluster number

        Returns:
            Human-readable cluster label

        Example:
            >>> label = _generate_cluster_label(
            ...     {"var1": 0.8, "var2": 0.3}, ["var1", "var2"], 0
            ... )
            >>> print(label)  # "High var1 + medium var2"
        """
        # Sort variables by absolute centroid value
        sorted_vars = sorted(
            variable_names, key=lambda v: abs(centroid[v]), reverse=True
        )

        # Take top 2 variables
        top_vars = sorted_vars[:2]

        # Generate descriptive terms
        terms = []
        for var in top_vars:
            value = centroid[var]
            if abs(value) < 0.3:
                level = "low"
            elif abs(value) < 0.7:
                level = "medium"
            else:
                level = "high"

            terms.append(f"{level} {var}")

        if len(terms) == 0:
            return f"Cluster {cluster_num + 1}"
        elif len(terms) == 1:
            return terms[0].capitalize()
        else:
            return f"{terms[0].capitalize()} + {terms[1]}"
