"""Tests for utils module."""

import pytest
from synth_lab.gen_synth import utils


class TestGerarId:
    """Tests for gerar_id function."""

    def test_default_length(self):
        """Test ID generation with default length."""
        id_result = utils.gerar_id()
        assert len(id_result) == 6
        assert id_result.isalnum()
        assert id_result.islower() or id_result.isdigit()

    def test_custom_length(self):
        """Test ID generation with custom length."""
        id_result = utils.gerar_id(tamanho=10)
        assert len(id_result) == 10

    def test_uniqueness(self):
        """Test that generated IDs are unique."""
        ids = [utils.gerar_id() for _ in range(100)]
        assert len(set(ids)) > 95  # At least 95% unique


class TestWeightedChoice:
    """Tests for weighted_choice function."""

    def test_returns_valid_option(self):
        """Test that result is one of the provided options."""
        options = {"A": 0.7, "B": 0.3}
        result = utils.weighted_choice(options)
        assert result in options.keys()

    def test_distribution(self):
        """Test that weighted choice follows approximate distribution."""
        options = {"A": 0.9, "B": 0.1}
        results = [utils.weighted_choice(options) for _ in range(1000)]
        a_count = results.count("A")
        # With 90% weight, expect roughly 850-950 A's in 1000 tries
        assert 850 <= a_count <= 950


class TestNormalDistribution:
    """Tests for normal_distribution function."""

    def test_default_parameters(self):
        """Test normal distribution with default parameters."""
        value = utils.normal_distribution()
        assert 0 <= value <= 100

    def test_respects_bounds(self):
        """Test that values respect min/max bounds."""
        values = [utils.normal_distribution(50, 15, 0, 100) for _ in range(100)]
        assert all(0 <= v <= 100 for v in values)

    def test_custom_bounds(self):
        """Test custom min/max bounds."""
        value = utils.normal_distribution(mean=10, std=2, min_val=5, max_val=15)
        assert 5 <= value <= 15


class TestEscolaridadeFunctions:
    """Tests for escolaridade helper functions."""

    def test_escolaridade_index_valid(self):
        """Test index retrieval for valid escolaridade."""
        assert utils.escolaridade_index("Sem instrução") == 0
        assert utils.escolaridade_index("Superior completo") == 6
        assert utils.escolaridade_index("Pós-graduação") == 7

    def test_escolaridade_index_invalid(self):
        """Test index retrieval for invalid escolaridade."""
        assert utils.escolaridade_index("Invalid") == 0

    def test_escolaridade_compativel_true(self):
        """Test compatibility check when escolaridade meets minimum."""
        assert utils.escolaridade_compativel(
            "Superior completo", "Médio completo"
        ) is True
        assert utils.escolaridade_compativel(
            "Pós-graduação", "Superior completo"
        ) is True

    def test_escolaridade_compativel_false(self):
        """Test compatibility check when escolaridade doesn't meet minimum."""
        assert utils.escolaridade_compativel(
            "Médio completo", "Superior completo"
        ) is False
        assert utils.escolaridade_compativel(
            "Fundamental completo", "Médio completo"
        ) is False

    def test_escolaridade_compativel_equal(self):
        """Test compatibility when escolaridades are equal."""
        assert utils.escolaridade_compativel(
            "Superior completo", "Superior completo"
        ) is True
