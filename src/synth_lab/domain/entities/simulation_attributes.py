"""
Simulation attributes entities for synth-lab.

Defines models for observable attributes and latent traits used in
Monte Carlo feature impact simulations.

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Data model: specs/016-feature-impact-simulation/data-model.md
"""

from typing import Self

from pydantic import BaseModel, Field, model_validator


class SimulationObservables(BaseModel):
    """
    Observable attributes generated during gensynth.

    These are directly observable characteristics of a synth that can
    be measured or inferred from their profile.
    """

    digital_literacy: float = Field(
        ge=0.0,
        le=1.0,
        description="Digital literacy level. Generated via Beta(2,4) -> mostly low-medium.",
    )

    similar_tool_experience: float = Field(
        ge=0.0,
        le=1.0,
        description="Experience with similar tools. Generated via Beta(3,3) -> symmetric.",
    )

    motor_ability: float = Field(
        ge=0.0,
        le=1.0,
        description="Motor ability derived from disabilities. "
        "nenhuma=1.0, leve=0.8, moderada=0.5, severa=0.2",
    )

    time_availability: float = Field(
        ge=0.0,
        le=1.0,
        description="Time availability. Generated via Beta(2,3) -> mostly low.",
    )

    domain_expertise: float = Field(
        ge=0.0,
        le=1.0,
        description="Domain expertise level. Generated via Beta(3,3) -> symmetric.",
    )


class SimulationLatentTraits(BaseModel):
    """
    Latent traits derived from observable attributes.

    These are computed characteristics that represent underlying
    behavioral tendencies relevant to feature adoption.
    """

    capability_mean: float = Field(
        ge=0.0,
        le=1.0,
        description="Mean capability. "
        "0.40*digital_literacy + 0.35*similar_tool_experience + "
        "0.15*motor_ability + 0.10*domain_expertise",
    )

    trust_mean: float = Field(
        ge=0.0,
        le=1.0,
        description="Mean trust level. 0.60*similar_tool_experience + 0.40*digital_literacy",
    )

    friction_tolerance_mean: float = Field(
        ge=0.0,
        le=1.0,
        description="Mean friction tolerance. "
        "0.40*time_availability + 0.35*digital_literacy + "
        "0.25*similar_tool_experience",
    )

    exploration_prob: float = Field(
        ge=0.0,
        le=1.0,
        description="Exploration probability. "
        "0.50*digital_literacy + 0.30*(1-similar_tool_experience) + "
        "0.20*time_availability",
    )


class SimulationAttributes(BaseModel):
    """
    Complete simulation attributes for a synth.

    Combines observable attributes and derived latent traits for use
    in Monte Carlo feature impact simulations.
    """

    observables: SimulationObservables
    latent_traits: SimulationLatentTraits

    @model_validator(mode="after")
    def validate_all_values_in_range(self) -> Self:
        """Ensure all values are within [0, 1] range."""
        for field_name, value in self.observables.model_dump().items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Observable {field_name} must be in [0,1], got {value}")
        for field_name, value in self.latent_traits.model_dump().items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Latent trait {field_name} must be in [0,1], got {value}")
        return self


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create valid SimulationObservables
    total_tests += 1
    try:
        obs = SimulationObservables(
            digital_literacy=0.35,
            similar_tool_experience=0.42,
            motor_ability=0.85,
            time_availability=0.28,
            domain_expertise=0.55,
        )
        if obs.digital_literacy != 0.35:
            all_validation_failures.append(f"digital_literacy mismatch: {obs.digital_literacy}")
    except Exception as e:
        all_validation_failures.append(f"SimulationObservables creation failed: {e}")

    # Test 2: Create valid SimulationLatentTraits
    total_tests += 1
    try:
        traits = SimulationLatentTraits(
            capability_mean=0.42,
            trust_mean=0.39,
            friction_tolerance_mean=0.35,
            exploration_prob=0.38,
        )
        if traits.capability_mean != 0.42:
            all_validation_failures.append(f"capability_mean mismatch: {traits.capability_mean}")
    except Exception as e:
        all_validation_failures.append(f"SimulationLatentTraits creation failed: {e}")

    # Test 3: Create valid SimulationAttributes
    total_tests += 1
    try:
        attrs = SimulationAttributes(
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
        if attrs.observables.digital_literacy != 0.35:
            all_validation_failures.append("SimulationAttributes observables mismatch")
    except Exception as e:
        all_validation_failures.append(f"SimulationAttributes creation failed: {e}")

    # Test 4: Reject value below 0
    total_tests += 1
    try:
        SimulationObservables(
            digital_literacy=-0.1,
            similar_tool_experience=0.5,
            motor_ability=0.5,
            time_availability=0.5,
            domain_expertise=0.5,
        )
        all_validation_failures.append("Should reject negative digital_literacy")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for negative value: {e}")

    # Test 5: Reject value above 1
    total_tests += 1
    try:
        SimulationObservables(
            digital_literacy=1.5,
            similar_tool_experience=0.5,
            motor_ability=0.5,
            time_availability=0.5,
            domain_expertise=0.5,
        )
        all_validation_failures.append("Should reject digital_literacy > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for value > 1: {e}")

    # Test 6: Edge case - all zeros
    total_tests += 1
    try:
        attrs = SimulationAttributes(
            observables=SimulationObservables(
                digital_literacy=0.0,
                similar_tool_experience=0.0,
                motor_ability=0.0,
                time_availability=0.0,
                domain_expertise=0.0,
            ),
            latent_traits=SimulationLatentTraits(
                capability_mean=0.0,
                trust_mean=0.0,
                friction_tolerance_mean=0.0,
                exploration_prob=0.0,
            ),
        )
        if attrs.observables.digital_literacy != 0.0:
            all_validation_failures.append("Zero values should be accepted")
    except Exception as e:
        all_validation_failures.append(f"Zero values test failed: {e}")

    # Test 7: Edge case - all ones
    total_tests += 1
    try:
        attrs = SimulationAttributes(
            observables=SimulationObservables(
                digital_literacy=1.0,
                similar_tool_experience=1.0,
                motor_ability=1.0,
                time_availability=1.0,
                domain_expertise=1.0,
            ),
            latent_traits=SimulationLatentTraits(
                capability_mean=1.0,
                trust_mean=1.0,
                friction_tolerance_mean=1.0,
                exploration_prob=1.0,
            ),
        )
        if attrs.observables.digital_literacy != 1.0:
            all_validation_failures.append("One values should be accepted")
    except Exception as e:
        all_validation_failures.append(f"One values test failed: {e}")

    # Test 8: Model dump produces dict
    total_tests += 1
    try:
        attrs = SimulationAttributes(
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
        dump = attrs.model_dump()
        if "observables" not in dump:
            all_validation_failures.append("model_dump missing observables")
        if "latent_traits" not in dump:
            all_validation_failures.append("model_dump missing latent_traits")
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
