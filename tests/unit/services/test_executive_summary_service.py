"""
Unit tests for ExecutiveSummaryService.

Tests LLM-powered executive summary generation from multiple insights.

References:
    - Service: src/synth_lab/services/executive_summary_service.py
    - Spec: specs/023-quantitative-ai-insights/spec.md
"""

from unittest.mock import MagicMock

import pytest

from synth_lab.domain.entities.chart_insight import ChartInsight
from synth_lab.domain.entities.experiment import (
    Experiment,
    ScorecardData,
)
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
def mock_experiment_repo():
    """Mock experiment repository for testing."""
    repo = MagicMock()
    return repo


@pytest.fixture
def mock_document_service():
    """Mock document service for testing."""
    service = MagicMock()
    return service


@pytest.fixture
def summary_service(
    mock_llm_client, mock_cache_repo, mock_experiment_repo, mock_document_service
):
    """Create ExecutiveSummaryService with mocked dependencies."""
    return ExecutiveSummaryService(
        llm_client=mock_llm_client,
        cache_repo=mock_cache_repo,
        experiment_repo=mock_experiment_repo,
        document_service=mock_document_service,
    )


@pytest.fixture
def sample_insights():
    """Sample chart insights for summary generation."""
    return [
        ChartInsight(
            analysis_id="ana_12345678",
            chart_type="shap_summary",
            summary="Confiança e capacidade do usuário influenciam fortemente o sucesso",
            status="completed",
        ),
        ChartInsight(
            analysis_id="ana_12345678",
            chart_type="pca_scatter",
            summary="Segmentação clara mostra necessidades diversas de usuários",
            status="completed",
        ),
    ]


@pytest.fixture
def sample_experiment():
    """Sample experiment for context testing."""
    return Experiment(
        id="exp_12345678",
        name="Entrega Agendada",
        hypothesis="Usuários preferem agendar entregas para horários específicos",
        description="Funcionalidade de delivery com agendamento",
        scorecard_data=ScorecardData(
            feature_name="Entrega Agendada",
            description_text="Permite agendar entregas para horários específicos",
        ),
    )


class TestBuildMarkdownSynthesisPrompt:
    """Test _build_markdown_synthesis_prompt method."""

    def test_builds_prompt_from_multiple_insights(self, summary_service, sample_insights):
        """Should build synthesis prompt from all insights."""
        prompt = summary_service._build_markdown_synthesis_prompt(sample_insights)

        assert isinstance(prompt, str)
        assert len(prompt) > 200  # Should be substantial
        # Should reference chart types
        assert "shap_summary" in prompt
        assert "pca_scatter" in prompt

    def test_prompt_includes_all_insight_summaries(
        self, summary_service, sample_insights
    ):
        """Should include summaries from all insights."""
        prompt = summary_service._build_markdown_synthesis_prompt(sample_insights)

        # Should include insight summaries
        assert "confiança" in prompt.lower() or "capacidade" in prompt.lower()
        assert "segmentação" in prompt.lower() or "necessidades" in prompt.lower()

    def test_handles_minimum_insights(self, summary_service):
        """Should handle minimum number of insights (2)."""
        min_insights = [
            ChartInsight(
                analysis_id="ana_12345678",
                chart_type=f"chart_{i}",
                summary="Test summary",
                status="completed",
            )
            for i in range(2)
        ]

        prompt = summary_service._build_markdown_synthesis_prompt(min_insights)
        assert len(prompt) > 100

    def test_prompt_includes_markdown_format_instructions(
        self, summary_service, sample_insights
    ):
        """Should include markdown formatting instructions."""
        prompt = summary_service._build_markdown_synthesis_prompt(sample_insights)

        # Should have markdown section headers
        assert "## Visão Geral" in prompt
        assert "## Explicabilidade" in prompt
        assert "## Segmentação" in prompt
        assert "## Casos Extremos" in prompt
        assert "## Recomendações" in prompt
        # Should explicitly say to avoid JSON
        assert "JSON" in prompt

    def test_prompt_includes_experiment_context(
        self, summary_service, sample_insights, sample_experiment
    ):
        """Should include experiment context when provided."""
        prompt = summary_service._build_markdown_synthesis_prompt(
            sample_insights, sample_experiment
        )

        # Should include experiment details
        assert "Entrega Agendada" in prompt
        assert "agendar entregas" in prompt
        assert "Contexto do Experimento" in prompt

    def test_prompt_includes_specificity_guidelines(
        self, summary_service, sample_insights, sample_experiment
    ):
        """Should include guidelines to be specific about the feature."""
        prompt = summary_service._build_markdown_synthesis_prompt(
            sample_insights, sample_experiment
        )

        assert "SEJA ESPECÍFICO" in prompt
        assert "CONTEXTUALIZE" in prompt
        assert "EVITE GENÉRICO" in prompt

    def test_prompt_without_experiment_still_works(
        self, summary_service, sample_insights
    ):
        """Should work without experiment context (backwards compatible)."""
        prompt = summary_service._build_markdown_synthesis_prompt(sample_insights, None)

        assert len(prompt) > 200
        assert "## Visão Geral" in prompt
        # Should NOT have experiment context section
        assert "Contexto do Experimento" not in prompt


class TestGenerateMarkdownSummary:
    """Test generate_markdown_summary method."""

    def test_fetches_experiment_for_context(
        self, summary_service, sample_insights, sample_experiment
    ):
        """Should fetch experiment to provide context in prompt."""
        experiment_id = "exp_12345678"
        analysis_id = "ana_12345678"

        # Setup mocks
        summary_service.document_service.start_generation.return_value = MagicMock()
        summary_service.cache_repo.get_all_chart_insights.return_value = sample_insights
        summary_service.experiment_repo.get_by_id.return_value = sample_experiment
        summary_service.llm.complete.return_value = "## Visão Geral\nTest summary"

        # Execute
        summary_service.generate_markdown_summary(experiment_id, analysis_id)

        # Verify experiment was fetched
        summary_service.experiment_repo.get_by_id.assert_called_once_with(experiment_id)

    def test_fails_with_too_few_insights(self, summary_service):
        """Should fail if less than 2 completed insights."""
        experiment_id = "exp_12345678"
        analysis_id = "ana_12345678"
        too_few_insights = [
            ChartInsight(
                analysis_id=analysis_id,
                chart_type="shap_summary",
                summary="Test",
                status="completed",
            ),
        ]

        summary_service.document_service.start_generation.return_value = MagicMock()
        summary_service.cache_repo.get_all_chart_insights.return_value = too_few_insights

        with pytest.raises(ValueError, match="at least 2"):
            summary_service.generate_markdown_summary(experiment_id, analysis_id)

    def test_stores_result_in_document_service(
        self, summary_service, sample_insights, sample_experiment
    ):
        """Should store generated markdown in document service."""
        experiment_id = "exp_12345678"
        analysis_id = "ana_12345678"
        expected_markdown = "## Visão Geral\nTest summary content"

        # Setup mocks
        summary_service.document_service.start_generation.return_value = MagicMock()
        summary_service.cache_repo.get_all_chart_insights.return_value = sample_insights
        summary_service.experiment_repo.get_by_id.return_value = sample_experiment
        summary_service.llm.complete.return_value = expected_markdown

        # Execute
        result = summary_service.generate_markdown_summary(experiment_id, analysis_id)

        # Verify
        assert result == expected_markdown
        summary_service.document_service.complete_generation.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
