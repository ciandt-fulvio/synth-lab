"""
Chart data service for UX Research analysis.

Generates data structures for visualization charts based on simulation outcomes.

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
    BoxPlotChart,
    BoxPlotStats,
    CorrelationPoint,
    CorrelationStats,
    FailureHeatmapChart,
    HeatmapCell,
    OutcomeDistributionChart,
    RegionAnalysis,
    RegionBoxPlot,
    SankeyChart,
    SankeyLink,
    SankeyNode,
    ScatterCorrelationChart,
    SensitivityResult,
    SynthDistribution,
    SynthOutcome,
    TornadoBar,
    TornadoChart,
    TrendlinePoint,
    TryVsSuccessChart,
    TryVsSuccessPoint,
)
from synth_lab.services.simulation.feature_extraction import get_attribute_value


class ChartDataService:
    """
    Service for generating chart data from simulation outcomes.

    Provides methods for Phase 1 (Overview) and Phase 2 (Location) charts.
    """

    # =========================================================================
    # Phase 1: Visão Geral (User Story 1)
    # =========================================================================

    def get_try_vs_success(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        x_threshold: float = 0.5,
        y_threshold: float = 0.5,
    ) -> TryVsSuccessChart:
        """
        Generate Try vs Success scatter plot data.

        Each point represents one synth:
        - X-axis: attempt_rate = 1 - did_not_try_rate
        - Y-axis: success_rate

        Quadrants:
        - ok: high attempt, high success (X >= threshold, Y >= threshold)
        - usability_issue: high attempt, low success (X >= threshold, Y < threshold)
        - discovery_issue: low attempt, high success (X < threshold, Y >= threshold)
        - low_value: low attempt, low success (X < threshold, Y < threshold)

        Args:
            simulation_id: ID of the simulation.
            outcomes: List of SynthOutcome entities.
            x_threshold: X-axis threshold for quadrant division.
            y_threshold: Y-axis threshold for quadrant division.

        Returns:
            TryVsSuccessChart with points and quadrant counts.
        """
        logger.info(
            f"Generating Try vs Success chart for {simulation_id} with {len(outcomes)} synths"
        )

        points: list[TryVsSuccessPoint] = []
        quadrant_counts = {
            "low_value": 0,
            "usability_issue": 0,
            "discovery_issue": 0,
            "ok": 0,
        }

        for outcome in outcomes:
            attempt_rate = 1.0 - outcome.did_not_try_rate
            success_rate = outcome.success_rate

            # Determine quadrant
            if attempt_rate >= x_threshold:
                if success_rate >= y_threshold:
                    quadrant = "ok"
                else:
                    quadrant = "usability_issue"
            else:
                if success_rate >= y_threshold:
                    quadrant = "discovery_issue"
                else:
                    quadrant = "low_value"

            point = TryVsSuccessPoint(
                synth_id=outcome.synth_id,
                attempt_rate=attempt_rate,
                success_rate=success_rate,
                quadrant=quadrant,
            )
            points.append(point)
            quadrant_counts[quadrant] += 1

        return TryVsSuccessChart(
            simulation_id=simulation_id,
            points=points,
            quadrant_counts=quadrant_counts,
            quadrant_thresholds={"x": x_threshold, "y": y_threshold},
            total_synths=len(outcomes),
        )

    def get_outcome_distribution(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        sort_by: Literal["success_rate", "failed_rate", "did_not_try_rate"] = "success_rate",
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
        success_rates: list[float] = []
        failed_rates: list[float] = []
        did_not_try_rates: list[float] = []

        for outcome in outcomes:
            sort_key = getattr(outcome, sort_by)
            dist = SynthDistribution(
                synth_id=outcome.synth_id,
                did_not_try_rate=outcome.did_not_try_rate,
                failed_rate=outcome.failed_rate,
                success_rate=outcome.success_rate,
                sort_key=sort_key,
            )
            distributions.append(dist)
            success_rates.append(outcome.success_rate)
            failed_rates.append(outcome.failed_rate)
            did_not_try_rates.append(outcome.did_not_try_rate)

        # Sort
        reverse = order == "desc"
        distributions.sort(key=lambda d: d.sort_key, reverse=reverse)

        # Limit
        distributions = distributions[:limit]

        # Calculate summary
        summary = {
            "avg_success": float(np.mean(success_rates)) if success_rates else 0.0,
            "avg_failed": float(np.mean(failed_rates)) if failed_rates else 0.0,
            "avg_did_not_try": float(np.mean(did_not_try_rates)) if did_not_try_rates else 0.0,
            "median_success": float(np.median(success_rates)) if success_rates else 0.0,
            "std_success": float(np.std(success_rates)) if success_rates else 0.0,
        }

        # Get worst/best performers (from full list, not limited)
        all_sorted = sorted(outcomes, key=lambda o: o.success_rate)
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

    def get_sankey(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
    ) -> SankeyChart:
        """
        Generate Sankey diagram data using dominant outcome classification.

        Each synth is categorized by its dominant outcome (highest rate):
        - If did_not_try_rate is highest -> "Não Tentou"
        - If success_rate is highest -> "Sucesso"
        - If failed_rate is highest -> "Falhou"

        Flow: All -> [Tentaram, Não Tentaram] -> [Sucesso, Falharam]

        Args:
            simulation_id: ID of the simulation.
            outcomes: List of SynthOutcome entities.

        Returns:
            SankeyChart with nodes and links (discrete counts).
        """
        logger.info(f"Generating Sankey diagram for {simulation_id}")

        total = len(outcomes)
        if total == 0:
            return SankeyChart(
                simulation_id=simulation_id,
                total_synths=0,
                nodes=[],
                links=[],
            )

        # Classify each synth by dominant outcome
        not_attempted = 0
        success = 0
        failed = 0

        for o in outcomes:
            # Find dominant outcome
            rates = {
                "did_not_try": o.did_not_try_rate,
                "success": o.success_rate,
                "failed": o.failed_rate,
            }
            dominant = max(rates, key=rates.get)

            if dominant == "did_not_try":
                not_attempted += 1
            elif dominant == "success":
                success += 1
            else:
                failed += 1

        # Attempted = success + failed (those who tried)
        attempted = success + failed

        # Create nodes
        nodes = [
            SankeyNode(id="all", label=f"Todos ({total})", value=total),
            SankeyNode(id="attempted", label=f"Tentaram ({attempted})", value=attempted),
            SankeyNode(
                id="not_attempted", label=f"Não Tentaram ({not_attempted})", value=not_attempted
            ),
            SankeyNode(id="success", label=f"Sucesso ({success})", value=success),
            SankeyNode(id="failed", label=f"Falharam ({failed})", value=failed),
        ]

        # Create links
        links = [
            SankeyLink(
                source="all",
                target="attempted",
                value=attempted,
                percentage=round(100 * attempted / total, 1) if total > 0 else 0.0,
            ),
            SankeyLink(
                source="all",
                target="not_attempted",
                value=not_attempted,
                percentage=round(100 * not_attempted / total, 1) if total > 0 else 0.0,
            ),
            SankeyLink(
                source="attempted",
                target="success",
                value=success,
                percentage=round(100 * success / attempted, 1) if attempted > 0 else 0.0,
            ),
            SankeyLink(
                source="attempted",
                target="failed",
                value=failed,
                percentage=round(100 * failed / attempted, 1) if attempted > 0 else 0.0,
            ),
        ]

        return SankeyChart(
            simulation_id=simulation_id,
            total_synths=total,
            nodes=nodes,
            links=links,
        )

    # =========================================================================
    # Phase 2: Localização de Problemas (User Story 2)
    # =========================================================================

    def get_failure_heatmap(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        x_axis: str = "capability_mean",
        y_axis: str = "trust_mean",
        bins: int = 5,
        metric: Literal["failed_rate", "success_rate", "did_not_try_rate"] = "failed_rate",
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
        region_analysis: RegionAnalysis | None,
        metric: Literal["success_rate", "failed_rate", "did_not_try_rate"] = "success_rate",
        include_baseline: bool = True,
    ) -> BoxPlotChart:
        """
        Generate box plot data by region.

        Uses existing region analysis to group synths.

        Args:
            simulation_id: ID of the simulation.
            outcomes: List of SynthOutcome entities.
            region_analysis: Existing region analysis result.
            metric: Metric to display.
            include_baseline: Include baseline stats for entire population.

        Returns:
            BoxPlotChart with region-wise statistics.
        """
        logger.info(f"Generating box plot for {simulation_id}, metric={metric}")

        # Calculate baseline stats
        all_values = [get_attribute_value(o, metric) for o in outcomes]
        baseline_stats = self._calculate_box_stats(all_values)

        regions: list[RegionBoxPlot] = []

        if region_analysis and region_analysis.regions:
            # Create lookup for synth outcomes
            outcome_map = {o.synth_id: o for o in outcomes}

            for region in region_analysis.regions:
                # Get metric values for synths in this region
                region_values = []
                for synth_id in region.synth_ids:
                    if synth_id in outcome_map:
                        value = get_attribute_value(outcome_map[synth_id], metric)
                        region_values.append(value)

                if region_values:
                    stats = self._calculate_box_stats(region_values)
                    region_box = RegionBoxPlot(
                        region_id=region.region_id,
                        region_label=region.rule_text[:50]
                        if len(region.rule_text) > 50
                        else region.rule_text,
                        synth_count=len(region_values),
                        stats=stats,
                    )
                    regions.append(region_box)

        return BoxPlotChart(
            simulation_id=simulation_id,
            metric=metric,
            regions=regions,
            baseline_stats=baseline_stats if include_baseline else self._calculate_box_stats([]),
        )

    def _calculate_box_stats(self, values: list[float]) -> BoxPlotStats:
        """Calculate box plot statistics for a list of values."""
        if not values:
            return BoxPlotStats(
                min=0.0,
                q1=0.0,
                median=0.0,
                q3=0.0,
                max=0.0,
                mean=0.0,
                outliers=[],
            )

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
        x_axis: str = "trust_mean",
        y_axis: str = "success_rate",
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
            points.append(
                CorrelationPoint(
                    synth_id=outcome.synth_id,
                    x_value=x_val,
                    y_value=y_val,
                )
            )
            x_values.append(x_val)
            y_values.append(y_val)

        # Calculate correlation
        x_arr = np.array(x_values)
        y_arr = np.array(y_values)

        if len(x_arr) >= 2:
            pearson_r, p_value = stats.pearsonr(x_arr, y_arr)
            slope, intercept = np.polyfit(x_arr, y_arr, 1)
        else:
            pearson_r, p_value = 0.0, 1.0
            slope, intercept = 0.0, 0.0

        correlation = CorrelationStats(
            pearson_r=float(pearson_r),
            p_value=float(p_value),
            r_squared=float(pearson_r**2),
            is_significant=p_value < 0.05,
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

    def get_tornado(
        self,
        simulation_id: str,
        sensitivity_result: SensitivityResult | None,
    ) -> TornadoChart:
        """
        Generate tornado diagram data from sensitivity analysis.

        Args:
            simulation_id: ID of the simulation.
            sensitivity_result: Existing sensitivity analysis result.

        Returns:
            TornadoChart with bars sorted by sensitivity.
        """
        logger.info(f"Generating tornado for {simulation_id}")

        if not sensitivity_result:
            return TornadoChart(
                simulation_id=simulation_id,
                baseline_success=0.0,
                bars=[],
                deltas_used=[],
                most_sensitive="",
            )

        bars: list[TornadoBar] = []

        # Sort dimensions by sensitivity index
        sorted_dims = sorted(
            sensitivity_result.dimensions, key=lambda d: d.sensitivity_index, reverse=True
        )

        for rank, dim in enumerate(sorted_dims, 1):
            bar = TornadoBar(
                dimension=dim.dimension,
                rank=rank,
                sensitivity_index=dim.sensitivity_index,
                negative_impact=dim.delta_success_low,
                positive_impact=dim.delta_success_high,
                baseline_value=dim.baseline_value,
                label_negative=f"-{abs(dim.delta_pct):.0f}% → {dim.delta_success_low:+.1%}",
                label_positive=f"+{abs(dim.delta_pct):.0f}% → {dim.delta_success_high:+.1%}",
            )
            bars.append(bar)

        return TornadoChart(
            simulation_id=simulation_id,
            baseline_success=sensitivity_result.baseline_success,
            bars=bars,
            deltas_used=[dim.delta_pct for dim in sorted_dims] if sorted_dims else [],
            most_sensitive=sorted_dims[0].dimension if sorted_dims else "",
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

    # Create sample outcomes for tests
    def create_outcome(
        synth_id: str,
        success: float,
        failed: float,
        capability: float = 0.5,
        trust: float = 0.5,
    ) -> SynthOutcome:
        return SynthOutcome(
            simulation_id="sim_test",
            synth_id=synth_id,
            success_rate=success,
            failed_rate=failed,
            did_not_try_rate=1.0 - success - failed,
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
        create_outcome("synth_001", 0.70, 0.20, capability=0.8, trust=0.7),  # ok
        create_outcome("synth_002", 0.30, 0.50, capability=0.6, trust=0.6),  # usability_issue
        create_outcome("synth_003", 0.60, 0.10, capability=0.2, trust=0.8),  # discovery_issue
        create_outcome("synth_004", 0.20, 0.30, capability=0.3, trust=0.2),  # low_value
        create_outcome("synth_005", 0.55, 0.35, capability=0.5, trust=0.5),  # ok
    ]

    service = ChartDataService()

    # Test 1: get_try_vs_success
    total_tests += 1
    try:
        chart = service.get_try_vs_success("sim_test", outcomes)
        if chart.total_synths != 5:
            all_validation_failures.append(f"try_vs_success total_synths: {chart.total_synths}")
        if len(chart.points) != 5:
            all_validation_failures.append(f"try_vs_success points count: {len(chart.points)}")
        # synth_001 has attempt_rate=0.9 (1-0.1), success=0.7 -> ok quadrant
        p1 = next((p for p in chart.points if p.synth_id == "synth_001"), None)
        if p1 and p1.quadrant != "ok":
            all_validation_failures.append(f"synth_001 quadrant: {p1.quadrant}")
    except Exception as e:
        all_validation_failures.append(f"try_vs_success failed: {e}")

    # Test 2: get_try_vs_success with custom thresholds
    total_tests += 1
    try:
        chart = service.get_try_vs_success("sim_test", outcomes, x_threshold=0.9, y_threshold=0.6)
        if chart.quadrant_thresholds["x"] != 0.9:
            all_validation_failures.append(f"custom threshold x: {chart.quadrant_thresholds['x']}")
    except Exception as e:
        all_validation_failures.append(f"try_vs_success custom thresholds failed: {e}")

    # Test 3: get_outcome_distribution
    total_tests += 1
    try:
        chart = service.get_outcome_distribution("sim_test", outcomes, limit=3)
        if len(chart.distributions) != 3:
            all_validation_failures.append(f"distribution limit: {len(chart.distributions)}")
        if chart.total_synths != 5:
            all_validation_failures.append(f"distribution total_synths: {chart.total_synths}")
        if "avg_success" not in chart.summary:
            all_validation_failures.append("distribution missing avg_success")
    except Exception as e:
        all_validation_failures.append(f"outcome_distribution failed: {e}")

    # Test 4: get_outcome_distribution sorted asc
    total_tests += 1
    try:
        chart = service.get_outcome_distribution("sim_test", outcomes, order="asc", limit=5)
        # First should be lowest success (synth_004 with 0.20)
        if chart.distributions[0].synth_id != "synth_004":
            all_validation_failures.append(
                f"distribution asc first: {chart.distributions[0].synth_id}"
            )
    except Exception as e:
        all_validation_failures.append(f"outcome_distribution asc failed: {e}")

    # Test 5: get_sankey
    total_tests += 1
    try:
        chart = service.get_sankey("sim_test", outcomes)
        if chart.total_synths != 5:
            all_validation_failures.append(f"sankey total_synths: {chart.total_synths}")
        if len(chart.nodes) != 5:
            all_validation_failures.append(f"sankey nodes count: {len(chart.nodes)}")
        if len(chart.links) != 4:
            all_validation_failures.append(f"sankey links count: {len(chart.links)}")
    except Exception as e:
        all_validation_failures.append(f"sankey failed: {e}")

    # Test 6: get_failure_heatmap
    total_tests += 1
    try:
        chart = service.get_failure_heatmap("sim_test", outcomes, bins=3)
        if chart.bins != 3:
            all_validation_failures.append(f"heatmap bins: {chart.bins}")
        if len(chart.cells) != 9:  # 3x3
            all_validation_failures.append(f"heatmap cells count: {len(chart.cells)}")
    except Exception as e:
        all_validation_failures.append(f"failure_heatmap failed: {e}")

    # Test 7: get_scatter_correlation
    total_tests += 1
    try:
        chart = service.get_scatter_correlation("sim_test", outcomes)
        if len(chart.points) != 5:
            all_validation_failures.append(f"scatter points count: {len(chart.points)}")
        if len(chart.trendline) != 2:
            all_validation_failures.append(f"scatter trendline count: {len(chart.trendline)}")
        # Should have correlation stats
        if chart.correlation.pearson_r is None:
            all_validation_failures.append("scatter missing pearson_r")
    except Exception as e:
        all_validation_failures.append(f"scatter_correlation failed: {e}")

    # Test 8: get_box_plot without region
    total_tests += 1
    try:
        chart = service.get_box_plot("sim_test", outcomes, region_analysis=None)
        if chart.baseline_stats.mean == 0.0:
            all_validation_failures.append("box_plot baseline mean should not be 0")
        if len(chart.regions) != 0:
            all_validation_failures.append(
                f"box_plot regions without analysis: {len(chart.regions)}"
            )
    except Exception as e:
        all_validation_failures.append(f"box_plot failed: {e}")

    # Test 9: get_tornado without sensitivity
    total_tests += 1
    try:
        chart = service.get_tornado("sim_test", sensitivity_result=None)
        if len(chart.bars) != 0:
            all_validation_failures.append(f"tornado bars without sensitivity: {len(chart.bars)}")
    except Exception as e:
        all_validation_failures.append(f"tornado failed: {e}")

    # Test 10: empty outcomes
    total_tests += 1
    try:
        chart = service.get_try_vs_success("sim_test", [])
        if chart.total_synths != 0:
            all_validation_failures.append(f"empty try_vs_success total: {chart.total_synths}")
        sankey = service.get_sankey("sim_test", [])
        if sankey.total_synths != 0:
            all_validation_failures.append(f"empty sankey total: {sankey.total_synths}")
    except Exception as e:
        all_validation_failures.append(f"empty outcomes handling failed: {e}")

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
