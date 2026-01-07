"""
T003 [TEST] Experiment entity tests.

Tests for Experiment domain entity including ID generation and field validation.

References:
    - Data model: specs/018-experiment-hub/data-model.md
"""

import pytest

from synth_lab.domain.entities.experiment import (
    Experiment,
    generate_experiment_id,
)


class TestGenerateExperimentId:
    """Tests for experiment ID generation."""

    def test_generates_exp_prefix(self) -> None:
        """Verify ID starts with 'exp_' prefix."""
        exp_id = generate_experiment_id()
        assert exp_id.startswith("exp_"), f"ID should start with 'exp_': {exp_id}"

    def test_generates_8_char_hex_suffix(self) -> None:
        """Verify ID has 8-character hex suffix after prefix."""
        exp_id = generate_experiment_id()
        suffix = exp_id[4:]  # Remove 'exp_' prefix
        assert len(suffix) == 8, f"Suffix should be 8 chars: {suffix}"
        # Verify it's valid hex
        int(suffix, 16)

    def test_generates_unique_ids(self) -> None:
        """Verify IDs are unique."""
        ids = {generate_experiment_id() for _ in range(100)}
        assert len(ids) == 100, "Generated IDs should be unique"


class TestExperimentEntity:
    """Tests for Experiment entity."""

    def test_create_with_required_fields(self) -> None:
        """Create experiment with only required fields."""
        exp = Experiment(
            name="Test Feature",
            hypothesis="This will improve conversion by 10%",
        )
        assert exp.name == "Test Feature"
        assert exp.hypothesis == "This will improve conversion by 10%"
        assert exp.description is None
        assert exp.id.startswith("exp_")
        assert exp.created_at is not None
        assert exp.updated_at is None

    def test_create_with_all_fields(self) -> None:
        """Create experiment with all fields."""
        exp = Experiment(
            id="exp_12345678",
            name="Full Feature",
            hypothesis="Hypothesis text",
            description="Optional description",
        )
        assert exp.id == "exp_12345678"
        assert exp.description == "Optional description"

    def test_name_max_length_100(self) -> None:
        """Verify name accepts up to 100 characters."""
        name_100 = "x" * 100
        exp = Experiment(name=name_100, hypothesis="test")
        assert len(exp.name) == 100

    def test_name_rejects_over_100_chars(self) -> None:
        """Verify name rejects more than 100 characters."""
        name_101 = "x" * 101
        with pytest.raises(ValueError):
            Experiment(name=name_101, hypothesis="test")

    def test_hypothesis_max_length_500(self) -> None:
        """Verify hypothesis accepts up to 500 characters."""
        hypothesis_500 = "x" * 500
        exp = Experiment(name="test", hypothesis=hypothesis_500)
        assert len(exp.hypothesis) == 500

    def test_hypothesis_rejects_over_500_chars(self) -> None:
        """Verify hypothesis rejects more than 500 characters."""
        hypothesis_501 = "x" * 501
        with pytest.raises(ValueError):
            Experiment(name="test", hypothesis=hypothesis_501)

    def test_description_max_length_2000(self) -> None:
        """Verify description accepts up to 2000 characters."""
        desc_2000 = "x" * 2000
        exp = Experiment(name="test", hypothesis="test", description=desc_2000)
        assert len(exp.description) == 2000

    def test_description_rejects_over_2000_chars(self) -> None:
        """Verify description rejects more than 2000 characters."""
        desc_2001 = "x" * 2001
        with pytest.raises(ValueError):
            Experiment(name="test", hypothesis="test", description=desc_2001)

    def test_id_pattern_validation(self) -> None:
        """Verify ID must match exp_[a-z0-9_]+ pattern."""
        # Valid patterns
        exp = Experiment(id="exp_abcd1234", name="test", hypothesis="test")
        assert exp.id == "exp_abcd1234"

        # Short suffix is also valid (pattern allows any length >= 1)
        exp_short = Experiment(id="exp_12345", name="test", hypothesis="test")
        assert exp_short.id == "exp_12345"

        # Invalid pattern - doesn't start with exp_
        with pytest.raises(ValueError):
            Experiment(id="invalid", name="test", hypothesis="test")

    def test_model_dump(self) -> None:
        """Verify model_dump produces valid dict."""
        exp = Experiment(name="Test", hypothesis="Hypothesis")
        data = exp.model_dump()
        assert "id" in data
        assert "name" in data
        assert data["name"] == "Test"

    def test_model_dump_mode_json(self) -> None:
        """Verify model_dump with mode='json' serializes dates."""
        exp = Experiment(name="Test", hypothesis="Hypothesis")
        data = exp.model_dump(mode="json")
        assert isinstance(data["created_at"], str)
