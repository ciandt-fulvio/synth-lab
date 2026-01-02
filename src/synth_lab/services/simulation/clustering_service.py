"""
Clustering service for UX Research analysis.

Provides K-Means and Hierarchical clustering for persona segmentation.

References:
    - scikit-learn K-Means: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html
    - scipy hierarchical: https://docs.scipy.org/doc/scipy/reference/cluster.hierarchy.html
    - Spec: specs/017-analysis-ux-research/spec.md
"""

import numpy as np
from loguru import logger
from scipy.cluster import hierarchy
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from synth_lab.domain.entities import (
    ClusterProfile,
    ClusterRadar,
    DendrogramNode,
    ElbowDataPoint,
    HierarchicalResult,
    KMeansResult,
    PCAScatterChart,
    PCAScatterPoint,
    RadarAxis,
    RadarChart,
    SuggestedCut,
    SynthOutcome)
from synth_lab.services.simulation.cluster_labeling_service import (
    ClusterLabelingService)
from synth_lab.services.simulation.feature_extraction import get_attribute_value


class ClusteringService:
    """
    Service for clustering synths into personas.

    Provides K-Means and Hierarchical clustering with visualization support.
    """

    # Default features for clustering (latent traits that drive simulation outcomes)
    # Using only latent traits for clustering to avoid curse of dimensionality
    DEFAULT_FEATURES = [
        "capability_mean",
        "trust_mean",
        "friction_tolerance_mean",
        "exploration_prob",
    ]

    # Color palette for clusters (up to 10 clusters) - distinct colors with purple/violet tones
    CLUSTER_COLORS = [
        "#8B5CF6",  # Violet
        "#EC4899",  # Pink
        "#F59E0B",  # Amber
        "#10B981",  # Emerald
        "#3B82F6",  # Blue
        "#EF4444",  # Red
        "#6366F1",  # Indigo
        "#14B8A6",  # Teal
        "#F97316",  # Orange
        "#A855F7",  # Purple
    ]

    def cluster_kmeans(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        n_clusters: int | None = None,
        features: list[str] | None = None) -> KMeansResult:
        """
        Perform K-Means clustering on synth outcomes.

        Args:
            simulation_id: ID of the simulation.
            outcomes: List of SynthOutcome entities.
            n_clusters: Number of clusters to create. If None, uses automatic detection.
            features: List of feature names to use. Defaults to DEFAULT_FEATURES.

        Returns:
            KMeansResult with cluster profiles and assignments.

        Raises:
            ValueError: If too few synths or invalid parameters.
        """
        if len(outcomes) < 10:
            raise ValueError(f"Clustering requires at least 10 synths, got {len(outcomes)}")

        # Use default features if none provided or empty
        if not features:
            features = self.DEFAULT_FEATURES

        # Extract and normalize features
        X, synth_ids = self._extract_features(outcomes, features)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Calculate elbow data and detect recommended K
        elbow_data = self._calculate_elbow(X_scaled, max_k=min(10, len(outcomes) - 1))
        recommended_k = self._detect_knee_point(elbow_data)

        # Use automatic K detection if n_clusters not provided
        if n_clusters is None:
            n_clusters = recommended_k
            logger.info(
                f"Using automatic K detection: K={n_clusters} (from {len(outcomes)} synths)"
            )
        else:
            n_synths = len(outcomes)
            logger.info(
                f"Using manual K={n_clusters} (recommended K={recommended_k}, {n_synths} synths)"
            )

        if n_clusters >= len(outcomes):
            raise ValueError(
                f"n_clusters ({n_clusters}) must be less than number of synths ({len(outcomes)})"
            )

        # Perform K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        # Calculate metrics
        n_unique_labels = len(np.unique(labels))
        inertia = kmeans.inertia_

        # silhouette_score requires at least 2 distinct clusters
        if n_unique_labels < 2:
            logger.warning(
                f"K-Means converged to only {n_unique_labels} cluster(s). "
                "Data may have duplicate/very similar points. Silhouette score set to 0.0"
            )
            silhouette = 0.0
        else:
            silhouette = silhouette_score(X_scaled, labels)

        # Build cluster profiles
        clusters = self._build_cluster_profiles(
            outcomes=outcomes,
            labels=labels,
            centroids=kmeans.cluster_centers_,
            scaler=scaler,
            feature_names=features)

        # Build synth assignments
        synth_assignments = {synth_id: int(label) for synth_id, label in zip(synth_ids, labels)}

        return KMeansResult(
            simulation_id=simulation_id,
            n_clusters=n_clusters,
            features_used=features,
            silhouette_score=float(silhouette),
            inertia=float(inertia),
            clusters=clusters,
            synth_assignments=synth_assignments,
            elbow_data=elbow_data,
            recommended_k=recommended_k)

    def cluster_hierarchical(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        features: list[str] | None = None,
        linkage_method: str = "ward") -> HierarchicalResult:
        """
        Perform hierarchical clustering on synth outcomes.

        Args:
            simulation_id: ID of the simulation.
            outcomes: List of SynthOutcome entities.
            features: List of feature names to use.
            linkage_method: Linkage method ('ward', 'complete', 'average', 'single').

        Returns:
            HierarchicalResult with dendrogram data.
        """
        if len(outcomes) < 10:
            raise ValueError(f"Clustering requires at least 10 synths, got {len(outcomes)}")

        if not features:
            features = self.DEFAULT_FEATURES

        logger.info(f"Hierarchical clustering {len(outcomes)} synths with {linkage_method} linkage")

        # Extract and normalize features
        X, synth_ids = self._extract_features(outcomes, features)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Perform hierarchical clustering
        linkage_matrix = hierarchy.linkage(X_scaled, method=linkage_method)

        # Build dendrogram nodes
        nodes = self._build_dendrogram_nodes(linkage_matrix, synth_ids)

        # Suggest good cut points
        suggested_cuts = self._suggest_cuts(X_scaled=X_scaled, linkage_matrix=linkage_matrix)

        return HierarchicalResult(
            simulation_id=simulation_id,
            linkage_method=linkage_method,
            features_used=features,
            nodes=nodes,
            linkage_matrix=linkage_matrix.tolist(),
            suggested_cuts=suggested_cuts)

    # =========================================================================
    # Convenience Wrapper Methods (for router compatibility)
    # =========================================================================

    def kmeans(
        self,
        outcomes: list[SynthOutcome],
        k: int = 4,
        features: list[str] | None = None) -> KMeansResult:
        """
        Convenience wrapper for cluster_kmeans.

        Args:
            outcomes: List of SynthOutcome entities.
            k: Number of clusters.
            features: Optional feature list.

        Returns:
            KMeansResult with cluster profiles.
        """
        # Extract analysis_id from first outcome if available
        analysis_id = outcomes[0].analysis_id if outcomes else "unknown"
        return self.cluster_kmeans(
            simulation_id=analysis_id,
            outcomes=outcomes,
            n_clusters=k,
            features=features)

    def hierarchical(
        self,
        outcomes: list[SynthOutcome],
        features: list[str] | None = None) -> HierarchicalResult:
        """
        Convenience wrapper for cluster_hierarchical.

        Args:
            outcomes: List of SynthOutcome entities.
            features: Optional feature list.

        Returns:
            HierarchicalResult with dendrogram data.
        """
        analysis_id = outcomes[0].analysis_id if outcomes else "unknown"
        return self.cluster_hierarchical(
            simulation_id=analysis_id,
            outcomes=outcomes,
            features=features)

    def elbow_method(
        self,
        outcomes: list[SynthOutcome],
        max_k: int = 10,
        features: list[str] | None = None) -> list[ElbowDataPoint]:
        """
        Calculate elbow method data for K selection.

        Args:
            outcomes: List of SynthOutcome entities.
            max_k: Maximum K to test.
            features: Optional feature list.

        Returns:
            List of ElbowDataPoint with inertia and silhouette for each K.
        """
        if len(outcomes) < 10:
            raise ValueError(f"Elbow method requires at least 10 synths, got {len(outcomes)}")

        if not features:
            features = self.DEFAULT_FEATURES

        # Extract and normalize features
        X, _ = self._extract_features(outcomes, features)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Calculate elbow data
        actual_max_k = min(max_k, len(outcomes) - 1)
        return self._calculate_elbow(X_scaled, max_k=actual_max_k)

    def radar_comparison(
        self,
        kmeans_result: KMeansResult) -> RadarChart:
        """
        Convenience wrapper for get_radar_chart.

        Args:
            kmeans_result: K-Means clustering result.

        Returns:
            RadarChart for cluster comparison.
        """
        return self.get_radar_chart(
            simulation_id=kmeans_result.simulation_id,
            kmeans_result=kmeans_result)

    def cut_dendrogram(
        self,
        hierarchical_result: HierarchicalResult,
        n_clusters: int) -> HierarchicalResult:
        """
        Cut dendrogram at specified number of clusters.

        Args:
            hierarchical_result: Original hierarchical result.
            n_clusters: Number of clusters to cut into.

        Returns:
            Updated HierarchicalResult with cluster assignments.
        """
        linkage_matrix = np.array(hierarchical_result.linkage_matrix)

        # Cut the dendrogram
        labels = hierarchy.fcluster(linkage_matrix, n_clusters, criterion="maxclust")

        # Convert labels to 0-indexed
        labels = labels - 1

        # Build synth to cluster mapping
        # Extract synth_ids from leaf nodes
        synth_ids = [node.synth_id for node in hierarchical_result.nodes if node.synth_id]

        cluster_assignments = {synth_id: int(label) for synth_id, label in zip(synth_ids, labels)}

        # Return updated result
        return HierarchicalResult(
            simulation_id=hierarchical_result.simulation_id,
            linkage_method=hierarchical_result.linkage_method,
            features_used=hierarchical_result.features_used,
            nodes=hierarchical_result.nodes,
            linkage_matrix=hierarchical_result.linkage_matrix,
            suggested_cuts=hierarchical_result.suggested_cuts,
            cluster_assignments=cluster_assignments,
            n_clusters=n_clusters)

    def get_radar_chart(
        self,
        simulation_id: str,
        kmeans_result: KMeansResult) -> RadarChart:
        """
        Generate radar chart for cluster comparison.

        Args:
            simulation_id: ID of the simulation.
            kmeans_result: K-Means clustering result.

        Returns:
            RadarChart with normalized cluster profiles.
        """
        logger.info(f"Generating radar chart for {len(kmeans_result.clusters)} clusters")

        # Calculate baseline (overall mean) for each feature
        all_centroids = [cluster.centroid for cluster in kmeans_result.clusters]
        all_sizes = [cluster.size for cluster in kmeans_result.clusters]

        # Weighted average for baseline
        baseline = {}
        for feature in kmeans_result.features_used:
            weighted_sum = sum(
                centroid.get(feature, 0) * size for centroid, size in zip(all_centroids, all_sizes)
            )
            baseline[feature] = weighted_sum / sum(all_sizes)

        # Find min/max for normalization
        feature_ranges = {}
        for feature in kmeans_result.features_used:
            values = [centroid.get(feature, 0) for centroid in all_centroids]
            feature_ranges[feature] = (min(values), max(values))

        # Build cluster radars
        cluster_radars = []
        for i, cluster in enumerate(kmeans_result.clusters):
            axes = []
            for feature in kmeans_result.features_used:
                value = cluster.centroid.get(feature, 0)

                # Normalize to 0-1
                min_val, max_val = feature_ranges[feature]
                if max_val - min_val > 0:
                    normalized = (value - min_val) / (max_val - min_val)
                else:
                    normalized = 0.5

                axes.append(
                    RadarAxis(
                        name=feature,
                        label=feature.replace("_", " ").title(),
                        value=float(value),
                        normalized=float(normalized))
                )

            cluster_radars.append(
                ClusterRadar(
                    cluster_id=cluster.cluster_id,
                    label=cluster.suggested_label,
                    explanation=cluster.suggested_explanation,
                    color=self.CLUSTER_COLORS[i % len(self.CLUSTER_COLORS)],
                    axes=axes,
                    success_rate=cluster.avg_success_rate)
            )

        # Build axis labels and baseline
        axis_labels = [feature.replace("_", " ").title() for feature in kmeans_result.features_used]
        baseline_values = [baseline[feature] for feature in kmeans_result.features_used]

        return RadarChart(
            simulation_id=simulation_id,
            clusters=cluster_radars,
            axis_labels=axis_labels,
            baseline=baseline_values)

    def get_pca_scatter(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        kmeans_result: KMeansResult) -> PCAScatterChart:
        """
        Generate PCA 2D scatter plot with cluster colors.

        Args:
            simulation_id: ID of the simulation.
            outcomes: List of synth outcomes.
            kmeans_result: K-Means clustering result.

        Returns:
            PCAScatterChart with 2D projections and cluster colors.
        """
        logger.info(f"Generating PCA scatter for {len(outcomes)} synths")

        # Extract features (same as clustering)
        X, synth_ids = self._extract_features(outcomes, kmeans_result.features_used)
        X_scaled = StandardScaler().fit_transform(X)

        # PCA to 2D
        pca = PCA(n_components=2, random_state=42)
        X_pca = pca.fit_transform(X_scaled)

        # Build points with cluster assignment and colors
        points = []
        for i, synth_id in enumerate(synth_ids):
            cluster_id = kmeans_result.synth_assignments.get(synth_id, -1)
            cluster_profile = next(
                (c for c in kmeans_result.clusters if c.cluster_id == cluster_id),
                None)

            if cluster_profile:
                color = self.CLUSTER_COLORS[cluster_id % len(self.CLUSTER_COLORS)]
                label = cluster_profile.suggested_label
            else:
                color = "#94a3b8"  # Cinza para não atribuído
                label = "Não atribuído"

            points.append(
                PCAScatterPoint(
                    synth_id=synth_id,
                    x=float(X_pca[i, 0]),
                    y=float(X_pca[i, 1]),
                    cluster_id=cluster_id,
                    cluster_label=label,
                    color=color)
            )

        return PCAScatterChart(
            simulation_id=simulation_id,
            points=points,
            explained_variance=[
                float(pca.explained_variance_ratio_[0]),
                float(pca.explained_variance_ratio_[1]),
            ],
            total_variance=float(pca.explained_variance_ratio_.sum()))

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    def _extract_features(
        self, outcomes: list[SynthOutcome], features: list[str]
    ) -> tuple[np.ndarray, list[str]]:
        """
        Extract feature matrix from outcomes.

        Args:
            outcomes: List of SynthOutcome entities.
            features: List of feature names.

        Returns:
            Tuple of (feature matrix, synth_ids).
        """
        X = []
        synth_ids = []

        for outcome in outcomes:
            row = []
            for feature in features:
                value = get_attribute_value(outcome, feature)
                row.append(float(value) if value is not None else 0.0)
            X.append(row)
            synth_ids.append(outcome.synth_id)

        return np.array(X), synth_ids

    def _calculate_elbow(self, X_scaled: np.ndarray, max_k: int = 10) -> list[ElbowDataPoint]:
        """
        Calculate elbow method data for k from 2 to max_k.

        Args:
            X_scaled: Normalized feature matrix.
            max_k: Maximum k to test.

        Returns:
            List of ElbowDataPoint entities.
        """
        elbow_data = []

        for k in range(2, max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_scaled)

            inertia = kmeans.inertia_

            # silhouette_score requires at least 2 distinct clusters
            n_unique_labels = len(np.unique(labels))
            if n_unique_labels < 2:
                silhouette = 0.0
            else:
                silhouette = silhouette_score(X_scaled, labels)

            elbow_data.append(
                ElbowDataPoint(k=k, inertia=float(inertia), silhouette=float(silhouette))
            )

        return elbow_data

    def _detect_knee_point(self, elbow_data: list[ElbowDataPoint]) -> int:
        """
        Detecta knee point usando KneeLocator.

        Args:
            elbow_data: Lista de pontos do elbow method.

        Returns:
            K recomendado.
        """
        from kneed import KneeLocator

        if len(elbow_data) < 3:
            logger.warning("Menos de 3 pontos elbow, usando K=3 default")
            return 3

        k_values = [point.k for point in elbow_data]
        inertias = [point.inertia for point in elbow_data]

        try:
            kl = KneeLocator(k_values, inertias, curve="convex", direction="decreasing")
            knee_k = kl.knee

            if knee_k is None:
                # Fallback: melhor silhouette
                best = max(elbow_data, key=lambda x: x.silhouette)
                knee_k = best.k
                logger.warning(f"Knee detection failed, usando best silhouette K={knee_k}")
            else:
                logger.info(f"Knee detectado em K={knee_k}")

            return knee_k
        except Exception as e:
            logger.warning(f"Erro knee detection: {e}, default K=3")
            return 3

    def _build_cluster_profiles(
        self,
        outcomes: list[SynthOutcome],
        labels: np.ndarray,
        centroids: np.ndarray,
        scaler: StandardScaler,
        feature_names: list[str]) -> list[ClusterProfile]:
        """
        Build cluster profiles from K-Means results.

        Args:
            outcomes: Original synth outcomes.
            labels: Cluster labels for each synth.
            centroids: Cluster centroids (scaled).
            scaler: StandardScaler used for normalization.
            feature_names: Names of features.

        Returns:
            List of ClusterProfile entities.
        """
        n_clusters = len(centroids)
        total_synths = len(outcomes)

        # Inverse transform centroids to original scale
        centroids_orig = scaler.inverse_transform(centroids)

        # Calculate global means for comparison
        global_means = {}
        for feature in feature_names:
            values = [get_attribute_value(outcome, feature) or 0 for outcome in outcomes]
            global_means[feature] = np.mean(values)

        profiles = []

        for cluster_id in range(n_clusters):
            # Get synths in this cluster
            cluster_mask = labels == cluster_id
            cluster_outcomes = [
                outcome for outcome, in_cluster in zip(outcomes, cluster_mask) if in_cluster
            ]

            if not cluster_outcomes:
                continue

            # Calculate cluster stats
            size = len(cluster_outcomes)
            percentage = (size / total_synths) * 100

            avg_success = np.mean([o.success_rate for o in cluster_outcomes])
            avg_failed = np.mean([o.failed_rate for o in cluster_outcomes])
            avg_did_not_try = np.mean([o.did_not_try_rate for o in cluster_outcomes])

            # Build centroid dict
            centroid_dict = {
                feature: float(centroids_orig[cluster_id, i])
                for i, feature in enumerate(feature_names)
            }

            # Identify high/low traits
            high_traits = []
            low_traits = []
            for feature, value in centroid_dict.items():
                global_mean = global_means.get(feature, 0.5)
                if value > global_mean * 1.2:  # 20% above mean
                    high_traits.append(feature)
                elif value < global_mean * 0.8:  # 20% below mean
                    low_traits.append(feature)

            # Temporary label (will be replaced by LLM-generated label)
            temp_label = f"Cluster {cluster_id + 1}"

            profiles.append(
                ClusterProfile(
                    cluster_id=cluster_id,
                    size=size,
                    percentage=float(percentage),
                    centroid=centroid_dict,
                    avg_success_rate=float(avg_success),
                    avg_failed_rate=float(avg_failed),
                    avg_did_not_try_rate=float(avg_did_not_try),
                    high_traits=high_traits,
                    low_traits=low_traits,
                    suggested_label=temp_label,
                    synth_ids=[o.synth_id for o in cluster_outcomes])
            )

        # Generate descriptive labels via LLM
        if profiles:
            labeling_service = ClusterLabelingService()
            llm_labels = labeling_service.generate_labels(profiles)

            # Update profiles with LLM-generated labels and explanations
            for profile in profiles:
                if profile.cluster_id in llm_labels:
                    label_data = llm_labels[profile.cluster_id]
                    profile.suggested_label = label_data.get("name", profile.suggested_label)
                    profile.suggested_explanation = label_data.get("explanation", "")

        return profiles

    def _suggest_label(
        self,
        cluster_id: int,
        avg_success: float,
        high_traits: list[str],
        low_traits: list[str]) -> str:
        """
        Suggest a human-readable label for the cluster.

        Args:
            cluster_id: Cluster identifier.
            avg_success: Average success rate.
            high_traits: Traits above average.
            low_traits: Traits below average.

        Returns:
            Suggested label string.
        """
        # Success-based labels
        if avg_success > 0.7:
            if "capability_mean" in high_traits and "trust_mean" in high_traits:
                return "Power Users"
            elif "trust_mean" in high_traits:
                return "Engaged Users"
            else:
                return "High Performers"
        elif avg_success < 0.3:
            if "capability_mean" in low_traits and "trust_mean" in low_traits:
                return "Strugglers"
            elif "trust_mean" in low_traits:
                return "Skeptical Users"
            else:
                return "Low Performers"
        else:
            if "capability_mean" in high_traits:
                return "Capable Underperformers"
            elif "trust_mean" in high_traits:
                return "Trusting Users"
            else:
                return f"Cluster {cluster_id + 1}"

    def _build_dendrogram_nodes(
        self, linkage_matrix: np.ndarray, synth_ids: list[str]
    ) -> list[DendrogramNode]:
        """
        Build dendrogram nodes from scipy linkage matrix.

        Args:
            linkage_matrix: Scipy linkage matrix.
            synth_ids: List of synth IDs (leaf nodes).

        Returns:
            List of DendrogramNode entities.
        """
        n_leaves = len(synth_ids)
        nodes = []

        # Add leaf nodes
        for i, synth_id in enumerate(synth_ids):
            nodes.append(DendrogramNode(id=i, synth_id=synth_id, distance=0.0, count=1))

        # Add internal nodes from linkage matrix
        for i, row in enumerate(linkage_matrix):
            node_id = n_leaves + i
            left_child = int(row[0])
            right_child = int(row[1])
            distance = float(row[2])
            count = int(row[3])

            nodes.append(
                DendrogramNode(
                    id=node_id,
                    left_child=left_child,
                    right_child=right_child,
                    distance=distance,
                    count=count)
            )

        return nodes

    def _suggest_cuts(self, X_scaled: np.ndarray, linkage_matrix: np.ndarray) -> list[SuggestedCut]:
        """
        Suggest good cut points for the dendrogram.

        Args:
            X_scaled: Normalized feature matrix.
            linkage_matrix: Scipy linkage matrix.

        Returns:
            List of SuggestedCut entities.
        """
        suggested_cuts = []

        # Try cuts for k=2 to k=min(10, n_samples-1)
        max_k = min(10, len(X_scaled) - 1)

        for k in range(2, max_k + 1):
            # Cut at k clusters
            labels = hierarchy.fcluster(linkage_matrix, k, criterion="maxclust")

            # Calculate silhouette score
            try:
                silhouette = silhouette_score(X_scaled, labels)
            except ValueError:
                # Skip if too few samples per cluster
                continue

            # Find the distance threshold for this cut
            # This is the maximum distance within k clusters
            distances = linkage_matrix[:, 2]
            cut_height = distances[-(k - 1)] if k > 1 else distances[-1]

            suggested_cuts.append(
                SuggestedCut(
                    n_clusters=k,
                    distance=float(cut_height),
                    silhouette_estimate=float(silhouette))
            )

        # Sort by silhouette score (best first)
        suggested_cuts.sort(key=lambda x: x.silhouette_estimate, reverse=True)

        return suggested_cuts[:5]  # Return top 5 suggestions


if __name__ == "__main__":
    """Validation: Test clustering service with sample data."""
    import sys

    from synth_lab.domain.entities import (
        SimulationAttributes,
        SimulationLatentTraits,
        SimulationObservables,
        SynthOutcome)

    all_validation_failures = []
    total_tests = 0

    # Test 1: K-Means clustering
    total_tests += 1
    try:
        # Create sample outcomes
        outcomes = []
        for i in range(30):
            success_rate = 0.5 + np.random.rand() * 0.2
            failed_rate = 0.2
            did_not_try_rate = max(0.0, 1.0 - success_rate - failed_rate)
            # Ensure rates sum to 1.0
            total = success_rate + failed_rate + did_not_try_rate
            if total > 0:
                success_rate = success_rate / total
                failed_rate = failed_rate / total
                did_not_try_rate = did_not_try_rate / total

            outcomes.append(
                SynthOutcome(
                    synth_id=f"synth_{i:03d}",
                    simulation_id="sim_test",
                    success_rate=success_rate,
                    failed_rate=failed_rate,
                    did_not_try_rate=did_not_try_rate,
                    synth_attributes=SimulationAttributes(
                        observables=SimulationObservables(
                            digital_literacy=0.5,
                            similar_tool_experience=0.4,
                            motor_ability=0.8,
                            time_availability=0.3,
                            domain_expertise=0.6),
                        latent_traits=SimulationLatentTraits(
                            capability_mean=0.5 + np.random.rand() * 0.3,
                            trust_mean=0.5 + np.random.rand() * 0.3,
                            friction_tolerance_mean=0.5 + np.random.rand() * 0.3,
                            exploration_prob=0.35)))
            )

        service = ClusteringService()
        result = service.cluster_kmeans(simulation_id="sim_test", outcomes=outcomes, n_clusters=3)

        if result.n_clusters != 3 or len(result.clusters) != 3:
            all_validation_failures.append(
                f"K-Means: Expected 3 clusters, got {len(result.clusters)}"
            )
        if result.silhouette_score <= 0:
            all_validation_failures.append(
                f"K-Means: Expected positive silhouette score, got {result.silhouette_score}"
            )
    except Exception as e:
        all_validation_failures.append(f"K-Means clustering failed: {e}")

    # Test 2: Hierarchical clustering
    total_tests += 1
    try:
        service = ClusteringService()
        result = service.cluster_hierarchical(simulation_id="sim_test", outcomes=outcomes)

        if result.method != "hierarchical":
            all_validation_failures.append(
                f"Hierarchical: Expected method='hierarchical', got '{result.method}'"
            )
        if len(result.nodes) == 0:
            all_validation_failures.append("Hierarchical: Expected dendrogram nodes, got none")
    except Exception as e:
        all_validation_failures.append(f"Hierarchical clustering failed: {e}")

    # Test 3: Radar chart generation
    total_tests += 1
    try:
        kmeans = service.cluster_kmeans(simulation_id="sim_test", outcomes=outcomes, n_clusters=3)
        radar = service.get_radar_chart(simulation_id="sim_test", kmeans_result=kmeans)

        if len(radar.clusters) != 3:
            all_validation_failures.append(
                f"Radar chart: Expected 3 clusters, got {len(radar.clusters)}"
            )
        if len(radar.axis_labels) == 0:
            all_validation_failures.append("Radar chart: Expected axis labels, got none")
    except Exception as e:
        all_validation_failures.append(f"Radar chart generation failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("ClusteringService is validated and ready for use")
        sys.exit(0)
