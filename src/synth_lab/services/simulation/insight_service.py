"""
LLM-powered insights for chart analysis.

Generates captions, explanations, evidence, and recommendations
for simulation charts using LLM with Phoenix tracing.

Functions:
- _generate_caption(): Generate short caption (<=20 tokens)
- generate_insight(): Generate full insight with explanation and evidence
- get_all_insights(): Get all cached insights for a simulation
- generate_executive_summary(): Generate summary across all charts

References:
    - Entities: src/synth_lab/domain/entities/chart_insight.py
    - Spec: specs/017-analysis-ux-research/spec.md (US6)
    - Data Model: specs/017-analysis-ux-research/data-model.md
    - LLM Client: src/synth_lab/infrastructure/llm_client.py

Sample usage:
    from synth_lab.services.simulation.insight_service import InsightService

    service = InsightService()
    insight = service.generate_insight("sim_123", "try_vs_success", chart_data)

Expected output:
    ChartInsight with caption, explanation, evidence, and recommendation
"""

import json
from datetime import datetime
from typing import Any

from loguru import logger

from synth_lab.domain.entities.chart_insight import (
    ChartCaption,
    ChartInsight,
    ChartType,
    SimulationInsights,
)
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("insight-service")


class InsightGenerationError(Exception):
    """Error raised when insight generation fails."""

    pass


class InsightService:
    """LLM-powered chart insight generator with caching."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        """
        Initialize with optional LLM client.

        Args:
            llm_client: LLM client instance. If None, uses global client.
        """
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="insight_service")
        # In-memory cache: {simulation_id: {chart_type: ChartInsight}}
        self._cache: dict[str, dict[str, ChartInsight]] = {}

    def _generate_caption(
        self,
        simulation_id: str,
        chart_type: ChartType,
        chart_data: dict[str, Any],
    ) -> ChartCaption:
        """
        Generate a short caption for a chart (<=20 tokens).

        Args:
            simulation_id: Simulation identifier
            chart_type: Type of chart
            chart_data: Chart data to analyze

        Returns:
            ChartCaption with caption and key metric
        """
        with _tracer.start_as_current_span(
            "InsightService: _generate_caption",
            attributes={
                "simulation_id": simulation_id,
                "chart_type": chart_type,
            },
        ):
            prompt = self._build_caption_prompt(chart_type, chart_data)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a UX research analyst. Generate a short, factual caption "
                        "(maximum 20 tokens) that highlights the most important finding from "
                        "the chart data. Return JSON with caption, key_metric, key_value, and confidence."
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            response = self.llm.complete_json(
                messages=messages,
                temperature=0.3,
                operation_name="generate_caption",
            )

            try:
                data = json.loads(response)
            except json.JSONDecodeError as e:
                raise InsightGenerationError(f"Invalid JSON response: {e}") from e

            return ChartCaption(
                simulation_id=simulation_id,
                chart_type=chart_type,
                caption=data.get("caption", "Analysis pending"),
                key_metric=data.get("key_metric", "unknown"),
                key_value=float(data.get("key_value", 0.0)),
                confidence=float(data.get("confidence", 0.8)),
            )

    def generate_insight(
        self,
        simulation_id: str,
        chart_type: ChartType,
        chart_data: dict[str, Any],
        force_regenerate: bool = False,
    ) -> ChartInsight:
        """
        Generate full insight for a chart.

        Args:
            simulation_id: Simulation identifier
            chart_type: Type of chart
            chart_data: Chart data to analyze
            force_regenerate: If True, bypass cache

        Returns:
            ChartInsight with caption, explanation, evidence, recommendation

        Raises:
            InsightGenerationError: If LLM call fails
        """
        with _tracer.start_as_current_span(
            "InsightService: generate_insight",
            attributes={
                "simulation_id": simulation_id,
                "chart_type": chart_type,
                "force_regenerate": force_regenerate,
            },
        ):
            # Check cache first
            if not force_regenerate:
                cached = self._get_cached_insight(simulation_id, chart_type)
                if cached is not None:
                    self.logger.debug(
                        f"Returning cached insight for {simulation_id}/{chart_type}"
                    )
                    return cached

            prompt = self._build_insight_prompt(chart_type, chart_data)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a senior UX research analyst. Analyze the chart data and "
                        "provide a comprehensive insight. Return JSON with:\n"
                        "- caption: Short factual summary (<=20 tokens)\n"
                        "- explanation: Detailed analysis (<=200 tokens)\n"
                        "- evidence: List of data points supporting the insight\n"
                        "- recommendation: Actionable suggestion based on findings\n"
                        "- key_metric: Name of the highlighted metric\n"
                        "- key_value: Numeric value of the key metric\n"
                        "- confidence: Confidence score 0-1"
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            try:
                response = self.llm.complete_json(
                    messages=messages,
                    temperature=0.5,
                    operation_name="generate_insight",
                )
            except Exception as e:
                raise InsightGenerationError(
                    f"LLM call failed for {chart_type}: {e}"
                ) from e

            try:
                data = json.loads(response)
            except json.JSONDecodeError as e:
                raise InsightGenerationError(
                    f"Invalid JSON response for {chart_type}: {e}"
                ) from e

            # Build insight with defaults for missing fields
            insight = ChartInsight(
                simulation_id=simulation_id,
                chart_type=chart_type,
                caption=data.get("caption", "Analysis pending"),
                explanation=data.get(
                    "explanation", "Detailed analysis is being generated."
                ),
                evidence=data.get("evidence", []),
                recommendation=data.get("recommendation"),
                confidence=float(data.get("confidence", 0.8)),
            )

            # Cache the insight
            self._cache_insight(simulation_id, chart_type, insight)

            self.logger.info(
                f"Generated insight for {simulation_id}/{chart_type}: {insight.caption}"
            )

            return insight

    def _build_caption_prompt(
        self,
        chart_type: ChartType,
        chart_data: dict[str, Any],
    ) -> str:
        """Build prompt for caption generation."""
        data_str = json.dumps(chart_data, indent=2, default=str)

        return f"""
Generate a short caption (maximum 20 tokens) for this {chart_type} chart.

## Chart Data
{data_str}

Return JSON:
{{"caption": "...", "key_metric": "...", "key_value": 0.0, "confidence": 0.9}}
"""

    def _build_insight_prompt(
        self,
        chart_type: ChartType,
        chart_data: dict[str, Any],
    ) -> str:
        """Build prompt for full insight generation."""
        data_str = json.dumps(chart_data, indent=2, default=str)

        chart_descriptions = {
            "try_vs_success": "quadrant chart showing try rate vs success rate",
            "distribution": "histogram showing distribution of values",
            "sankey": "flow diagram showing user journey transitions",
            "failure_heatmap": "heatmap showing failure patterns",
            "scatter": "scatter plot showing correlation between variables",
            "tornado": "tornado chart showing sensitivity analysis",
            "box_plot": "box plot showing value distributions by category",
            "clustering": "cluster visualization showing user segments",
            "outliers": "outlier detection chart highlighting anomalies",
            "shap_summary": "SHAP summary showing feature importance",
            "pdp": "partial dependence plot showing feature effects",
        }

        chart_desc = chart_descriptions.get(chart_type, f"{chart_type} visualization")

        return f"""
Analyze this {chart_desc} and provide a comprehensive insight.

## Chart Type
{chart_type}

## Chart Data
{data_str}

## Requirements
1. Caption: Maximum 20 tokens, factual, highlights key finding
2. Explanation: Maximum 200 tokens, detailed analysis
3. Evidence: List of specific data points (numbers, percentages)
4. Recommendation: Actionable suggestion for product team

Return JSON:
{{
    "caption": "...",
    "explanation": "...",
    "evidence": ["point 1", "point 2", ...],
    "recommendation": "...",
    "key_metric": "...",
    "key_value": 0.0,
    "confidence": 0.9
}}
"""

    def _get_cached_insight(
        self,
        simulation_id: str,
        chart_type: ChartType,
    ) -> ChartInsight | None:
        """Get cached insight if available."""
        if simulation_id not in self._cache:
            return None
        return self._cache[simulation_id].get(chart_type)

    def _cache_insight(
        self,
        simulation_id: str,
        chart_type: ChartType,
        insight: ChartInsight,
    ) -> None:
        """Cache an insight."""
        if simulation_id not in self._cache:
            self._cache[simulation_id] = {}
        self._cache[simulation_id][chart_type] = insight

    def clear_cache(self, simulation_id: str | None = None) -> None:
        """
        Clear insight cache.

        Args:
            simulation_id: If provided, clear only for this simulation.
                          If None, clear all cached insights.
        """
        if simulation_id is not None:
            if simulation_id in self._cache:
                del self._cache[simulation_id]
        else:
            self._cache.clear()

    def get_all_insights(self, simulation_id: str) -> SimulationInsights:
        """
        Get all cached insights for a simulation.

        Args:
            simulation_id: Simulation identifier

        Returns:
            SimulationInsights with all available insights
        """
        insights = self._cache.get(simulation_id, {})

        return SimulationInsights(
            simulation_id=simulation_id,
            insights=insights,
            total_charts_analyzed=len(insights),
        )

    def generate_executive_summary(self, simulation_id: str) -> str | None:
        """
        Generate executive summary across all insights.

        Args:
            simulation_id: Simulation identifier

        Returns:
            Executive summary text, or None if no insights available
        """
        with _tracer.start_as_current_span(
            "InsightService: generate_executive_summary",
            attributes={"simulation_id": simulation_id},
        ):
            insights = self._cache.get(simulation_id, {})

            if not insights:
                return None

            # Build summary of all insights
            insights_summary = []
            for chart_type, insight in insights.items():
                insights_summary.append(
                    f"- {chart_type}: {insight.caption}"
                )

            insights_text = "\n".join(insights_summary)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a senior UX research analyst. Synthesize the chart insights "
                        "into a concise executive summary (maximum 100 words) that highlights "
                        "the most important findings and prioritized recommendations."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""
Create an executive summary for this simulation analysis:

## Chart Insights
{insights_text}

## Full Details
{json.dumps({ct: {"caption": i.caption, "recommendation": i.recommendation}
             for ct, i in insights.items()}, indent=2)}

Provide a concise summary highlighting key findings and top priority recommendations.
""",
                },
            ]

            response = self.llm.complete(
                messages=messages,
                temperature=0.5,
                operation_name="generate_executive_summary",
            )

            self.logger.info(f"Generated executive summary for {simulation_id}")

            # Update the SimulationInsights in cache with summary
            if simulation_id in self._cache:
                # We don't update cache here since SimulationInsights is generated on-demand
                pass

            return response


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys
    from unittest.mock import MagicMock

    print("=== InsightService Validation ===\n")

    all_validation_failures: list[str] = []
    total_tests = 0

    # Create mock LLM client
    mock_llm = MagicMock()

    # Test 1: Service instantiation
    total_tests += 1
    try:
        service = InsightService(llm_client=mock_llm)
        if service.llm is not mock_llm:
            all_validation_failures.append("Service should use provided LLM client")
        else:
            print("Test 1 PASSED: Service instantiation works correctly")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Test 2: Prompt building for try_vs_success
    total_tests += 1
    try:
        prompt = service._build_insight_prompt(
            chart_type="try_vs_success",
            chart_data={"quadrants": {"strugglers": {"percentage": 42.0}}},
        )
        if "try_vs_success" not in prompt.lower() and "quadrant" not in prompt.lower():
            all_validation_failures.append("Prompt should reference chart type")
        elif "20 token" not in prompt.lower():
            all_validation_failures.append("Prompt should mention token limits")
        elif "json" not in prompt.lower():
            all_validation_failures.append("Prompt should request JSON output")
        else:
            print("Test 2 PASSED: Insight prompt built correctly")
    except Exception as e:
        all_validation_failures.append(f"Prompt building failed: {e}")

    # Test 3: Caption prompt building
    total_tests += 1
    try:
        prompt = service._build_caption_prompt(
            chart_type="clustering",
            chart_data={"n_clusters": 3},
        )
        if "clustering" not in prompt.lower():
            all_validation_failures.append("Caption prompt should include chart type")
        elif "20 token" not in prompt.lower():
            all_validation_failures.append("Caption prompt should mention token limit")
        else:
            print("Test 3 PASSED: Caption prompt built correctly")
    except Exception as e:
        all_validation_failures.append(f"Caption prompt building failed: {e}")

    # Test 4: Cache operations
    total_tests += 1
    try:
        # Manually cache an insight
        test_insight = ChartInsight(
            simulation_id="sim_test",
            chart_type="try_vs_success",
            caption="Test caption",
            explanation="Test explanation",
        )
        service._cache_insight("sim_test", "try_vs_success", test_insight)

        # Retrieve from cache
        cached = service._get_cached_insight("sim_test", "try_vs_success")
        if cached is None:
            all_validation_failures.append("Cache should return stored insight")
        elif cached.caption != "Test caption":
            all_validation_failures.append("Cached insight caption mismatch")
        else:
            print("Test 4 PASSED: Cache operations work correctly")
    except Exception as e:
        all_validation_failures.append(f"Cache operations failed: {e}")

    # Test 5: Clear cache for simulation
    total_tests += 1
    try:
        service._cache_insight("sim_1", "sankey", test_insight)
        service._cache_insight("sim_2", "clustering", test_insight)

        service.clear_cache(simulation_id="sim_1")

        if service._get_cached_insight("sim_1", "sankey") is not None:
            all_validation_failures.append("sim_1 cache should be cleared")
        elif service._get_cached_insight("sim_2", "clustering") is None:
            all_validation_failures.append("sim_2 cache should remain")
        else:
            print("Test 5 PASSED: Selective cache clear works correctly")
    except Exception as e:
        all_validation_failures.append(f"Cache clear failed: {e}")

    # Test 6: Get all insights
    total_tests += 1
    try:
        service.clear_cache()
        service._cache_insight(
            "sim_all",
            "try_vs_success",
            ChartInsight(
                simulation_id="sim_all",
                chart_type="try_vs_success",
                caption="Cap 1",
                explanation="Exp 1",
            ),
        )
        service._cache_insight(
            "sim_all",
            "clustering",
            ChartInsight(
                simulation_id="sim_all",
                chart_type="clustering",
                caption="Cap 2",
                explanation="Exp 2",
            ),
        )

        result = service.get_all_insights("sim_all")
        if not isinstance(result, SimulationInsights):
            all_validation_failures.append("Should return SimulationInsights")
        elif len(result.insights) != 2:
            all_validation_failures.append(f"Should have 2 insights, got {len(result.insights)}")
        elif result.total_charts_analyzed != 2:
            all_validation_failures.append("total_charts_analyzed should be 2")
        else:
            print("Test 6 PASSED: Get all insights works correctly")
    except Exception as e:
        all_validation_failures.append(f"Get all insights failed: {e}")

    # Test 7: Empty simulation insights
    total_tests += 1
    try:
        result = service.get_all_insights("nonexistent")
        if result.simulation_id != "nonexistent":
            all_validation_failures.append("Should have correct simulation_id")
        elif len(result.insights) != 0:
            all_validation_failures.append("Should have 0 insights for nonexistent sim")
        else:
            print("Test 7 PASSED: Empty simulation returns empty insights")
    except Exception as e:
        all_validation_failures.append(f"Empty simulation test failed: {e}")

    # Test 8: Executive summary with no insights
    total_tests += 1
    try:
        service.clear_cache()
        summary = service.generate_executive_summary("empty_sim")
        if summary is not None:
            all_validation_failures.append("Should return None for empty simulation")
        elif mock_llm.complete.called:
            all_validation_failures.append("Should not call LLM for empty simulation")
        else:
            print("Test 8 PASSED: Executive summary handles empty simulation")
    except Exception as e:
        all_validation_failures.append(f"Executive summary empty test failed: {e}")

    # Final result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print(
            "\nNote: Actual LLM calls require OPENAI_API_KEY and are not tested in validation"
        )
        sys.exit(0)
