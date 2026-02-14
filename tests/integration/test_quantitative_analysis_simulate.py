"""
T030 Integration test for run_simulation with mocked LLM.

Tests the full flow: load model → load synths → run simulation → save results
→ generate AI interpretations.

References:
    - Service: src/synth_lab/services/quantitative_analysis_service.py
    - Engine: src/synth_lab/services/simulation_engine.py
    - Contracts: specs/042-quantitative-analysis/contracts/api.md
"""

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
    exp.synth_group_id = "grp_test1234"
    return exp


@pytest.mark.integration
class TestRunSimulation:
    """Integration tests for run_simulation()."""

    def test_returns_complete_results(self, mock_causal_model, mock_experiment):
        """Verify simulation returns all required sections."""
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
        llm.complete_json.return_value = "Interpretação mock"

        service = QuantitativeAnalysisService(
            llm_client=llm,
            causal_model_repo=causal_repo,
            experiment_repo=exp_repo,
            simulation_run_repo=sim_repo,
        )

        with patch.object(service, '_load_synths_raw', return_value=_make_mock_synths(20)):
            result = service.run_simulation("exp_12345678")

        assert "stats" in result
        assert "segments" in result
        assert "sensitivity" in result
        assert "interpretations" in result

    def test_stats_have_required_keys(self, mock_causal_model, mock_experiment):
        """Verify stats contain mean, median, std, p10, p90."""
        causal_repo = MagicMock()
        causal_repo.get_by_experiment.return_value = mock_causal_model

        sim_repo = MagicMock()
        orm_run = MagicMock()
        orm_run.id = "sr_test1234"
        orm_run.experiment_id = "exp_12345678"
        orm_run.causal_model_id = "cm_test1234"
        orm_run.n_iterations = 3000
        orm_run.n_synths = 20
        orm_run.created_at = "2026-02-14T10:35:00Z"
        # Return the actual stats from the simulation
        def capture_stats(**kwargs):
            orm_run.stats = kwargs["stats"]
            return orm_run
        sim_repo.create_run.side_effect = capture_stats

        exp_repo = MagicMock()
        exp_repo.get_by_id.return_value = mock_experiment

        llm = MagicMock()
        llm.complete_json.return_value = "Mock AI text"

        service = QuantitativeAnalysisService(
            llm_client=llm,
            causal_model_repo=causal_repo,
            experiment_repo=exp_repo,
            simulation_run_repo=sim_repo,
        )

        with patch.object(service, '_load_synths_raw', return_value=_make_mock_synths(20)):
            result = service.run_simulation("exp_12345678")

        stats = result["stats"]
        for key in ("mean", "median", "std", "p10", "p90"):
            assert key in stats

    def test_all_three_interpretations_generated(self, mock_causal_model, mock_experiment):
        """Verify 3 AI interpretation calls are made (distribution, segments, sensitivity)."""
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
        llm.complete_json.return_value = "AI interpretation text"

        guide_service = MagicMock()

        service = QuantitativeAnalysisService(
            llm_client=llm,
            causal_model_repo=causal_repo,
            experiment_repo=exp_repo,
            simulation_run_repo=sim_repo,
            interview_guide_service=guide_service,
        )

        with patch.object(service, '_load_synths_raw', return_value=_make_mock_synths(20)):
            result = service.run_simulation("exp_12345678")

        # 3 LLM calls for interpretations (interview guide uses separate service)
        assert llm.complete_json.call_count == 3

        interps = result["interpretations"]
        assert "distribution" in interps
        assert "segments" in interps
        assert "sensitivity" in interps

    def test_saves_interpretations_to_repo(self, mock_causal_model, mock_experiment):
        """Verify interpretations are saved via simulation_run_repo."""
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
        llm.complete_json.return_value = "AI text"

        service = QuantitativeAnalysisService(
            llm_client=llm,
            causal_model_repo=causal_repo,
            experiment_repo=exp_repo,
            simulation_run_repo=sim_repo,
        )

        with patch.object(service, '_load_synths_raw', return_value=_make_mock_synths(20)):
            service.run_simulation("exp_12345678")

        sim_repo.create_interpretations.assert_called_once()
        saved = sim_repo.create_interpretations.call_args[0][0]
        assert len(saved) == 3
        sections = {i["section"] for i in saved}
        assert sections == {"distribution", "segments", "sensitivity"}

    def test_raises_when_no_model(self):
        """ValueError raised when no causal model exists."""
        causal_repo = MagicMock()
        causal_repo.get_by_experiment.return_value = None

        service = QuantitativeAnalysisService(
            llm_client=MagicMock(),
            causal_model_repo=causal_repo,
            experiment_repo=MagicMock(),
        )

        with pytest.raises(ValueError, match="No causal model"):
            service.run_simulation("exp_12345678")

    def test_uses_gpt4o_mini_for_interpretations(self, mock_causal_model, mock_experiment):
        """Verify gpt-4o-mini is used for interpretation calls."""
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
        llm.complete_json.return_value = "AI text"

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

        for call in llm.complete_json.call_args_list:
            model = call.kwargs.get("model") or call[1].get("model")
            assert model == "gpt-4o-mini"
