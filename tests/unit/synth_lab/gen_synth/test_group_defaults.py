"""
Unit tests for group_defaults module.

Tests the expand_education_distribution function and default constants.
"""

import pytest

from synth_lab.domain.constants.group_defaults import (
    ESCOLARIDADE_EXPANSION_RATIOS,
    expand_education_distribution,
)


class TestExpandEducationDistribution:
    """Tests for expand_education_distribution function."""

    def test_expands_4_level_to_8_level(self):
        """Test that 4-level education distribution expands to 8-level."""
        input_dist = {
            "sem_instrucao": 0.1,
            "fundamental": 0.3,
            "medio": 0.3,
            "superior": 0.3,
        }

        result = expand_education_distribution(input_dist)

        # Should have 8 levels (display names matching ibge_distributions.json)
        expected_keys = [
            "Sem instrução",
            "Fundamental incompleto",
            "Fundamental completo",
            "Médio incompleto",
            "Médio completo",
            "Superior incompleto",
            "Superior completo",
            "Pós-graduação",
        ]
        assert set(result.keys()) == set(expected_keys)

    def test_expanded_distribution_sums_to_one(self):
        """Test that expanded distribution sums to approximately 1.0."""
        input_dist = {
            "sem_instrucao": 0.1,
            "fundamental": 0.3,
            "medio": 0.3,
            "superior": 0.3,
        }

        result = expand_education_distribution(input_dist)

        total = sum(result.values())
        assert abs(total - 1.0) < 0.01, f"Expected sum ~1.0, got {total}"

    def test_preserves_proportions(self):
        """Test that expanded distribution preserves the original proportions."""
        input_dist = {
            "sem_instrucao": 0.1,
            "fundamental": 0.4,
            "medio": 0.3,
            "superior": 0.2,
        }

        result = expand_education_distribution(input_dist)

        # sem_instrucao maps directly (with display name)
        assert result["Sem instrução"] == 0.1

        # fundamental expands to two levels
        fundamental_sum = result["Fundamental incompleto"] + result["Fundamental completo"]
        assert abs(fundamental_sum - 0.4) < 0.01

        # medio expands to two levels
        medio_sum = result["Médio incompleto"] + result["Médio completo"]
        assert abs(medio_sum - 0.3) < 0.01

        # superior expands to three levels
        superior_sum = (
            result["Superior incompleto"]
            + result["Superior completo"]
            + result["Pós-graduação"]
        )
        assert abs(superior_sum - 0.2) < 0.01

    def test_handles_ibge_defaults(self):
        """Test with IBGE default distribution."""
        ibge_dist = {
            "sem_instrucao": 0.068,
            "fundamental": 0.329,
            "medio": 0.314,
            "superior": 0.289,
        }

        result = expand_education_distribution(ibge_dist)

        # Verify sum
        total = sum(result.values())
        assert abs(total - 1.0) < 0.01

        # Verify all values are positive
        for key, value in result.items():
            assert value >= 0, f"{key} has negative value: {value}"

    def test_handles_extreme_distribution(self):
        """Test with extreme distribution (all in one category)."""
        extreme_dist = {
            "sem_instrucao": 0.0,
            "fundamental": 0.0,
            "medio": 0.0,
            "superior": 1.0,
        }

        result = expand_education_distribution(extreme_dist)

        # All superior levels should sum to 1.0
        superior_sum = (
            result["Superior incompleto"]
            + result["Superior completo"]
            + result["Pós-graduação"]
        )
        assert abs(superior_sum - 1.0) < 0.01

        # Other levels should be 0
        assert result["Sem instrução"] == 0.0
        assert result["Fundamental incompleto"] == 0.0
        assert result["Fundamental completo"] == 0.0

    def test_uses_correct_expansion_ratios(self):
        """Test that correct expansion ratios are used."""
        # Verify the ratios exist and sum correctly
        for category, ratios in ESCOLARIDADE_EXPANSION_RATIOS.items():
            ratio_sum = sum(ratios.values())
            assert abs(ratio_sum - 1.0) < 0.01, f"{category} ratios don't sum to 1.0"

    def test_handles_missing_keys(self):
        """Test that function handles missing keys with defaults."""
        # Only provide some keys
        input_dist = {
            "fundamental": 0.5,
            "superior": 0.5,
        }

        result = expand_education_distribution(input_dist)

        # Missing keys should default to 0
        assert result["Sem instrução"] == 0.0
        assert result["Médio incompleto"] == 0.0
        assert result["Médio completo"] == 0.0

        # Total should still work (0.5 + 0.5 = 1.0)
        total = sum(result.values())
        assert abs(total - 1.0) < 0.01

    def test_handles_uniform_distribution(self):
        """Test that function handles uniform distribution."""
        input_dist = {
            "sem_instrucao": 0.25,
            "fundamental": 0.25,
            "medio": 0.25,
            "superior": 0.25,
        }

        result = expand_education_distribution(input_dist)

        # Should still produce valid output
        assert len(result) == 8
        total = sum(result.values())
        assert abs(total - 1.0) < 0.01
