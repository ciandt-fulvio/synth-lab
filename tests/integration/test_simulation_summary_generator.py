"""
Integration tests for SimulationSummaryGeneratorService.

Tests the full generation flow: load experiment + simulation run + group stats
→ LLM descobertas → assemble markdown → save document.

References:
    - Service: src/synth_lab/services/simulation_summary_generator_service.py
    - Feature: specs/042-quantitative-analysis/spec.md
"""

from unittest.mock import MagicMock, call

import pytest

from synth_lab.services.simulation_summary_generator_service import (
    SimulationSummaryGeneratorService,
)


def _make_mock_experiment(name: str = "Pix Parcelado", synth_group_id: str = "grp_test1234") -> MagicMock:
    exp = MagicMock()
    exp.name = name
    exp.hypothesis = "Alta renda adota mais rápido"
    exp.description = "Experimento para validar hipótese de adoção"
    exp.synth_group_id = synth_group_id
    return exp


def _make_mock_orm_run(
    n_synths: int = 20,
    mean: float = 42.0,
) -> MagicMock:
    orm_run = MagicMock()
    orm_run.id = "sr_test1234"
    orm_run.n_synths = n_synths
    orm_run.n_iterations = 3000
    orm_run.stats = {
        "mean": mean,
        "median": mean - 1.0,
        "p10": mean - 4.0,
        "p90": mean + 4.0,
        "std": 3.0,
    }
    orm_run.distribution = [mean + (i % 10 - 5) * 0.5 for i in range(100)]
    orm_run.segments = {
        "age": {"buckets": [
            {"label": "18-29", "adoption_rate": 38.0, "count": 7},
            {"label": "30-49", "adoption_rate": 44.0, "count": 9},
            {"label": "50+", "adoption_rate": 40.0, "count": 4},
        ]},
        "income": {"buckets": [
            {"label": "baixa", "adoption_rate": 30.0, "count": 6},
            {"label": "media", "adoption_rate": 42.0, "count": 8},
            {"label": "alta", "adoption_rate": 55.0, "count": 6},
        ]},
        "education": {"buckets": [
            {"label": "baixa", "adoption_rate": 32.0, "count": 5},
            {"label": "media", "adoption_rate": 41.0, "count": 8},
            {"label": "alta", "adoption_rate": 50.0, "count": 7},
        ]},
    }
    orm_run.sensitivity = [
        {"header": "Familiaridade Digital", "impact": 12.5, "mean_low": 30.0, "mean_high": 55.0},
        {"header": "Renda Normalizada", "impact": 8.2, "mean_low": 35.0, "mean_high": 50.0},
        {"header": "Confiança", "impact": 5.1, "mean_low": 38.0, "mean_high": 46.0},
    ]

    interp_dist = MagicMock()
    interp_dist.section = "distribution"
    interp_dist.raw_text = "Distribuição centrada em 42%"
    interp_dist.ai_text = "Com 80% de confiança, a adoção fica entre 38% e 46%"

    interp_seg = MagicMock()
    interp_seg.section = "segments"
    interp_seg.raw_text = "Alta renda lidera"
    interp_seg.ai_text = "Segmento de alta renda apresenta taxa 83% maior"

    interp_sens = MagicMock()
    interp_sens.section = "sensitivity"
    interp_sens.raw_text = "Familiaridade Digital é a premissa mais impactante"
    interp_sens.ai_text = "Familiaridade Digital explica 45% da variância total"

    orm_run.interpretations = [interp_dist, interp_seg, interp_sens]
    return orm_run


@pytest.mark.integration
class TestSimulationSummaryGeneratorGenerate:
    """Tests for SimulationSummaryGeneratorService.generate()."""

    def test_generates_and_saves_document(self):
        """Verify generate() calls document_service.save_document() with markdown."""
        experiment_repo = MagicMock()
        experiment_repo.get_by_id.return_value = _make_mock_experiment()

        sim_repo = MagicMock()
        sim_repo.get_latest_by_experiment.return_value = _make_mock_orm_run()

        llm = MagicMock()
        llm.complete.return_value = "Os resultados indicam adoção moderada com potencial em alta renda."

        doc_service = MagicMock()
        synth_group_service = MagicMock()
        synth_group_service.get_group_statistics.return_value = None
        interview_guide_repo = MagicMock()
        interview_guide_repo.get_by_experiment_id.return_value = None

        service = SimulationSummaryGeneratorService(
            llm_client=llm,
            document_service=doc_service,
            simulation_run_repo=sim_repo,
            experiment_repo=experiment_repo,
            synth_group_service=synth_group_service,
            interview_guide_repo=interview_guide_repo,
        )

        service.generate("exp_12345678")

        doc_service.save_document.assert_called_once()
        call_kwargs = doc_service.save_document.call_args[1]
        assert call_kwargs["experiment_id"] == "exp_12345678"
        assert call_kwargs["markdown_content"]
        assert len(call_kwargs["markdown_content"]) > 100

    def test_raises_when_experiment_not_found(self):
        """ValueError raised when experiment does not exist."""
        experiment_repo = MagicMock()
        experiment_repo.get_by_id.return_value = None

        service = SimulationSummaryGeneratorService(
            llm_client=MagicMock(),
            document_service=MagicMock(),
            simulation_run_repo=MagicMock(),
            experiment_repo=experiment_repo,
        )

        with pytest.raises(ValueError, match="Experiment not found"):
            service.generate("exp_nonexistent")

    def test_raises_when_no_simulation_run(self):
        """ValueError raised when no simulation results exist yet."""
        experiment_repo = MagicMock()
        experiment_repo.get_by_id.return_value = _make_mock_experiment()

        sim_repo = MagicMock()
        sim_repo.get_latest_by_experiment.return_value = None

        service = SimulationSummaryGeneratorService(
            llm_client=MagicMock(),
            document_service=MagicMock(),
            simulation_run_repo=sim_repo,
            experiment_repo=experiment_repo,
        )

        with pytest.raises(ValueError, match="No simulation results"):
            service.generate("exp_12345678")

    def test_makes_exactly_one_llm_call(self):
        """Verify exactly one LLM call for descobertas (not for each section)."""
        experiment_repo = MagicMock()
        experiment_repo.get_by_id.return_value = _make_mock_experiment()

        sim_repo = MagicMock()
        sim_repo.get_latest_by_experiment.return_value = _make_mock_orm_run()

        llm = MagicMock()
        llm.complete.return_value = "Descobertas mock"

        doc_service = MagicMock()
        synth_group_service = MagicMock()
        synth_group_service.get_group_statistics.return_value = None
        interview_guide_repo = MagicMock()
        interview_guide_repo.get_by_experiment_id.return_value = None

        service = SimulationSummaryGeneratorService(
            llm_client=llm,
            document_service=doc_service,
            simulation_run_repo=sim_repo,
            experiment_repo=experiment_repo,
            synth_group_service=synth_group_service,
            interview_guide_repo=interview_guide_repo,
        )

        service.generate("exp_12345678")

        assert llm.complete.call_count == 1

    def test_uses_gpt4o_mini_by_default(self):
        """Verify the default model is gpt-4o-mini for cost control."""
        experiment_repo = MagicMock()
        experiment_repo.get_by_id.return_value = _make_mock_experiment()

        sim_repo = MagicMock()
        sim_repo.get_latest_by_experiment.return_value = _make_mock_orm_run()

        llm = MagicMock()
        llm.complete.return_value = "Descobertas mock"

        doc_service = MagicMock()
        synth_group_service = MagicMock()
        synth_group_service.get_group_statistics.return_value = None
        interview_guide_repo = MagicMock()
        interview_guide_repo.get_by_experiment_id.return_value = None

        service = SimulationSummaryGeneratorService(
            llm_client=llm,
            document_service=doc_service,
            simulation_run_repo=sim_repo,
            experiment_repo=experiment_repo,
            synth_group_service=synth_group_service,
            interview_guide_repo=interview_guide_repo,
        )

        service.generate("exp_12345678")

        call_kwargs = llm.complete.call_args[1]
        assert call_kwargs.get("model") == "gpt-4o-mini"

    def test_document_saved_with_simulation_summary_type(self):
        """Verify document is saved with SIMULATION_SUMMARY document type."""
        from synth_lab.domain.entities.experiment_document import DocumentType

        experiment_repo = MagicMock()
        experiment_repo.get_by_id.return_value = _make_mock_experiment()

        sim_repo = MagicMock()
        sim_repo.get_latest_by_experiment.return_value = _make_mock_orm_run()

        llm = MagicMock()
        llm.complete.return_value = "Descobertas mock"

        doc_service = MagicMock()
        synth_group_service = MagicMock()
        synth_group_service.get_group_statistics.return_value = None
        interview_guide_repo = MagicMock()
        interview_guide_repo.get_by_experiment_id.return_value = None

        service = SimulationSummaryGeneratorService(
            llm_client=llm,
            document_service=doc_service,
            simulation_run_repo=sim_repo,
            experiment_repo=experiment_repo,
            synth_group_service=synth_group_service,
            interview_guide_repo=interview_guide_repo,
        )

        service.generate("exp_12345678")

        call_kwargs = doc_service.save_document.call_args[1]
        assert call_kwargs["document_type"] == DocumentType.SIMULATION_SUMMARY


@pytest.mark.integration
class TestSimulationSummaryMarkdownContent:
    """Tests for the markdown report structure."""

    def _run_generate(self, orm_run=None, guide_text: str | None = None) -> str:
        """Helper: run generate() and return the markdown string."""
        experiment_repo = MagicMock()
        experiment_repo.get_by_id.return_value = _make_mock_experiment()

        sim_repo = MagicMock()
        sim_repo.get_latest_by_experiment.return_value = orm_run or _make_mock_orm_run()

        llm = MagicMock()
        llm.complete.return_value = "Descobertas geradas pelo LLM."

        doc_service = MagicMock()
        synth_group_service = MagicMock()
        synth_group_service.get_group_statistics.return_value = None

        guide = None
        if guide_text:
            guide = MagicMock()
            guide.questions = guide_text
        interview_guide_repo = MagicMock()
        interview_guide_repo.get_by_experiment_id.return_value = guide

        service = SimulationSummaryGeneratorService(
            llm_client=llm,
            document_service=doc_service,
            simulation_run_repo=sim_repo,
            experiment_repo=experiment_repo,
            synth_group_service=synth_group_service,
            interview_guide_repo=interview_guide_repo,
        )

        service.generate("exp_12345678")

        return doc_service.save_document.call_args[1]["markdown_content"]

    def test_report_contains_experiment_name(self):
        """Report title must include the experiment name."""
        markdown = self._run_generate()
        assert "Pix Parcelado" in markdown

    def test_report_contains_stats_table(self):
        """Report must have a stats table with key metrics."""
        markdown = self._run_generate()
        assert "Média" in markdown
        assert "Mediana" in markdown
        assert "P10" in markdown
        assert "P90" in markdown

    def test_report_contains_segments_section(self):
        """Report must include all three segment dimensions."""
        markdown = self._run_generate()
        assert "Faixa Etária" in markdown
        assert "Faixa de Renda" in markdown
        assert "Escolaridade" in markdown

    def test_report_contains_sensitivity_section(self):
        """Report must include sensitivity ranking."""
        markdown = self._run_generate()
        assert "Sensibilidade" in markdown
        assert "Familiaridade Digital" in markdown

    def test_report_contains_ai_interpretations(self):
        """AI interpretations from simulation run are included in report."""
        markdown = self._run_generate()
        assert "80% de confiança" in markdown
        assert "alta renda" in markdown.lower()

    def test_report_contains_descobertas_section(self):
        """Report must include the Descobertas Principais section."""
        markdown = self._run_generate()
        assert "Descobertas Principais" in markdown
        assert "Descobertas geradas pelo LLM." in markdown

    def test_interview_guide_appended_when_available(self):
        """When interview guide exists, it is appended as Anexo B."""
        guide_text = "**Pergunta 1:** Como você usa o Pix hoje?"
        markdown = self._run_generate(guide_text=guide_text)
        assert "Roteiro de Entrevista" in markdown
        assert guide_text in markdown

    def test_no_interview_appendix_when_guide_missing(self):
        """No Anexo B section when interview guide is not available."""
        markdown = self._run_generate(guide_text=None)
        assert "Anexo B" not in markdown

    def test_histogram_included_when_distribution_present(self):
        """Unicode histogram block included when distribution data is available."""
        markdown = self._run_generate()
        # Distribution has data → should contain the code block
        assert "```" in markdown


@pytest.mark.integration
class TestSimulationSummaryErrorResilience:
    """Tests for graceful error handling."""

    def test_succeeds_when_group_stats_unavailable(self):
        """generate() should not raise if synth group stats cannot be loaded."""
        experiment_repo = MagicMock()
        experiment_repo.get_by_id.return_value = _make_mock_experiment()

        sim_repo = MagicMock()
        sim_repo.get_latest_by_experiment.return_value = _make_mock_orm_run()

        llm = MagicMock()
        llm.complete.return_value = "Descobertas ok"

        doc_service = MagicMock()
        synth_group_service = MagicMock()
        synth_group_service.get_group_statistics.side_effect = RuntimeError("DB error")
        interview_guide_repo = MagicMock()
        interview_guide_repo.get_by_experiment_id.return_value = None

        service = SimulationSummaryGeneratorService(
            llm_client=llm,
            document_service=doc_service,
            simulation_run_repo=sim_repo,
            experiment_repo=experiment_repo,
            synth_group_service=synth_group_service,
            interview_guide_repo=interview_guide_repo,
        )

        # Should not raise — group stats failure is non-fatal
        service.generate("exp_12345678")
        doc_service.save_document.assert_called_once()

    def test_succeeds_when_llm_fails(self):
        """generate() should not raise if LLM call fails — fallback text used."""
        experiment_repo = MagicMock()
        experiment_repo.get_by_id.return_value = _make_mock_experiment()

        sim_repo = MagicMock()
        sim_repo.get_latest_by_experiment.return_value = _make_mock_orm_run()

        llm = MagicMock()
        llm.complete.side_effect = RuntimeError("OpenAI timeout")

        doc_service = MagicMock()
        synth_group_service = MagicMock()
        synth_group_service.get_group_statistics.return_value = None
        interview_guide_repo = MagicMock()
        interview_guide_repo.get_by_experiment_id.return_value = None

        service = SimulationSummaryGeneratorService(
            llm_client=llm,
            document_service=doc_service,
            simulation_run_repo=sim_repo,
            experiment_repo=experiment_repo,
            synth_group_service=synth_group_service,
            interview_guide_repo=interview_guide_repo,
        )

        # Should not raise — LLM failure uses fallback text
        service.generate("exp_12345678")

        markdown = doc_service.save_document.call_args[1]["markdown_content"]
        assert "não foi possível gerar" in markdown.lower()

    def test_succeeds_when_interview_guide_repo_fails(self):
        """generate() should not raise if interview guide repo fails."""
        experiment_repo = MagicMock()
        experiment_repo.get_by_id.return_value = _make_mock_experiment()

        sim_repo = MagicMock()
        sim_repo.get_latest_by_experiment.return_value = _make_mock_orm_run()

        llm = MagicMock()
        llm.complete.return_value = "Descobertas ok"

        doc_service = MagicMock()
        synth_group_service = MagicMock()
        synth_group_service.get_group_statistics.return_value = None
        interview_guide_repo = MagicMock()
        interview_guide_repo.get_by_experiment_id.side_effect = RuntimeError("DB error")

        service = SimulationSummaryGeneratorService(
            llm_client=llm,
            document_service=doc_service,
            simulation_run_repo=sim_repo,
            experiment_repo=experiment_repo,
            synth_group_service=synth_group_service,
            interview_guide_repo=interview_guide_repo,
        )

        service.generate("exp_12345678")
        doc_service.save_document.assert_called_once()
