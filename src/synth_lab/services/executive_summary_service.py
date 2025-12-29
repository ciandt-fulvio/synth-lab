"""
ExecutiveSummaryService for AI-generated executive summaries.

Synthesizes multiple chart insights into a comprehensive executive summary
using o1-mini reasoning model. Aggregates insights across all chart types
to provide strategic recommendations.

References:
    - Entity: src/synth_lab/domain/entities/executive_summary.py
    - Entity: src/synth_lab/domain/entities/chart_insight.py
    - Repository: src/synth_lab/repositories/analysis_cache_repository.py
    - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 2, 3)
    - Config: src/synth_lab/infrastructure/config.py (REASONING_MODEL)

Sample usage:
    from synth_lab.services.executive_summary_service import ExecutiveSummaryService

    service = ExecutiveSummaryService()
    summary = service.generate_summary("ana_12345678")

Expected output:
    ExecutiveSummary with overview, explainability, segmentation, edge_cases, and recommendations
"""

from loguru import logger

from synth_lab.domain.entities.chart_insight import ChartInsight
from synth_lab.domain.entities.executive_summary import ExecutiveSummary
from synth_lab.infrastructure.config import REASONING_MODEL
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.analysis_cache_repository import AnalysisCacheRepository

_tracer = get_tracer()


class ExecutiveSummaryService:
    """Service for generating AI-powered executive summaries."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        cache_repo: AnalysisCacheRepository | None = None,
    ):
        """
        Initialize ExecutiveSummaryService.

        Args:
            llm_client: LLM client for reasoning. Defaults to singleton.
            cache_repo: Cache repository for persistence. Defaults to new instance.
        """
        self.llm = llm_client or get_llm_client()
        self.cache_repo = cache_repo or AnalysisCacheRepository()
        self.logger = logger.bind(component="executive_summary_service")

    def generate_summary(self, analysis_id: str) -> ExecutiveSummary:
        """
        Generate executive summary from all chart insights.

        Requires at least 3 completed insights to generate a meaningful summary.
        If some insights failed, creates a "partial" summary.

        Args:
            analysis_id: Analysis ID (e.g., "ana_12345678")

        Returns:
            ExecutiveSummary with status="completed", "partial", or "failed"

        Raises:
            ValueError: If less than 3 completed insights available
        """
        with _tracer.start_as_current_span("generate_executive_summary"):
            try:
                # Retrieve all insights
                all_insights = self.cache_repo.get_all_chart_insights(analysis_id)
                completed_insights = [i for i in all_insights if i.status == "completed"]

                # Validate minimum insights
                if len(completed_insights) < 3:
                    raise ValueError(
                        f"Need at least 3 completed insights to generate summary, got {len(completed_insights)}"
                    )

                # Build synthesis prompt
                prompt = self._build_synthesis_prompt(completed_insights)

                # Call LLM with reasoning model
                self.logger.info(
                    f"Generating executive summary for {analysis_id} from {len(completed_insights)} insights"
                )
                llm_response = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    model=REASONING_MODEL,
                )

                # Determine status (partial if some insights failed)
                status = "partial" if len(completed_insights) < len(all_insights) else "completed"

                # Parse response into ExecutiveSummary
                summary = ExecutiveSummary(
                    analysis_id=analysis_id,
                    overview=llm_response["overview"],
                    explainability=llm_response["explainability"],
                    segmentation=llm_response["segmentation"],
                    edge_cases=llm_response["edge_cases"],
                    recommendations=llm_response["recommendations"],
                    included_chart_types=[i.chart_type for i in completed_insights],
                    status=status,
                    model=REASONING_MODEL,
                )

                # Store in cache
                self.cache_repo.store_executive_summary(summary)
                self.logger.info(f"Executive summary generated: {summary.status}")

                return summary

            except ValueError:
                raise  # Re-raise validation errors
            except Exception as e:
                self.logger.error(f"Failed to generate executive summary: {e}")
                # Create failed summary
                failed_summary = ExecutiveSummary(
                    analysis_id=analysis_id,
                    overview="Failed to generate summary",
                    explainability="Error occurred during generation",
                    segmentation="Summary generation failed",
                    edge_cases="Error details: " + str(e),
                    recommendations=["Review error logs", "Retry summary generation"],
                    included_chart_types=[],
                    status="failed",
                    model=REASONING_MODEL,
                )
                self.cache_repo.store_executive_summary(failed_summary)
                return failed_summary

    def _build_synthesis_prompt(self, insights: list[ChartInsight]) -> str:
        """
        Build LLM prompt to synthesize multiple insights.

        Args:
            insights: List of completed chart insights

        Returns:
            Formatted synthesis prompt
        """
        # Group insights by category
        overview_charts = ["try_vs_success"]
        explainability_charts = ["shap_summary", "pdp"]
        segmentation_charts = ["pca_scatter", "radar_comparison"]
        edge_case_charts = ["extreme_cases", "outliers"]

        insights_by_category = {
            "overview": [i for i in insights if i.chart_type in overview_charts],
            "explainability": [i for i in insights if i.chart_type in explainability_charts],
            "segmentation": [i for i in insights if i.chart_type in segmentation_charts],
            "edge_cases": [i for i in insights if i.chart_type in edge_case_charts],
        }

        # Build insight summaries
        insight_texts = []
        for insight in insights:
            insight_text = f"""
**Chart: {insight.chart_type}**
- Problem: {insight.problem_understanding}
- Trends: {insight.trends_observed}
- Key Findings:
{chr(10).join(f"  • {finding}" for finding in insight.key_findings)}
- Summary: {insight.summary}
"""
            insight_texts.append(insight_text)

        all_insights_text = "\n".join(insight_texts)

        return f"""You are a UX researcher creating an executive summary from quantitative analysis insights.

**Your Task:**
Synthesize the following {len(insights)} chart insights into a comprehensive executive summary for product stakeholders.

**All Chart Insights:**
{all_insights_text}

**Required Output (JSON format):**
{{
  "overview": "What was tested and overall results (≤200 words). Synthesize insights from Try vs Success and overall outcome distribution.",
  "explainability": "Key drivers and feature impacts (≤200 words). Synthesize SHAP and PDP insights about what influences success.",
  "segmentation": "User groups and behavioral patterns (≤200 words). Synthesize PCA and radar insights about user segments.",
  "edge_cases": "Surprises, anomalies, unexpected findings (≤200 words). Synthesize extreme cases and outlier insights.",
  "recommendations": [
    "First actionable recommendation for product team (based on cross-cutting insights)",
    "Second actionable recommendation",
    "Third recommendation (optional - only if strongly supported by insights)"
  ]
}}

**Guidelines:**
- 2-3 recommendations required (not 4+)
- Synthesize across insights - don't just list individual findings
- Focus on strategic implications for product decisions
- Prioritize recommendations by impact and feasibility
- Identify patterns that emerge across multiple chart types
- Highlight the most important insight from each category
- Make recommendations concrete and actionable

**Example Quality:**
- ❌ BAD: "Users struggle with the feature" → Too vague
- ✅ GOOD: "30% failure rate concentrated among low-trust users (SHAP #1 driver). Recommendation: Add visible security badges to checkout flow."

**Cross-Insight Synthesis:**
- Connect findings across charts (e.g., if SHAP shows trust matters AND extreme cases show high-capability failures, the issue might be security perception, not actual security)
- Identify which user segments (from PCA) align with which feature importance patterns (from SHAP)
- Prioritize recommendations based on segment size × success impact
"""

if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Service instantiation
    total_tests += 1
    try:
        service = ExecutiveSummaryService()
        if service.llm is None:
            all_validation_failures.append("LLM client not initialized")
        if service.cache_repo is None:
            all_validation_failures.append("Cache repository not initialized")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Test 2: Prompt building
    total_tests += 1
    try:
        service = ExecutiveSummaryService()
        sample_insights = [
            ChartInsight(
                analysis_id="ana_12345678",
                chart_type=f"chart_{i}",
                problem_understanding=f"Problem {i}",
                trends_observed=f"Trends {i}",
                key_findings=[f"F{i}1", f"F{i}2"],
                summary=f"Summary {i}",
                status="completed",
            )
            for i in range(3)
        ]
        prompt = service._build_synthesis_prompt(sample_insights)
        if len(prompt) < 200:
            all_validation_failures.append("Synthesis prompt too short")
        if "overview" not in prompt or "recommendations" not in prompt:
            all_validation_failures.append("Prompt missing required sections")
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
        print("ExecutiveSummaryService is validated and ready for use")
        sys.exit(0)
