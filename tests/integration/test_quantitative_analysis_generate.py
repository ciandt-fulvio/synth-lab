"""
T014 Integration test for generate_causal_model() with mocked OpenAI.

Tests the full flow: experiment context → 2-pass LLM call → model saved with edges.
Pass 1: Topology (nodes as dicts, edges without options).
Pass 2: Node premissa options for interaction + outcome nodes.

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

# Mock Pass 1: Topology response (nodes as dicts with type, edges structural)
MOCK_TOPOLOGY_RESPONSE = {
    "label": "Modelo Causal: Adoção do Pix Parcelado",
    "interceptMu": 0.1,
    "interceptSigma": 0.4,
    "nodes": [
        {"name": "Aversão a Risco", "type": "sensitivity", "sensitivity_key": "risk_aversion", "description": "Mede quanto o usuário evita risco financeiro."},
        {"name": "Cap. Digital", "type": "sensitivity", "sensitivity_key": "digital_capability", "description": "Habilidade do usuário com tecnologia."},
        {"name": "Facilidade de Uso", "type": "product", "description": "Quão fácil é usar o Pix Parcelado."},
        {"name": "Transparência", "type": "product", "description": "Clareza nas taxas e condições."},
        {"name": "Confiança", "type": "interaction", "description": "Confiança gerada pela combinação de baixa aversão a risco e facilidade de uso."},
        {"name": "Percepção de Valor", "type": "interaction", "description": "Valor percebido pela combinação de capacidade digital e transparência."},
        {"name": "Adoção", "type": "outcome", "description": "Probabilidade de adoção do Pix Parcelado."},
    ],
    "edges": [
        {"id": "e1", "from": "Aversão a Risco", "to": "Confiança", "direction": -1, "edge_type": "likert", "weight": 0.7},
        {"id": "e2", "from": "Facilidade de Uso", "to": "Confiança", "direction": 1, "edge_type": "likert", "weight": 0.6},
        {"id": "e3", "from": "Cap. Digital", "to": "Percepção de Valor", "direction": 1, "edge_type": "likert", "weight": 0.5},
        {"id": "e4", "from": "Transparência", "to": "Percepção de Valor", "direction": 1, "edge_type": "likert", "weight": 0.6},
        {"id": "e5", "from": "Confiança", "to": "Adoção", "direction": 1, "edge_type": "likert", "weight": 0.7},
        {"id": "e6", "from": "Percepção de Valor", "to": "Adoção", "direction": 1, "edge_type": "likert", "weight": 0.6},
    ],
}

# Mock Pass 2: Node premissa options for interaction nodes only (outcome built from interactions)
MOCK_NODE_OPTIONS_RESPONSE = {
    "nodes": [
        {
            "name": "Confiança",
            "header": "Qual o peso de Confiança no modelo?",
            "options": [
                {"text": "Confiança é absolutamente crítica para adoção.", "mu": 0.80, "sigma": 0.15},
                {"text": "Confiança tem influência significativa.", "mu": 0.65, "sigma": 0.25},
                {"text": "Não sei avaliar o peso de Confiança.", "mu": 0.50, "sigma": 0.50},
                {"text": "Confiança tem influência limitada.", "mu": 0.30, "sigma": 0.25},
                {"text": "Confiança é negligível para adoção.", "mu": 0.15, "sigma": 0.15},
            ],
            "default": 1,
        },
        {
            "name": "Percepção de Valor",
            "header": "Qual o peso de Percepção de Valor no modelo?",
            "options": [
                {"text": "Percepção de valor é o fator mais importante.", "mu": 0.80, "sigma": 0.15},
                {"text": "Percepção de valor tem forte influência.", "mu": 0.65, "sigma": 0.25},
                {"text": "Não sei avaliar o peso de Percepção de Valor.", "mu": 0.50, "sigma": 0.50},
                {"text": "Percepção de valor tem pouca influência.", "mu": 0.30, "sigma": 0.25},
                {"text": "Percepção de valor não importa.", "mu": 0.15, "sigma": 0.15},
            ],
            "default": 0,
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
    """Create a mock LLM client that returns topology then node options."""
    client = MagicMock()
    # First call: topology, Second call: node options
    client.complete_json.side_effect = [
        json.dumps(MOCK_TOPOLOGY_RESPONSE),
        json.dumps(MOCK_NODE_OPTIONS_RESPONSE),
    ]
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
    orm_model.label = MOCK_TOPOLOGY_RESPONSE["label"]
    orm_model.intercept_mu = MOCK_TOPOLOGY_RESPONSE["interceptMu"]
    orm_model.intercept_sigma = MOCK_TOPOLOGY_RESPONSE["interceptSigma"]
    orm_model.nodes = [n["name"] for n in MOCK_TOPOLOGY_RESPONSE["nodes"]]
    orm_model.node_metadata = {
        n["name"]: {"name": n["name"], "node_type": n["type"]}
        for n in MOCK_TOPOLOGY_RESPONSE["nodes"]
    }
    orm_model.created_at = "2026-02-14T10:30:00Z"

    # Mock edges (structural, no options)
    edges = []
    for e in MOCK_TOPOLOGY_RESPONSE["edges"]:
        edge = MagicMock()
        edge.id = e["id"]
        edge.from_node = e["from"]
        edge.to_node = e["to"]
        edge.user_var = None
        edge.direction = e["direction"]
        edge.header = f"{e['from']} → {e['to']}"
        edge.options = None
        edge.default_option = 0
        edge.selected_option = None
        edge.edge_type = e["edge_type"]
        edge.weight = e.get("weight")
        edges.append(edge)

    orm_model.edges = edges
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

        assert result["label"] == MOCK_TOPOLOGY_RESPONSE["label"]
        assert len(result["nodes"]) == 7
        assert len(result["edges"]) == 6
        assert result["intercept_mu"] == 0.1
        assert result["intercept_sigma"] == 0.4

    def test_calls_llm_twice_for_two_passes(
        self, mock_llm_client, mock_causal_model_repo, mock_experiment_repo
    ):
        """Verify LLM is called twice: Pass 1 (topology) + Pass 2 (node options)."""
        service = QuantitativeAnalysisService(
            llm_client=mock_llm_client,
            causal_model_repo=mock_causal_model_repo,
            experiment_repo=mock_experiment_repo,
        )

        service.generate_causal_model("exp_12345678")

        assert mock_llm_client.complete_json.call_count == 2

        # Pass 1: topology with gpt-5.2
        call1 = mock_llm_client.complete_json.call_args_list[0]
        messages1 = call1.kwargs.get("messages") or call1[1].get("messages")
        model1 = call1.kwargs.get("model") or call1[1].get("model")
        assert "causal DAG" in messages1[0]["content"]
        assert "Pix Parcelado" in messages1[1]["content"]
        assert model1 == "gpt-5.2"

        # Pass 2: node options with gpt-4.1-nano
        call2 = mock_llm_client.complete_json.call_args_list[1]
        model2 = call2.kwargs.get("model") or call2[1].get("model")
        assert model2 == "gpt-4.1-nano"

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

    def test_saves_model_with_node_metadata_premissas(
        self, mock_llm_client, mock_causal_model_repo, mock_experiment_repo
    ):
        """Verify model is saved with node premissa options in node_metadata."""
        service = QuantitativeAnalysisService(
            llm_client=mock_llm_client,
            causal_model_repo=mock_causal_model_repo,
            experiment_repo=mock_experiment_repo,
        )

        service.generate_causal_model("exp_12345678")

        mock_causal_model_repo.create_with_edges.assert_called_once()
        call_kwargs = mock_causal_model_repo.create_with_edges.call_args.kwargs

        node_metadata = call_kwargs["node_metadata"]

        # Interaction nodes should have premissa options
        assert "Confiança" in node_metadata
        assert node_metadata["Confiança"]["header"] == "Qual o peso de Confiança no modelo?"
        assert len(node_metadata["Confiança"]["options"]) == 5
        assert node_metadata["Confiança"]["default_option"] == 1
        assert node_metadata["Confiança"]["selected_option"] is None

        # Outcome node options built from interaction names (2 interactions)
        assert "Adoção" in node_metadata
        assert len(node_metadata["Adoção"]["options"]) == 2
        option_texts = [o["text"] for o in node_metadata["Adoção"]["options"]]
        assert "Confiança" in option_texts
        assert "Percepção de Valor" in option_texts
        assert node_metadata["Adoção"]["default_option"] == 0

        # Product nodes should NOT have premissa options
        assert "Facilidade de Uso" in node_metadata
        assert "options" not in node_metadata["Facilidade de Uso"] or not node_metadata["Facilidade de Uso"].get("options")

    def test_edges_are_structural_no_options(
        self, mock_llm_client, mock_causal_model_repo, mock_experiment_repo
    ):
        """Verify all edges are structural (no Likert options on edges)."""
        service = QuantitativeAnalysisService(
            llm_client=mock_llm_client,
            causal_model_repo=mock_causal_model_repo,
            experiment_repo=mock_experiment_repo,
        )

        service.generate_causal_model("exp_12345678")

        call_kwargs = mock_causal_model_repo.create_with_edges.call_args.kwargs
        for edge in call_kwargs["edges"]:
            assert edge["options"] is None
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
