"""
Experiment entity for synth-lab.

Represents a feature or hypothesis to be tested. Central container that groups
related simulations and interviews.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - Data model: specs/018-experiment-hub/data-model.md
"""

import secrets
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


def generate_experiment_id() -> str:
    """
    Generate an experiment ID with exp_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format exp_[a-f0-9]{8}
    """
    return f"exp_{secrets.token_hex(4)}"


class Experiment(BaseModel):
    """
    Experiment entity representing a feature/hypothesis to test.

    Attributes:
        id: Unique identifier (exp_[a-f0-9]{8})
        name: Short name of the feature (max 100 chars)
        hypothesis: Description of the hypothesis to test (max 500 chars)
        description: Additional context, links, references (max 2000 chars)
        created_at: ISO 8601 timestamp of creation
        updated_at: ISO 8601 timestamp of last update
    """

    id: str = Field(
        default_factory=generate_experiment_id,
        pattern=r"^exp_[a-f0-9]{8}$",
        description="Unique experiment ID.",
    )

    name: str = Field(
        max_length=100,
        description="Short name of the feature.",
    )

    hypothesis: str = Field(
        max_length=500,
        description="Description of the hypothesis to test.",
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context, links, references.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp.",
    )

    updated_at: datetime | None = Field(
        default=None,
        description="Last update timestamp.",
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v

    @field_validator("hypothesis")
    @classmethod
    def validate_hypothesis_not_empty(cls, v: str) -> str:
        """Ensure hypothesis is not empty."""
        if not v or not v.strip():
            raise ValueError("hypothesis cannot be empty")
        return v


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create with required fields
    total_tests += 1
    try:
        exp = Experiment(name="Test", hypothesis="Test hypothesis")
        if not exp.id.startswith("exp_"):
            all_validation_failures.append(f"ID should start with exp_: {exp.id}")
        if exp.name != "Test":
            all_validation_failures.append(f"Name mismatch: {exp.name}")
    except Exception as e:
        all_validation_failures.append(f"Create with required fields failed: {e}")

    # Test 2: ID generation uniqueness
    total_tests += 1
    try:
        ids = {generate_experiment_id() for _ in range(100)}
        if len(ids) != 100:
            all_validation_failures.append("IDs should be unique")
    except Exception as e:
        all_validation_failures.append(f"ID generation test failed: {e}")

    # Test 3: Name max length
    total_tests += 1
    try:
        exp = Experiment(name="x" * 100, hypothesis="test")
        if len(exp.name) != 100:
            all_validation_failures.append(f"Name should be 100 chars: {len(exp.name)}")
    except Exception as e:
        all_validation_failures.append(f"Name max length test failed: {e}")

    # Test 4: Reject name over 100 chars
    total_tests += 1
    try:
        Experiment(name="x" * 101, hypothesis="test")
        all_validation_failures.append("Should reject name > 100 chars")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for name > 100: {e}")

    # Test 5: Hypothesis max length
    total_tests += 1
    try:
        exp = Experiment(name="test", hypothesis="x" * 500)
        if len(exp.hypothesis) != 500:
            all_validation_failures.append(f"Hypothesis should be 500 chars")
    except Exception as e:
        all_validation_failures.append(f"Hypothesis max length test failed: {e}")

    # Test 6: Reject hypothesis over 500 chars
    total_tests += 1
    try:
        Experiment(name="test", hypothesis="x" * 501)
        all_validation_failures.append("Should reject hypothesis > 500 chars")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for hypothesis > 500: {e}")

    # Test 7: model_dump
    total_tests += 1
    try:
        exp = Experiment(name="Test", hypothesis="Hypothesis")
        data = exp.model_dump()
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
