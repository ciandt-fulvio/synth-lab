"""
Feature mechanisms entities for synth-lab.

Defines models for feature structural mechanisms that interact with user
sensitivities to produce emergent behavioral states in simulations.

References:
    - Spec: specs/038-mechanism-based-simulation/spec.md
    - Data model: specs/038-mechanism-based-simulation/data-model.md
"""

from pydantic import BaseModel, Field


class FeatureMechanisms(BaseModel):
    """
    Feature mechanisms that interact with user sensitivities.

    Each mechanism represents a structural property of the feature:
    - irreversibility: Actions cannot be undone (0=reversible, 1=permanent)
    - network_effect: Value depends on others using it (0=individual, 1=requires network)
    - institutional_trust: Requires trust in institution (0=peer, 1=institutional)
    - habit_displacement: Replaces existing habits (0=additive, 1=replacement)
    - learning_curve: Requires learning new skills (0=intuitive, 1=complex)
    - social_visibility: Usage is visible to others (0=private, 1=public)

    Default value of 0.0 represents mechanism not present.
    """

    irreversibility: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which actions are permanent/irreversible",
    )

    network_effect: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which value depends on others using it",
    )

    institutional_trust: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which feature requires trust in institution",
    )

    habit_displacement: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which feature replaces existing habits",
    )

    learning_curve: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which feature requires learning new skills",
    )

    social_visibility: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which usage is visible to others",
    )

    def has_any_mechanism(self) -> bool:
        """Check if any mechanism is non-zero."""
        return any(
            [
                self.irreversibility > 0,
                self.network_effect > 0,
                self.institutional_trust > 0,
                self.habit_displacement > 0,
                self.learning_curve > 0,
                self.social_visibility > 0,
            ]
        )


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: Create FeatureMechanisms with defaults (all zeros)
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms()
        if mechanisms.irreversibility != 0.0:
            all_validation_failures.append(
                f"irreversibility default should be 0.0: {mechanisms.irreversibility}"
            )
        if mechanisms.has_any_mechanism():
            all_validation_failures.append("has_any_mechanism should be False for defaults")
    except Exception as e:
        all_validation_failures.append(f"Default FeatureMechanisms creation failed: {e}")

    # Test 2: Create FeatureMechanisms with all values set
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(
            irreversibility=0.9,
            network_effect=0.7,
            institutional_trust=0.8,
            habit_displacement=0.4,
            learning_curve=0.5,
            social_visibility=0.3,
        )
        if mechanisms.irreversibility != 0.9:
            all_validation_failures.append(f"irreversibility mismatch: {mechanisms.irreversibility}")
        if mechanisms.network_effect != 0.7:
            all_validation_failures.append(f"network_effect mismatch: {mechanisms.network_effect}")
        if not mechanisms.has_any_mechanism():
            all_validation_failures.append("has_any_mechanism should be True")
    except Exception as e:
        all_validation_failures.append(f"FeatureMechanisms with values failed: {e}")

    # Test 3: Reject value below 0
    total_tests += 1
    try:
        FeatureMechanisms(irreversibility=-0.1)
        all_validation_failures.append("Should reject negative irreversibility")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for negative value: {e}")

    # Test 4: Reject value above 1
    total_tests += 1
    try:
        FeatureMechanisms(network_effect=1.5)
        all_validation_failures.append("Should reject network_effect > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for value > 1: {e}")

    # Test 5: Edge case - boundary values (0.0 and 1.0)
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(
            irreversibility=0.0,
            network_effect=1.0,
            institutional_trust=0.0,
            habit_displacement=1.0,
            learning_curve=0.0,
            social_visibility=1.0,
        )
        if mechanisms.irreversibility != 0.0:
            all_validation_failures.append("0.0 should be accepted")
        if mechanisms.network_effect != 1.0:
            all_validation_failures.append("1.0 should be accepted")
        if not mechanisms.has_any_mechanism():
            all_validation_failures.append("has_any_mechanism should be True with some 1.0 values")
    except Exception as e:
        all_validation_failures.append(f"Boundary values test failed: {e}")

    # Test 6: has_any_mechanism with single non-zero value
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(learning_curve=0.1)
        if not mechanisms.has_any_mechanism():
            all_validation_failures.append("has_any_mechanism should be True with learning_curve=0.1")
    except Exception as e:
        all_validation_failures.append(f"Single non-zero test failed: {e}")

    # Test 7: Model dump produces valid dict
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(
            irreversibility=0.9,
            network_effect=0.7,
        )
        dump = mechanisms.model_dump()
        if "irreversibility" not in dump:
            all_validation_failures.append("model_dump missing irreversibility")
        if dump["irreversibility"] != 0.9:
            all_validation_failures.append("model_dump irreversibility value mismatch")
        if dump["network_effect"] != 0.7:
            all_validation_failures.append("model_dump network_effect value mismatch")
        if dump["institutional_trust"] != 0.0:
            all_validation_failures.append("model_dump institutional_trust should default to 0.0")
    except Exception as e:
        all_validation_failures.append(f"model_dump test failed: {e}")

    # Test 8: All 6 mechanism fields exist
    total_tests += 1
    expected_fields = {
        "irreversibility",
        "network_effect",
        "institutional_trust",
        "habit_displacement",
        "learning_curve",
        "social_visibility",
    }
    actual_fields = set(FeatureMechanisms.model_fields.keys())
    if expected_fields != actual_fields:
        all_validation_failures.append(
            f"Field mismatch: expected {expected_fields}, got {actual_fields}"
        )

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"❌ VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
