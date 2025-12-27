"""
T004 [TEST] SynthGroup entity tests.

Tests for SynthGroup domain entity including ID generation and field validation.

References:
    - Data model: specs/018-experiment-hub/data-model.md
"""

import pytest

from synth_lab.domain.entities.synth_group import (
    SynthGroup,
    generate_synth_group_id,
)


class TestGenerateSynthGroupId:
    """Tests for synth group ID generation."""

    def test_generates_grp_prefix(self) -> None:
        """Verify ID starts with 'grp_' prefix."""
        grp_id = generate_synth_group_id()
        assert grp_id.startswith("grp_"), f"ID should start with 'grp_': {grp_id}"

    def test_generates_8_char_hex_suffix(self) -> None:
        """Verify ID has 8-character hex suffix after prefix."""
        grp_id = generate_synth_group_id()
        suffix = grp_id[4:]  # Remove 'grp_' prefix
        assert len(suffix) == 8, f"Suffix should be 8 chars: {suffix}"
        # Verify it's valid hex
        int(suffix, 16)

    def test_generates_unique_ids(self) -> None:
        """Verify IDs are unique."""
        ids = {generate_synth_group_id() for _ in range(100)}
        assert len(ids) == 100, "Generated IDs should be unique"


class TestSynthGroupEntity:
    """Tests for SynthGroup entity."""

    def test_create_with_required_fields(self) -> None:
        """Create synth group with only required fields."""
        group = SynthGroup(name="December 2025 Generation")
        assert group.name == "December 2025 Generation"
        assert group.description is None
        assert group.id.startswith("grp_")
        assert group.created_at is not None

    def test_create_with_all_fields(self) -> None:
        """Create synth group with all fields."""
        group = SynthGroup(
            id="grp_12345678",
            name="Full Group",
            description="Optional description",
        )
        assert group.id == "grp_12345678"
        assert group.description == "Optional description"

    def test_id_pattern_validation(self) -> None:
        """Verify ID must match grp_[a-f0-9]{8} pattern."""
        # Valid pattern
        group = SynthGroup(id="grp_abcd1234", name="test")
        assert group.id == "grp_abcd1234"

        # Invalid patterns
        with pytest.raises(ValueError):
            SynthGroup(id="invalid", name="test")

        with pytest.raises(ValueError):
            SynthGroup(id="grp_12345", name="test")  # Too short

    def test_name_required(self) -> None:
        """Verify name is required."""
        with pytest.raises(ValueError):
            SynthGroup(name="")

    def test_model_dump(self) -> None:
        """Verify model_dump produces valid dict."""
        group = SynthGroup(name="Test Group")
        data = group.model_dump()
        assert "id" in data
        assert "name" in data
        assert data["name"] == "Test Group"

    def test_model_dump_mode_json(self) -> None:
        """Verify model_dump with mode='json' serializes dates."""
        group = SynthGroup(name="Test Group")
        data = group.model_dump(mode="json")
        assert isinstance(data["created_at"], str)
