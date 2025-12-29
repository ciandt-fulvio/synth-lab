"""
InsightService for AI-generated chart insights.

Generates LLM-powered insights for individual chart types using o1-mini reasoning model.
Stores results in analysis_cache table for retrieval by frontend.

References:
    - Entity: src/synth_lab/domain/entities/chart_insight.py
    - Repository: src/synth_lab/repositories/analysis_cache_repository.py
    - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 1, 3)
    - Config: src/synth_lab/infrastructure/config.py (REASONING_MODEL)

Sample usage:
    from synth_lab.services.insight_service import InsightService

    service = InsightService()
    chart_data = {"quadrants": [...], "total_synths": 500}
    insight = service.generate_insight("ana_12345678", "try_vs_success", chart_data)

Expected output:
    ChartInsight with problem_understanding, trends_observed, key_findings, and summary
"""

from typing import Any

from loguru import logger

from synth_lab.domain.entities.chart_insight import ChartInsight
from synth_lab.infrastructure.config import REASONING_MODEL
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.analysis_cache_repository import AnalysisCacheRepository

_tracer = get_tracer()


class InsightService:
    """Service for generating AI-powered chart insights."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        cache_repo: AnalysisCacheRepository | None = None,
    ):
        """
        Initialize InsightService.

        Args:
            llm_client: LLM client for reasoning. Defaults to singleton.
            cache_repo: Cache repository for persistence. Defaults to new instance.
        """
        self.llm = llm_client or get_llm_client()
        self.cache_repo = cache_repo or AnalysisCacheRepository()
        self.logger = logger.bind(component="insight_service")

    def generate_insight(
        self,
        analysis_id: str,
        chart_type: str,
        chart_data: dict[str, Any],
    ) -> ChartInsight:
        """
        Generate insight for a specific chart type.

        Uses LLM to analyze chart data and produce structured insight.
        Stores result in cache for retrieval.

        Args:
            analysis_id: Analysis ID (e.g., "ana_12345678")
            chart_type: Chart type (e.g., "try_vs_success", "shap_summary")
            chart_data: Chart data to analyze

        Returns:
            ChartInsight with status="completed" or status="failed"
        """
        with _tracer.start_as_current_span(f"generate_insight_{chart_type}"):
            try:
                # Build prompt based on chart type
                prompt = self._build_prompt_for_chart_type(chart_type, chart_data)

                # Call LLM with reasoning model
                self.logger.info(f"Generating insight for {chart_type} (analysis: {analysis_id})")
                llm_response = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    model=REASONING_MODEL,
                )

                # Parse response into ChartInsight
                insight = self._parse_insight_response(llm_response, analysis_id, chart_type)

                # Store in cache
                self.cache_repo.store_chart_insight(insight)
                self.logger.info(f"Insight generated for {chart_type}: {insight.status}")

                return insight

            except Exception as e:
                self.logger.error(f"Failed to generate insight for {chart_type}: {e}")
                # Create failed insight
                failed_insight = ChartInsight(
                    analysis_id=analysis_id,
                    chart_type=chart_type,
                    problem_understanding="Failed to generate insight",
                    trends_observed="Error occurred during generation",
                    key_findings=["Generation failed", str(e)],
                    summary="Insight generation failed due to error",
                    status="failed",
                )
                self.cache_repo.store_chart_insight(failed_insight)
                return failed_insight

    def _build_prompt_for_chart_type(self, chart_type: str, chart_data: dict[str, Any]) -> str:
        """
        Build LLM prompt for specific chart type.

        Args:
            chart_type: Type of chart
            chart_data: Chart data

        Returns:
            Formatted prompt string
        """
        prompt_builders = {
            "try_vs_success": self._build_prompt_try_vs_success,
            "shap_summary": self._build_prompt_shap_summary,
            "pdp": self._build_prompt_pdp,
            "pca_scatter": self._build_prompt_pca_scatter,
            "radar_comparison": self._build_prompt_radar_comparison,
            "extreme_cases": self._build_prompt_extreme_cases,
            "outliers": self._build_prompt_outliers,
        }

        builder = prompt_builders.get(chart_type)
        if builder is None:
            raise ValueError(f"Unknown chart type: {chart_type}")

        return builder(chart_data)

    def _build_prompt_try_vs_success(self, chart_data: dict[str, Any]) -> str:
        """Build prompt for Try vs Success chart."""
        return f"""Analyze this "Try vs Success" chart data and provide AI-generated insight.

**Chart Data:**
{chart_data}

**Your Task:**
You are a UX researcher analyzing quantitative data from a feature simulation. The "Try vs Success" chart shows:
- How many users attempted the feature (tried)
- How many succeeded after trying
- How many failed after trying
- How many didn't even try

**Required Output (JSON format):**
{{
  "problem_understanding": "Brief description of what is being tested (≤50 words)",
  "trends_observed": "Key patterns in the data - try rate, success rate, failure patterns (≤100 words)",
  "key_findings": [
    "First actionable insight for product team",
    "Second actionable insight",
    "Third insight (if applicable)",
    "Fourth insight (if applicable)"
  ],
  "summary": "Concise summary synthesizing the analysis (≤200 words)"
}}

**Guidelines:**
- 2-4 key findings required
- Focus on actionable insights for product decisions
- Explain what the numbers mean in human terms
- Identify concerning patterns or opportunities
"""

    def _build_prompt_shap_summary(self, chart_data: dict[str, Any]) -> str:
        """Build prompt for SHAP Summary chart."""
        return f"""Analyze this SHAP Summary chart data and provide AI-generated insight.

**Chart Data:**
{chart_data}

**Your Task:**
You are a data scientist explaining feature importance analysis. The SHAP Summary chart shows which user attributes most strongly influence success/failure.

**Required Output (JSON format):**
{{
  "problem_understanding": "What feature importance is being measured (≤50 words)",
  "trends_observed": "Top 3-5 most important features and their impact direction (≤100 words)",
  "key_findings": [
    "Insight about the most important feature",
    "Insight about surprising feature importance",
    "Actionable recommendation based on feature analysis",
    "Additional finding (if applicable)"
  ],
  "summary": "What this feature importance analysis tells us (≤200 words)"
}}

**Guidelines:**
- Explain SHAP values in non-technical terms
- Identify which features to prioritize in product design
- Highlight surprising or counterintuitive findings
"""

    def _build_prompt_pdp(self, chart_data: dict[str, Any]) -> str:
        """Build prompt for PDP (Partial Dependence Plot) chart."""
        return f"""Analyze this Partial Dependence Plot (PDP) data and provide AI-generated insight.

**Chart Data:**
{chart_data}

**Your Task:**
Explain how a specific feature affects success probability across its range of values.

**Required Output (JSON format):**
{{
  "problem_understanding": "Which feature-outcome relationship is being analyzed (≤50 words)",
  "trends_observed": "How the feature affects success probability - linear, threshold, optimal range (≤100 words)",
  "key_findings": [
    "Insight about optimal feature value range",
    "Insight about threshold effects or non-linear patterns",
    "Product recommendation based on this relationship",
    "Additional observation (if applicable)"
  ],
  "summary": "Synthesis of feature-outcome relationship (≤200 words)"
}}

**Guidelines:**
- Identify sweet spots, thresholds, or diminishing returns
- Recommend optimal feature value ranges
- Explain non-linear effects if present
"""

    def _build_prompt_pca_scatter(self, chart_data: dict[str, Any]) -> str:
        """Build prompt for PCA Scatter chart."""
        return f"""Analyze this PCA Scatter plot data and provide AI-generated insight.

**Chart Data:**
{chart_data}

**Your Task:**
Explain user segmentation patterns revealed by dimensionality reduction (PCA).

**Required Output (JSON format):**
{{
  "problem_understanding": "What user segmentation is being revealed (≤50 words)",
  "trends_observed": "How many clusters/segments, their characteristics, separation quality (≤100 words)",
  "key_findings": [
    "Insight about most distinct user segment",
    "Insight about segment overlap or confusion",
    "Product strategy recommendation for different segments",
    "Additional pattern (if applicable)"
  ],
  "summary": "What these user segments mean for product strategy (≤200 words)"
}}

**Guidelines:**
- Describe segments in behavioral terms, not technical PCA terms
- Identify which segments need different product experiences
- Highlight segment sizes and success rates
"""

    def _build_prompt_radar_comparison(self, chart_data: dict[str, Any]) -> str:
        """Build prompt for Radar Comparison chart."""
        return f"""Analyze this Radar Comparison chart and provide AI-generated insight.

**Chart Data:**
{chart_data}

**Your Task:**
Compare user cluster profiles across multiple dimensions (capability, motivation, trust, etc.).

**Required Output (JSON format):**
{{
  "problem_understanding": "What cluster profiles are being compared (≤50 words)",
  "trends_observed": "Key differences between clusters across dimensions (≤100 words)",
  "key_findings": [
    "Insight about cluster with highest success potential",
    "Insight about cluster needing most support",
    "Design recommendation to serve different cluster needs",
    "Additional comparison insight (if applicable)"
  ],
  "summary": "Strategic implications of cluster differences (≤200 words)"
}}

**Guidelines:**
- Compare clusters on actionable dimensions
- Identify which clusters to prioritize
- Recommend targeted interventions per cluster
"""

    def _build_prompt_extreme_cases(self, chart_data: dict[str, Any]) -> str:
        """Build prompt for Extreme Cases chart."""
        return f"""Analyze this Extreme Cases data and provide AI-generated insight.

**Chart Data:**
{chart_data}

**Your Task:**
Explain surprising or counterintuitive success/failure cases.

**Required Output (JSON format):**
{{
  "problem_understanding": "What extreme cases are being examined (≤50 words)",
  "trends_observed": "Patterns in unexpected successes and unexpected failures (≤100 words)",
  "key_findings": [
    "Insight from unexpected success cases",
    "Insight from unexpected failure cases",
    "Hypothesis about what makes these cases extreme",
    "Product implication (if applicable)"
  ],
  "summary": "What extreme cases reveal about feature design (≤200 words)"
}}

**Guidelines:**
- Focus on actionable insights from edge cases
- Identify feature design blind spots
- Suggest how to better serve extreme user profiles
"""

    def _build_prompt_outliers(self, chart_data: dict[str, Any]) -> str:
        """Build prompt for Outliers chart."""
        return f"""Analyze this Outliers data and provide AI-generated insight.

**Chart Data:**
{chart_data}

**Your Task:**
Identify and explain statistical outliers in user behavior.

**Required Output (JSON format):**
{{
  "problem_understanding": "What outlier behavior is being identified (≤50 words)",
  "trends_observed": "Characteristics of outlier users, outlier frequency (≤100 words)",
  "key_findings": [
    "Insight about what makes users outliers",
    "Insight about whether outliers should be addressed",
    "Design recommendation for outlier cases",
    "Additional pattern (if applicable)"
  ],
  "summary": "Strategic decision on handling outliers (≤200 words)"
}}

**Guidelines:**
- Distinguish between noise and meaningful outliers
- Recommend whether to design for outliers or focus on mainstream
- Identify potential data quality issues
"""

    def _parse_insight_response(
        self,
        llm_response: dict[str, Any],
        analysis_id: str,
        chart_type: str,
    ) -> ChartInsight:
        """
        Parse LLM JSON response into ChartInsight entity.

        Args:
            llm_response: LLM response dict
            analysis_id: Analysis ID
            chart_type: Chart type

        Returns:
            ChartInsight entity

        Raises:
            ValueError: If response is invalid
        """
        # Validate required fields
        required_fields = ["problem_understanding", "trends_observed", "key_findings", "summary"]
        missing = [f for f in required_fields if f not in llm_response]
        if missing:
            raise ValueError(f"Missing required fields in LLM response: {missing}")

        # Validate key_findings length
        key_findings = llm_response["key_findings"]
        if not isinstance(key_findings, list) or len(key_findings) < 2 or len(key_findings) > 4:
            raise ValueError(f"key_findings must be a list of 2-4 items, got {len(key_findings)}")

        return ChartInsight(
            analysis_id=analysis_id,
            chart_type=chart_type,
            problem_understanding=llm_response["problem_understanding"],
            trends_observed=llm_response["trends_observed"],
            key_findings=key_findings,
            summary=llm_response["summary"],
            status="completed",
            model=REASONING_MODEL,
            reasoning_trace=llm_response.get("reasoning_trace"),
        )


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Service instantiation
    total_tests += 1
    try:
        service = InsightService()
        if service.llm is None:
            all_validation_failures.append("LLM client not initialized")
        if service.cache_repo is None:
            all_validation_failures.append("Cache repository not initialized")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Test 2: Prompt building for all chart types
    total_tests += 1
    try:
        service = InsightService()
        chart_types = [
            "try_vs_success",
            "shap_summary",
            "pdp",
            "pca_scatter",
            "radar_comparison",
            "extreme_cases",
            "outliers",
        ]
        for chart_type in chart_types:
            prompt = service._build_prompt_for_chart_type(chart_type, {"test": "data"})
            if len(prompt) < 100:
                all_validation_failures.append(f"Prompt too short for {chart_type}")
    except Exception as e:
        all_validation_failures.append(f"Prompt building failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("InsightService is validated and ready for use")
        sys.exit(0)
