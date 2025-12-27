"""
Feature scorecard entities for synth-lab.

Defines models for feature scorecards used in impact simulations.

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Data model: specs/016-feature-impact-simulation/data-model.md
"""

import secrets
from datetime import datetime, timezone
from typing import Self

from pydantic import BaseModel, Field, model_validator


def generate_scorecard_id() -> str:
    """Generate an 8-character alphanumeric ID."""
    return secrets.token_hex(4)


class ScorecardDimension(BaseModel):
    """
    A dimension of the scorecard with score, rules, and uncertainty.

    Each dimension represents a measurable aspect of the feature
    that affects user adoption and success.
    """

    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Score value in [0,1] range.",
    )

    rules_applied: list[str] = Field(
        default_factory=list,
        description="Objective rules applied. Ex: ['2 conceitos novos', 'estados invisiveis']",
    )

    min_uncertainty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum uncertainty value.",
    )

    max_uncertainty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Maximum uncertainty value.",
    )

    @model_validator(mode="after")
    def validate_uncertainty_range(self) -> Self:
        """Ensure min_uncertainty <= max_uncertainty."""
        if self.min_uncertainty > self.max_uncertainty:
            raise ValueError(
                f"min_uncertainty ({self.min_uncertainty}) must be <= "
                f"max_uncertainty ({self.max_uncertainty})"
            )
        return self


class ScorecardIdentification(BaseModel):
    """Identification information for a scorecard."""

    feature_name: str = Field(description="Name of the feature being evaluated.")

    use_scenario: str = Field(description="Scenario of use for the feature.")

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp.",
    )

    evaluators: list[str] = Field(
        default_factory=list,
        description="List of evaluators. Ex: ['Produto: Joao', 'UX: Maria']",
    )


class FeatureScorecard(BaseModel):
    """
    Complete feature scorecard for simulation.

    Contains all information needed to evaluate a feature's impact
    on different synth profiles.
    """

    id: str = Field(
        default_factory=generate_scorecard_id,
        pattern=r"^[a-zA-Z0-9]{8}$",
        description="8-character alphanumeric ID.",
    )

    experiment_id: str | None = Field(
        default=None,
        description="ID of the parent experiment (exp_xxxxxxxx format).",
    )

    identification: ScorecardIdentification

    # Rich description
    description_text: str = Field(description="Text description of the feature.")

    description_media_urls: list[str] = Field(
        default_factory=list,
        description="URLs to videos, photos, etc.",
    )

    # Dimensions
    complexity: ScorecardDimension = Field(
        description="Complexity dimension with score and rules."
    )

    initial_effort: ScorecardDimension = Field(
        description="Initial effort dimension with score and rules."
    )

    perceived_risk: ScorecardDimension = Field(
        description="Perceived risk dimension with score and rules."
    )

    time_to_value: ScorecardDimension = Field(
        description="Time to value dimension with score and rules."
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

    # Metadata
    version: str = Field(
        default="1.0.0",
        description="Schema version.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp.",
    )

    updated_at: datetime | None = Field(
        default=None,
        description="Last update timestamp.",
    )


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create valid ScorecardDimension
    total_tests += 1
    try:
        dim = ScorecardDimension(
            score=0.4,
            rules_applied=["2 conceitos novos"],
            min_uncertainty=0.3,
            max_uncertainty=0.5,
        )
        if dim.score != 0.4:
            all_validation_failures.append(f"Score mismatch: {dim.score}")
    except Exception as e:
        all_validation_failures.append(f"ScorecardDimension creation failed: {e}")

    # Test 2: Reject invalid uncertainty range
    total_tests += 1
    try:
        ScorecardDimension(
            score=0.4,
            min_uncertainty=0.6,
            max_uncertainty=0.3,
        )
        all_validation_failures.append("Should reject min > max uncertainty")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid uncertainty: {e}")

    # Test 3: Create valid ScorecardIdentification
    total_tests += 1
    try:
        ident = ScorecardIdentification(
            feature_name="Novo Fluxo de Onboarding",
            use_scenario="Primeiro acesso ao produto",
            evaluators=["PM: Joao", "UX: Maria"],
        )
        if ident.feature_name != "Novo Fluxo de Onboarding":
            all_validation_failures.append(f"Feature name mismatch: {ident.feature_name}")
        if ident.created_at is None:
            all_validation_failures.append("created_at should be set automatically")
    except Exception as e:
        all_validation_failures.append(f"ScorecardIdentification creation failed: {e}")

    # Test 4: Create valid FeatureScorecard
    total_tests += 1
    try:
        scorecard = FeatureScorecard(
            identification=ScorecardIdentification(
                feature_name="Novo Fluxo",
                use_scenario="Primeiro acesso",
            ),
            description_text="Fluxo simplificado com 3 passos",
            complexity=ScorecardDimension(score=0.4),
            initial_effort=ScorecardDimension(score=0.3),
            perceived_risk=ScorecardDimension(score=0.2),
            time_to_value=ScorecardDimension(score=0.5),
        )
        if len(scorecard.id) != 8:
            all_validation_failures.append(f"ID should be 8 chars: {scorecard.id}")
        if scorecard.version != "1.0.0":
            all_validation_failures.append(f"Version mismatch: {scorecard.version}")
    except Exception as e:
        all_validation_failures.append(f"FeatureScorecard creation failed: {e}")

    # Test 5: Reject score out of range
    total_tests += 1
    try:
        ScorecardDimension(score=1.5)
        all_validation_failures.append("Should reject score > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for score > 1: {e}")

    # Test 6: ID generation is unique
    total_tests += 1
    try:
        id1 = generate_scorecard_id()
        id2 = generate_scorecard_id()
        if id1 == id2:
            all_validation_failures.append("Generated IDs should be unique")
        if len(id1) != 8:
            all_validation_failures.append(f"ID length should be 8: {len(id1)}")
    except Exception as e:
        all_validation_failures.append(f"ID generation test failed: {e}")

    # Test 7: Model dump produces valid dict
    total_tests += 1
    try:
        scorecard = FeatureScorecard(
            identification=ScorecardIdentification(
                feature_name="Test",
                use_scenario="Test",
            ),
            description_text="Test",
            complexity=ScorecardDimension(score=0.4),
            initial_effort=ScorecardDimension(score=0.3),
            perceived_risk=ScorecardDimension(score=0.2),
            time_to_value=ScorecardDimension(score=0.5),
        )
        dump = scorecard.model_dump()
        if "complexity" not in dump:
            all_validation_failures.append("model_dump missing complexity")
        if dump["complexity"]["score"] != 0.4:
            all_validation_failures.append("model_dump complexity score mismatch")
    except Exception as e:
        all_validation_failures.append(f"model_dump test failed: {e}")

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
