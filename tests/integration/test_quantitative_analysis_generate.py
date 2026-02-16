"""
T014 Integration test for generate_causal_model() with mocked OpenAI.

Tests the full flow: experiment context → LLM call → model saved with edges.
Verifies Phoenix tracing span is created.

References:
    - Service: src/synth_lab/services/quantitative_analysis_service.py
    - Contracts: specs/042-quantitative-analysis/contracts/api.md
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from synth_lab.services.quantitative_analysis_service import (
    QuantitativeAnalysisService,
)

# Mock LLM response matching DAG_SYSTEM expected output
MOCK_DAG_RESPONSE = {
    "label": "Modelo Causal: Adoção do Pix Parcelado",
    "interceptMu": 0.1,
    "interceptSigma": 0.4,
    "nodes": [
        "Idade", "Renda", "Escolaridade",
        "Familiaridade Digital", "Confiança",
        "Percepção de Valor", "Adoção",
    ],
    "edges": [
        {
            "id": "e1",
            "from": "Idade",
            "to": "Familiaridade Digital",
            "userVar": "ageNorm",
            "direction": -1,
            "header": "A respeito de quanto a Familiaridade Digital é influenciada pela idade",
            "options": [
                {"text": "Pessoas mais jovens têm familiaridade digital significativamente maior.", "mu": 0.80, "sigma": 0.15},
                {"text": "A idade tem influência relevante na familiaridade digital.", "mu": 0.65, "sigma": 0.25},
                {"text": "Não sei dizer se a idade impacta a familiaridade digital.", "mu": 0.50, "sigma": 0.50},
                {"text": "Pode haver alguma relação fraca entre idade e familiaridade digital.", "mu": 0.30, "sigma": 0.25},
                {"text": "A idade não influencia a familiaridade digital.", "mu": 0.15, "sigma": 0.15},
            ],
            "default": 0,
        },
        {
            "id": "e2",
            "from": "Renda",
            "to": "Percepção de Valor",
            "userVar": "incomeNorm",
            "direction": 1,
            "header": "A respeito de quanto a Percepção de Valor é influenciada pela renda",
            "options": [
                {"text": "Renda alta aumenta muito a percepção de valor.", "mu": 0.80, "sigma": 0.15},
                {"text": "A renda tem influência relevante na percepção de valor.", "mu": 0.65, "sigma": 0.25},
                {"text": "Não sei dizer se a renda impacta a percepção de valor.", "mu": 0.50, "sigma": 0.50},
                {"text": "Pode haver alguma relação fraca entre renda e percepção de valor.", "mu": 0.30, "sigma": 0.25},
                {"text": "A renda não influencia a percepção de valor.", "mu": 0.15, "sigma": 0.15},
            ],
            "default": 1,
        },
    ],
}


@pytest.fixture
def mock_experiment():
    """Create a mock experiment with required fields."""
    exp = MagicMock()
    exp.name = "Pix Parcelado"
    exp.hypothesis = "Usuários de alta renda adotarão Pix Parcelado mais rápido"
    exp.description = "Testar adoção do novo produto financeiro"
    return exp


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client that returns valid DAG JSON."""
    client = MagicMock()
    client.complete_json.return_value = json.dumps(MOCK_DAG_RESPONSE)
    return client


@pytest.fixture
def mock_causal_model_repo():
    """Create a mock causal model repository."""
    repo = MagicMock()
    repo.delete_by_experiment.return_value = False
    # create_with_edges returns a mock ORM model
    orm_model = MagicMock()
    orm_model.id = "cm_test1234"
    orm_model.experiment_id = "exp_12345678"
    orm_model.label = MOCK_DAG_RESPONSE["label"]
    orm_model.intercept_mu = MOCK_DAG_RESPONSE["interceptMu"]
    orm_model.intercept_sigma = MOCK_DAG_RESPONSE["interceptSigma"]
    orm_model.nodes = MOCK_DAG_RESPONSE["nodes"]
    orm_model.created_at = "2026-02-14T10:30:00Z"

    # Mock edges
    edge1 = MagicMock()
    edge1.id = "e1"
    edge1.from_node = "Idade"
    edge1.to_node = "Familiaridade Digital"
    edge1.user_var = "ageNorm"
    edge1.direction = -1
    edge1.header = MOCK_DAG_RESPONSE["edges"][0]["header"]
    edge1.options = MOCK_DAG_RESPONSE["edges"][0]["options"]
    edge1.default_option = 0
    edge1.selected_option = None

    edge2 = MagicMock()
    edge2.id = "e2"
    edge2.from_node = "Renda"
    edge2.to_node = "Percepção de Valor"
    edge2.user_var = "incomeNorm"
    edge2.direction = 1
    edge2.header = MOCK_DAG_RESPONSE["edges"][1]["header"]
    edge2.options = MOCK_DAG_RESPONSE["edges"][1]["options"]
    edge2.default_option = 1
    edge2.selected_option = None

    orm_model.edges = [edge1, edge2]
    repo.create_with_edges.return_value = orm_model
    return repo


@pytest.fixture
def mock_experiment_repo(mock_experiment):
    """Create a mock experiment repository."""
    repo = MagicMock()
    repo.get_by_id.return_value = mock_experiment
    return repo


@pytest.mark.integration
class TestGenerateCausalModel:
    """Integration tests for generate_causal_model()."""

    def test_generates_model_with_correct_structure(
        self, mock_llm_client, mock_causal_model_repo, mock_experiment_repo
    ):
        """Verify model is generated with nodes, edges, and metadata."""
        service = QuantitativeAnalysisService(
            llm_client=mock_llm_client,
            causal_model_repo=mock_causal_model_repo,
            experiment_repo=mock_experiment_repo,
        )

        result = service.generate_causal_model("exp_12345678")

        assert result["label"] == MOCK_DAG_RESPONSE["label"]
        assert len(result["nodes"]) == 7
        assert len(result["edges"]) == 2
        assert result["intercept_mu"] == 0.1
        assert result["intercept_sigma"] == 0.4

    def test_calls_llm_with_dag_system_prompt(
        self, mock_llm_client, mock_causal_model_repo, mock_experiment_repo
    ):
        """Verify LLM is called with correct system prompt and model."""
        service = QuantitativeAnalysisService(
            llm_client=mock_llm_client,
            causal_model_repo=mock_causal_model_repo,
            experiment_repo=mock_experiment_repo,
        )

        service.generate_causal_model("exp_12345678")

        call_args = mock_llm_client.complete_json.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
        assert messages[0]["role"] == "system"
        assert "causal DAG" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert "Pix Parcelado" in messages[1]["content"]

        # Verify model is gpt-5.1
        model = call_args.kwargs.get("model") or call_args[1].get("model")
        assert model == "gpt-5.1"

    def test_deletes_existing_model_before_generating(
        self, mock_llm_client, mock_causal_model_repo, mock_experiment_repo
    ):
        """Verify existing model is deleted before generating a new one."""
        service = QuantitativeAnalysisService(
            llm_client=mock_llm_client,
            causal_model_repo=mock_causal_model_repo,
            experiment_repo=mock_experiment_repo,
        )

        service.generate_causal_model("exp_12345678")

        mock_causal_model_repo.delete_by_experiment.assert_called_once_with("exp_12345678")

    def test_saves_model_with_edges_via_repository(
        self, mock_llm_client, mock_causal_model_repo, mock_experiment_repo
    ):
        """Verify model and edges are saved via repository."""
        service = QuantitativeAnalysisService(
            llm_client=mock_llm_client,
            causal_model_repo=mock_causal_model_repo,
            experiment_repo=mock_experiment_repo,
        )

        service.generate_causal_model("exp_12345678")

        mock_causal_model_repo.create_with_edges.assert_called_once()
        call_kwargs = mock_causal_model_repo.create_with_edges.call_args.kwargs
        assert call_kwargs["experiment_id"] == "exp_12345678"
        assert len(call_kwargs["edges"]) == 2
        assert call_kwargs["edges"][0]["from_node"] == "Idade"
        assert call_kwargs["edges"][0]["user_var"] == "ageNorm"

    def test_edges_have_selected_option_null(
        self, mock_llm_client, mock_causal_model_repo, mock_experiment_repo
    ):
        """Verify all edges start with selected_option = None."""
        service = QuantitativeAnalysisService(
            llm_client=mock_llm_client,
            causal_model_repo=mock_causal_model_repo,
            experiment_repo=mock_experiment_repo,
        )

        result = service.generate_causal_model("exp_12345678")

        for edge in result["edges"]:
            assert edge["selected_option"] is None

    def test_raises_for_missing_experiment(
        self, mock_llm_client, mock_causal_model_repo
    ):
        """Verify ValueError raised when experiment not found."""
        experiment_repo = MagicMock()
        experiment_repo.get_by_id.return_value = None

        service = QuantitativeAnalysisService(
            llm_client=mock_llm_client,
            causal_model_repo=mock_causal_model_repo,
            experiment_repo=experiment_repo,
        )

        with pytest.raises(ValueError, match="not found"):
            service.generate_causal_model("exp_nonexistent")

    def test_phoenix_tracing_span_created(
        self, mock_llm_client, mock_causal_model_repo, mock_experiment_repo
    ):
        """Verify Phoenix tracing span is created for DAG generation."""
        service = QuantitativeAnalysisService(
            llm_client=mock_llm_client,
            causal_model_repo=mock_causal_model_repo,
            experiment_repo=mock_experiment_repo,
        )

        with patch(
            "synth_lab.services.quantitative_analysis_service._tracer"
        ) as mock_tracer:
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
                return_value=mock_span
            )
            mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
                return_value=False
            )

            service.generate_causal_model("exp_12345678")

            mock_tracer.start_as_current_span.assert_called_once()
            call_args = mock_tracer.start_as_current_span.call_args
            assert "generate_causal_model" in call_args[0][0]
