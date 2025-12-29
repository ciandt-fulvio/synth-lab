"""
Chart data entities for UX Research analysis.

Defines models for visualization data structures used in analysis endpoints.

References:
    - Spec: specs/017-analysis-ux-research/spec.md
    - Data model: specs/017-analysis-ux-research/data-model.md
"""

from typing import Literal

from pydantic import BaseModel, Field

# =============================================================================
# 1. Try vs Success Chart
# =============================================================================


class TryVsSuccessPoint(BaseModel):
    """Individual point in the Try vs Success scatter plot."""

    synth_id: str = Field(description="ID of the synth.")
    attempt_rate: float = Field(ge=0.0, le=1.0, description="X-axis: 1 - did_not_try_rate.")
    success_rate: float = Field(ge=0.0, le=1.0, description="Y-axis: success_rate.")
    quadrant: Literal["low_value", "usability_issue", "discovery_issue", "ok"] = Field(
        description="Quadrant classification based on thresholds."
    )


class TryVsSuccessChart(BaseModel):
    """Complete data for Try vs Success chart."""

    simulation_id: str = Field(description="ID of the simulation.")
    points: list[TryVsSuccessPoint] = Field(description="All synth points.")
    quadrant_counts: dict[str, int] = Field(
        description='Count per quadrant: {"low_value": 50, "usability_issue": 210, ...}'
    )
    quadrant_thresholds: dict[str, float] = Field(
        description='Threshold values: {"x": 0.5, "y": 0.5}'
    )
    total_synths: int = Field(description="Total number of synths.")


# =============================================================================
# 2. Outcome Distribution Chart
# =============================================================================


class SynthDistribution(BaseModel):
    """Outcome distribution for a single synth."""

    synth_id: str = Field(description="ID of the synth.")
    did_not_try_rate: float = Field(ge=0.0, le=1.0)
    failed_rate: float = Field(ge=0.0, le=1.0)
    success_rate: float = Field(ge=0.0, le=1.0)
    sort_key: float = Field(description="Value used for sorting.")


class OutcomeDistributionChart(BaseModel):
    """Data for outcome distribution chart."""

    simulation_id: str = Field(description="ID of the simulation.")
    distributions: list[SynthDistribution] = Field(description="Distribution per synth.")
    summary: dict[str, float] = Field(
        description='Summary stats: {"avg_success": 0.42, "avg_failed": 0.35, ...}'
    )
    worst_performers: list[str] = Field(description="Top synth_ids with lowest success.")
    best_performers: list[str] = Field(description="Top synth_ids with highest success.")
    total_synths: int = Field(description="Total number of synths.")


# =============================================================================
# 3. Sankey Chart
# =============================================================================


class SankeyNode(BaseModel):
    """Node in the Sankey diagram."""

    id: str = Field(description='Node ID: "all", "attempted", "not_attempted", "success", "failed"')
    label: str = Field(description='Display label: "Todos (500)", "Tentaram (375)"')
    value: int = Field(ge=0, description="Absolute count.")


class SankeyLink(BaseModel):
    """Link between Sankey nodes."""

    source: str = Field(description="Source node ID.")
    target: str = Field(description="Target node ID.")
    value: int = Field(ge=0, description="Flow count.")
    percentage: float = Field(ge=0.0, le=100.0, description="Percentage of total.")


class SankeyChart(BaseModel):
    """Complete data for Sankey diagram."""

    simulation_id: str = Field(description="ID of the simulation.")
    total_synths: int = Field(description="Total number of synths.")
    nodes: list[SankeyNode] = Field(description="All nodes.")
    links: list[SankeyLink] = Field(description="All links.")


# =============================================================================
# 4. Failure Heatmap Chart
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
    metric: str = Field(
        description='Metric being displayed: "failed_rate", "success_rate", "did_not_try_rate"'
    )
    bins: int = Field(ge=2, description="Number of bins per axis.")
    cells: list[HeatmapCell] = Field(description="All heatmap cells.")
    max_value: float = Field(description="Maximum metric value across cells.")
    min_value: float = Field(description="Minimum metric value across cells.")
    critical_cells: list[HeatmapCell] = Field(
        description="Cells with value above critical threshold."
    )
    critical_threshold: float = Field(description="Threshold for critical cells.")


# =============================================================================
# 5. Box Plot Chart
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
    metric: str = Field(
        description='Metric being displayed: "success_rate", "failed_rate", "did_not_try_rate"'
    )
    regions: list[RegionBoxPlot] = Field(description="Box plot per region.")
    baseline_stats: BoxPlotStats = Field(description="Baseline statistics for entire population.")


# =============================================================================
# 6. Scatter Correlation Chart
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
# 7. Attribute Correlation Chart
# =============================================================================


class AttributeCorrelation(BaseModel):
    """Correlation of a single attribute with outcome metrics."""

    attribute: str = Field(description="Attribute name (e.g., 'capability_mean').")
    attribute_label: str = Field(description="Display label in Portuguese.")
    correlation_attempt: float = Field(
        ge=-1.0, le=1.0, description="Pearson correlation with attempt_rate."
    )
    correlation_success: float = Field(
        ge=-1.0, le=1.0, description="Pearson correlation with success_rate."
    )
    p_value_attempt: float = Field(ge=0.0, description="P-value for attempt correlation.")
    p_value_success: float = Field(ge=0.0, description="P-value for success correlation.")
    is_significant_attempt: bool = Field(description="True if p < 0.05 for attempt.")
    is_significant_success: bool = Field(description="True if p < 0.05 for success.")


class AttributeCorrelationChart(BaseModel):
    """Data for attribute correlation chart."""

    simulation_id: str = Field(description="ID of the simulation.")
    correlations: list[AttributeCorrelation] = Field(
        description="Correlations sorted by abs(correlation_success) desc."
    )
    total_synths: int = Field(description="Total number of synths analyzed.")


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: TryVsSuccessPoint creation
    total_tests += 1
    try:
        point = TryVsSuccessPoint(
            synth_id="synth_001",
            attempt_rate=0.75,
            success_rate=0.40,
            quadrant="ok",
        )
        if point.quadrant != "ok":
            all_validation_failures.append(f"quadrant mismatch: {point.quadrant}")
    except Exception as e:
        all_validation_failures.append(f"TryVsSuccessPoint creation failed: {e}")

    # Test 2: TryVsSuccessChart creation
    total_tests += 1
    try:
        chart = TryVsSuccessChart(
            simulation_id="sim_001",
            points=[point],
            quadrant_counts={
                "low_value": 50,
                "usability_issue": 210,
                "discovery_issue": 40,
                "ok": 200,
            },
            quadrant_thresholds={"x": 0.5, "y": 0.5},
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
            did_not_try_rate=0.20,
            failed_rate=0.35,
            success_rate=0.45,
            sort_key=0.45,
        )
        if dist.success_rate != 0.45:
            all_validation_failures.append(f"success_rate mismatch: {dist.success_rate}")
    except Exception as e:
        all_validation_failures.append(f"SynthDistribution creation failed: {e}")

    # Test 4: SankeyNode and SankeyLink creation
    total_tests += 1
    try:
        node = SankeyNode(id="all", label="Todos (500)", value=500)
        link = SankeyLink(source="all", target="attempted", value=375, percentage=75.0)
        if link.percentage != 75.0:
            all_validation_failures.append(f"percentage mismatch: {link.percentage}")
    except Exception as e:
        all_validation_failures.append(f"Sankey entities creation failed: {e}")

    # Test 5: HeatmapCell creation
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

    # Test 6: BoxPlotStats creation
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

    # Test 7: CorrelationStats creation
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

    # Test 8: Reject invalid quadrant
    total_tests += 1
    try:
        TryVsSuccessPoint(
            synth_id="synth_001",
            attempt_rate=0.75,
            success_rate=0.40,
            quadrant="invalid_quadrant",  # type: ignore
        )
        all_validation_failures.append("Should reject invalid quadrant")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid quadrant: {e}")

    # Test 9: Reject attempt_rate > 1
    total_tests += 1
    try:
        TryVsSuccessPoint(
            synth_id="synth_001",
            attempt_rate=1.5,  # Invalid
            success_rate=0.40,
            quadrant="ok",
        )
        all_validation_failures.append("Should reject attempt_rate > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid attempt_rate: {e}")

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
