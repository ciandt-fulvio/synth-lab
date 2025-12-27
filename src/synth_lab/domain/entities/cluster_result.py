"""
Cluster Result Entities for UX Research Analysis.

This module defines Pydantic models for clustering results, including:
- K-Means clustering with elbow method
- Hierarchical clustering with dendrogram
- Radar charts for cluster visualization

Dependencies:
- pydantic: https://docs.pydantic.dev/latest/

Sample Input:
    ClusterProfile with cluster metadata and synth assignments

Expected Output:
    Validated cluster result entities ready for API responses
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ClusterProfile(BaseModel):
    """Profile of a cluster."""

    cluster_id: int = Field(..., description="Cluster identifier")
    size: int = Field(..., description="Number of synths in this cluster")
    percentage: float = Field(..., description="Percentage of total synths")
    centroid: dict[str, float] = Field(..., description="Mean of each feature")
    avg_success_rate: float = Field(..., description="Average success rate")
    avg_failed_rate: float = Field(..., description="Average failed rate")
    avg_did_not_try_rate: float = Field(..., description="Average did not try rate")
    high_traits: list[str] = Field(
        default_factory=list, description="Traits above the mean"
    )
    low_traits: list[str] = Field(
        default_factory=list, description="Traits below the mean"
    )
    suggested_label: str = Field(..., description="Human-readable label")
    synth_ids: list[str] = Field(
        default_factory=list, description="Synths in this cluster"
    )


class ElbowDataPoint(BaseModel):
    """Point for the Elbow Method graph."""

    k: int = Field(..., description="Number of clusters")
    inertia: float = Field(..., description="Within-cluster sum of squares")
    silhouette: float = Field(..., description="Silhouette score")


class KMeansResult(BaseModel):
    """Result of K-Means clustering."""

    simulation_id: str = Field(..., description="Simulation identifier")
    n_clusters: int = Field(..., description="Number of clusters")
    method: Literal["kmeans"] = Field(default="kmeans", description="Clustering method")
    features_used: list[str] = Field(..., description="Features used for clustering")
    silhouette_score: float = Field(..., description="Overall silhouette score")
    inertia: float = Field(..., description="Within-cluster sum of squares")
    clusters: list[ClusterProfile] = Field(..., description="Cluster profiles")
    synth_assignments: dict[str, int] = Field(
        ..., description="Synth ID to cluster ID mapping"
    )
    elbow_data: list[ElbowDataPoint] = Field(
        default_factory=list, description="Elbow method data points"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Creation timestamp",
    )


class DendrogramNode(BaseModel):
    """Node in the dendrogram tree."""

    id: int = Field(..., description="Node identifier")
    synth_id: str | None = Field(None, description="Synth ID if leaf node")
    left_child: int | None = Field(None, description="Left child node ID")
    right_child: int | None = Field(None, description="Right child node ID")
    distance: float = Field(..., description="Linkage distance")
    count: int = Field(..., description="Number of leaves below this node")


class SuggestedCut(BaseModel):
    """Suggested cut point for dendrogram."""

    n_clusters: int = Field(..., description="Number of clusters at this cut")
    distance: float = Field(..., description="Cut distance threshold")
    silhouette_estimate: float = Field(..., description="Estimated silhouette score")


class HierarchicalResult(BaseModel):
    """Result of hierarchical clustering."""

    simulation_id: str = Field(..., description="Simulation identifier")
    method: Literal["hierarchical"] = Field(
        default="hierarchical", description="Clustering method"
    )
    linkage_method: str = Field(..., description="Linkage method used")
    features_used: list[str] = Field(..., description="Features used for clustering")
    nodes: list[DendrogramNode] = Field(..., description="Dendrogram nodes")
    linkage_matrix: list[list[float]] = Field(
        ..., description="Scipy linkage matrix"
    )
    suggested_cuts: list[SuggestedCut] = Field(
        default_factory=list, description="Suggested cut points"
    )
    cluster_assignments: dict[str, int] | None = Field(
        None, description="Synth to cluster mapping if cut"
    )
    n_clusters: int | None = Field(None, description="Number of clusters if cut")
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Creation timestamp",
    )


class RadarAxis(BaseModel):
    """Axis in a radar chart."""

    name: str = Field(..., description="Feature name")
    label: str = Field(..., description="Human-readable label")
    value: float = Field(..., description="Actual value")
    normalized: float = Field(..., description="Normalized value 0-1")


class ClusterRadar(BaseModel):
    """Radar chart data for a single cluster."""

    cluster_id: int = Field(..., description="Cluster identifier")
    label: str = Field(..., description="Cluster label")
    color: str = Field(..., description="Color for visualization")
    axes: list[RadarAxis] = Field(..., description="Radar axes")
    success_rate: float = Field(..., description="Average success rate")


class RadarChart(BaseModel):
    """Radar chart comparing multiple clusters."""

    simulation_id: str = Field(..., description="Simulation identifier")
    clusters: list[ClusterRadar] = Field(..., description="Cluster radar data")
    axis_labels: list[str] = Field(..., description="Axis labels")
    baseline: list[float] = Field(..., description="Baseline values for each axis")


class DendrogramBranch(BaseModel):
    """Branch for dendrogram rendering."""

    x_start: float = Field(..., description="Starting X coordinate")
    x_end: float = Field(..., description="Ending X coordinate")
    y_start: float = Field(..., description="Starting Y coordinate")
    y_end: float = Field(..., description="Ending Y coordinate")
    is_leaf: bool = Field(..., description="Whether this is a leaf node")
    synth_id: str | None = Field(None, description="Synth ID if leaf")
    cluster_id: int | None = Field(None, description="Cluster ID if assigned")
    count: int = Field(..., description="Number of leaves below")


class DendrogramChart(BaseModel):
    """Dendrogram visualization data."""

    simulation_id: str = Field(..., description="Simulation identifier")
    branches: list[DendrogramBranch] = Field(..., description="Dendrogram branches")
    leaves: list[dict] = Field(..., description="Leaf node positions")
    cut_lines: list[dict] = Field(..., description="Suggested cut lines")
    width: float = Field(..., description="Chart width")
    height: float = Field(..., description="Chart height")


if __name__ == "__main__":
    """Validation: Test cluster entity models with sample data."""
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: ClusterProfile creation
    total_tests += 1
    try:
        profile = ClusterProfile(
            cluster_id=0,
            size=120,
            percentage=24.0,
            centroid={"capability_mean": 0.72, "trust_mean": 0.68},
            avg_success_rate=0.75,
            avg_failed_rate=0.15,
            avg_did_not_try_rate=0.10,
            high_traits=["capability_mean", "trust_mean"],
            low_traits=[],
            suggested_label="Power Users",
            synth_ids=["synth_001", "synth_002"],
        )
        if profile.cluster_id != 0 or profile.suggested_label != "Power Users":
            all_validation_failures.append(
                f"ClusterProfile: Expected cluster_id=0 and label='Power Users', got {profile.cluster_id} and '{profile.suggested_label}'"
            )
    except Exception as e:
        all_validation_failures.append(f"ClusterProfile creation failed: {e}")

    # Test 2: KMeansResult creation
    total_tests += 1
    try:
        elbow_point = ElbowDataPoint(k=3, inertia=1234.5, silhouette=0.42)
        kmeans = KMeansResult(
            simulation_id="sim_001",
            n_clusters=3,
            features_used=["capability_mean", "trust_mean"],
            silhouette_score=0.42,
            inertia=1234.5,
            clusters=[profile],
            synth_assignments={"synth_001": 0, "synth_002": 0},
            elbow_data=[elbow_point],
        )
        if kmeans.n_clusters != 3 or kmeans.method != "kmeans":
            all_validation_failures.append(
                f"KMeansResult: Expected n_clusters=3 and method='kmeans', got {kmeans.n_clusters} and '{kmeans.method}'"
            )
    except Exception as e:
        all_validation_failures.append(f"KMeansResult creation failed: {e}")

    # Test 3: HierarchicalResult creation
    total_tests += 1
    try:
        node = DendrogramNode(id=0, synth_id="synth_001", distance=0.0, count=1)
        cut = SuggestedCut(n_clusters=3, distance=2.5, silhouette_estimate=0.38)
        hierarchical = HierarchicalResult(
            simulation_id="sim_001",
            linkage_method="ward",
            features_used=["capability_mean"],
            nodes=[node],
            linkage_matrix=[[0, 1, 0.5, 2]],
            suggested_cuts=[cut],
        )
        if (
            hierarchical.method != "hierarchical"
            or hierarchical.linkage_method != "ward"
        ):
            all_validation_failures.append(
                f"HierarchicalResult: Expected method='hierarchical' and linkage='ward', got '{hierarchical.method}' and '{hierarchical.linkage_method}'"
            )
    except Exception as e:
        all_validation_failures.append(f"HierarchicalResult creation failed: {e}")

    # Test 4: RadarChart creation
    total_tests += 1
    try:
        axis = RadarAxis(
            name="capability_mean", label="Capability", value=0.72, normalized=0.72
        )
        cluster_radar = ClusterRadar(
            cluster_id=0,
            label="Power Users",
            color="#FF6B6B",
            axes=[axis],
            success_rate=0.75,
        )
        radar = RadarChart(
            simulation_id="sim_001",
            clusters=[cluster_radar],
            axis_labels=["Capability"],
            baseline=[0.5],
        )
        if radar.simulation_id != "sim_001" or len(radar.clusters) != 1:
            all_validation_failures.append(
                f"RadarChart: Expected simulation_id='sim_001' and 1 cluster, got '{radar.simulation_id}' and {len(radar.clusters)} clusters"
            )
    except Exception as e:
        all_validation_failures.append(f"RadarChart creation failed: {e}")

    # Test 5: DendrogramChart creation
    total_tests += 1
    try:
        branch = DendrogramBranch(
            x_start=0.0,
            x_end=1.0,
            y_start=0.0,
            y_end=0.5,
            is_leaf=True,
            synth_id="synth_001",
            count=1,
        )
        dendrogram = DendrogramChart(
            simulation_id="sim_001",
            branches=[branch],
            leaves=[{"x": 0, "synth_id": "synth_001"}],
            cut_lines=[{"y": 2.5, "n_clusters": 3}],
            width=800.0,
            height=600.0,
        )
        if dendrogram.width != 800.0 or dendrogram.height != 600.0:
            all_validation_failures.append(
                f"DendrogramChart: Expected width=800.0 and height=600.0, got {dendrogram.width} and {dendrogram.height}"
            )
    except Exception as e:
        all_validation_failures.append(f"DendrogramChart creation failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results"
        )
        print("Cluster entity models are validated and ready for use")
        sys.exit(0)
