"""
Chart data service for UX Research analysis.

Generates data structures for visualization charts based on simulation outcomes.
Uses a 2-outcome model: adopted / not_adopted.

References:
    - Spec: specs/017-analysis-ux-research/spec.md
    - Data model: specs/017-analysis-ux-research/data-model.md
    - Quickstart: specs/017-analysis-ux-research/quickstart.md
"""

from typing import Literal

import numpy as np
from loguru import logger
from scipy import stats

from synth_lab.domain.entities import (
    AttributeCorrelation,
    AttributeCorrelationChart,
    BoxPlotChart,
    BoxPlotStats,
    CorrelationPoint,
    CorrelationStats,
    FailureHeatmapChart,
    HeatmapCell,
    OutcomeDistributionChart,
    RegionBoxPlot,
    ScatterCorrelationChart,
    SynthDistribution,
    SynthOutcome,
    TrendlinePoint,
)
from synth_lab.services.simulation.feature_extraction import get_attribute_value


class ChartDataService:
    """
    Service for generating chart data from simulation outcomes.

    Provides methods for Phase 1 (Overview) and Phase 2 (Location) charts.
    Uses a 2-outcome model: adopted / not_adopted.
    """

    # =========================================================================
    # Phase 1: Visao Geral (User Story 1)
    # =========================================================================

    def get_outcome_distribution(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        sort_by: Literal["adopted_rate", "not_adopted_rate"] = "adopted_rate",
        order: Literal["asc", "desc"] = "desc",
        limit: int = 50,
    ) -> OutcomeDistributionChart:
        """
        Generate outcome distribution chart data.

        Shows distribution of outcomes across synths, sorted by specified metric.

        Args:
            simulation_id: ID of the simulation.
            outcomes: List of SynthOutcome entities.
            sort_by: Field to sort by.
            order: Sort order (asc or desc).
            limit: Maximum number of synths to return.

        Returns:
            OutcomeDistributionChart with sorted distributions.
        """
        logger.info(
            f"Generating distribution chart for {simulation_id}, "
            f"sort_by={sort_by}, order={order}, limit={limit}"
        )

        # Build distributions
        distributions: list[SynthDistribution] = []
        adopted_rates: list[float] = []
        not_adopted_rates: list[float] = []

        for outcome in outcomes:
            sort_key = getattr(outcome, sort_by)
            dist = SynthDistribution(
                synth_id=outcome.synth_id,
                adopted_rate=outcome.adopted_rate,
                not_adopted_rate=outcome.not_adopted_rate,
                sort_key=sort_key,
            )
            distributions.append(dist)
            adopted_rates.append(outcome.adopted_rate)
            not_adopted_rates.append(outcome.not_adopted_rate)

        # Sort
        reverse = order == "desc"
        distributions.sort(key=lambda d: d.sort_key, reverse=reverse)

        # Limit
        distributions = distributions[:limit]

        # Calculate summary
        summary = {
            "avg_adopted": float(np.mean(adopted_rates)) if adopted_rates else 0.0,
            "avg_not_adopted": float(np.mean(not_adopted_rates)) if not_adopted_rates else 0.0,
            "median_adopted": float(np.median(adopted_rates)) if adopted_rates else 0.0,
            "std_adopted": float(np.std(adopted_rates)) if adopted_rates else 0.0,
        }

        # Get worst/best performers (from full list, not limited)
        all_sorted = sorted(outcomes, key=lambda o: o.adopted_rate)
        worst_performers = [o.synth_id for o in all_sorted[:10]]
        best_performers = [o.synth_id for o in all_sorted[-10:][::-1]]

        return OutcomeDistributionChart(
            simulation_id=simulation_id,
            distributions=distributions,
            summary=summary,
            worst_performers=worst_performers,
            best_performers=best_performers,
            total_synths=len(outcomes),
        )

    # =========================================================================
    # Phase 2: Localizacao de Problemas (User Story 2)
    # =========================================================================

    def get_failure_heatmap(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        x_axis: str = "digital_literacy",
        y_axis: str = "domain_expertise",
        bins: int = 5,
        metric: Literal["adopted_rate", "not_adopted_rate"] = "not_adopted_rate",
        critical_threshold: float = 0.7,
    ) -> FailureHeatmapChart:
        """
        Generate failure heatmap data.

        Creates a 2D binned heatmap showing metric values across two attributes.

        Args:
            simulation_id: ID of the simulation.
            outcomes: List of SynthOutcome entities.
            x_axis: Attribute for X axis.
            y_axis: Attribute for Y axis.
            bins: Number of bins per axis.
            metric: Metric to display in cells.
            critical_threshold: Threshold for marking critical cells.

        Returns:
            FailureHeatmapChart with cells and critical cells.
        """
        logger.info(
            f"Generating heatmap for {simulation_id}, "
            f"x={x_axis}, y={y_axis}, bins={bins}, metric={metric}"
        )

        if not outcomes:
            return FailureHeatmapChart(
                simulation_id=simulation_id,
                x_axis=x_axis,
                y_axis=y_axis,
                metric=metric,
                bins=bins,
                cells=[],
                max_value=0.0,
                min_value=0.0,
                critical_cells=[],
                critical_threshold=critical_threshold,
            )

        # Extract values
        x_values = [get_attribute_value(o, x_axis) for o in outcomes]
        y_values = [get_attribute_value(o, y_axis) for o in outcomes]
        metric_values = [get_attribute_value(o, metric) for o in outcomes]
        synth_ids = [o.synth_id for o in outcomes]

        # Create bin edges
        x_edges = np.linspace(0, 1, bins + 1)
        y_edges = np.linspace(0, 1, bins + 1)

        # Create cells
        cells: list[HeatmapCell] = []
        all_metric_values: list[float] = []

        for i in range(bins):
            for j in range(bins):
                x_min, x_max = float(x_edges[i]), float(x_edges[i + 1])
                y_min, y_max = float(y_edges[j]), float(y_edges[j + 1])

                # Find synths in this cell
                cell_indices = [
                    k
                    for k in range(len(outcomes))
                    if x_min <= x_values[k] < x_max and y_min <= y_values[k] < y_max
                ]

                # Handle edge case for last bin (include max)
                if i == bins - 1:
                    cell_indices.extend(
                        [
                            k
                            for k in range(len(outcomes))
                            if x_values[k] == x_max and y_min <= y_values[k] < y_max
                        ]
                    )
                if j == bins - 1:
                    cell_indices.extend(
                        [
                            k
                            for k in range(len(outcomes))
                            if x_min <= x_values[k] < x_max and y_values[k] == y_max
                        ]
                    )
                if i == bins - 1 and j == bins - 1:
                    cell_indices.extend(
                        [
                            k
                            for k in range(len(outcomes))
                            if x_values[k] == x_max and y_values[k] == y_max
                        ]
                    )

                # Remove duplicates
                cell_indices = list(set(cell_indices))

                if cell_indices:
                    cell_metrics = [metric_values[k] for k in cell_indices]
                    cell_synths = [synth_ids[k] for k in cell_indices]
                    avg_metric = float(np.mean(cell_metrics))
                else:
                    cell_synths = []
                    avg_metric = 0.0

                cell = HeatmapCell(
                    x_bin=f"{x_min:.1f}-{x_max:.1f}",
                    y_bin=f"{y_min:.1f}-{y_max:.1f}",
                    x_range=(x_min, x_max),
                    y_range=(y_min, y_max),
                    metric_value=avg_metric,
                    synth_count=len(cell_indices),
                    synth_ids=cell_synths,
                )
                cells.append(cell)
                all_metric_values.append(avg_metric)

        # Find critical cells
        critical_cells = [
            c for c in cells if c.metric_value >= critical_threshold and c.synth_count > 0
        ]

        return FailureHeatmapChart(
            simulation_id=simulation_id,
            x_axis=x_axis,
            y_axis=y_axis,
            metric=metric,
            bins=bins,
            cells=cells,
            max_value=max(all_metric_values) if all_metric_values else 0.0,
            min_value=min(all_metric_values) if all_metric_values else 0.0,
            critical_cells=critical_cells,
            critical_threshold=critical_threshold,
        )

    def get_box_plot(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        metric: Literal["adopted_rate", "not_adopted_rate"] = "adopted_rate",
        include_baseline: bool = True,
    ) -> BoxPlotChart:
        """
        Generate box plot data for the entire population.

        Args:
            simulation_id: ID of the simulation.
            outcomes: List of SynthOutcome entities.
            metric: Metric to display.
            include_baseline: Include baseline stats for entire population.

        Returns:
            BoxPlotChart with population-wide statistics.
        """
        logger.info(f"Generating box plot for {simulation_id}, metric={metric}")

        # Calculate baseline stats
        all_values = [get_attribute_value(o, metric) for o in outcomes]
        baseline_stats = self._calculate_box_stats(all_values)

        # No region segmentation - return baseline only
        regions: list[RegionBoxPlot] = []

        return BoxPlotChart(
            simulation_id=simulation_id,
            metric=metric,
            regions=regions,
            baseline_stats=baseline_stats if include_baseline else self._calculate_box_stats([]),
        )

    def _calculate_box_stats(self, values: list[float]) -> BoxPlotStats:
        """Calculate box plot statistics for a list of values."""
        if not values:
            return BoxPlotStats(min=0.0, q1=0.0, median=0.0, q3=0.0, max=0.0, mean=0.0, outliers=[])

        arr = np.array(values)
        q1 = float(np.percentile(arr, 25))
        q3 = float(np.percentile(arr, 75))
        iqr = q3 - q1

        # Outliers are outside 1.5 * IQR
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = [float(v) for v in arr if v < lower_bound or v > upper_bound]

        return BoxPlotStats(
            min=float(np.min(arr)),
            q1=q1,
            median=float(np.median(arr)),
            q3=q3,
            max=float(np.max(arr)),
            mean=float(np.mean(arr)),
            outliers=outliers,
        )

    def get_scatter_correlation(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        x_axis: str = "digital_literacy",
        y_axis: str = "adopted_rate",
        show_trendline: bool = True,
    ) -> ScatterCorrelationChart:
        """
        Generate scatter correlation chart data.

        Shows correlation between two attributes with optional trend line.

        Args:
            simulation_id: ID of the simulation.
            outcomes: List of SynthOutcome entities.
            x_axis: Attribute for X axis.
            y_axis: Attribute for Y axis.
            show_trendline: Include trend line calculation.

        Returns:
            ScatterCorrelationChart with points and correlation stats.
        """
        logger.info(f"Generating scatter for {simulation_id}, x={x_axis}, y={y_axis}")

        if not outcomes:
            return ScatterCorrelationChart(
                simulation_id=simulation_id,
                x_axis=x_axis,
                y_axis=y_axis,
                points=[],
                correlation=CorrelationStats(
                    pearson_r=0.0,
                    p_value=1.0,
                    r_squared=0.0,
                    is_significant=False,
                    trend_slope=0.0,
                    trend_intercept=0.0,
                ),
                trendline=[],
            )

        # Extract values
        points: list[CorrelationPoint] = []
        x_values: list[float] = []
        y_values: list[float] = []

        for outcome in outcomes:
            x_val = get_attribute_value(outcome, x_axis)
            y_val = get_attribute_value(outcome, y_axis)
            points.append(CorrelationPoint(synth_id=outcome.synth_id, x_value=x_val, y_value=y_val))
            x_values.append(x_val)
            y_values.append(y_val)

        # Calculate correlation
        x_arr = np.array(x_values)
        y_arr = np.array(y_values)

        if len(x_arr) >= 2:
            try:
                pearson_r, p_value = stats.pearsonr(x_arr, y_arr)
                # Handle NaN (occurs when variance is zero)
                if np.isnan(pearson_r) or np.isnan(p_value):
                    pearson_r, p_value = 0.0, 1.0
            except Exception:
                pearson_r, p_value = 0.0, 1.0

            try:
                slope, intercept = np.polyfit(x_arr, y_arr, 1)
                # Handle NaN from polyfit
                if np.isnan(slope) or np.isnan(intercept):
                    slope, intercept = 0.0, float(np.mean(y_arr))
            except Exception:
                slope, intercept = 0.0, float(np.mean(y_arr)) if len(y_arr) > 0 else 0.0
        else:
            pearson_r, p_value = 0.0, 1.0
            slope, intercept = 0.0, 0.0

        correlation = CorrelationStats(
            pearson_r=float(pearson_r),
            p_value=float(p_value),
            r_squared=float(pearson_r**2),
            is_significant=p_value < 0.05 and not np.isnan(p_value),
            trend_slope=float(slope),
            trend_intercept=float(intercept),
        )

        # Calculate trendline points
        trendline: list[TrendlinePoint] = []
        if show_trendline and len(x_arr) >= 2:
            x_min, x_max = float(np.min(x_arr)), float(np.max(x_arr))
            trendline = [
                TrendlinePoint(x=x_min, y=slope * x_min + intercept),
                TrendlinePoint(x=x_max, y=slope * x_max + intercept),
            ]

        return ScatterCorrelationChart(
            simulation_id=simulation_id,
            x_axis=x_axis,
            y_axis=y_axis,
            points=points,
            correlation=correlation,
            trendline=trendline,
        )

    # =========================================================================
    # Phase 2b: Attribute Correlations
    # =========================================================================

    # Attribute labels in Portuguese
    ATTRIBUTE_LABELS: dict[str, str] = {
        "capability_mean": "Capacidade Media",
        "trust_mean": "Confianca Media",
        "friction_tolerance_mean": "Tolerancia a Atrito",
        "exploration_prob": "Propensao a Explorar",
        "digital_literacy": "Literacia Digital",
        "similar_tool_experience": "Experiencia Similar",
        "motor_ability": "Habilidade Motora",
        "time_availability": "Tempo Disponivel",
        "domain_expertise": "Expertise no Dominio",
    }

    def get_attribute_correlations(
        self, simulation_id: str, outcomes: list[SynthOutcome]
    ) -> AttributeCorrelationChart:
        """
        Calculate correlation of each synth attribute with adopted_rate.

        Returns correlations sorted by absolute correlation (descending).

        Args:
            simulation_id: ID of the simulation.
            outcomes: List of SynthOutcome entities.

        Returns:
            AttributeCorrelationChart with correlations for each attribute.
        """
        logger.info(f"Calculating attribute correlations for {simulation_id}")

        if not outcomes or len(outcomes) < 3:
            return AttributeCorrelationChart(
                simulation_id=simulation_id, correlations=[], total_synths=len(outcomes)
            )

        # Calculate adopted_rate for each synth
        adopted_rates = np.array([o.adopted_rate for o in outcomes])

        # All attributes to analyze
        all_attributes = [
            "capability_mean",
            "trust_mean",
            "friction_tolerance_mean",
            "exploration_prob",
            "digital_literacy",
            "similar_tool_experience",
            "motor_ability",
            "time_availability",
            "domain_expertise",
        ]

        correlations: list[AttributeCorrelation] = []

        for attr in all_attributes:
            # Extract attribute values
            attr_values = np.array([get_attribute_value(o, attr) for o in outcomes])

            # Calculate correlation with adopted_rate
            try:
                corr_adopted, p_adopted = stats.pearsonr(attr_values, adopted_rates)
                # Handle NaN (occurs when variance is zero)
                if np.isnan(corr_adopted) or np.isnan(p_adopted):
                    corr_adopted, p_adopted = 0.0, 1.0
            except Exception:
                corr_adopted, p_adopted = 0.0, 1.0

            correlations.append(
                AttributeCorrelation(
                    attribute=attr,
                    attribute_label=self.ATTRIBUTE_LABELS.get(attr, attr),
                    correlation_adopted=float(corr_adopted),
                    p_value_adopted=float(p_adopted),
                    is_significant_adopted=p_adopted < 0.05,
                )
            )

        # Keep fixed order (same as X_AXIS_OPTIONS in frontend)
        # No sorting - order matches dropdown for consistency

        return AttributeCorrelationChart(
            simulation_id=simulation_id, correlations=correlations, total_synths=len(outcomes)
        )



# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    from synth_lab.domain.entities.simulation_attributes import (
        SimulationAttributes,
        SimulationLatentTraits,
        SimulationObservables,
    )

    all_validation_failures: list[str] = []
    total_tests = 0

    # Create sample outcomes for tests (2-outcome model)
    def create_outcome(
        synth_id: str, adopted: float, capability: float = 0.5, trust: float = 0.5
    ) -> SynthOutcome:
        return SynthOutcome(
            analysis_id="ana_12345678",
            synth_id=synth_id,
            adopted_rate=adopted,
            not_adopted_rate=1.0 - adopted,
            synth_attributes=SimulationAttributes(
                observables=SimulationObservables(
                    digital_literacy=0.5,
                    similar_tool_experience=0.4,
                    motor_ability=0.8,
                    time_availability=0.3,
                    domain_expertise=0.6,
                ),
                latent_traits=SimulationLatentTraits(
                    capability_mean=capability,
                    trust_mean=trust,
                    friction_tolerance_mean=0.40,
                    exploration_prob=0.35,
                ),
            ),
        )

    outcomes = [
        create_outcome("synth_001", 0.80, capability=0.8, trust=0.7),
        create_outcome("synth_002", 0.30, capability=0.6, trust=0.6),
        create_outcome("synth_003", 0.55, capability=0.2, trust=0.8),
        create_outcome("synth_004", 0.15, capability=0.3, trust=0.2),
        create_outcome("synth_005", 0.70, capability=0.5, trust=0.5),
    ]

    service = ChartDataService()

    # Test 1: get_outcome_distribution
    total_tests += 1
    try:
        chart = service.get_outcome_distribution("sim_test", outcomes, limit=3)
        if len(chart.distributions) != 3:
            all_validation_failures.append(f"distribution limit: {len(chart.distributions)}")
        if chart.total_synths != 5:
            all_validation_failures.append(f"distribution total_synths: {chart.total_synths}")
        if "avg_adopted" not in chart.summary:
            all_validation_failures.append("distribution missing avg_adopted")
    except Exception as e:
        all_validation_failures.append(f"outcome_distribution failed: {e}")

    # Test 2: get_outcome_distribution sorted asc
    total_tests += 1
    try:
        chart = service.get_outcome_distribution("sim_test", outcomes, order="asc", limit=5)
        # First should be lowest adopted (synth_004 with 0.15)
        if chart.distributions[0].synth_id != "synth_004":
            all_validation_failures.append(
                f"distribution asc first: {chart.distributions[0].synth_id}"
            )
    except Exception as e:
        all_validation_failures.append(f"outcome_distribution asc failed: {e}")

    # Test 3: get_failure_heatmap
    total_tests += 1
    try:
        chart = service.get_failure_heatmap("sim_test", outcomes, bins=3)
        if chart.bins != 3:
            all_validation_failures.append(f"heatmap bins: {chart.bins}")
        if len(chart.cells) != 9:  # 3x3
            all_validation_failures.append(f"heatmap cells count: {len(chart.cells)}")
    except Exception as e:
        all_validation_failures.append(f"failure_heatmap failed: {e}")

    # Test 4: get_scatter_correlation
    total_tests += 1
    try:
        chart = service.get_scatter_correlation("sim_test", outcomes)
        if len(chart.points) != 5:
            all_validation_failures.append(f"scatter points count: {len(chart.points)}")
        if len(chart.trendline) != 2:
            all_validation_failures.append(f"scatter trendline count: {len(chart.trendline)}")
        if chart.correlation.pearson_r is None:
            all_validation_failures.append("scatter missing pearson_r")
    except Exception as e:
        all_validation_failures.append(f"scatter_correlation failed: {e}")

    # Test 5: get_box_plot
    total_tests += 1
    try:
        chart = service.get_box_plot("sim_test", outcomes)
        if chart.baseline_stats.mean == 0.0:
            all_validation_failures.append("box_plot baseline mean should not be 0")
        if len(chart.regions) != 0:
            all_validation_failures.append(
                f"box_plot regions without analysis: {len(chart.regions)}"
            )
    except Exception as e:
        all_validation_failures.append(f"box_plot failed: {e}")

    # Test 6: empty outcomes
    total_tests += 1
    try:
        chart = service.get_outcome_distribution("sim_test", [])
        if chart.total_synths != 0:
            all_validation_failures.append(f"empty distribution total: {chart.total_synths}")
    except Exception as e:
        all_validation_failures.append(f"empty outcomes handling failed: {e}")

    # Test 7: get_attribute_correlations
    total_tests += 1
    try:
        chart = service.get_attribute_correlations("sim_test", outcomes)
        if len(chart.correlations) != 9:
            all_validation_failures.append(
                f"attribute_correlations count: {len(chart.correlations)}"
            )
        # Should have correlation_adopted field
        first = chart.correlations[0]
        if not hasattr(first, "correlation_adopted"):
            all_validation_failures.append("missing correlation_adopted field")
    except Exception as e:
        all_validation_failures.append(f"attribute_correlations failed: {e}")

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
