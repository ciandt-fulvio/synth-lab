"""
Synth outcome entities for synth-lab.

Defines models for analysis outcomes per synth.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - Data model: specs/019-experiment-refactor/data-model.md
"""

import secrets
from typing import Self

from pydantic import BaseModel, Field, model_validator

from synth_lab.domain.entities.simulation_attributes import SimulationAttributes


def generate_outcome_id() -> str:
    """
    Generate an outcome ID with out_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format out_[a-f0-9]{8}
    """
    return f"out_{secrets.token_hex(4)}"


class SynthOutcome(BaseModel):
    """
    Result of analysis for a specific synth.

    Contains the outcome proportions from Monte Carlo analysis
    and a snapshot of the synth's attributes at analysis time.

    Attributes:
        id: Unique identifier (out_[a-f0-9]{8})
        analysis_id: Parent analysis run ID
        synth_id: ID of the synth
        did_not_try_rate: Proportion that did not try (0-1)
        failed_rate: Proportion that tried but failed (0-1)
        success_rate: Proportion that succeeded (0-1)
        synth_attributes: Synth attributes at time of analysis
    """

    id: str = Field(
        default_factory=generate_outcome_id,
        pattern=r"^out_[a-f0-9]{8}$",
        description="Unique outcome ID.",
    )

    analysis_id: str = Field(
        pattern=r"^ana_[a-f0-9]{8}$",
        description="Parent analysis run ID.",
    )

    synth_id: str = Field(
        description="ID of the synth.",
    )

    # Outcome proportions [0, 1]
    did_not_try_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion of executions where synth did not try.",
    )

    failed_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion of executions where synth tried but failed.",
    )

    success_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion of executions where synth succeeded.",
    )

    # Snapshot of synth attributes
    synth_attributes: SimulationAttributes = Field(
        description="Synth's simulation attributes at time of analysis.",
    )

    @model_validator(mode="after")
    def validate_rates_sum(self) -> Self:
        """Ensure rates sum to 1.0 (with tolerance for rounding)."""
        total = self.did_not_try_rate + self.failed_rate + self.success_rate
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Rates must sum to 1.0, got {total}")
        return self


# Legacy alias for backward compatibility
# TODO: Remove in future version
LegacySynthOutcome = SynthOutcome


if __name__ == "__main__":
    import sys

    from synth_lab.domain.entities.simulation_attributes import (
        SimulationLatentTraits,
        SimulationObservables,
    )

    all_validation_failures = []
    total_tests = 0

    # Create sample attributes for tests
    sample_attrs = SimulationAttributes(
        observables=SimulationObservables(
            digital_literacy=0.35,
            similar_tool_experience=0.42,
            motor_ability=0.85,
            time_availability=0.28,
            domain_expertise=0.55,
        ),
        latent_traits=SimulationLatentTraits(
            capability_mean=0.42,
            trust_mean=0.39,
            friction_tolerance_mean=0.35,
            exploration_prob=0.38,
        ),
    )

    # Test 1: Create valid SynthOutcome
    total_tests += 1
    try:
        outcome = SynthOutcome(
            analysis_id="ana_12345678",
            synth_id="synth_001",
            did_not_try_rate=0.22,
            failed_rate=0.38,
            success_rate=0.40,
            synth_attributes=sample_attrs,
        )
        if outcome.success_rate != 0.40:
            all_validation_failures.append(f"success_rate mismatch: {outcome.success_rate}")
        if not outcome.id.startswith("out_"):
            all_validation_failures.append(f"ID should start with out_: {outcome.id}")
    except Exception as e:
        all_validation_failures.append(f"SynthOutcome creation failed: {e}")

    # Test 2: Reject rates that don't sum to 1
    total_tests += 1
    try:
        SynthOutcome(
            analysis_id="ana_12345678",
            synth_id="synth_001",
            did_not_try_rate=0.30,
            failed_rate=0.30,
            success_rate=0.30,  # Sum = 0.90
            synth_attributes=sample_attrs,
        )
        all_validation_failures.append("Should reject rates that don't sum to 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid rates: {e}")

    # Test 3: Accept rates with small rounding error
    total_tests += 1
    try:
        outcome = SynthOutcome(
            analysis_id="ana_12345678",
            synth_id="synth_001",
            did_not_try_rate=0.333,
            failed_rate=0.333,
            success_rate=0.334,  # Sum = 1.000
            synth_attributes=sample_attrs,
        )
        # Should accept within tolerance
    except Exception as e:
        all_validation_failures.append(f"Should accept rates within tolerance: {e}")

    # Test 4: Reject rate below 0
    total_tests += 1
    try:
        SynthOutcome(
            analysis_id="ana_12345678",
            synth_id="synth_001",
            did_not_try_rate=-0.1,
            failed_rate=0.5,
            success_rate=0.6,
            synth_attributes=sample_attrs,
        )
        all_validation_failures.append("Should reject negative rate")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for negative rate: {e}")

    # Test 5: Reject rate above 1
    total_tests += 1
    try:
        SynthOutcome(
            analysis_id="ana_12345678",
            synth_id="synth_001",
            did_not_try_rate=1.5,
            failed_rate=0.0,
            success_rate=-0.5,  # Sum = 1.0 but individual invalid
            synth_attributes=sample_attrs,
        )
        all_validation_failures.append("Should reject rate > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for rate > 1: {e}")

    # Test 6: Edge case - all did_not_try
    total_tests += 1
    try:
        outcome = SynthOutcome(
            analysis_id="ana_12345678",
            synth_id="synth_001",
            did_not_try_rate=1.0,
            failed_rate=0.0,
            success_rate=0.0,
            synth_attributes=sample_attrs,
        )
        if outcome.did_not_try_rate != 1.0:
            all_validation_failures.append("All did_not_try should be valid")
    except Exception as e:
        all_validation_failures.append(f"All did_not_try test failed: {e}")

    # Test 7: Edge case - all success
    total_tests += 1
    try:
        outcome = SynthOutcome(
            analysis_id="ana_12345678",
            synth_id="synth_001",
            did_not_try_rate=0.0,
            failed_rate=0.0,
            success_rate=1.0,
            synth_attributes=sample_attrs,
        )
        if outcome.success_rate != 1.0:
            all_validation_failures.append("All success should be valid")
    except Exception as e:
        all_validation_failures.append(f"All success test failed: {e}")

    # Test 8: Model dump includes synth_attributes
    total_tests += 1
    try:
        outcome = SynthOutcome(
            analysis_id="ana_12345678",
            synth_id="synth_001",
            did_not_try_rate=0.22,
            failed_rate=0.38,
            success_rate=0.40,
            synth_attributes=sample_attrs,
        )
        dump = outcome.model_dump()
        if "synth_attributes" not in dump:
            all_validation_failures.append("model_dump missing synth_attributes")
        if "observables" not in dump["synth_attributes"]:
            all_validation_failures.append("model_dump missing observables")
        if "analysis_id" not in dump:
            all_validation_failures.append("model_dump missing analysis_id")
    except Exception as e:
        all_validation_failures.append(f"model_dump test failed: {e}")

    # Test 9: Reject invalid analysis_id format
    total_tests += 1
    try:
        SynthOutcome(
            analysis_id="invalid_id",
            synth_id="synth_001",
            did_not_try_rate=0.22,
            failed_rate=0.38,
            success_rate=0.40,
            synth_attributes=sample_attrs,
        )
        all_validation_failures.append("Should reject invalid analysis_id format")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid analysis_id: {e}")

    # Test 10: ID generation uniqueness
    total_tests += 1
    try:
        ids = {generate_outcome_id() for _ in range(100)}
        if len(ids) != 100:
            all_validation_failures.append("IDs should be unique")
    except Exception as e:
        all_validation_failures.append(f"ID generation test failed: {e}")

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
