"""
Unit tests for ExecutiveSummaryService.

Tests LLM-powered executive summary generation from multiple insights.

References:
    - Service: src/synth_lab/services/executive_summary_service.py
    - Entity: src/synth_lab/domain/entities/executive_summary.py
    - Spec: specs/023-quantitative-ai-insights/spec.md
"""

from unittest.mock import MagicMock, patch

import pytest

from synth_lab.domain.entities.chart_insight import ChartInsight
from synth_lab.domain.entities.executive_summary import ExecutiveSummary
from synth_lab.services.executive_summary_service import ExecutiveSummaryService


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_cache_repo():
    """Mock cache repository for testing."""
    repo = MagicMock()
    return repo


@pytest.fixture
def summary_service(mock_llm_client, mock_cache_repo):
    """Create ExecutiveSummaryService with mocked dependencies."""
    return ExecutiveSummaryService(llm_client=mock_llm_client, cache_repo=mock_cache_repo)


@pytest.fixture
def sample_insights():
    """Sample chart insights for summary generation."""
    return [
        ChartInsight(
            analysis_id="ana_12345678",
            chart_type="try_vs_success",
            problem_understanding="Testing checkout flow",
            trends_observed="80% try rate, 50% success rate",
            key_findings=["High engagement", "Moderate conversion"],
            summary="Checkout has good engagement but needs conversion improvement",
            status="completed",
        ),
        ChartInsight(
            analysis_id="ana_12345678",
            chart_type="shap_summary",
            problem_understanding="Understanding feature importance",
            trends_observed="Trust and capability are top drivers",
            key_findings=["Trust is #1 driver", "Digital literacy matters"],
            summary="User trust and capability strongly influence success",
            status="completed",
        ),
        ChartInsight(
            analysis_id="ana_12345678",
            chart_type="pca_scatter",
            problem_understanding="Identifying user segments",
            trends_observed="3 distinct behavioral clusters",
            key_findings=["Cluster 1: high success", "Cluster 2: low trust"],
            summary="Clear segmentation shows diverse user needs",
            status="completed",
        ),
    ]


class TestBuildSynthesisPrompt:
    """Test _build_synthesis_prompt method."""

    def test_builds_prompt_from_multiple_insights(self, summary_service, sample_insights):
        """Should build synthesis prompt from all insights."""
        prompt = summary_service._build_synthesis_prompt(sample_insights)

        assert isinstance(prompt, str)
        assert len(prompt) > 200  # Should be substantial
        # Should reference multiple charts
        assert "try_vs_success" in prompt or "Try vs Success" in prompt
        assert "shap" in prompt or "SHAP" in prompt
        assert "pca" in prompt or "PCA" in prompt

    def test_prompt_includes_all_insight_content(self, summary_service, sample_insights):
        """Should include key findings from all insights."""
        prompt = summary_service._build_synthesis_prompt(sample_insights)

        # Should include findings from insights
        assert "engagement" in prompt.lower() or "conversion" in prompt.lower()
        assert "trust" in prompt.lower() or "capability" in prompt.lower()

    def test_handles_minimum_insights(self, summary_service):
        """Should handle minimum number of insights (3)."""
        min_insights = [
            ChartInsight(
                analysis_id="ana_12345678",
                chart_type=f"chart_{i}",
                problem_understanding="Test",
                trends_observed="Test",
                key_findings=["Finding 1", "Finding 2"],
                summary="Test summary",
                status="completed",
            )
            for i in range(3)
        ]

        prompt = summary_service._build_synthesis_prompt(min_insights)
        assert len(prompt) > 100


class TestGenerateSummary:
    """Test generate_summary main method."""

    @patch("synth_lab.services.executive_summary_service.ExecutiveSummaryService._build_synthesis_prompt")
    def test_generates_summary_from_insights(
        self, mock_build_prompt, summary_service, sample_insights
    ):
        """Should orchestrate prompt building, LLM call, parsing, and storage."""
        analysis_id = "ana_12345678"

        # Setup mocks
        mock_build_prompt.return_value = "Synthesize these insights..."
        mock_llm_response = {
            "overview": "Tested checkout with 500 synths, 50% success rate",
            "explainability": "Trust and capability are main drivers",
            "segmentation": "3 distinct user groups identified",
            "edge_cases": "High-capability users failing unexpectedly",
            "recommendations": [
                "Add trust signals to checkout",
                "Simplify flow for low-literacy users",
            ],
        }
        summary_service.llm.complete_json.return_value = mock_llm_response
        summary_service.cache_repo.get_all_chart_insights.return_value = sample_insights

        # Execute
        result = summary_service.generate_summary(analysis_id)

        # Verify
        summary_service.cache_repo.get_all_chart_insights.assert_called_once_with(analysis_id)
        mock_build_prompt.assert_called_once_with(sample_insights)
        summary_service.llm.complete_json.assert_called_once()
        assert isinstance(result, ExecutiveSummary)
        assert result.analysis_id == analysis_id
        assert result.status == "completed"
        assert len(result.recommendations) == 2
        assert len(result.included_chart_types) == 3

    def test_handles_partial_insights(self, summary_service):
        """Should handle case where some insights failed."""
        analysis_id = "ana_12345678"
        partial_insights = [
            ChartInsight(
                analysis_id=analysis_id,
                chart_type="try_vs_success",
                problem_understanding="Test",
                trends_observed="Test",
                key_findings=["F1", "F2"],
                summary="Test",
                status="completed",
            ),
            ChartInsight(
                analysis_id=analysis_id,
                chart_type="shap_summary",
                problem_understanding="Test",
                trends_observed="Test",
                key_findings=["F1", "F2"],
                summary="Test",
                status="failed",  # Failed insight
            ),
            ChartInsight(
                analysis_id=analysis_id,
                chart_type="pca_scatter",
                problem_understanding="Test",
                trends_observed="Test",
                key_findings=["F1", "F2"],
                summary="Test",
                status="completed",
            ),
            ChartInsight(
                analysis_id=analysis_id,
                chart_type="radar_comparison",
                problem_understanding="Test",
                trends_observed="Test",
                key_findings=["F1", "F2"],
                summary="Test",
                status="completed",
            ),
        ]

        summary_service.cache_repo.get_all_chart_insights.return_value = partial_insights
        summary_service.llm.complete_json.return_value = {
            "overview": "Test",
            "explainability": "Test",
            "segmentation": "Test",
            "edge_cases": "Test",
            "recommendations": ["R1", "R2"],
        }

        result = summary_service.generate_summary(analysis_id)

        # Should still generate summary with status "partial"
        assert result.status == "partial"
        assert len(result.included_chart_types) == 3  # Only completed ones

    def test_fails_with_too_few_insights(self, summary_service):
        """Should fail if less than 3 completed insights."""
        analysis_id = "ana_12345678"
        too_few_insights = [
            ChartInsight(
                analysis_id=analysis_id,
                chart_type="try_vs_success",
                problem_understanding="Test",
                trends_observed="Test",
                key_findings=["F1", "F2"],
                summary="Test",
                status="completed",
            ),
            ChartInsight(
                analysis_id=analysis_id,
                chart_type="shap_summary",
                problem_understanding="Test",
                trends_observed="Test",
                key_findings=["F1", "F2"],
                summary="Test",
                status="completed",
            ),
        ]

        summary_service.cache_repo.get_all_chart_insights.return_value = too_few_insights

        with pytest.raises(ValueError, match="at least 3"):
            summary_service.generate_summary(analysis_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
