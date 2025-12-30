"""
Unit tests for observable label utilities.

Tests:
- value_to_label() boundary values and error handling
- format_observables_with_labels() complete formatting

References:
    - Module: src/synth_lab/services/observable_labels.py
    - Spec: specs/022-observable-latent-traits/spec.md (US1, US4)
"""

import pytest

from synth_lab.domain.entities.simulation_attributes import SimulationObservables
from synth_lab.services.observable_labels import (
    ObservableWithLabel,
    format_observable_with_label,
    format_observables_with_labels,
    value_to_label,
)


class TestValueToLabel:
    """Tests for value_to_label function."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            # Muito Baixo: [0, 0.20)
            (0.00, "Muito Baixo"),
            (0.10, "Muito Baixo"),
            (0.19, "Muito Baixo"),
            # Baixo: [0.20, 0.40)
            (0.20, "Baixo"),
            (0.30, "Muito Baixo"),  # This will fail - 0.30 should be "Baixo"
            (0.39, "Baixo"),
            # Médio: [0.40, 0.60)
            (0.40, "Médio"),
            (0.50, "Médio"),
            (0.59, "Médio"),
            # Alto: [0.60, 0.80)
            (0.60, "Alto"),
            (0.70, "Alto"),
            (0.79, "Alto"),
            # Muito Alto: [0.80, 1.00]
            (0.80, "Muito Alto"),
            (0.90, "Muito Alto"),
            (1.00, "Muito Alto"),
        ],
    )
    def test_boundary_values(self, value: float, expected: str) -> None:
        """Value to label conversion respects boundaries correctly."""
        # Fix test case - 0.30 should be "Baixo", not "Muito Baixo"
        if value == 0.30:
            expected = "Baixo"
        result = value_to_label(value)
        assert result == expected, f"value_to_label({value}) = '{result}', expected '{expected}'"

    def test_rejects_negative_values(self) -> None:
        """Negative values are rejected with ValueError."""
        with pytest.raises(ValueError, match=r"Value must be in \[0, 1\]"):
            value_to_label(-0.1)

    def test_rejects_values_above_one(self) -> None:
        """Values > 1 are rejected with ValueError."""
        with pytest.raises(ValueError, match=r"Value must be in \[0, 1\]"):
            value_to_label(1.5)

    def test_exact_boundary_zero(self) -> None:
        """Exact zero returns 'Muito Baixo'."""
        assert value_to_label(0.0) == "Muito Baixo"

    def test_exact_boundary_one(self) -> None:
        """Exact one returns 'Muito Alto'."""
        assert value_to_label(1.0) == "Muito Alto"


class TestFormatObservableWithLabel:
    """Tests for format_observable_with_label function."""

    def test_digital_literacy_formatting(self) -> None:
        """Digital literacy is correctly formatted with label."""
        result = format_observable_with_label("digital_literacy", 0.35)

        assert result.key == "digital_literacy"
        assert result.name == "Literacia Digital"
        assert result.value == 0.35
        assert result.label == "Baixo"
        assert "tecnologia" in result.description.lower()

    def test_motor_ability_high_value(self) -> None:
        """Motor ability with high value gets 'Muito Alto' label."""
        result = format_observable_with_label("motor_ability", 0.85)

        assert result.key == "motor_ability"
        assert result.name == "Capacidade Motora"
        assert result.value == 0.85
        assert result.label == "Muito Alto"

    def test_unknown_key_raises_error(self) -> None:
        """Unknown observable key raises ValueError."""
        with pytest.raises(ValueError, match=r"Unknown observable key"):
            format_observable_with_label("unknown_key", 0.5)

    def test_all_five_observables_work(self) -> None:
        """All 5 observable keys can be formatted."""
        keys = [
            "digital_literacy",
            "similar_tool_experience",
            "motor_ability",
            "time_availability",
            "domain_expertise",
        ]
        for key in keys:
            result = format_observable_with_label(key, 0.5)
            assert result.key == key
            assert result.label == "Médio"
            assert result.description


class TestFormatObservablesWithLabels:
    """Tests for format_observables_with_labels function."""

    def test_returns_five_formatted_observables(self) -> None:
        """Returns exactly 5 formatted observables."""
        obs = SimulationObservables(
            digital_literacy=0.35,
            similar_tool_experience=0.42,
            motor_ability=0.85,
            time_availability=0.28,
            domain_expertise=0.55,
        )
        result = format_observables_with_labels(obs)

        assert len(result) == 5
        assert all(isinstance(item, ObservableWithLabel) for item in result)

    def test_all_observables_have_labels(self) -> None:
        """All returned observables have proper labels."""
        obs = SimulationObservables(
            digital_literacy=0.35,
            similar_tool_experience=0.42,
            motor_ability=0.85,
            time_availability=0.28,
            domain_expertise=0.55,
        )
        result = format_observables_with_labels(obs)

        # Find specific observables
        digital = next(o for o in result if o.key == "digital_literacy")
        motor = next(o for o in result if o.key == "motor_ability")
        time_avail = next(o for o in result if o.key == "time_availability")

        assert digital.label == "Baixo"  # 0.35 -> Baixo
        assert motor.label == "Muito Alto"  # 0.85 -> Muito Alto
        assert time_avail.label == "Baixo"  # 0.28 -> Baixo

    def test_observables_have_portuguese_names(self) -> None:
        """All observable names are in Portuguese."""
        obs = SimulationObservables(
            digital_literacy=0.5,
            similar_tool_experience=0.5,
            motor_ability=0.5,
            time_availability=0.5,
            domain_expertise=0.5,
        )
        result = format_observables_with_labels(obs)

        # Check for Portuguese indicators
        names = [o.name for o in result]
        assert "Literacia Digital" in names
        assert "Capacidade Motora" in names
        assert "Disponibilidade de Tempo" in names

    def test_edge_case_all_zeros(self) -> None:
        """Handles edge case with all zero values."""
        obs = SimulationObservables(
            digital_literacy=0.0,
            similar_tool_experience=0.0,
            motor_ability=0.0,
            time_availability=0.0,
            domain_expertise=0.0,
        )
        result = format_observables_with_labels(obs)

        assert len(result) == 5
        assert all(o.label == "Muito Baixo" for o in result)

    def test_edge_case_all_ones(self) -> None:
        """Handles edge case with all one values."""
        obs = SimulationObservables(
            digital_literacy=1.0,
            similar_tool_experience=1.0,
            motor_ability=1.0,
            time_availability=1.0,
            domain_expertise=1.0,
        )
        result = format_observables_with_labels(obs)

        assert len(result) == 5
        assert all(o.label == "Muito Alto" for o in result)


class TestObservableWithLabelDataclass:
    """Tests for ObservableWithLabel dataclass."""

    def test_dataclass_fields(self) -> None:
        """ObservableWithLabel has all required fields."""
        obj = ObservableWithLabel(
            key="test_key",
            name="Test Name",
            value=0.5,
            label="Médio",
            description="Test description",
        )

        assert obj.key == "test_key"
        assert obj.name == "Test Name"
        assert obj.value == 0.5
        assert obj.label == "Médio"
        assert obj.description == "Test description"
