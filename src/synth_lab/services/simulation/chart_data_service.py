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
    AttributeCorrelation,
    AttributeCorrelationChart,
    BoxPlotChart,
    BoxPlotStats,
    CorrelationPoint,
    CorrelationStats,
    FailureHeatmapChart,
    FeatureScorecard,
    HeatmapCell,
    OutcomeCounts,
    OutcomeDistributionChart,
    RegionAnalysis,
    RegionBoxPlot,
    SankeyFlowChart,
    SankeyLink,
    SankeyNode,
    ScatterCorrelationChart,
    SynthDistribution,
    SynthOutcome,
    TrendlinePoint,
    TryVsSuccessChart,
    TryVsSuccessPoint)
from synth_lab.domain.entities.experiment import (
    ScorecardData)
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
        y_threshold: float = 0.5) -> TryVsSuccessChart:
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
                quadrant=quadrant)
            points.append(point)
            quadrant_counts[quadrant] += 1

        return TryVsSuccessChart(
            simulation_id=simulation_id,
            points=points,
            quadrant_counts=quadrant_counts,
            quadrant_thresholds={"x": x_threshold, "y": y_threshold},
            total_synths=len(outcomes))

    def get_outcome_distribution(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        sort_by: Literal["success_rate", "failed_rate", "did_not_try_rate"] = "success_rate",
        order: Literal["asc", "desc"] = "desc",
        limit: int = 50) -> OutcomeDistributionChart:
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
                sort_key=sort_key)
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
            total_synths=len(outcomes))

    # =========================================================================
    # Phase 2: Localização de Problemas (User Story 2)
    # =========================================================================

    def get_failure_heatmap(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        x_axis: str = "digital_literacy",
        y_axis: str = "domain_expertise",
        bins: int = 5,
        metric: Literal["failed_rate", "success_rate", "did_not_try_rate"] = "failed_rate",
        critical_threshold: float = 0.7) -> FailureHeatmapChart:
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
                critical_threshold=critical_threshold)

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
                    synth_ids=cell_synths)
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
            critical_threshold=critical_threshold)

    def get_box_plot(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        region_analysis: RegionAnalysis | None,
        metric: Literal["success_rate", "failed_rate", "did_not_try_rate"] = "success_rate",
        include_baseline: bool = True) -> BoxPlotChart:
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
                        stats=stats)
                    regions.append(region_box)

        return BoxPlotChart(
            simulation_id=simulation_id,
            metric=metric,
            regions=regions,
            baseline_stats=baseline_stats if include_baseline else self._calculate_box_stats([]))

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
                outliers=[])

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
            outliers=outliers)

    def get_scatter_correlation(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
        x_axis: str = "digital_literacy",
        y_axis: str = "success_rate",
        show_trendline: bool = True) -> ScatterCorrelationChart:
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
                    trend_intercept=0.0),
                trendline=[])

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
                    y_value=y_val)
            )
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
            trend_intercept=float(intercept))

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
            trendline=trendline)

    # =========================================================================
    # Phase 2b: Attribute Correlations
    # =========================================================================

    # Attribute labels in Portuguese
    ATTRIBUTE_LABELS: dict[str, str] = {
        "capability_mean": "Capacidade Média",
        "trust_mean": "Confiança Média",
        "friction_tolerance_mean": "Tolerância a Atrito",
        "exploration_prob": "Propensão a Explorar",
        "digital_literacy": "Literacia Digital",
        "similar_tool_experience": "Experiência Similar",
        "motor_ability": "Habilidade Motora",
        "time_availability": "Tempo Disponível",
        "domain_expertise": "Expertise no Domínio",
    }

    def get_attribute_correlations(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome]) -> AttributeCorrelationChart:
        """
        Calculate correlation of each synth attribute with attempt_rate and success_rate.

        Returns correlations sorted by absolute correlation with success_rate (descending).

        Args:
            simulation_id: ID of the simulation.
            outcomes: List of SynthOutcome entities.

        Returns:
            AttributeCorrelationChart with correlations for each attribute.
        """
        logger.info(f"Calculating attribute correlations for {simulation_id}")

        if not outcomes or len(outcomes) < 3:
            return AttributeCorrelationChart(
                simulation_id=simulation_id,
                correlations=[],
                total_synths=len(outcomes))

        # Calculate attempt_rate and success_rate for each synth
        attempt_rates = np.array([1.0 - o.did_not_try_rate for o in outcomes])
        success_rates = np.array([o.success_rate for o in outcomes])

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

            # Calculate correlation with attempt_rate
            try:
                corr_attempt, p_attempt = stats.pearsonr(attr_values, attempt_rates)
                # Handle NaN (occurs when variance is zero)
                if np.isnan(corr_attempt) or np.isnan(p_attempt):
                    corr_attempt, p_attempt = 0.0, 1.0
            except Exception:
                corr_attempt, p_attempt = 0.0, 1.0

            # Calculate correlation with success_rate
            try:
                corr_success, p_success = stats.pearsonr(attr_values, success_rates)
                # Handle NaN (occurs when variance is zero)
                if np.isnan(corr_success) or np.isnan(p_success):
                    corr_success, p_success = 0.0, 1.0
            except Exception:
                corr_success, p_success = 0.0, 1.0

            correlations.append(
                AttributeCorrelation(
                    attribute=attr,
                    attribute_label=self.ATTRIBUTE_LABELS.get(attr, attr),
                    correlation_attempt=float(corr_attempt),
                    correlation_success=float(corr_success),
                    p_value_attempt=float(p_attempt),
                    p_value_success=float(p_success),
                    is_significant_attempt=p_attempt < 0.05,
                    is_significant_success=p_success < 0.05)
            )

        # Keep fixed order (same as X_AXIS_OPTIONS in frontend)
        # No sorting - order matches dropdown for consistency

        return AttributeCorrelationChart(
            simulation_id=simulation_id,
            correlations=correlations,
            total_synths=len(outcomes))

    # =========================================================================
    # Sankey Flow Chart (Outcome Flow Visualization)
    # =========================================================================

    # Node colors following design system
    SANKEY_COLORS = {
        "population": "#6366f1",  # indigo
        "did_not_try": "#f59e0b",  # amber
        "failed": "#ef4444",  # red
        "success": "#22c55e",  # green
        # did_not_try causes (based on P(attempt) formula)
        "effort_barrier": "#fbbf24",  # amber-400
        "risk_barrier": "#fb923c",  # orange-400
        # failed causes (based on P(success|attempt) formula)
        "capability_barrier": "#f87171",  # red-400
        "patience_barrier": "#fca5a5",  # red-300
    }

    # Node labels in Portuguese
    SANKEY_LABELS = {
        "population": "População",
        "did_not_try": "Não tentou",
        "failed": "Falhou",
        "success": "Sucesso",
        # did_not_try causes
        "effort_barrier": "Esforço inicial alto",
        "risk_barrier": "Risco percebido",
        # failed causes
        "capability_barrier": "Capability insuficiente",
        "patience_barrier": "Desistiu antes do valor",
    }

    # Note: Tie-breaking priority moved to diagnose methods directly
    FAILED_PRIORITY = {
        "capability_gap": 2,  # capability_barrier
        "patience_gap": 1,  # patience_barrier
    }

    def get_dominant_outcome(
        self,
        outcome: SynthOutcome) -> Literal["did_not_try", "failed", "success"]:
        """
        Determine the dominant outcome for a synth.

        The dominant outcome is the one with the highest rate.
        Tie-breaking priority: success > failed > did_not_try.

        Args:
            outcome: SynthOutcome entity.

        Returns:
            The dominant outcome type.
        """
        rates = {
            "success": outcome.success_rate,
            "failed": outcome.failed_rate,
            "did_not_try": outcome.did_not_try_rate,
        }
        # Sort by rate (desc), then by priority (success > failed > did_not_try)
        priority = {"success": 3, "failed": 2, "did_not_try": 1}
        sorted_outcomes = sorted(
            rates.items(), key=lambda x: (x[1], priority[x[0]]), reverse=True
        )
        return sorted_outcomes[0][0]

    def diagnose_did_not_try(
        self,
        outcome: SynthOutcome,
        scorecard: FeatureScorecard | ScorecardData) -> str:
        """
        Diagnose root cause for did_not_try outcome.

        Based on P(attempt) formula from Monte Carlo simulation:
        logit = 2.0*motivation + 1.5*trust - 2.0*perceived_risk - 1.5*initial_effort

        Gaps calculated as (barrier - enabler) weighted by simulation weights:
        - effort_gap = 1.5*initial_effort - 2.0*motivation (effort vs motivation)
        - risk_gap = 2.0*perceived_risk - 1.5*trust (risk vs trust)

        Args:
            outcome: SynthOutcome entity with synth_attributes.
            scorecard: Feature scorecard with dimensions.

        Returns:
            Root cause barrier ID (effort_barrier, risk_barrier).
        """
        attrs = outcome.synth_attributes
        if not attrs:
            return "effort_barrier"  # Default fallback

        # Get motivation from observables or use baseline
        # In the simulation, motivation is derived from task_criticality
        # Using 0.5 as baseline since we don't have direct motivation storage
        motivation = 0.5

        # Calculate weighted gaps matching simulation P(attempt) formula
        # P(attempt) decreases when: high effort vs low motivation, high risk vs low trust
        gaps = {
            # Effort barrier: high initial_effort relative to motivation
            "effort_gap": (1.5 * scorecard.initial_effort.score) - (2.0 * motivation),
            # Risk barrier: high perceived_risk relative to trust
            "risk_gap": (2.0 * scorecard.perceived_risk.score) - (1.5 * attrs.latent_traits.trust_mean),
        }

        # Find largest gap with tie-breaking (effort has priority)
        priority = {"effort_gap": 1, "risk_gap": 0}
        sorted_gaps = sorted(
            gaps.items(),
            key=lambda x: (x[1], priority.get(x[0], 0)),
            reverse=True)
        largest_gap = sorted_gaps[0][0]

        # Map gap to barrier
        gap_to_barrier = {
            "effort_gap": "effort_barrier",
            "risk_gap": "risk_barrier",
        }
        return gap_to_barrier[largest_gap]

    def diagnose_failed(
        self,
        outcome: SynthOutcome,
        scorecard: FeatureScorecard | ScorecardData) -> str:
        """
        Diagnose root cause for failed outcome.

        Calculates gaps between scorecard dimensions and synth traits.
        The largest positive gap indicates the primary barrier.

        Gap formulas:
        - capability_gap = complexity.score - capability_mean
        - patience_gap = time_to_value.score - friction_tolerance_mean

        Args:
            outcome: SynthOutcome entity with synth_attributes.
            scorecard: Feature scorecard with dimensions.

        Returns:
            Root cause barrier ID (capability_barrier, patience_barrier).
        """
        attrs = outcome.synth_attributes
        if not attrs:
            return "capability_barrier"  # Default fallback

        gaps = {
            "capability_gap": scorecard.complexity.score - attrs.latent_traits.capability_mean,
            "patience_gap": scorecard.time_to_value.score - attrs.latent_traits.friction_tolerance_mean,
        }

        # Find largest gap with tie-breaking
        sorted_gaps = sorted(
            gaps.items(),
            key=lambda x: (x[1], self.FAILED_PRIORITY.get(x[0], 0)),
            reverse=True)
        largest_gap = sorted_gaps[0][0]

        # Map gap to barrier
        gap_to_barrier = {
            "capability_gap": "capability_barrier",
            "patience_gap": "patience_barrier",
        }
        return gap_to_barrier[largest_gap]

    def get_sankey_flow(
        self,
        analysis_id: str,
        outcomes: list[SynthOutcome],
        scorecard: FeatureScorecard | ScorecardData) -> SankeyFlowChart:
        """
        Generate Sankey flow chart data for outcome flow visualization.

        Creates a 3-level Sankey diagram:
        - Level 1: Population
        - Level 2: Outcomes (did_not_try, failed, success)
        - Level 3: Root causes (for did_not_try and failed only)

        Args:
            analysis_id: Analysis run ID.
            outcomes: List of SynthOutcome entities.
            scorecard: Feature scorecard for gap calculation.

        Returns:
            SankeyFlowChart with nodes and links.
        """
        logger.info(f"Generating Sankey flow chart for {analysis_id} with {len(outcomes)} synths")

        if not outcomes:
            return SankeyFlowChart(
                analysis_id=analysis_id,
                nodes=[],
                links=[],
                total_synths=0,
                outcome_counts=OutcomeCounts(did_not_try=0, failed=0, success=0))

        total_synths = len(outcomes)

        # Step 1: Calculate average rates across all synths (matching distribution chart)
        avg_did_not_try = sum(o.did_not_try_rate for o in outcomes) / total_synths
        avg_failed = sum(o.failed_rate for o in outcomes) / total_synths
        avg_success = sum(o.success_rate for o in outcomes) / total_synths

        # Convert rates to counts (rounded to maintain whole numbers)
        did_not_try_count = round(avg_did_not_try * total_synths)
        failed_count = round(avg_failed * total_synths)
        success_count = round(avg_success * total_synths)

        # Adjust for rounding to ensure total matches
        total_counted = did_not_try_count + failed_count + success_count
        if total_counted != total_synths:
            # Adjust the largest category
            diff = total_synths - total_counted
            if success_count >= failed_count and success_count >= did_not_try_count:
                success_count += diff
            elif failed_count >= did_not_try_count:
                failed_count += diff
            else:
                did_not_try_count += diff

        outcome_counts = OutcomeCounts(
            did_not_try=did_not_try_count,
            failed=failed_count,
            success=success_count)

        # Step 2: Diagnose root causes using rate-weighted distribution
        # For each synth, weight the root cause by their did_not_try_rate or failed_rate
        root_cause_weights: dict[str, float] = {
            # did_not_try causes (from P(attempt) formula)
            "effort_barrier": 0.0,
            "risk_barrier": 0.0,
            # failed causes (from P(success|attempt) formula)
            "capability_barrier": 0.0,
            "patience_barrier": 0.0,
        }

        for o in outcomes:
            # Weight by did_not_try_rate for did_not_try causes
            if o.did_not_try_rate > 0:
                cause = self.diagnose_did_not_try(o, scorecard)
                root_cause_weights[cause] += o.did_not_try_rate

            # Weight by failed_rate for failed causes
            if o.failed_rate > 0:
                cause = self.diagnose_failed(o, scorecard)
                root_cause_weights[cause] += o.failed_rate

        # Convert weighted sums to counts proportional to outcome counts
        # did_not_try causes (only 2: effort and risk)
        total_dnt_weight = root_cause_weights["effort_barrier"] + root_cause_weights["risk_barrier"]
        # failed causes
        total_failed_weight = root_cause_weights["capability_barrier"] + root_cause_weights["patience_barrier"]

        root_cause_counts: dict[str, int] = {}

        # Distribute did_not_try_count among its causes
        if total_dnt_weight > 0 and did_not_try_count > 0:
            for cause in ["effort_barrier", "risk_barrier"]:
                proportion = root_cause_weights[cause] / total_dnt_weight
                root_cause_counts[cause] = round(proportion * did_not_try_count)

            # Adjust for rounding
            dnt_assigned = sum(root_cause_counts.get(c, 0) for c in ["effort_barrier", "risk_barrier"])
            if dnt_assigned != did_not_try_count:
                # Find the cause with highest weight and adjust
                max_cause = max(["effort_barrier", "risk_barrier"],
                               key=lambda c: root_cause_weights[c])
                root_cause_counts[max_cause] += did_not_try_count - dnt_assigned
        else:
            for cause in ["effort_barrier", "risk_barrier"]:
                root_cause_counts[cause] = 0

        # Distribute failed_count among its causes
        if total_failed_weight > 0 and failed_count > 0:
            for cause in ["capability_barrier", "patience_barrier"]:
                proportion = root_cause_weights[cause] / total_failed_weight
                root_cause_counts[cause] = round(proportion * failed_count)

            # Adjust for rounding
            failed_assigned = sum(root_cause_counts.get(c, 0) for c in ["capability_barrier", "patience_barrier"])
            if failed_assigned != failed_count:
                max_cause = max(["capability_barrier", "patience_barrier"],
                               key=lambda c: root_cause_weights[c])
                root_cause_counts[max_cause] += failed_count - failed_assigned
        else:
            for cause in ["capability_barrier", "patience_barrier"]:
                root_cause_counts[cause] = 0

        # Step 3: Build nodes
        nodes: list[SankeyNode] = []
        total_synths = len(outcomes)

        # Level 1: Population
        nodes.append(
            SankeyNode(
                id="population",
                label=self.SANKEY_LABELS["population"],
                level=1,
                color=self.SANKEY_COLORS["population"],
                value=total_synths)
        )

        # Level 2: Outcomes (only include if count > 0)
        for outcome_id in ["did_not_try", "failed", "success"]:
            count = getattr(outcome_counts, outcome_id)
            if count > 0:
                nodes.append(
                    SankeyNode(
                        id=outcome_id,
                        label=self.SANKEY_LABELS[outcome_id],
                        level=2,
                        color=self.SANKEY_COLORS[outcome_id],
                        value=count)
                )

        # Level 3: Root causes (only include if count > 0)
        for cause_id, count in root_cause_counts.items():
            if count > 0:
                nodes.append(
                    SankeyNode(
                        id=cause_id,
                        label=self.SANKEY_LABELS[cause_id],
                        level=3,
                        color=self.SANKEY_COLORS[cause_id],
                        value=count)
                )

        # Step 4: Build links (only include if value > 0)
        links: list[SankeyLink] = []

        # Level 1 → Level 2 links
        for outcome_id in ["did_not_try", "failed", "success"]:
            count = getattr(outcome_counts, outcome_id)
            if count > 0:
                links.append(
                    SankeyLink(source="population", target=outcome_id, value=count)
                )

        # Level 2 → Level 3 links for did_not_try
        for cause_id in ["effort_barrier", "risk_barrier"]:
            count = root_cause_counts[cause_id]
            if count > 0:
                links.append(
                    SankeyLink(source="did_not_try", target=cause_id, value=count)
                )

        # Level 2 → Level 3 links for failed
        for cause_id in ["capability_barrier", "patience_barrier"]:
            count = root_cause_counts[cause_id]
            if count > 0:
                links.append(
                    SankeyLink(source="failed", target=cause_id, value=count)
                )

        return SankeyFlowChart(
            analysis_id=analysis_id,
            nodes=nodes,
            links=links,
            total_synths=total_synths,
            outcome_counts=outcome_counts)


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    from synth_lab.domain.entities.simulation_attributes import (
        SimulationAttributes,
        SimulationLatentTraits,
        SimulationObservables)

    all_validation_failures: list[str] = []
    total_tests = 0

    # Create sample outcomes for tests
    def create_outcome(
        synth_id: str,
        success: float,
        failed: float,
        capability: float = 0.5,
        trust: float = 0.5) -> SynthOutcome:
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
                    domain_expertise=0.6),
                latent_traits=SimulationLatentTraits(
                    capability_mean=capability,
                    trust_mean=trust,
                    friction_tolerance_mean=0.40,
                    exploration_prob=0.35)))

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

    # Test 5: get_failure_heatmap
    total_tests += 1
    try:
        chart = service.get_failure_heatmap("sim_test", outcomes, bins=3)
        if chart.bins != 3:
            all_validation_failures.append(f"heatmap bins: {chart.bins}")
        if len(chart.cells) != 9:  # 3x3
            all_validation_failures.append(f"heatmap cells count: {len(chart.cells)}")
    except Exception as e:
        all_validation_failures.append(f"failure_heatmap failed: {e}")

    # Test 6: get_scatter_correlation
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

    # Test 7: get_box_plot without region
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

    # Test 8: empty outcomes
    total_tests += 1
    try:
        chart = service.get_try_vs_success("sim_test", [])
        if chart.total_synths != 0:
            all_validation_failures.append(f"empty try_vs_success total: {chart.total_synths}")
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
