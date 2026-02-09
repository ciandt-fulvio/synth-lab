"""
Chart data entities for UX Research analysis.

Defines models for visualization data structures used in analysis endpoints.
Uses a 2-outcome model: adopted / not_adopted.

References:
    - Spec: specs/017-analysis-ux-research/spec.md
    - Data model: specs/017-analysis-ux-research/data-model.md
"""

from typing import Literal

from pydantic import BaseModel, Field

# =============================================================================
# 1. Adoption Rate Distribution Chart (formerly Try vs Success)
# =============================================================================


class TryVsSuccessPoint(BaseModel):
    """Individual point in the adoption rate distribution."""

    synth_id: str = Field(description="ID of the synth.")
    adopted_rate: float = Field(ge=0.0, le=1.0, description="Adoption rate.")
    bucket: Literal["low", "medium", "high"] = Field(
        description="Bucket classification based on thresholds."
    )


class TryVsSuccessChart(BaseModel):
    """Complete data for adoption rate distribution chart."""

    simulation_id: str = Field(description="ID of the simulation.")
    points: list[TryVsSuccessPoint] = Field(description="All synth points.")
    bucket_counts: dict[str, int] = Field(
        description='Count per bucket: {"low": 50, "medium": 210, "high": 240}'
    )
    bucket_thresholds: dict[str, float] = Field(
        description='Threshold values: {"low_max": 0.33, "high_min": 0.66}'
    )
    total_synths: int = Field(description="Total number of synths.")


# =============================================================================
# 2. Outcome Distribution Chart
# =============================================================================


class SynthDistribution(BaseModel):
    """Outcome distribution for a single synth."""

    synth_id: str = Field(description="ID of the synth.")
    adopted_rate: float = Field(ge=0.0, le=1.0)
    not_adopted_rate: float = Field(ge=0.0, le=1.0)
    sort_key: float = Field(description="Value used for sorting.")


class OutcomeDistributionChart(BaseModel):
    """Data for outcome distribution chart."""

    simulation_id: str = Field(description="ID of the simulation.")
    distributions: list[SynthDistribution] = Field(description="Distribution per synth.")
    summary: dict[str, float] = Field(
        description='Summary stats: {"avg_adopted": 0.42, "avg_not_adopted": 0.58, ...}'
    )
    worst_performers: list[str] = Field(description="Top synth_ids with lowest adoption.")
    best_performers: list[str] = Field(description="Top synth_ids with highest adoption.")
    total_synths: int = Field(description="Total number of synths.")


# =============================================================================
# 3. Failure Heatmap Chart
# =============================================================================


class HeatmapCell(BaseModel):
    """Single cell in the heatmap."""

    x_bin: str = Field(description='Bin label: "0.0-0.2", "0.2-0.4", etc.')
    y_bin: str = Field(description="Bin label for Y axis.")
    x_range: tuple[float, float] = Field(description="X range: (0.0, 0.2)")
    y_range: tuple[float, float] = Field(description="Y range.")
    metric_value: float = Field(description="Average metric value in this cell.")
    synth_count: int = Field(ge=0, description="Number of synths in cell.")
    synth_ids: list[str] = Field(description="List of synth IDs in cell.")


class FailureHeatmapChart(BaseModel):
    """Data for failure heatmap."""

    simulation_id: str = Field(description="ID of the simulation.")
    x_axis: str = Field(description='X axis attribute: "capability_mean"')
    y_axis: str = Field(description='Y axis attribute: "trust_mean"')
    metric: str = Field(description='Metric being displayed: "adopted_rate" or "not_adopted_rate"')
    bins: int = Field(ge=2, description="Number of bins per axis.")
    cells: list[HeatmapCell] = Field(description="All heatmap cells.")
    max_value: float = Field(description="Maximum metric value across cells.")
    min_value: float = Field(description="Minimum metric value across cells.")
    critical_cells: list[HeatmapCell] = Field(
        description="Cells with value above critical threshold."
    )
    critical_threshold: float = Field(description="Threshold for critical cells.")


# =============================================================================
# 4. Box Plot Chart
# =============================================================================


class BoxPlotStats(BaseModel):
    """Statistics for a box plot."""

    min: float = Field(description="Minimum value.")
    q1: float = Field(description="25th percentile.")
    median: float = Field(description="50th percentile.")
    q3: float = Field(description="75th percentile.")
    max: float = Field(description="Maximum value.")
    mean: float = Field(description="Mean value.")
    outliers: list[float] = Field(default_factory=list, description="Outlier values.")


class RegionBoxPlot(BaseModel):
    """Box plot for a specific region."""

    region_id: str = Field(description="ID of the region.")
    region_label: str = Field(description="Simplified rule text.")
    synth_count: int = Field(ge=0, description="Number of synths in region.")
    stats: BoxPlotStats = Field(description="Box plot statistics.")


class BoxPlotChart(BaseModel):
    """Data for box plot by region chart."""

    simulation_id: str = Field(description="ID of the simulation.")
    metric: str = Field(description='Metric being displayed: "adopted_rate" or "not_adopted_rate"')
    regions: list[RegionBoxPlot] = Field(description="Box plot per region.")
    baseline_stats: BoxPlotStats = Field(description="Baseline statistics for entire population.")


# =============================================================================
# 5. Scatter Correlation Chart
# =============================================================================


class CorrelationPoint(BaseModel):
    """Point in correlation scatter plot."""

    synth_id: str = Field(description="ID of the synth.")
    x_value: float = Field(description="X-axis value.")
    y_value: float = Field(description="Y-axis value.")


class CorrelationStats(BaseModel):
    """Correlation statistics."""

    pearson_r: float = Field(ge=-1.0, le=1.0, description="Pearson correlation coefficient.")
    p_value: float = Field(ge=0.0, description="Statistical p-value.")
    r_squared: float = Field(ge=0.0, le=1.0, description="R-squared value.")
    is_significant: bool = Field(description="True if p < 0.05.")
    trend_slope: float = Field(description="Slope of trend line.")
    trend_intercept: float = Field(description="Y-intercept of trend line.")


class TrendlinePoint(BaseModel):
    """Point on the trend line."""

    x: float = Field(description="X coordinate.")
    y: float = Field(description="Y coordinate.")


class ScatterCorrelationChart(BaseModel):
    """Data for scatter correlation chart."""

    simulation_id: str = Field(description="ID of the simulation.")
    x_axis: str = Field(description="X-axis attribute name.")
    y_axis: str = Field(description="Y-axis attribute name.")
    points: list[CorrelationPoint] = Field(description="All data points.")
    correlation: CorrelationStats = Field(description="Correlation statistics.")
    trendline: list[TrendlinePoint] = Field(description="Trend line points.")


# =============================================================================
# 6. Attribute Correlation Chart
# =============================================================================


class AttributeCorrelation(BaseModel):
    """Correlation of a single attribute with adoption rate."""

    attribute: str = Field(description="Attribute name (e.g., 'capability_mean').")
    attribute_label: str = Field(description="Display label in Portuguese.")
    correlation_adopted: float = Field(
        ge=-1.0, le=1.0, description="Pearson correlation with adopted_rate."
    )
    p_value_adopted: float = Field(ge=0.0, description="P-value for adoption correlation.")
    is_significant_adopted: bool = Field(description="True if p < 0.05 for adoption.")


class AttributeCorrelationChart(BaseModel):
    """Data for attribute correlation chart."""

    simulation_id: str = Field(description="ID of the simulation.")
    correlations: list[AttributeCorrelation] = Field(
        description="Correlations sorted by abs(correlation_success) desc."
    )
    total_synths: int = Field(description="Total number of synths analyzed.")


# =============================================================================
# 7. Sankey Flow Chart
# =============================================================================


class SankeyNode(BaseModel):
    """A node in the Sankey diagram."""

    id: str = Field(description="Unique node identifier (e.g., 'population', 'adopted').")
    label: str = Field(description="Display label in Portuguese.")
    level: Literal[1, 2] = Field(description="Diagram level (1=Population, 2=Outcome).")
    color: str = Field(description="Hex color code for node.")
    value: int = Field(ge=0, description="Count of synths at this node.")


class SankeyLink(BaseModel):
    """A flow link between two nodes."""

    source: str = Field(description="Source node ID.")
    target: str = Field(description="Target node ID.")
    value: int = Field(ge=0, description="Number of synths in this flow.")


class OutcomeCounts(BaseModel):
    """Aggregated outcome counts."""

    adopted: int = Field(ge=0, description="Count of synths classified as adopted.")
    not_adopted: int = Field(ge=0, description="Count of synths classified as not adopted.")


class SankeyFlowChart(BaseModel):
    """Complete Sankey flow data for visualization."""

    analysis_id: str = Field(description="Analysis run ID (ana_[a-f0-9]{8}).")
    nodes: list[SankeyNode] = Field(description="All nodes in the diagram.")
    links: list[SankeyLink] = Field(description="All flow links between nodes.")
    total_synths: int = Field(ge=0, description="Total population count.")
    outcome_counts: OutcomeCounts = Field(description="Aggregated counts per outcome.")


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: TryVsSuccessPoint creation (now adoption rate distribution)
    total_tests += 1
    try:
        point = TryVsSuccessPoint(
            synth_id="synth_001",
            adopted_rate=0.75,
            bucket="high",
        )
        if point.bucket != "high":
            all_validation_failures.append(f"bucket mismatch: {point.bucket}")
    except Exception as e:
        all_validation_failures.append(f"TryVsSuccessPoint creation failed: {e}")

    # Test 2: TryVsSuccessChart creation
    total_tests += 1
    try:
        chart = TryVsSuccessChart(
            simulation_id="sim_001",
            points=[point],
            bucket_counts={
                "low": 50,
                "medium": 210,
                "high": 240,
            },
            bucket_thresholds={"low_max": 0.33, "high_min": 0.66},
            total_synths=500,
        )
        if chart.total_synths != 500:
            all_validation_failures.append(f"total_synths mismatch: {chart.total_synths}")
    except Exception as e:
        all_validation_failures.append(f"TryVsSuccessChart creation failed: {e}")

    # Test 3: SynthDistribution creation
    total_tests += 1
    try:
        dist = SynthDistribution(
            synth_id="synth_001",
            adopted_rate=0.45,
            not_adopted_rate=0.55,
            sort_key=0.45,
        )
        if dist.adopted_rate != 0.45:
            all_validation_failures.append(f"adopted_rate mismatch: {dist.adopted_rate}")
    except Exception as e:
        all_validation_failures.append(f"SynthDistribution creation failed: {e}")

    # Test 4: HeatmapCell creation
    total_tests += 1
    try:
        cell = HeatmapCell(
            x_bin="0.0-0.2",
            y_bin="0.0-0.2",
            x_range=(0.0, 0.2),
            y_range=(0.0, 0.2),
            metric_value=0.85,
            synth_count=45,
            synth_ids=["synth_001", "synth_002"],
        )
        if cell.metric_value != 0.85:
            all_validation_failures.append(f"metric_value mismatch: {cell.metric_value}")
    except Exception as e:
        all_validation_failures.append(f"HeatmapCell creation failed: {e}")

    # Test 5: BoxPlotStats creation
    total_tests += 1
    try:
        stats = BoxPlotStats(
            min=0.1,
            q1=0.25,
            median=0.45,
            q3=0.65,
            max=0.95,
            mean=0.42,
            outliers=[0.02, 0.98],
        )
        if stats.median != 0.45:
            all_validation_failures.append(f"median mismatch: {stats.median}")
    except Exception as e:
        all_validation_failures.append(f"BoxPlotStats creation failed: {e}")

    # Test 6: CorrelationStats creation
    total_tests += 1
    try:
        corr = CorrelationStats(
            pearson_r=0.72,
            p_value=0.0001,
            r_squared=0.52,
            is_significant=True,
            trend_slope=0.65,
            trend_intercept=0.12,
        )
        if not corr.is_significant:
            all_validation_failures.append("is_significant should be True")
    except Exception as e:
        all_validation_failures.append(f"CorrelationStats creation failed: {e}")

    # Test 7: Reject invalid bucket
    total_tests += 1
    try:
        TryVsSuccessPoint(
            synth_id="synth_001",
            adopted_rate=0.75,
            bucket="invalid_bucket",  # type: ignore
        )
        all_validation_failures.append("Should reject invalid bucket")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid bucket: {e}")

    # Test 8: Reject adopted_rate > 1
    total_tests += 1
    try:
        TryVsSuccessPoint(
            synth_id="synth_001",
            adopted_rate=1.5,  # Invalid
            bucket="high",
        )
        all_validation_failures.append("Should reject adopted_rate > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid adopted_rate: {e}")

    # Test 9: OutcomeCounts with 2 outcomes
    total_tests += 1
    try:
        counts = OutcomeCounts(adopted=300, not_adopted=200)
        if counts.adopted != 300:
            all_validation_failures.append(f"adopted mismatch: {counts.adopted}")
    except Exception as e:
        all_validation_failures.append(f"OutcomeCounts creation failed: {e}")

    # Test 10: AttributeCorrelation with adopted fields
    total_tests += 1
    try:
        attr_corr = AttributeCorrelation(
            attribute="capability_mean",
            attribute_label="Capacidade Média",
            correlation_adopted=0.72,
            p_value_adopted=0.001,
            is_significant_adopted=True,
        )
        if not attr_corr.is_significant_adopted:
            all_validation_failures.append("is_significant_adopted should be True")
    except Exception as e:
        all_validation_failures.append(f"AttributeCorrelation creation failed: {e}")

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
