"""
Unit tests for InsightService.

Tests LLM-generated chart insights with database persistence including:
- Full insight generation (caption + explanation + evidence + recommendation)
- Database persistence via repository
- Force regeneration flag
- Executive summary generation

References:
    - Entities: src/synth_lab/domain/entities/chart_insight.py
    - Repository: src/synth_lab/repositories/insight_repository.py
    - Spec: specs/017-analysis-ux-research/spec.md (US6)
    - Data Model: specs/017-analysis-ux-research/data-model.md
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from synth_lab.domain.entities.chart_insight import (
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
def mock_repository():
    """Create a mock InsightRepository."""
    repo = MagicMock()
    repo.get.return_value = None  # No cached insight by default
    repo.get_all_for_simulation.return_value = {}
    repo.get_executive_summary.return_value = None
    repo.save.return_value = "ins_test123"
    repo.save_executive_summary.return_value = "ins_exec123"
    repo.delete_for_simulation.return_value = 0
    return repo


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


# =============================================================================
# Test Classes
# =============================================================================


class TestInsightGeneration:
    """Tests for full chart insight generation."""

    def test_generate_insight_returns_insight_object(
        self, mock_llm_client, mock_repository, sample_chart_data_try_vs_success
    ):
        """Full insight generation returns ChartInsight instance."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        insight = service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        assert isinstance(insight, ChartInsight)
        assert insight.simulation_id == "sim_12345678"
        assert insight.chart_type == "try_vs_success"

    def test_generate_insight_includes_all_fields(
        self, mock_llm_client, mock_repository, sample_chart_data_try_vs_success
    ):
        """Generated insight contains caption, explanation, evidence, recommendation."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        insight = service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        assert insight.caption != ""
        assert insight.explanation != ""
        assert len(insight.evidence) > 0
        assert insight.recommendation is not None

    def test_generate_insight_checks_repository_first(
        self, mock_llm_client, mock_repository, sample_chart_data_try_vs_success
    ):
        """Generated insights check repository before calling LLM."""
        from synth_lab.services.simulation.insight_service import InsightService

        # Setup: repository has cached insight
        cached_insight = ChartInsight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            caption="Cached caption",
            explanation="Cached explanation",
        )
        mock_repository.get.return_value = cached_insight

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        insight = service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        # Should return cached
        assert insight.caption == "Cached caption"
        # LLM should NOT be called
        mock_llm_client.complete_json.assert_not_called()
        # Repository should be checked
        mock_repository.get.assert_called_once_with("sim_12345678", "try_vs_success")

    def test_generate_insight_saves_to_repository(
        self, mock_llm_client, mock_repository, sample_chart_data_try_vs_success
    ):
        """Generated insights are saved to repository."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        # Repository save should be called
        mock_repository.save.assert_called_once()
        call_args = mock_repository.save.call_args
        assert call_args[0][0] == "sim_12345678"  # simulation_id
        assert call_args[0][1] == "try_vs_success"  # chart_type

    def test_generate_insight_force_bypasses_cache(
        self, mock_llm_client, mock_repository, sample_chart_data_try_vs_success
    ):
        """Force flag bypasses repository cache."""
        from synth_lab.services.simulation.insight_service import InsightService

        # Setup: repository has cached insight
        cached_insight = ChartInsight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            caption="Cached caption",
            explanation="Cached explanation",
        )
        mock_repository.get.return_value = cached_insight

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        insight = service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
            force=True,
        )

        # Should NOT use cached (LLM called)
        mock_llm_client.complete_json.assert_called_once()
        # Repository get should NOT be called when force=True
        mock_repository.get.assert_not_called()
        # Result should be from LLM, not cache
        assert insight.caption == "42% of synths struggle with the feature"

    def test_generate_insight_clustering(
        self, mock_llm_client, mock_repository, sample_chart_data_clustering
    ):
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

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        insight = service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="clustering",
            chart_data=sample_chart_data_clustering,
        )

        assert insight.chart_type == "clustering"
        assert "segment" in insight.caption.lower() or "cluster" in insight.caption.lower()


class TestInsightPromptBuilding:
    """Tests for insight prompt construction."""

    def test_prompt_includes_chart_data(
        self, mock_llm_client, mock_repository, sample_chart_data_try_vs_success
    ):
        """Prompt includes relevant chart data."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        prompt = service._build_insight_prompt(
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        assert "quadrants" in prompt or "42" in prompt
        assert "try_vs_success" in prompt.lower() or "quadrant" in prompt.lower()

    def test_prompt_requests_structured_output(self, mock_llm_client, mock_repository):
        """Prompt requests JSON structured output."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        prompt = service._build_insight_prompt(
            chart_type="distribution",
            chart_data={"histogram": [10, 20, 30, 25, 15]},
        )

        assert "json" in prompt.lower() or "JSON" in prompt

    def test_prompt_specifies_token_limits(self, mock_llm_client, mock_repository):
        """Prompt includes token limit guidance."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        prompt = service._build_insight_prompt(
            chart_type="try_vs_success",
            chart_data={},
        )

        # Should mention token limits for caption and explanation
        assert "20" in prompt or "token" in prompt.lower()


class TestClearInsights:
    """Tests for clearing insights from repository."""

    def test_clear_insights_calls_repository(self, mock_llm_client, mock_repository):
        """clear_insights calls repository delete method."""
        from synth_lab.services.simulation.insight_service import InsightService

        mock_repository.delete_for_simulation.return_value = 3

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        deleted = service.clear_insights("sim_12345678")

        mock_repository.delete_for_simulation.assert_called_once_with("sim_12345678")
        assert deleted == 3


class TestGetAllInsights:
    """Tests for retrieving all insights for a simulation."""

    def test_get_all_insights_returns_simulation_insights(
        self, mock_llm_client, mock_repository
    ):
        """Get all insights returns SimulationInsights object."""
        from synth_lab.services.simulation.insight_service import InsightService

        # Setup mock repository
        mock_repository.get_all_for_simulation.return_value = {
            "try_vs_success": ChartInsight(
                simulation_id="sim_1",
                chart_type="try_vs_success",
                caption="Caption 1",
                explanation="Explanation 1",
            ),
            "clustering": ChartInsight(
                simulation_id="sim_1",
                chart_type="clustering",
                caption="Caption 2",
                explanation="Explanation 2",
            ),
        }
        mock_repository.get_executive_summary.return_value = None

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        result = service.get_all_insights("sim_1")

        assert isinstance(result, SimulationInsights)
        assert result.simulation_id == "sim_1"
        assert len(result.insights) == 2
        assert "try_vs_success" in result.insights
        assert "clustering" in result.insights

    def test_get_all_insights_empty_simulation(self, mock_llm_client, mock_repository):
        """Get all insights for simulation with no insights."""
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        result = service.get_all_insights("nonexistent_sim")

        assert isinstance(result, SimulationInsights)
        assert result.simulation_id == "nonexistent_sim"
        assert len(result.insights) == 0
        assert result.total_charts_analyzed == 0

    def test_get_all_insights_includes_total_count(self, mock_llm_client, mock_repository):
        """SimulationInsights includes total charts analyzed."""
        from synth_lab.services.simulation.insight_service import InsightService

        mock_repository.get_all_for_simulation.return_value = {
            "try_vs_success": ChartInsight(
                simulation_id="sim_1",
                chart_type="try_vs_success",
                caption="Caption 1",
                explanation="Explanation 1",
            ),
            "sankey": ChartInsight(
                simulation_id="sim_1",
                chart_type="sankey",
                caption="Caption 2",
                explanation="Explanation 2",
            ),
        }

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        result = service.get_all_insights("sim_1")

        assert result.total_charts_analyzed == 2


class TestExecutiveSummary:
    """Tests for executive summary generation."""

    def test_generate_executive_summary(self, mock_llm_client, mock_repository):
        """Executive summary aggregates all insights."""
        mock_llm_client.complete.return_value = (
            "The simulation reveals significant usability challenges: 42% of users "
            "struggle with the feature, with 3 distinct user segments identified. "
            "Priority should be given to improving onboarding for low-literacy users."
        )
        mock_repository.get_executive_summary.return_value = None
        mock_repository.get_all_for_simulation.return_value = {
            "try_vs_success": ChartInsight(
                simulation_id="sim_1",
                chart_type="try_vs_success",
                caption="42% struggle",
                explanation="Details",
            ),
        }

        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        summary = service.generate_executive_summary("sim_1")

        assert summary is not None
        assert len(summary) > 0
        mock_llm_client.complete.assert_called()
        mock_repository.save_executive_summary.assert_called_once()

    def test_executive_summary_returns_cached(self, mock_llm_client, mock_repository):
        """Executive summary returns cached version if exists."""
        mock_repository.get_executive_summary.return_value = "Cached executive summary"

        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        summary = service.generate_executive_summary("sim_1")

        assert summary == "Cached executive summary"
        mock_llm_client.complete.assert_not_called()

    def test_executive_summary_force_regenerates(self, mock_llm_client, mock_repository):
        """Executive summary with force=True regenerates via LLM."""
        mock_repository.get_executive_summary.return_value = "Cached summary"
        mock_repository.get_all_for_simulation.return_value = {
            "try_vs_success": ChartInsight(
                simulation_id="sim_1",
                chart_type="try_vs_success",
                caption="Caption",
                explanation="Explanation",
            ),
        }
        mock_llm_client.complete.return_value = "New executive summary"

        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        summary = service.generate_executive_summary("sim_1", force=True)

        assert summary == "New executive summary"
        mock_llm_client.complete.assert_called()

    def test_executive_summary_no_insights(self, mock_llm_client, mock_repository):
        """Executive summary for simulation with no insights."""
        mock_repository.get_executive_summary.return_value = None
        mock_repository.get_all_for_simulation.return_value = {}

        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        summary = service.generate_executive_summary("empty_sim")

        # Should return None for no insights
        assert summary is None
        # LLM should not be called
        mock_llm_client.complete.assert_not_called()


class TestLLMErrorHandling:
    """Tests for LLM error handling."""

    def test_llm_failure_raises_exception(
        self, mock_llm_client, mock_repository, sample_chart_data_try_vs_success
    ):
        """LLM failure raises appropriate exception."""
        mock_llm_client.complete_json.side_effect = Exception("API Error")
        from synth_lab.services.simulation.insight_service import (
            InsightGenerationError,
            InsightService,
        )

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        with pytest.raises(InsightGenerationError) as exc_info:
            service.generate_insight(
                simulation_id="sim_12345678",
                chart_type="try_vs_success",
                chart_data=sample_chart_data_try_vs_success,
            )

        assert "API Error" in str(exc_info.value) or "failed" in str(exc_info.value).lower()

    def test_malformed_llm_response_handled(
        self, mock_llm_client, mock_repository, sample_chart_data_try_vs_success
    ):
        """Malformed LLM JSON response is handled gracefully."""
        mock_llm_client.complete_json.return_value = "not valid json {"
        from synth_lab.services.simulation.insight_service import (
            InsightGenerationError,
            InsightService,
        )

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        with pytest.raises(InsightGenerationError):
            service.generate_insight(
                simulation_id="sim_12345678",
                chart_type="try_vs_success",
                chart_data=sample_chart_data_try_vs_success,
            )

    def test_missing_fields_in_response(
        self, mock_llm_client, mock_repository, sample_chart_data_try_vs_success
    ):
        """Missing required fields in LLM response use defaults."""
        mock_llm_client.complete_json.return_value = json.dumps(
            {
                "caption": "Only caption, missing other fields",
                # Missing: explanation, evidence, recommendation
            }
        )
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repository)

        insight = service.generate_insight(
            simulation_id="sim_12345678",
            chart_type="try_vs_success",
            chart_data=sample_chart_data_try_vs_success,
        )

        # Should use defaults for missing fields
        assert insight.caption == "Only caption, missing other fields"
        assert insight.explanation is not None  # Should have default


class TestServiceInstantiation:
    """Tests for InsightService instantiation."""

    def test_instantiate_with_custom_client(self, mock_repository):
        """Service can be instantiated with custom LLM client."""
        mock_client = MagicMock()
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_client, repository=mock_repository)

        assert service.llm is mock_client

    def test_instantiate_with_custom_repository(self, mock_llm_client):
        """Service can be instantiated with custom repository."""
        mock_repo = MagicMock()
        from synth_lab.services.simulation.insight_service import InsightService

        service = InsightService(llm_client=mock_llm_client, repository=mock_repo)

        assert service.repository is mock_repo

    def test_instantiate_with_default_client(self, mock_repository):
        """Service uses default LLM client if none provided."""
        from synth_lab.services.simulation.insight_service import InsightService

        with patch("synth_lab.services.simulation.insight_service.get_llm_client") as mock_get:
            mock_get.return_value = MagicMock()
            service = InsightService(repository=mock_repository)

            mock_get.assert_called_once()
            assert service.llm is not None


class TestPhoenixTracing:
    """Tests for Phoenix/OpenTelemetry tracing integration."""

    def test_insight_generation_creates_span(
        self, mock_llm_client, mock_repository, sample_chart_data_try_vs_success
    ):
        """Insight generation creates tracing span."""
        from synth_lab.services.simulation.insight_service import InsightService

        with patch("synth_lab.services.simulation.insight_service._tracer") as mock_tracer:
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
                return_value=mock_span
            )
            mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
                return_value=False
            )

            service = InsightService(llm_client=mock_llm_client, repository=mock_repository)
            service.generate_insight(
                simulation_id="sim_12345678",
                chart_type="try_vs_success",
                chart_data=sample_chart_data_try_vs_success,
            )

            mock_tracer.start_as_current_span.assert_called()
