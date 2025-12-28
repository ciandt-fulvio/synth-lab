"""
SynthGroup entity for synth-lab.

Represents a grouping of synths generated together, allowing tracking of
"batches" or "generations" of synths.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - Data model: specs/018-experiment-hub/data-model.md
"""

import secrets
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

# Default synth group - always exists and is used when no group is specified
DEFAULT_SYNTH_GROUP_ID = "grp_00000001"
DEFAULT_SYNTH_GROUP_NAME = "Default"
DEFAULT_SYNTH_GROUP_DESCRIPTION = "Grupo padrão para synths sem grupo específico"


def generate_synth_group_id() -> str:
    """
    Generate a synth group ID with grp_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format grp_[a-f0-9]{8}
    """
    return f"grp_{secrets.token_hex(4)}"


class SynthGroup(BaseModel):
    """
    SynthGroup entity representing a batch of synths generated together.

    Attributes:
        id: Unique identifier (grp_[a-f0-9]{8})
        name: Descriptive name for the group
        description: Optional description of purpose/context
        created_at: ISO 8601 timestamp of creation
    """

    id: str = Field(
        default_factory=generate_synth_group_id,
        pattern=r"^grp_[a-f0-9]{8}$",
        description="Unique synth group ID.",
    )

    name: str = Field(
        description="Descriptive name for the group.",
    )

    description: str | None = Field(
        default=None,
        description="Optional description of purpose/context.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp.",
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create with required fields
    total_tests += 1
    try:
        group = SynthGroup(name="December 2025 Generation")
        if not group.id.startswith("grp_"):
            all_validation_failures.append(f"ID should start with grp_: {group.id}")
        if group.name != "December 2025 Generation":
            all_validation_failures.append(f"Name mismatch: {group.name}")
    except Exception as e:
        all_validation_failures.append(f"Create with required fields failed: {e}")

    # Test 2: ID generation uniqueness
    total_tests += 1
    try:
        ids = {generate_synth_group_id() for _ in range(100)}
        if len(ids) != 100:
            all_validation_failures.append("IDs should be unique")
    except Exception as e:
        all_validation_failures.append(f"ID generation test failed: {e}")

    # Test 3: Create with all fields
    total_tests += 1
    try:
        group = SynthGroup(
            id="grp_12345678",
            name="Full Group",
            description="Optional description",
        )
        if group.id != "grp_12345678":
            all_validation_failures.append(f"ID mismatch: {group.id}")
        if group.description != "Optional description":
            all_validation_failures.append(f"Description mismatch: {group.description}")
    except Exception as e:
        all_validation_failures.append(f"Create with all fields failed: {e}")

    # Test 4: Reject empty name
    total_tests += 1
    try:
        SynthGroup(name="")
        all_validation_failures.append("Should reject empty name")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for empty name: {e}")

    # Test 5: Reject invalid ID pattern
    total_tests += 1
    try:
        SynthGroup(id="invalid", name="test")
        all_validation_failures.append("Should reject invalid ID pattern")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid ID: {e}")

    # Test 6: model_dump
    total_tests += 1
    try:
        group = SynthGroup(name="Test Group")
        data = group.model_dump()
        if "id" not in data or "name" not in data:
            all_validation_failures.append("model_dump missing fields")
    except Exception as e:
        all_validation_failures.append(f"model_dump test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
