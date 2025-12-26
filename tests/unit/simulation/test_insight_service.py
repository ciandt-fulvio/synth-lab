"""
Unit tests for InsightService.

Tests LLM-generated chart insights including:
- Caption generation (<=20 tokens)
- Full insight generation (caption + explanation + evidence + recommendation)
- In-memory caching
- Insight retrieval

References:
    - Entities: src/synth_lab/domain/entities/chart_insight.py
    - Spec: specs/017-analysis-ux-research/spec.md (US6)
    - Data Model: specs/017-analysis-ux-research/data-model.md
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from synth_lab.domain.entities.chart_insight import (
    ChartCaption,
    ChartInsight,
    ChartType,
    SimulationInsights,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = MagicMock()
    # Default response for caption generation
    client.complete.return_value = "42% of synths struggle with the feature"
    # Default response for JSON insight generation
    client.complete_json.return_value = json.dumps(
        {
            "caption": "42% of synths struggle with the feature",
            "explanation": "Nearly half of the synthetic users in this simulation "
            "encountered difficulties completing the feature task, "
            "suggesting significant usability barriers.",
            "evidence": [
                "42% in struggle quadrant (high try, low success)",
                "Average success rate: 0.35 for strugglers",
                "Most affected: low digital literacy users",
            ],
            "recommendation": "Consider adding progressive disclosure or "
            "contextual help to reduce cognitive load.",
            "key_metric": "struggle_percentage",
            "key_value": 42.0,
            "confidence": 0.92,
        }
    )
    return client


@pytest.fixture
def sample_chart_data_try_vs_success():
    """Sample chart data for try_vs_success quadrant chart."""
    return {
        "chart_type": "try_vs_success",
        "quadrants": {
            "power_users": {"count": 25, "percentage": 25.0},
            "strugglers": {"count": 42, "percentage": 42.0},
            "skeptics": {"count": 18, "percentage": 18.0},
            "unaware": {"count": 15, "percentage": 15.0},
        },
        "total_synths": 100,
        "avg_success_rate": 0.45,
        "avg_try_rate": 0.67,
    }


@pytest.fixture
def sample_chart_data_clustering():
    """Sample chart data for clustering analysis."""
    return {
        "chart_type": "clustering",
        "n_clusters": 3,
        "silhouette_score": 0.72,
        "clusters": [
            {
                "id": 0,
                "size": 30,
                "label": "Power Users",
                "avg_success_rate": 0.85,
                "centroid": {"capability": 0.8, "trust": 0.75},
            },
            {
                "id": 1,
                "size": 40,
                "label": "Strugglers",
                "avg_success_rate": 0.15,
                "centroid": {"capability": 0.25, "trust": 0.3},
            },
            {
                "id": 2,
                "size": 30,
                "label": "Casual",
                "avg_success_rate": 0.55,
                "centroid": {"capability": 0.5, "trust": 0.6},
            },
        ],
    }


@pytest.fixture
def sample_chart_data_sankey():
    """Sample chart data for Sankey flow diagram."""
    return {
        "chart_type": "sankey",
        "flows": [
            {"source": "Aware", "target": "Try", "value": 70},
            {"source": "Aware", "target": "Not Try", "value": 30},
            {"source": "Try", "target": "Success", "value": 45},
            {"source": "Try", "target": "Fail", "value": 25},
        ],
        "drop_off_points": [
            {"stage": "Awareness -> Try", "drop_off_rate": 0.30},
            {"stage": "Try -> Success", "drop_off_rate": 0.36},
        ],
    }


@pytest.fixture
def sample_chart_data_shap():
    """Sample chart data for SHAP summary."""
    return {
        "chart_type": "shap_summary",
        "feature_importance": [
            {"feature": "digital_literacy", "importance": 0.35, "direction": "positive"},
            {"feature": "perceived_risk", "importance": 0.28, "direction": "negative"},
            {"feature": "time_availability", "importance": 0.20, "direction": "positive"},
            {"feature": "trust_propensity", "importance": 0.12, "direction": "positive"},
        ],
        "model_r2": 0.78,
    }


# =============================================================================
# Test Classes
# =============================================================================


class TestCaptionGeneration:
    """Tests for chart caption generation."""

    def test_generate_caption_returns_caption_object(self, mock_llm_client):
        """Caption generation returns ChartCaption instance."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        caption = service._generate_caption(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data={"quadrants": {"strugglers": {"percentage": 42.0}}},
        )

        assert isinstance(caption, ChartCaption)
        assert caption.simulation_id == "sim_12345678"
        assert caption.chart_type == "try_vs_success"

    def test_generate_caption_calls_llm(self, mock_llm_client):
        """Caption generation makes LLM call with proper prompt."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        service._generate_caption(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data={"test": "data"},
        )

        # _generate_caption uses complete_json, not complete
        mock_llm_client.complete_json.assert_called_once()
        call_args = mock_llm_client.complete_json.call_args
        messages = call_args.kwargs.get("messages", call_args[0][0] if call_args[0] else None)
        assert any("caption" in str(m).lower() for m in messages)

    def test_generate_caption_extracts_key_metric(self, mock_llm_client, sample_chart_data_try_vs_success):
        """Caption includes key metric from chart data."""
        mock_llm_client.complete_json.return_value = json.dumps(
            {
                "caption": "42% struggle with feature",
                "key_metric": "struggle_percentage",
                "key_value": 42.0,
                "confidence": 0.95,
            }
        )
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        caption = service._generate_caption(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        assert caption.key_metric == "struggle_percentage"
        assert caption.key_value == 42.0

    def test_generate_caption_different_chart_types(self, mock_llm_client):
        """Caption generation works for all chart types."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        chart_types: list[ChartType] = [
            "try_vs_success",
            "distribution",
            "sankey",
            "clustering",
            "shap_summary",
        ]

        for chart_type in chart_types:
            caption = service._generate_caption(
                simulation_id="sim_12345678",
                chart_type=chart_type,
                chart_data={"chart_type": chart_type, "data": "test"},
            )
            assert caption.chart_type == chart_type


class TestInsightGeneration:
    """Tests for full chart insight generation."""

    def test_generate_insight_returns_insight_object(self, mock_llm_client, sample_chart_data_try_vs_success):
        """Full insight generation returns ChartInsight instance."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        insight = service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        assert isinstance(insight, ChartInsight)
        assert insight.simulation_id == "sim_12345678"
        assert insight.chart_type == "try_vs_success"

    def test_generate_insight_includes_all_fields(self, mock_llm_client, sample_chart_data_try_vs_success):
        """Generated insight contains caption, explanation, evidence, recommendation."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        insight = service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        assert insight.caption != ""
        assert insight.explanation != ""
        assert len(insight.evidence) > 0
        assert insight.recommendation is not None

    def test_generate_insight_caches_result(self, mock_llm_client, sample_chart_data_try_vs_success):
        """Generated insights are cached by simulation_id + chart_type."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        # First call
        insight1 = service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        # Second call - should return cached
        insight2 = service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        # Should be same object from cache
        assert insight1.generated_at == insight2.generated_at
        # LLM should only be called once
        assert mock_llm_client.complete_json.call_count == 1

    def test_generate_insight_force_regenerate(self, mock_llm_client, sample_chart_data_try_vs_success):
        """Force regenerate bypasses cache."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        # First call
        service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        # Second call with force_regenerate
        service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
            force_regenerate=True,
        )

        # LLM should be called twice
        assert mock_llm_client.complete_json.call_count == 2

    def test_generate_insight_clustering(self, mock_llm_client, sample_chart_data_clustering):
        """Clustering chart generates appropriate insight."""
        mock_llm_client.complete_json.return_value = json.dumps(
            {
                "caption": "3 distinct user segments identified",
                "explanation": "K-means clustering reveals 3 groups with clear separation.",
                "evidence": ["Silhouette score: 0.72", "40% in struggler segment"],
                "recommendation": "Target strugglers with simplified onboarding",
                "key_metric": "n_clusters",
                "key_value": 3,
                "confidence": 0.85,
            }
        )
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        insight = service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="clustering",
            chart_data=sample_chart_data_clustering,
        )

        assert insight.chart_type == "clustering"
        assert "segment" in insight.caption.lower() or "cluster" in insight.caption.lower()


class TestInsightPromptBuilding:
    """Tests for insight prompt construction."""

    def test_prompt_includes_chart_data(self, mock_llm_client, sample_chart_data_try_vs_success):
        """Prompt includes relevant chart data."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        prompt = service._build_insight_prompt(
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        assert "quadrants" in prompt or "42" in prompt
        assert "try_vs_success" in prompt.lower() or "quadrant" in prompt.lower()

    def test_prompt_requests_structured_output(self, mock_llm_client):
        """Prompt requests JSON structured output."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        prompt = service._build_insight_prompt(
            chart_type="distribution",
            chart_data={"histogram": [10, 20, 30, 25, 15]},
        )

        assert "json" in prompt.lower() or "JSON" in prompt

    def test_prompt_specifies_token_limits(self, mock_llm_client):
        """Prompt includes token limit guidance."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        prompt = service._build_insight_prompt(
            chart_type="try_vs_success",
            chart_data={},
        )

        # Should mention token limits for caption and explanation
        assert "20" in prompt or "token" in prompt.lower()


class TestCacheOperations:
    """Tests for insight caching."""

    def test_get_cached_insight_returns_none_for_missing(self, mock_llm_client):
        """Getting non-existent cached insight returns None."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        result = service._get_cached_insight("nonexistent_sim", "try_vs_success")

        assert result is None

    def test_get_cached_insight_returns_cached(self, mock_llm_client, sample_chart_data_try_vs_success):
        """Getting cached insight returns the insight."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        # Generate to cache
        original = service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        # Get from cache
        cached = service._get_cached_insight("sim_12345678", "try_vs_success")

        assert cached is not None
        assert cached.generated_at == original.generated_at

    def test_clear_cache_removes_all(self, mock_llm_client, sample_chart_data_try_vs_success):
        """Clearing cache removes all cached insights."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        # Generate multiple insights
        service.generate_insight("sim_1", "try_vs_success", sample_chart_data_try_vs_success)
        service.generate_insight("sim_1", "clustering", {"clusters": []})
        service.generate_insight("sim_2", "try_vs_success", sample_chart_data_try_vs_success)

        # Clear cache
        service.clear_cache()

        # All should be None now
        assert service._get_cached_insight("sim_1", "try_vs_success") is None
        assert service._get_cached_insight("sim_1", "clustering") is None
        assert service._get_cached_insight("sim_2", "try_vs_success") is None

    def test_clear_cache_for_simulation(self, mock_llm_client, sample_chart_data_try_vs_success):
        """Clear cache for specific simulation only."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        # Generate for different simulations
        service.generate_insight("sim_1", "try_vs_success", sample_chart_data_try_vs_success)
        service.generate_insight("sim_2", "try_vs_success", sample_chart_data_try_vs_success)

        # Clear only sim_1
        service.clear_cache(simulation_id="sim_1")

        # sim_1 should be cleared, sim_2 should remain
        assert service._get_cached_insight("sim_1", "try_vs_success") is None
        assert service._get_cached_insight("sim_2", "try_vs_success") is not None


class TestGetAllInsights:
    """Tests for retrieving all insights for a simulation."""

    def test_get_all_insights_returns_simulation_insights(
        self, mock_llm_client, sample_chart_data_try_vs_success, sample_chart_data_clustering
    ):
        """Get all insights returns SimulationInsights object."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        # Generate multiple insights
        service.generate_insight("sim_1", "try_vs_success", sample_chart_data_try_vs_success)
        service.generate_insight("sim_1", "clustering", sample_chart_data_clustering)

        # Get all
        result = service.get_all_insights("sim_1")

        assert isinstance(result, SimulationInsights)
        assert result.simulation_id == "sim_1"
        assert len(result.insights) == 2
        assert "try_vs_success" in result.insights
        assert "clustering" in result.insights

    def test_get_all_insights_empty_simulation(self, mock_llm_client):
        """Get all insights for simulation with no insights."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        result = service.get_all_insights("nonexistent_sim")

        assert isinstance(result, SimulationInsights)
        assert result.simulation_id == "nonexistent_sim"
        assert len(result.insights) == 0
        assert result.total_charts_analyzed == 0

    def test_get_all_insights_includes_chart_types_covered(
        self, mock_llm_client, sample_chart_data_try_vs_success
    ):
        """SimulationInsights includes list of covered chart types."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        service.generate_insight("sim_1", "try_vs_success", sample_chart_data_try_vs_success)
        service.generate_insight("sim_1", "sankey", {"flows": []})

        result = service.get_all_insights("sim_1")

        assert "try_vs_success" in result.chart_types_covered
        assert "sankey" in result.chart_types_covered
        assert result.total_charts_analyzed == 2


class TestExecutiveSummary:
    """Tests for executive summary generation."""

    def test_generate_executive_summary(
        self, mock_llm_client, sample_chart_data_try_vs_success, sample_chart_data_clustering
    ):
        """Executive summary aggregates all insights."""
        mock_llm_client.complete.return_value = (
            "The simulation reveals significant usability challenges: 42% of users "
            "struggle with the feature, with 3 distinct user segments identified. "
            "Priority should be given to improving onboarding for low-literacy users."
        )
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        # Generate insights first
        service.generate_insight("sim_1", "try_vs_success", sample_chart_data_try_vs_success)
        service.generate_insight("sim_1", "clustering", sample_chart_data_clustering)

        # Generate executive summary
        summary = service.generate_executive_summary("sim_1")

        assert summary is not None
        assert len(summary) > 0
        mock_llm_client.complete.assert_called()

    def test_executive_summary_no_insights(self, mock_llm_client):
        """Executive summary for simulation with no insights."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        summary = service.generate_executive_summary("empty_sim")

        # Should return None or empty string for no insights
        assert summary is None or summary == ""
        # LLM should not be called
        mock_llm_client.complete.assert_not_called()


class TestLLMErrorHandling:
    """Tests for LLM error handling."""

    def test_llm_failure_raises_exception(self, mock_llm_client, sample_chart_data_try_vs_success):
        """LLM failure raises appropriate exception."""
        mock_llm_client.complete_json.side_effect = Exception("API Error")
        from synth_lab.services.simulation.insight_service import InsightService, InsightGenerationError

        service = InsightService(llm_client=mock_llm_client)

        with pytest.raises(InsightGenerationError) as exc_info:
            service.generate_insight(
                simulation_id="sim_12345678",
                chart_type="try_vs_success",
                chart_data=sample_chart_data_try_vs_success,
            )

        assert "API Error" in str(exc_info.value) or "failed" in str(exc_info.value).lower()

    def test_malformed_llm_response_handled(self, mock_llm_client, sample_chart_data_try_vs_success):
        """Malformed LLM JSON response is handled gracefully."""
        mock_llm_client.complete_json.return_value = "not valid json {"
        from synth_lab.services.simulation.insight_service import InsightService, InsightGenerationError

        service = InsightService(llm_client=mock_llm_client)

        with pytest.raises(InsightGenerationError):
            service.generate_insight(
                simulation_id="sim_12345678",
                chart_type="try_vs_success",
                chart_data=sample_chart_data_try_vs_success,
            )

    def test_missing_fields_in_response(self, mock_llm_client, sample_chart_data_try_vs_success):
        """Missing required fields in LLM response are handled."""
        mock_llm_client.complete_json.return_value = json.dumps(
            {
                "caption": "Only caption, missing other fields",
                # Missing: explanation, evidence, recommendation
            }
        )
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client)

        # Should either raise or use defaults
        try:
            insight = service.generate_insight(
                simulation_id="sim_12345678",
                chart_type="try_vs_success",
                chart_data=sample_chart_data_try_vs_success,
            )
            # If it doesn't raise, explanation should have a default
            assert insight.caption == "Only caption, missing other fields"
            assert insight.explanation is not None  # Should have some default
        except Exception:
            # Also acceptable to raise
            pass


class TestServiceInstantiation:
    """Tests for InsightService instantiation."""

    def test_instantiate_with_custom_client(self):
        """Service can be instantiated with custom LLM client."""
        mock_client = MagicMock()
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_client)

        assert service.llm is mock_client

    def test_instantiate_with_default_client(self):
        """Service uses default LLM client if none provided."""
        from synth_lab.services.simulation.insight_service import InsightService

        with patch("synth_lab.services.simulation.insight_service.get_llm_client") as mock_get:
            mock_get.return_value = MagicMock()
            service = InsightService()

            mock_get.assert_called_once()
            assert service.llm is not None


class TestPhoenixTracing:
    """Tests for Phoenix/OpenTelemetry tracing integration."""

    def test_insight_generation_creates_span(self, mock_llm_client, sample_chart_data_try_vs_success):
        """Insight generation creates tracing span."""
        from synth_lab.services.simulation.insight_service import InsightService

        with patch("synth_lab.services.simulation.insight_service._tracer") as mock_tracer:
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
            mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

            service = InsightService(llm_client=mock_llm_client)
            service.generate_insight(
                simulation_id="sim_12345678",
                chart_type="try_vs_success",
                chart_data=sample_chart_data_try_vs_success,
            )

            mock_tracer.start_as_current_span.assert_called()
