"""
Tag entity for synth-lab.

Represents a tag for categorizing experiments.

References:
    - ORM model: synth_lab.models.orm.tag
"""

import secrets
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


def generate_tag_id() -> str:
    """
    Generate a tag ID with tag_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format tag_[a-f0-9]{8}
    """
    return f"tag_{secrets.token_hex(4)}"


class Tag(BaseModel):
    """
    Tag entity for experiment categorization.

    Attributes:
        id: Unique identifier (tag_[a-f0-9]{8})
        name: Tag name (max 50 chars, unique)
        created_at: ISO 8601 timestamp of creation
        updated_at: ISO 8601 timestamp of last update
    """

    id: str = Field(
        default_factory=generate_tag_id,
        pattern=r"^tag_[a-f0-9]{8}$",
        description="Unique tag ID.",
    )

    name: str = Field(
        max_length=50,
        description="Tag name.",
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
        return v.strip()


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create with required fields
    total_tests += 1
    try:
        tag = Tag(name="Test Tag")
        if not tag.id.startswith("tag_"):
            all_validation_failures.append(f"ID should start with tag_: {tag.id}")
        if tag.name != "Test Tag":
            all_validation_failures.append(f"Name mismatch: {tag.name}")
    except Exception as e:
        all_validation_failures.append(f"Create with required fields failed: {e}")

    # Test 2: ID generation uniqueness
    total_tests += 1
    try:
        ids = {generate_tag_id() for _ in range(100)}
        if len(ids) != 100:
            all_validation_failures.append("IDs should be unique")
    except Exception as e:
        all_validation_failures.append(f"ID generation test failed: {e}")

    # Test 3: Name max length
    total_tests += 1
    try:
        tag = Tag(name="x" * 50)
        if len(tag.name) != 50:
            all_validation_failures.append(f"Name should be 50 chars: {len(tag.name)}")
    except Exception as e:
        all_validation_failures.append(f"Name max length test failed: {e}")

    # Test 4: Reject name over 50 chars
    total_tests += 1
    try:
        Tag(name="x" * 51)
        all_validation_failures.append("Should reject name > 50 chars")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for name > 50: {e}")

    # Test 5: Reject empty name
    total_tests += 1
    try:
        Tag(name="")
        all_validation_failures.append("Should reject empty name")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for empty name: {e}")

    # Test 6: Reject whitespace-only name
    total_tests += 1
    try:
        Tag(name="   ")
        all_validation_failures.append("Should reject whitespace-only name")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for whitespace name: {e}")

    # Test 7: Trim whitespace from name
    total_tests += 1
    try:
        tag = Tag(name="  Test Tag  ")
        if tag.name != "Test Tag":
            all_validation_failures.append(f"Name should be trimmed: '{tag.name}'")
    except Exception as e:
        all_validation_failures.append(f"Trim whitespace test failed: {e}")

    # Test 8: model_dump works correctly
    total_tests += 1
    try:
        tag = Tag(name="Test Tag")
        data = tag.model_dump()
        if "name" not in data:
            all_validation_failures.append("model_dump missing name")
        if data["name"] != "Test Tag":
            all_validation_failures.append("model_dump name mismatch")
    except Exception as e:
        all_validation_failures.append(f"model_dump test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
