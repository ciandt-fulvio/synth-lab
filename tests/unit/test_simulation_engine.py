"""
T027 Unit test for simulation_engine with deterministic seed.

Tests run_monte_carlo with fixed seed=42, verifies stats within expected ranges,
distribution length, and segment buckets.

References:
    - Engine: src/synth_lab/services/simulation_engine.py
    - Spec: specs/042-quantitative-analysis/spec.md (Apêndice D)
"""

import numpy as np
import pytest

from synth_lab.services.simulation_engine import (
    compute_raw_interpretations,
    compute_segments,
    run_monte_carlo,
    run_sensitivity,
)


def _make_edges(n: int = 3) -> list[dict]:
    """Create test edges with standard Likert options."""
    options = [
        {"text": "Strong effect", "mu": 0.80, "sigma": 0.15},
        {"text": "Significant effect", "mu": 0.65, "sigma": 0.25},
        {"text": "Uncertain", "mu": 0.50, "sigma": 0.50},
        {"text": "Weak effect", "mu": 0.30, "sigma": 0.25},
        {"text": "No effect", "mu": 0.15, "sigma": 0.15},
    ]
    edges = []
    for i in range(n):
        edges.append({
            "id": f"e{i+1}",
            "from_node": f"Node{i}",
            "to_node": f"Node{i+1}",
            "user_var": "ageNorm",
            "direction": 1 if i % 2 == 0 else -1,
            "header": f"Edge {i+1} header",
            "options": options,
            "default_option": 2,
        })
    return edges


def _make_synths(n: int = 50) -> list[dict]:
    """Create test synths with varied demographics."""
    synths = []
    for i in range(n):
        synths.append({
            "data": {
                "demografia": {
                    "idade": 20 + (i * 60 // n),
                    "renda_mensal": 1000 + i * 400,
                    "escolaridade": ["fundamental completo", "médio completo", "superior completo"][i % 3],
                    "composicao_familiar": {"numero_pessoas": 1 + (i % 5)},
                },
                "deficiencias": {
                    "visual": {"tipo": "nenhuma" if i % 10 != 0 else "leve"},
                    "motora": {"tipo": "nenhuma" if i % 15 != 0 else "moderada"},
                },
                "sensitivities": {
                    "digital_capability": 0.3 + (i / n) * 0.5,
                    "risk_aversion": 0.2 + (i / n) * 0.6,
                    "institutional_trust_level": 0.4 + (i / n) * 0.3,
                    "friction_tolerance": 0.3 + (i / n) * 0.4,
                },
            }
        })
    return synths


def _make_user_var_matrix(synths: list[dict], edges: list[dict]) -> np.ndarray:
    """Create a simple user var matrix for testing."""
    from synth_lab.services.simulation_engine import extract_user_vars
    user_vars = [e["user_var"] for e in edges]
    return extract_user_vars(synths, user_vars)


@pytest.mark.unit
class TestRunMonteCarlo:
    """Unit tests for run_monte_carlo()."""

    def test_deterministic_with_seed(self):
        """Same seed produces identical results."""
        edges = _make_edges(3)
        selections = {"e1": 0, "e2": 1, "e3": 2}
        synths = _make_synths(30)
        uvm = _make_user_var_matrix(synths, edges)

        result1 = run_monte_carlo(edges, selections, uvm, 0.1, 0.4, n_iterations=100, seed=42)
        result2 = run_monte_carlo(edges, selections, uvm, 0.1, 0.4, n_iterations=100, seed=42)

        assert result1["stats"] == result2["stats"]
        assert result1["distribution"] == result2["distribution"]

    def test_distribution_length_matches_iterations(self):
        """Distribution array length equals n_iterations."""
        edges = _make_edges(2)
        selections = {"e1": 2, "e2": 2}
        synths = _make_synths(20)
        uvm = _make_user_var_matrix(synths, edges)

        result = run_monte_carlo(edges, selections, uvm, 0.1, 0.4, n_iterations=500, seed=42)

        assert len(result["distribution"]) == 500

    def test_stats_have_required_keys(self):
        """Stats dict contains mean, median, std, p10, p90."""
        edges = _make_edges(3)
        selections = {"e1": 0, "e2": 1, "e3": 2}
        synths = _make_synths(30)
        uvm = _make_user_var_matrix(synths, edges)

        result = run_monte_carlo(edges, selections, uvm, 0.1, 0.4, n_iterations=200, seed=42)

        for key in ("mean", "median", "std", "p10", "p90"):
            assert key in result["stats"]
            assert isinstance(result["stats"][key], float)

    def test_stats_within_valid_range(self):
        """All stats are between 0 and 100 (percentage)."""
        edges = _make_edges(4)
        selections = {"e1": 0, "e2": 1, "e3": 3, "e4": 4}
        synths = _make_synths(50)
        uvm = _make_user_var_matrix(synths, edges)

        result = run_monte_carlo(edges, selections, uvm, 0.1, 0.4, n_iterations=300, seed=42)

        assert 0 <= result["stats"]["mean"] <= 100
        assert 0 <= result["stats"]["median"] <= 100
        assert result["stats"]["p10"] <= result["stats"]["p90"]

    def test_uses_default_when_selection_missing(self):
        """Falls back to default_option when edge not in selections."""
        edges = _make_edges(2)
        selections = {}  # No selections — uses defaults
        synths = _make_synths(20)
        uvm = _make_user_var_matrix(synths, edges)

        result = run_monte_carlo(edges, selections, uvm, 0.1, 0.4, n_iterations=100, seed=42)

        assert "mean" in result["stats"]
        assert len(result["distribution"]) == 100


@pytest.mark.unit
class TestComputeSegments:
    """Unit tests for compute_segments()."""

    def test_returns_all_three_dimensions(self):
        """Result contains age, income, education keys."""
        edges = _make_edges(2)
        selections = {"e1": 1, "e2": 2}
        synths = _make_synths(30)
        uvm = _make_user_var_matrix(synths, edges)

        result = compute_segments(edges, selections, synths, uvm, 0.1, 0.4, seed=42)

        assert "age" in result
        assert "income" in result
        assert "education" in result

    def test_age_buckets_correct(self):
        """Age segments have expected bucket names."""
        edges = _make_edges(2)
        selections = {"e1": 1, "e2": 2}
        synths = _make_synths(30)
        uvm = _make_user_var_matrix(synths, edges)

        result = compute_segments(edges, selections, synths, uvm, 0.1, 0.4, seed=42)

        assert set(result["age"].keys()) == {"18-29", "30-49", "50+"}

    def test_segment_counts_sum_to_total(self):
        """All synths are accounted for in each dimension."""
        edges = _make_edges(2)
        selections = {"e1": 1, "e2": 2}
        synths = _make_synths(40)
        uvm = _make_user_var_matrix(synths, edges)

        result = compute_segments(edges, selections, synths, uvm, 0.1, 0.4, seed=42)

        for dim in ("age", "income", "education"):
            total = sum(v["count"] for v in result[dim].values())
            assert total == 40


@pytest.mark.unit
class TestRunSensitivity:
    """Unit tests for run_sensitivity()."""

    def test_returns_one_entry_per_edge(self):
        """Sensitivity results have one entry per edge."""
        edges = _make_edges(3)
        selections = {"e1": 2, "e2": 2, "e3": 2}
        synths = _make_synths(20)
        uvm = _make_user_var_matrix(synths, edges)

        result = run_sensitivity(edges, selections, uvm, 0.1, 0.4, seed=42)

        assert len(result) == 3

    def test_sorted_by_impact_descending(self):
        """Results sorted by impact from highest to lowest."""
        edges = _make_edges(3)
        selections = {"e1": 2, "e2": 2, "e3": 2}
        synths = _make_synths(20)
        uvm = _make_user_var_matrix(synths, edges)

        result = run_sensitivity(edges, selections, uvm, 0.1, 0.4, seed=42)

        impacts = [r["impact"] for r in result]
        assert impacts == sorted(impacts, reverse=True)

    def test_impact_non_negative(self):
        """All impact values are >= 0."""
        edges = _make_edges(2)
        selections = {"e1": 2, "e2": 2}
        synths = _make_synths(20)
        uvm = _make_user_var_matrix(synths, edges)

        result = run_sensitivity(edges, selections, uvm, 0.1, 0.4, seed=42)

        for item in result:
            assert item["impact"] >= 0

    def test_has_required_fields(self):
        """Each sensitivity item has required fields."""
        edges = _make_edges(2)
        selections = {"e1": 2, "e2": 2}
        synths = _make_synths(20)
        uvm = _make_user_var_matrix(synths, edges)

        result = run_sensitivity(edges, selections, uvm, 0.1, 0.4, seed=42)

        for item in result:
            assert "edge_id" in item
            assert "header" in item
            assert "impact" in item
            assert "mean_low" in item
            assert "mean_high" in item


@pytest.mark.unit
class TestComputeRawInterpretations:
    """Unit tests for compute_raw_interpretations()."""

    def test_returns_all_three_sections(self):
        """Result contains distribution, segments, sensitivity keys."""
        stats = {"mean": 42.0, "median": 41.0, "std": 3.5, "p10": 38.0, "p90": 46.0}
        segments = {
            "age": {"18-29": {"rate": 55.0, "count": 30}, "30-49": {"rate": 42.0, "count": 40}, "50+": {"rate": 28.0, "count": 30}},
            "income": {"baixa": {"rate": 35.0, "count": 33}, "media": {"rate": 43.0, "count": 34}, "alta": {"rate": 50.0, "count": 33}},
            "education": {"baixa": {"rate": 33.0, "count": 30}, "media": {"rate": 44.0, "count": 35}, "alta": {"rate": 52.0, "count": 35}},
        }
        sensitivity = [
            {"edge_id": "e1", "header": "Edge 1", "impact": 12.5, "mean_low": 48.0, "mean_high": 35.5},
            {"edge_id": "e2", "header": "Edge 2", "impact": 8.0, "mean_low": 46.0, "mean_high": 38.0},
        ]

        result = compute_raw_interpretations(stats, segments, sensitivity)

        assert "distribution" in result
        assert "segments" in result
        assert "sensitivity" in result

    def test_distribution_contains_confidence_interval(self):
        """Distribution text mentions p10 and p90."""
        stats = {"mean": 42.0, "median": 41.0, "std": 2.0, "p10": 38.0, "p90": 46.0}

        result = compute_raw_interpretations(stats, {"age": {}, "income": {}, "education": {}}, [])

        assert "38.0%" in result["distribution"]
        assert "46.0%" in result["distribution"]

    def test_classifies_uncertainty_levels(self):
        """Uncertainty classification based on std."""
        # High uncertainty
        stats_high = {"mean": 42.0, "median": 41.0, "std": 4.0, "p10": 35.0, "p90": 49.0}
        result_high = compute_raw_interpretations(stats_high, {"age": {}, "income": {}, "education": {}}, [])
        assert "alta" in result_high["distribution"]

        # Low uncertainty
        stats_low = {"mean": 42.0, "median": 41.5, "std": 1.0, "p10": 40.5, "p90": 43.5}
        result_low = compute_raw_interpretations(stats_low, {"age": {}, "income": {}, "education": {}}, [])
        assert "baixa" in result_low["distribution"]
