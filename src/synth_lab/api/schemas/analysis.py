"""
API schemas for UX Research analysis endpoints.

Defines request/response models for analysis API.

References:
    - Spec: specs/017-analysis-ux-research/spec.md
    - Data model: specs/017-analysis-ux-research/data-model.md
"""

from typing import Literal

from pydantic import BaseModel, Field

# =============================================================================
# Query Parameters for GET endpoints
# =============================================================================


class TryVsSuccessParams(BaseModel):
    """Query parameters for Try vs Success chart."""

    x_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="X-axis threshold for quadrant division."
    )
    y_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Y-axis threshold for quadrant division."
    )


class DistributionParams(BaseModel):
    """Query parameters for Outcome Distribution chart."""

    mode: Literal["by_synth", "by_percentile", "by_cluster"] = Field(
        default="by_synth", description="Aggregation mode."
    )
    sort_by: Literal["adopted_rate", "not_adopted_rate"] = Field(
        default="adopted_rate", description="Field to sort by."
    )
    order: Literal["asc", "desc"] = Field(default="desc", description="Sort order.")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum results to return.")


class HeatmapParams(BaseModel):
    """Query parameters for Failure Heatmap."""

    x_axis: str = Field(default="capability_mean", description="X-axis attribute.")
    y_axis: str = Field(default="trust_mean", description="Y-axis attribute.")
    bins: int = Field(default=5, ge=2, le=20, description="Number of bins per axis.")
    metric: Literal["adopted_rate", "not_adopted_rate"] = Field(
        default="not_adopted_rate", description="Metric to display in cells."
    )


class BoxPlotParams(BaseModel):
    """Query parameters for Box Plot by Region."""

    metric: Literal["adopted_rate", "not_adopted_rate"] = Field(
        default="adopted_rate", description="Metric to display."
    )
    include_baseline: bool = Field(default=True, description="Include baseline statistics.")


class ScatterParams(BaseModel):
    """Query parameters for Scatter Correlation chart."""

    x_axis: str = Field(default="trust_mean", description="X-axis attribute.")
    y_axis: str = Field(default="adopted_rate", description="Y-axis attribute.")
    show_trendline: bool = Field(default=True, description="Include trend line.")


class ExtremeCasesParams(BaseModel):
    """Query parameters for Extreme Cases endpoint."""

    type: Literal["all", "failures", "successes", "unstable", "unexpected"] = Field(
        default="all", description="Type of extreme cases to return."
    )
    limit: int = Field(default=10, ge=1, le=100, description="Number of cases per category.")
    include_interview_suggestions: bool = Field(
        default=True, description="Include interview questions."
    )


class OutliersParams(BaseModel):
    """Query parameters for Outliers detection."""

    contamination: float = Field(
        default=0.1, gt=0.0, lt=0.5, description="Expected proportion of outliers."
    )
    include_outcomes: bool = Field(default=True, description="Include outcome fields in features.")
    type: Literal["all", "unexpected_failure", "unexpected_success", "atypical_profile"] = Field(
        default="all", description="Type of outliers to return."
    )


class ShapParams(BaseModel):
    """Query parameters for SHAP explanation."""

    synth_id: str | None = Field(
        default=None, description="Synth ID for individual explanation. None for summary."
    )


class PDPParams(BaseModel):
    """Query parameters for Partial Dependence Plot."""

    feature: str = Field(description="Feature to analyze.")
    grid_resolution: int = Field(default=20, ge=5, le=100, description="Number of grid points.")


class PDPComparisonParams(BaseModel):
    """Query parameters for PDP Comparison."""

    features: str = Field(description="Comma-separated list of features to compare.")


class DendrogramParams(BaseModel):
    """Query parameters for Dendrogram visualization."""

    max_depth: int = Field(default=5, ge=1, le=20, description="Maximum tree depth to show.")
    truncate_mode: Literal["level", "lastp", "none"] = Field(
        default="level", description="Truncation mode for visualization."
    )
    color_threshold: float | None = Field(
        default=None, description="Distance threshold for coloring."
    )


# =============================================================================
# Request Bodies for POST endpoints
# =============================================================================


class ClusterRequest(BaseModel):
    """Request body for creating clustering."""

    method: Literal["kmeans", "hierarchical"] = Field(
        default="kmeans", description="Clustering method."
    )
    n_clusters: int = Field(default=4, ge=2, le=20, description="Number of clusters for K-Means.")
    features: list[str] | None = Field(
        default=None, description="Features to use. None = all latent traits."
    )
    include_outcomes: bool = Field(
        default=False, description="Include outcome rates in clustering features."
    )
    linkage: str = Field(default="ward", description="Linkage method for hierarchical clustering.")


class CutDendrogramRequest(BaseModel):
    """Request body for cutting dendrogram."""

    n_clusters: int = Field(ge=2, le=50, description="Number of clusters to cut into.")


# =============================================================================
# Mechanism Explanation Schemas (038-mechanism-based-simulation)
# =============================================================================


class ExplainSegmentRequest(BaseModel):
    """
    Request body for explaining segment behavior via mechanism×sensitivity interactions.

    Reference: specs/038-mechanism-based-simulation/spec.md
    """

    synth_ids: list[str] = Field(
        min_length=1,
        description="List of synth IDs that define the segment to explain.",
    )
    compare_to_population: bool = Field(
        default=True,
        description="Whether to compare segment to full population or just show absolute values.",
    )


class InteractionContributionResponse(BaseModel):
    """Single mechanism × sensitivity interaction contribution."""

    mechanism: str = Field(description="Mechanism name (e.g., 'irreversibility').")
    sensitivity: str = Field(description="Sensitivity name (e.g., 'risk_aversion').")
    product: float = Field(description="Interaction product (mechanism × sensitivity).")


class DifferentiatingFactorResponse(BaseModel):
    """Factor that differentiates segment from population."""

    interaction: InteractionContributionResponse = Field(
        description="The mechanism×sensitivity interaction."
    )
    segment_avg: float = Field(description="Average interaction value in the segment.")
    population_avg: float = Field(description="Average interaction value in the population.")
    delta: float = Field(description="Difference (segment_avg - population_avg).")


class SegmentExplanationResponse(BaseModel):
    """
    Response for segment explanation via mechanism×sensitivity interactions.

    Reference: specs/038-mechanism-based-simulation/spec.md
    """

    segment_size: int = Field(description="Number of synths in the segment.")
    segment_avg_adopted: float = Field(
        ge=0.0,
        le=1.0,
        description="Average adoption rate of the segment.",
    )
    population_avg_adopted: float = Field(
        ge=0.0,
        le=1.0,
        description="Average adoption rate of the full population.",
    )
    top_differentiating_factors: list[DifferentiatingFactorResponse] = Field(
        default_factory=list,
        description="Top factors differentiating this segment from population (sorted by delta magnitude).",
    )
    explanation_text: str = Field(
        description="Human-readable explanation of segment differences.",
    )


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: TryVsSuccessParams defaults
    total_tests += 1
    try:
        params = TryVsSuccessParams()
        if params.x_threshold != 0.5 or params.y_threshold != 0.5:
            all_validation_failures.append("TryVsSuccessParams defaults incorrect")
    except Exception as e:
        all_validation_failures.append(f"TryVsSuccessParams creation failed: {e}")

    # Test 2: TryVsSuccessParams with custom values
    total_tests += 1
    try:
        params = TryVsSuccessParams(x_threshold=0.6, y_threshold=0.4)
        if params.x_threshold != 0.6:
            all_validation_failures.append(f"x_threshold mismatch: {params.x_threshold}")
    except Exception as e:
        all_validation_failures.append(f"TryVsSuccessParams custom failed: {e}")

    # Test 3: DistributionParams defaults
    total_tests += 1
    try:
        params = DistributionParams()
        if params.mode != "by_synth" or params.limit != 50:
            all_validation_failures.append("DistributionParams defaults incorrect")
    except Exception as e:
        all_validation_failures.append(f"DistributionParams creation failed: {e}")

    # Test 4: HeatmapParams with custom bins
    total_tests += 1
    try:
        params = HeatmapParams(bins=7, metric="adopted_rate")
        if params.bins != 7 or params.metric != "adopted_rate":
            all_validation_failures.append("HeatmapParams values incorrect")
    except Exception as e:
        all_validation_failures.append(f"HeatmapParams creation failed: {e}")

    # Test 5: ClusterRequest defaults
    total_tests += 1
    try:
        req = ClusterRequest()
        if req.method != "kmeans" or req.n_clusters != 4:
            all_validation_failures.append("ClusterRequest defaults incorrect")
    except Exception as e:
        all_validation_failures.append(f"ClusterRequest creation failed: {e}")

    # Test 6: ClusterRequest with hierarchical
    total_tests += 1
    try:
        req = ClusterRequest(method="hierarchical", linkage="complete")
        if req.linkage != "complete":
            all_validation_failures.append(f"linkage mismatch: {req.linkage}")
    except Exception as e:
        all_validation_failures.append(f"ClusterRequest hierarchical failed: {e}")

    # Test 7: CutDendrogramRequest
    total_tests += 1
    try:
        req = CutDendrogramRequest(n_clusters=5)
        if req.n_clusters != 5:
            all_validation_failures.append(f"n_clusters mismatch: {req.n_clusters}")
    except Exception as e:
        all_validation_failures.append(f"CutDendrogramRequest creation failed: {e}")

    # Test 8: Reject invalid threshold > 1
    total_tests += 1
    try:
        TryVsSuccessParams(x_threshold=1.5)
        all_validation_failures.append("Should reject threshold > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid threshold: {e}")

    # Test 9: Reject invalid contamination
    total_tests += 1
    try:
        OutliersParams(contamination=0.6)  # > 0.5
        all_validation_failures.append("Should reject contamination > 0.5")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid contamination: {e}")

    # Test 10: Reject n_clusters < 2
    total_tests += 1
    try:
        ClusterRequest(n_clusters=1)
        all_validation_failures.append("Should reject n_clusters < 2")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid n_clusters: {e}")

    # Test 11: ExplainSegmentRequest with synth_ids
    total_tests += 1
    try:
        req = ExplainSegmentRequest(synth_ids=["synth_1", "synth_2"])
        if len(req.synth_ids) != 2 or req.compare_to_population is not True:
            all_validation_failures.append("ExplainSegmentRequest values incorrect")
    except Exception as e:
        all_validation_failures.append(f"ExplainSegmentRequest creation failed: {e}")

    # Test 12: ExplainSegmentRequest reject empty synth_ids
    total_tests += 1
    try:
        ExplainSegmentRequest(synth_ids=[])
        all_validation_failures.append("Should reject empty synth_ids")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for empty synth_ids: {e}")

    # Test 13: SegmentExplanationResponse creation
    total_tests += 1
    try:
        resp = SegmentExplanationResponse(
            segment_size=10,
            segment_avg_adopted=0.65,
            population_avg_adopted=0.50,
            top_differentiating_factors=[
                DifferentiatingFactorResponse(
                    interaction=InteractionContributionResponse(
                        mechanism="irreversibility",
                        sensitivity="risk_aversion",
                        product=0.72,
                    ),
                    segment_avg=0.72,
                    population_avg=0.45,
                    delta=0.27,
                )
            ],
            explanation_text="High risk-averse users show 27% stronger response to irreversibility.",
        )
        if resp.segment_size != 10 or resp.segment_avg_adopted != 0.65:
            all_validation_failures.append("SegmentExplanationResponse values incorrect")
        if len(resp.top_differentiating_factors) != 1:
            all_validation_failures.append("SegmentExplanationResponse factors incorrect")
    except Exception as e:
        all_validation_failures.append(f"SegmentExplanationResponse creation failed: {e}")

    # Test 14: InteractionContributionResponse
    total_tests += 1
    try:
        contrib = InteractionContributionResponse(
            mechanism="network_effect",
            sensitivity="social_dependency",
            product=0.56,
        )
        if contrib.mechanism != "network_effect" or contrib.product != 0.56:
            all_validation_failures.append("InteractionContributionResponse values incorrect")
    except Exception as e:
        all_validation_failures.append(f"InteractionContributionResponse creation failed: {e}")

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
