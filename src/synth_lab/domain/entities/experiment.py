"""
Experiment entity for synth-lab.

Represents a feature or hypothesis to be tested. Central hub that contains
an embedded scorecard and groups related analyses and interviews.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - Data model: specs/019-experiment-refactor/data-model.md
"""

import secrets
from datetime import datetime, timezone
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator


def generate_experiment_id() -> str:
    """
    Generate an experiment ID with exp_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format exp_[a-f0-9]{8}
    """
    return f"exp_{secrets.token_hex(4)}"


class ScorecardDimension(BaseModel):
    """
    A dimension of the scorecard with score and optional metadata.

    Attributes:
        score: Score value in [0,1] range
        rules_applied: Objective rules applied (e.g., ['2 conceitos novos'])
        lower_bound: Lower uncertainty bound
        upper_bound: Upper uncertainty bound
    """

    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Score value in [0,1] range.",
    )

    rules_applied: list[str] = Field(
        default_factory=list,
        description="Objective rules applied.",
    )

    lower_bound: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Lower uncertainty bound.",
    )

    upper_bound: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Upper uncertainty bound.",
    )

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Ensure lower_bound <= upper_bound if both are set."""
        if self.lower_bound is not None and self.upper_bound is not None:
            if self.lower_bound > self.upper_bound:
                raise ValueError(
                    f"lower_bound ({self.lower_bound}) must be <= upper_bound ({self.upper_bound})"
                )
        return self


class ScorecardData(BaseModel):
    """
    Scorecard data embedded in an experiment.

    Contains all dimensions and metadata needed for quantitative analysis.

    Attributes:
        feature_name: Name of the feature being evaluated
        scenario: Scenario of use (default: 'baseline')
        description_text: Text description of the feature
        description_media_urls: URLs to supporting media
        complexity: Complexity dimension
        initial_effort: Initial effort dimension
        perceived_risk: Perceived risk dimension
        time_to_value: Time to value dimension
        justification: LLM-generated justification
        impact_hypotheses: LLM-generated impact hypotheses
    """

    feature_name: str = Field(
        description="Name of the feature being evaluated.",
    )

    scenario: str = Field(
        default="baseline",
        description="Scenario of use for the feature.",
    )

    description_text: str = Field(
        description="Text description of the feature.",
    )

    description_media_urls: list[str] = Field(
        default_factory=list,
        description="URLs to videos, photos, etc.",
    )

    # Dimensions [0, 1]
    complexity: ScorecardDimension = Field(
        description="Complexity dimension with score and rules.",
    )

    initial_effort: ScorecardDimension = Field(
        description="Initial effort dimension with score and rules.",
    )

    perceived_risk: ScorecardDimension = Field(
        description="Perceived risk dimension with score and rules.",
    )

    time_to_value: ScorecardDimension = Field(
        description="Time to value dimension with score and rules.",
    )

    # LLM-generated fields
    justification: str | None = Field(
        default=None,
        description="LLM-generated justification for the scores.",
    )

    impact_hypotheses: list[str] = Field(
        default_factory=list,
        description="LLM-generated hypotheses about impact on synth groups.",
    )


class Experiment(BaseModel):
    """
    Experiment entity with embedded scorecard.

    Central hub that contains scorecard data and groups related
    analyses and interviews.

    Attributes:
        id: Unique identifier (exp_[a-f0-9]{8})
        name: Short name of the feature (max 100 chars)
        hypothesis: Description of the hypothesis to test (max 500 chars)
        description: Additional context, links, references (max 2000 chars)
        scorecard_data: Embedded scorecard (optional until filled)
        created_at: ISO 8601 timestamp of creation
        updated_at: ISO 8601 timestamp of last update
    """

    id: str = Field(
        default_factory=generate_experiment_id,
        pattern=r"^exp_[a-z0-9_]+$",
        description="Unique experiment ID (exp_ prefix + alphanumeric/underscore suffix).",
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

    # Embedded scorecard (optional until filled)
    scorecard_data: ScorecardData | None = Field(
        default=None,
        description="Embedded scorecard data.",
    )

    # Tags for categorization
    tags: list[str] = Field(
        default_factory=list,
        description="Tag names associated with this experiment.",
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

    def has_scorecard(self) -> bool:
        """Check if experiment has scorecard data filled."""
        return self.scorecard_data is not None


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
        if exp.has_scorecard():
            all_validation_failures.append("New experiment should not have scorecard")
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
            all_validation_failures.append("Hypothesis should be 500 chars")
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

    # Test 7: Create with scorecard
    total_tests += 1
    try:
        scorecard = ScorecardData(
            feature_name="Test Feature",
            description_text="A test feature",
            complexity=ScorecardDimension(score=0.3),
            initial_effort=ScorecardDimension(score=0.4),
            perceived_risk=ScorecardDimension(score=0.2),
            time_to_value=ScorecardDimension(score=0.6),
        )
        exp = Experiment(
            name="Test",
            hypothesis="Test hypothesis",
            scorecard_data=scorecard,
        )
        if not exp.has_scorecard():
            all_validation_failures.append("Experiment should have scorecard")
        if exp.scorecard_data.feature_name != "Test Feature":
            all_validation_failures.append("Scorecard feature_name mismatch")
    except Exception as e:
        all_validation_failures.append(f"Create with scorecard failed: {e}")

    # Test 8: ScorecardDimension validation
    total_tests += 1
    try:
        ScorecardDimension(score=1.5)
        all_validation_failures.append("Should reject score > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for score > 1: {e}")

    # Test 9: ScorecardDimension bounds validation
    total_tests += 1
    try:
        ScorecardDimension(score=0.5, lower_bound=0.6, upper_bound=0.4)
        all_validation_failures.append("Should reject lower > upper bound")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid bounds: {e}")

    # Test 10: model_dump includes scorecard
    total_tests += 1
    try:
        scorecard = ScorecardData(
            feature_name="Test",
            description_text="Test",
            complexity=ScorecardDimension(score=0.4),
            initial_effort=ScorecardDimension(score=0.3),
            perceived_risk=ScorecardDimension(score=0.2),
            time_to_value=ScorecardDimension(score=0.5),
        )
        exp = Experiment(
            name="Test",
            hypothesis="Hypothesis",
            scorecard_data=scorecard,
        )
        data = exp.model_dump()
        if "scorecard_data" not in data:
            all_validation_failures.append("model_dump missing scorecard_data")
        if data["scorecard_data"]["complexity"]["score"] != 0.4:
            all_validation_failures.append("model_dump complexity score mismatch")
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
