"""
T047 Integration test for auto-generate interview guide after simulation.

Tests that run_simulation triggers InterviewGuideGeneratorService with
the top 3 sensitivity premisses and saves/overwrites the guide.

References:
    - Service: src/synth_lab/services/quantitative_analysis_service.py
    - InterviewGuideService: src/synth_lab/services/interview_guide_generator_service.py
    - Spec: specs/042-quantitative-analysis/spec.md (FR-014, FR-017)
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from synth_lab.services.quantitative_analysis_service import (
    QuantitativeAnalysisService,
)


def _make_mock_edge(edge_id: str, user_var: str = "ageNorm", direction: int = 1, selected: int = 2) -> MagicMock:
    """Create a mock edge ORM object with valid options."""
    edge = MagicMock()
    edge.id = edge_id
    edge.from_node = "NodeA"
    edge.to_node = "NodeB"
    edge.user_var = user_var
    edge.direction = direction
    edge.header = f"Header for {edge_id}"
    edge.options = [
        {"text": "Strong", "mu": 0.80, "sigma": 0.15},
        {"text": "Significant", "mu": 0.65, "sigma": 0.25},
        {"text": "Uncertain", "mu": 0.50, "sigma": 0.50},
        {"text": "Weak", "mu": 0.30, "sigma": 0.25},
        {"text": "None", "mu": 0.15, "sigma": 0.15},
    ]
    edge.default_option = 2
    edge.selected_option = selected
    return edge


def _make_mock_synths(n: int = 20) -> list[dict]:
    """Create mock synth data dicts."""
    synths = []
    for i in range(n):
        synths.append({
            "id": f"syn_{i:03d}",
            "data": {
                "demografia": {
                    "idade": 20 + (i * 50 // n),
                    "renda_mensal": 2000 + i * 500,
                    "escolaridade": "médio completo",
                    "composicao_familiar": {"numero_pessoas": 2 + (i % 4)},
                },
                "deficiencias": {"visual": {"tipo": "nenhuma"}, "motora": {"tipo": "nenhuma"}},
                "sensitivities": {
                    "digital_capability": 0.5,
                    "risk_aversion": 0.4,
                    "institutional_trust_level": 0.6,
                    "friction_tolerance": 0.5,
                },
            }
        })
    return synths


@pytest.fixture
def mock_causal_model():
    """Create a mock causal model ORM with 3 edges."""
    model = MagicMock()
    model.id = "cm_test1234"
    model.experiment_id = "exp_12345678"
    model.label = "Test Model"
    model.intercept_mu = 0.1
    model.intercept_sigma = 0.4
    model.nodes = ["Idade", "Renda", "Confiança", "Adoção"]
    model.edges = [
        _make_mock_edge("e1", "ageNorm", -1, 0),
        _make_mock_edge("e2", "incomeNorm", 1, 1),
        _make_mock_edge("e3", "digitalCapability", 1, 2),
    ]
    return model


@pytest.fixture
def mock_experiment():
    """Create a mock experiment."""
    exp = MagicMock()
    exp.name = "Pix Parcelado"
    exp.hypothesis = "Alta renda adota mais rápido"
    exp.description = "Teste de adoção do Pix Parcelado"
    exp.synth_group_id = "grp_test1234"
    return exp


@pytest.mark.integration
class TestAutoGenerateInterviewGuide:
    """Integration tests for interview guide auto-generation after simulation."""

    def test_interview_guide_generated_after_simulation(self, mock_causal_model, mock_experiment):
        """Verify InterviewGuideGeneratorService is called after simulation."""
        causal_repo = MagicMock()
        causal_repo.get_by_experiment.return_value = mock_causal_model

        sim_repo = MagicMock()
        orm_run = MagicMock()
        orm_run.id = "sr_test1234"
        orm_run.experiment_id = "exp_12345678"
        orm_run.causal_model_id = "cm_test1234"
        orm_run.n_iterations = 3000
        orm_run.n_synths = 20
        orm_run.stats = {"mean": 42.0, "median": 41.0, "std": 3.0, "p10": 38.0, "p90": 46.0}
        orm_run.created_at = "2026-02-14T10:35:00Z"
        sim_repo.create_run.return_value = orm_run

        exp_repo = MagicMock()
        exp_repo.get_by_id.return_value = mock_experiment

        llm = MagicMock()
        llm.complete.return_value = "Mock AI text"

        guide_service = MagicMock()

        service = QuantitativeAnalysisService(
            llm_client=llm,
            causal_model_repo=causal_repo,
            experiment_repo=exp_repo,
            simulation_run_repo=sim_repo,
            interview_guide_service=guide_service,
        )

        with patch.object(service, '_load_synths_raw', return_value=_make_mock_synths(20)):
            service.run_simulation("exp_12345678")

        guide_service.generate_from_simulation_sync.assert_called_once()

    def test_interview_guide_receives_sensitivity_data(self, mock_causal_model, mock_experiment):
        """Verify sensitivity data is passed to the interview guide generator."""
        causal_repo = MagicMock()
        causal_repo.get_by_experiment.return_value = mock_causal_model

        sim_repo = MagicMock()
        orm_run = MagicMock()
        orm_run.id = "sr_test1234"
        orm_run.experiment_id = "exp_12345678"
        orm_run.causal_model_id = "cm_test1234"
        orm_run.n_iterations = 3000
        orm_run.n_synths = 20
        orm_run.stats = {"mean": 42.0, "median": 41.0, "std": 3.0, "p10": 38.0, "p90": 46.0}
        orm_run.created_at = "2026-02-14T10:35:00Z"
        sim_repo.create_run.return_value = orm_run

        exp_repo = MagicMock()
        exp_repo.get_by_id.return_value = mock_experiment

        llm = MagicMock()
        llm.complete.return_value = "Mock AI text"

        guide_service = MagicMock()

        service = QuantitativeAnalysisService(
            llm_client=llm,
            causal_model_repo=causal_repo,
            experiment_repo=exp_repo,
            simulation_run_repo=sim_repo,
            interview_guide_service=guide_service,
        )

        with patch.object(service, '_load_synths_raw', return_value=_make_mock_synths(20)):
            service.run_simulation("exp_12345678")

        call_kwargs = guide_service.generate_from_simulation_sync.call_args
        assert call_kwargs.kwargs["experiment_id"] == "exp_12345678"
        assert call_kwargs.kwargs["name"] == "Pix Parcelado"
        assert call_kwargs.kwargs["hypothesis"] == "Alta renda adota mais rápido"
        # sensitivity should be a list with entries
        assert isinstance(call_kwargs.kwargs["sensitivity"], list)
        assert len(call_kwargs.kwargs["sensitivity"]) > 0

    def test_simulation_succeeds_even_if_guide_fails(self, mock_causal_model, mock_experiment):
        """Verify simulation returns results even if interview guide generation fails."""
        causal_repo = MagicMock()
        causal_repo.get_by_experiment.return_value = mock_causal_model

        sim_repo = MagicMock()
        orm_run = MagicMock()
        orm_run.id = "sr_test1234"
        orm_run.experiment_id = "exp_12345678"
        orm_run.causal_model_id = "cm_test1234"
        orm_run.n_iterations = 3000
        orm_run.n_synths = 20
        orm_run.stats = {"mean": 42.0, "median": 41.0, "std": 3.0, "p10": 38.0, "p90": 46.0}
        orm_run.created_at = "2026-02-14T10:35:00Z"
        sim_repo.create_run.return_value = orm_run

        exp_repo = MagicMock()
        exp_repo.get_by_id.return_value = mock_experiment

        llm = MagicMock()
        llm.complete.return_value = "Mock AI text"

        guide_service = MagicMock()
        guide_service.generate_from_simulation_sync.side_effect = RuntimeError("LLM down")

        service = QuantitativeAnalysisService(
            llm_client=llm,
            causal_model_repo=causal_repo,
            experiment_repo=exp_repo,
            simulation_run_repo=sim_repo,
            interview_guide_service=guide_service,
        )

        with patch.object(service, '_load_synths_raw', return_value=_make_mock_synths(20)):
            result = service.run_simulation("exp_12345678")

        # Simulation results should still be returned despite guide failure
        assert "stats" in result
        assert "segments" in result
        assert "sensitivity" in result

    def test_guide_service_prompt_uses_gpt51(self):
        """Verify the generate_from_simulation_sync method calls LLM with gpt-5.1."""
        from synth_lab.services.interview_guide_generator_service import (
            InterviewGuideGeneratorService,
        )

        llm = MagicMock()
        # generate_from_simulation_sync uses llm.complete() (not complete_json)
        llm.complete.return_value = (
            "### Pergunta 1\n**Texto:** Como você percebe a influência da idade na confiança?\n"
            "**Valida:** Idade → Confiança\n**O que escutar:**\n- Sinal positivo\n- Sinal negativo\n"
            "- Sinal ambíguo\n**Dica para o entrevistador:** Aprofunde sobre experiências passadas."
        )

        guide_repo = MagicMock()
        guide_repo.get_by_experiment_id.return_value = None

        service = InterviewGuideGeneratorService(
            llm_client=llm,
            interview_guide_repo=guide_repo,
        )

        sensitivity = [
            {"header": "Idade afeta confiança", "impact": 12.5, "mean_low": 48.0, "mean_high": 35.5, "edge_id": "e1"},
            {"header": "Renda afeta adoção", "impact": 8.0, "mean_low": 46.0, "mean_high": 38.0, "edge_id": "e2"},
            {"header": "Escolaridade afeta uso", "impact": 5.0, "mean_low": 44.0, "mean_high": 39.0, "edge_id": "e3"},
        ]

        service.generate_from_simulation_sync(
            experiment_id="exp_123",
            name="Test Exp",
            hypothesis="Test hyp",
            sensitivity=sensitivity,
        )

        call_kwargs = llm.complete.call_args
        assert call_kwargs.kwargs.get("model") == "gpt-5.1"
        guide_repo.create.assert_called_once()
