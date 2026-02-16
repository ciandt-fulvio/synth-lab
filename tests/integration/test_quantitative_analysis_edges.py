"""
T015 Integration test for update_edge_selections().

Tests edge selection persistence, partial updates, and invalid edge rejection.

References:
    - Service: src/synth_lab/services/quantitative_analysis_service.py
    - Contracts: specs/042-quantitative-analysis/contracts/api.md
"""

from unittest.mock import MagicMock

import pytest

from synth_lab.services.quantitative_analysis_service import (
    QuantitativeAnalysisService,
)


def _make_mock_edge(edge_id: str, selected_option: int | None = None) -> MagicMock:
    """Create a mock edge ORM object."""
    edge = MagicMock()
    edge.id = edge_id
    edge.from_node = "Node A"
    edge.to_node = "Node B"
    edge.user_var = "ageNorm"
    edge.direction = 1
    edge.header = f"Header for {edge_id}"
    edge.options = [{"text": f"Option {i}", "mu": 0.8 - i * 0.15, "sigma": 0.15 + i * 0.05} for i in range(5)]
    edge.default_option = 2
    edge.selected_option = selected_option
    return edge


def _make_mock_model(edges: list[MagicMock]) -> MagicMock:
    """Create a mock causal model ORM object."""
    model = MagicMock()
    model.id = "cm_test1234"
    model.experiment_id = "exp_12345678"
    model.edges = edges
    return model


@pytest.mark.integration
class TestUpdateEdgeSelections:
    """Integration tests for update_edge_selections()."""

    def test_updates_single_edge(self):
        """Save selection for one edge, verify persistence."""
        edges = [_make_mock_edge("e1"), _make_mock_edge("e2"), _make_mock_edge("e3")]
        model = _make_mock_model(edges)

        repo = MagicMock()
        repo.get_by_experiment.return_value = model
        repo.update_edge_selections.return_value = {"updated": 1, "skipped": 0}

        # After update, simulate one edge answered
        edges_after = [_make_mock_edge("e1", selected_option=2), _make_mock_edge("e2"), _make_mock_edge("e3")]
        model_after = _make_mock_model(edges_after)
        repo.get_by_experiment.side_effect = [model, model_after]

        service = QuantitativeAnalysisService(
            llm_client=MagicMock(),
            causal_model_repo=repo,
            experiment_repo=MagicMock(),
        )

        result = service.update_edge_selections("exp_12345678", {"e1": 2})

        assert result["updated_count"] == 1
        assert result["answered_count"] == 1
        assert result["total_edges"] == 3
        assert result["all_answered"] is False

    def test_updates_multiple_edges(self):
        """Save selections for multiple edges at once."""
        edges = [_make_mock_edge("e1"), _make_mock_edge("e2"), _make_mock_edge("e3")]
        model = _make_mock_model(edges)

        repo = MagicMock()
        repo.get_by_experiment.return_value = model
        repo.update_edge_selections.return_value = {"updated": 3, "skipped": 0}

        # After update, all edges answered
        edges_after = [
            _make_mock_edge("e1", selected_option=0),
            _make_mock_edge("e2", selected_option=1),
            _make_mock_edge("e3", selected_option=4),
        ]
        model_after = _make_mock_model(edges_after)
        repo.get_by_experiment.side_effect = [model, model_after]

        service = QuantitativeAnalysisService(
            llm_client=MagicMock(),
            causal_model_repo=repo,
            experiment_repo=MagicMock(),
        )

        result = service.update_edge_selections(
            "exp_12345678", {"e1": 0, "e2": 1, "e3": 4}
        )

        assert result["updated_count"] == 3
        assert result["all_answered"] is True
        assert result["answered_count"] == 3
        assert result["total_edges"] == 3

    def test_partial_update_preserves_existing(self):
        """Update only some edges — others keep their selection."""
        edges = [
            _make_mock_edge("e1", selected_option=0),
            _make_mock_edge("e2"),
            _make_mock_edge("e3", selected_option=3),
        ]
        model = _make_mock_model(edges)

        repo = MagicMock()
        repo.get_by_experiment.return_value = model
        repo.update_edge_selections.return_value = {"updated": 1, "skipped": 0}

        # After update, e1 and e3 were already answered, now e2 is too
        edges_after = [
            _make_mock_edge("e1", selected_option=0),
            _make_mock_edge("e2", selected_option=2),
            _make_mock_edge("e3", selected_option=3),
        ]
        model_after = _make_mock_model(edges_after)
        repo.get_by_experiment.side_effect = [model, model_after]

        service = QuantitativeAnalysisService(
            llm_client=MagicMock(),
            causal_model_repo=repo,
            experiment_repo=MagicMock(),
        )

        result = service.update_edge_selections("exp_12345678", {"e2": 2})

        assert result["updated_count"] == 1
        assert result["all_answered"] is True
        assert result["answered_count"] == 3

    def test_skips_invalid_edge_id(self):
        """Invalid edge IDs are skipped, not raising errors."""
        edges = [_make_mock_edge("e1"), _make_mock_edge("e2")]
        model = _make_mock_model(edges)

        repo = MagicMock()
        repo.get_by_experiment.return_value = model
        repo.update_edge_selections.return_value = {"updated": 1, "skipped": 1}

        # After update, only e1 updated, e999 was skipped
        edges_after = [_make_mock_edge("e1", selected_option=3), _make_mock_edge("e2")]
        model_after = _make_mock_model(edges_after)
        repo.get_by_experiment.side_effect = [model, model_after]

        service = QuantitativeAnalysisService(
            llm_client=MagicMock(),
            causal_model_repo=repo,
            experiment_repo=MagicMock(),
        )

        result = service.update_edge_selections(
            "exp_12345678", {"e1": 3, "e999": 0}
        )

        assert result["updated_count"] == 1

    def test_raises_when_no_model_exists(self):
        """ValueError raised when experiment has no causal model."""
        repo = MagicMock()
        repo.get_by_experiment.return_value = None

        service = QuantitativeAnalysisService(
            llm_client=MagicMock(),
            causal_model_repo=repo,
            experiment_repo=MagicMock(),
        )

        with pytest.raises(ValueError, match="No causal model"):
            service.update_edge_selections("exp_12345678", {"e1": 0})
