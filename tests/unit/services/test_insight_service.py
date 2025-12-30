"""
Unit tests for InsightService.

Tests LLM-powered insight generation for individual charts.

References:
    - Service: src/synth_lab/services/insight_service.py
    - Entity: src/synth_lab/domain/entities/chart_insight.py
    - Spec: specs/023-quantitative-ai-insights/spec.md
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from synth_lab.domain.entities.chart_insight import ChartInsight
from synth_lab.services.insight_service import InsightService


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
def mock_analysis_repo():
    """Mock analysis repository for testing."""
    repo = MagicMock()
    return repo


@pytest.fixture
def mock_experiment_repo():
    """Mock experiment repository for testing."""
    repo = MagicMock()
    return repo


@pytest.fixture
def insight_service(mock_llm_client, mock_cache_repo, mock_analysis_repo, mock_experiment_repo):
    """Create InsightService with mocked dependencies."""
    return InsightService(
        llm_client=mock_llm_client,
        cache_repo=mock_cache_repo,
        analysis_repo=mock_analysis_repo,
        experiment_repo=mock_experiment_repo,
    )


@pytest.fixture
def sample_try_vs_success_data():
    """Sample Try vs Success chart data."""
    return {
        "quadrants": [
            {"type": "did_not_try", "count": 100, "rate": 0.2},
            {"type": "tried_failed", "count": 150, "rate": 0.3},
            {"type": "tried_succeeded", "count": 250, "rate": 0.5},
        ],
        "total_synths": 500,
    }


class TestBuildPromptTryVsSuccess:
    """Test _build_prompt_try_vs_success method."""

    def test_builds_prompt_with_chart_data(self, insight_service, sample_try_vs_success_data):
        """Should build prompt including chart data, hypothesis, and instructions."""
        hypothesis = "Usuários com alta capacidade terão maior taxa de sucesso"
        prompt = insight_service._build_prompt_try_vs_success(
            sample_try_vs_success_data, hypothesis
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial
        assert "Tentativa vs Sucesso" in prompt
        # Should include hypothesis
        assert hypothesis in prompt
        # Should request Portuguese output
        assert "PORTUGUÊS BRASILEIRO" in prompt

    def test_prompt_includes_output_format(self, insight_service, sample_try_vs_success_data):
        """Should specify JSON output format with resumo_key_findings."""
        hypothesis = "Test hypothesis"
        prompt = insight_service._build_prompt_try_vs_success(
            sample_try_vs_success_data, hypothesis
        )

        # Should request structured JSON output
        assert "JSON" in prompt
        assert "resumo_key_findings" in prompt


class TestBuildPromptForChartType:
    """Test _build_prompt_for_chart_type dispatcher."""

    def test_dispatches_to_correct_builder(self, insight_service):
        """Should call correct builder for each chart type."""
        chart_data = {"test": "data"}
        hypothesis = "Test hypothesis"

        # All supported chart types should work
        supported_types = [
            "try_vs_success",
            "shap_summary",
            "extreme_cases",
            "outliers",
            "pca_scatter",
            "radar_comparison",
        ]

        for chart_type in supported_types:
            prompt = insight_service._build_prompt_for_chart_type(
                chart_type, chart_data, hypothesis
            )
            assert isinstance(prompt, str)
            assert len(prompt) > 100
            assert "resumo_key_findings" in prompt

    def test_raises_for_unknown_chart_type(self, insight_service):
        """Should raise ValueError for unknown chart type."""
        with pytest.raises(ValueError, match="Unknown chart type"):
            insight_service._build_prompt_for_chart_type(
                "unknown_chart", {}, "hypothesis"
            )


class TestGenerateInsight:
    """Test generate_insight main method (integration with LLM)."""

    def test_generates_insight_for_try_vs_success(
        self, insight_service, sample_try_vs_success_data
    ):
        """Should orchestrate prompt building, LLM call, and storage."""
        analysis_id = "ana_12345678"
        chart_type = "try_vs_success"

        # Mock hypothesis lookup (returns empty for simplicity)
        insight_service.analysis_repo.get_by_id.return_value = None

        # Mock LLM response as JSON string
        mock_llm_response = json.dumps({
            "problem_understanding": "Testing feature adoption",
            "trends_observed": "High engagement, moderate success",
            "resumo_key_findings": "O teste revelou que 50% dos usuários conseguiram completar a tarefa.",
        })
        insight_service.llm.complete_json.return_value = mock_llm_response

        # Execute
        result = insight_service.generate_insight(
            analysis_id, chart_type, sample_try_vs_success_data
        )

        # Verify
        assert isinstance(result, ChartInsight)
        assert result.analysis_id == analysis_id
        assert result.chart_type == chart_type
        assert result.status == "completed"
        assert "50% dos usuários" in result.summary
        insight_service.llm.complete_json.assert_called_once()
        insight_service.cache_repo.store_chart_insight.assert_called_once()

    def test_marks_insight_as_failed_on_llm_error(self, insight_service):
        """Should create failed insight if LLM call fails."""
        analysis_id = "ana_12345678"
        chart_type = "shap_summary"
        chart_data = {"features": []}

        # Mock hypothesis lookup
        insight_service.analysis_repo.get_by_id.return_value = None

        # Simulate LLM failure
        insight_service.llm.complete_json.side_effect = Exception("LLM API error")

        result = insight_service.generate_insight(analysis_id, chart_type, chart_data)

        assert isinstance(result, ChartInsight)
        assert result.status == "failed"
        assert result.analysis_id == analysis_id
        assert result.chart_type == chart_type
        assert "Falha ao gerar insight" in result.summary

    def test_uses_summary_fallback_if_resumo_missing(self, insight_service):
        """Should fallback to 'summary' field if 'resumo_key_findings' is missing."""
        analysis_id = "ana_12345678"
        chart_type = "try_vs_success"
        chart_data = {"test": "data"}

        # Mock hypothesis lookup
        insight_service.analysis_repo.get_by_id.return_value = None

        # Mock LLM response without resumo_key_findings
        mock_llm_response = json.dumps({
            "problem_understanding": "Test",
            "trends_observed": "Test",
            "summary": "Fallback summary text",
        })
        insight_service.llm.complete_json.return_value = mock_llm_response

        result = insight_service.generate_insight(analysis_id, chart_type, chart_data)

        assert result.status == "completed"
        assert result.summary == "Fallback summary text"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
