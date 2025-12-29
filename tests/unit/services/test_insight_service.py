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
def insight_service(mock_llm_client, mock_cache_repo):
    """Create InsightService with mocked dependencies."""
    return InsightService(llm_client=mock_llm_client, cache_repo=mock_cache_repo)


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
        """Should build prompt including chart data and instructions."""
        prompt = insight_service._build_prompt_try_vs_success(sample_try_vs_success_data)

        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial
        assert "Try vs Success" in prompt or "try_vs_success" in prompt
        # Should include data context
        assert "500" in prompt or "0.2" in prompt or "0.3" in prompt or "0.5" in prompt

    def test_prompt_includes_output_format(self, insight_service, sample_try_vs_success_data):
        """Should specify JSON output format."""
        prompt = insight_service._build_prompt_try_vs_success(sample_try_vs_success_data)

        # Should request structured output
        assert "JSON" in prompt or "json" in prompt or "problem_understanding" in prompt


class TestParseInsightResponse:
    """Test _parse_insight_response method."""

    def test_parses_valid_json_response(self, insight_service):
        """Should parse valid LLM JSON response into ChartInsight."""
        analysis_id = "ana_12345678"
        chart_type = "try_vs_success"
        llm_response = {
            "problem_understanding": "Testing checkout flow with 500 synths",
            "trends_observed": "High try rate (80%), moderate success rate (50%)",
            "key_findings": [
                "30% of users fail after trying",
                "20% don't even attempt the feature",
            ],
            "summary": "Checkout has decent engagement but conversion needs improvement",
        }

        insight = insight_service._parse_insight_response(
            llm_response, analysis_id, chart_type
        )

        assert isinstance(insight, ChartInsight)
        assert insight.analysis_id == analysis_id
        assert insight.chart_type == chart_type
        assert insight.problem_understanding == llm_response["problem_understanding"]
        assert len(insight.key_findings) == 2
        assert insight.status == "completed"

    def test_handles_missing_fields_gracefully(self, insight_service):
        """Should handle incomplete LLM response."""
        analysis_id = "ana_12345678"
        chart_type = "shap_summary"
        incomplete_response = {
            "problem_understanding": "Test",
            "trends_observed": "Test",
            # Missing key_findings and summary
        }

        with pytest.raises((KeyError, ValueError)):
            insight_service._parse_insight_response(
                incomplete_response, analysis_id, chart_type
            )

    def test_validates_key_findings_length(self, insight_service):
        """Should enforce 2-4 key findings requirement."""
        analysis_id = "ana_12345678"
        chart_type = "pdp"

        # Too few findings
        response_too_few = {
            "problem_understanding": "Test",
            "trends_observed": "Test",
            "key_findings": ["Only one"],  # Should be 2-4
            "summary": "Test",
        }

        with pytest.raises(ValueError):
            insight_service._parse_insight_response(response_too_few, analysis_id, chart_type)


class TestGenerateInsight:
    """Test generate_insight main method (integration with LLM)."""

    @patch("synth_lab.services.insight_service.InsightService._build_prompt_try_vs_success")
    @patch("synth_lab.services.insight_service.InsightService._parse_insight_response")
    def test_generates_insight_for_try_vs_success(
        self, mock_parse, mock_build_prompt, insight_service, sample_try_vs_success_data
    ):
        """Should orchestrate prompt building, LLM call, parsing, and storage."""
        analysis_id = "ana_12345678"
        chart_type = "try_vs_success"

        # Setup mocks
        mock_build_prompt.return_value = "Generated prompt for try_vs_success"
        mock_llm_response = {
            "problem_understanding": "Testing feature adoption",
            "trends_observed": "High engagement, moderate success",
            "key_findings": ["Finding 1", "Finding 2"],
            "summary": "Summary text",
        }
        insight_service.llm.complete_json.return_value = mock_llm_response

        expected_insight = ChartInsight(
            analysis_id=analysis_id,
            chart_type=chart_type,
            problem_understanding="Testing feature adoption",
            trends_observed="High engagement, moderate success",
            key_findings=["Finding 1", "Finding 2"],
            summary="Summary text",
            status="completed",
        )
        mock_parse.return_value = expected_insight

        # Execute
        result = insight_service.generate_insight(
            analysis_id, chart_type, sample_try_vs_success_data
        )

        # Verify
        mock_build_prompt.assert_called_once_with(sample_try_vs_success_data)
        insight_service.llm.complete_json.assert_called_once()
        mock_parse.assert_called_once_with(mock_llm_response, analysis_id, chart_type)
        insight_service.cache_repo.store_chart_insight.assert_called_once_with(expected_insight)
        assert result == expected_insight

    def test_marks_insight_as_failed_on_llm_error(self, insight_service):
        """Should create failed insight if LLM call fails."""
        analysis_id = "ana_12345678"
        chart_type = "shap_summary"
        chart_data = {"features": []}

        # Simulate LLM failure
        insight_service.llm.complete_json.side_effect = Exception("LLM API error")

        result = insight_service.generate_insight(analysis_id, chart_type, chart_data)

        assert isinstance(result, ChartInsight)
        assert result.status == "failed"
        assert result.analysis_id == analysis_id
        assert result.chart_type == chart_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
