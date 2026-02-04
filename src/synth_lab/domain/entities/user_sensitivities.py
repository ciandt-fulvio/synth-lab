"""
User sensitivities entities for synth-lab.

Defines models for user psychological sensitivities that interact with feature
mechanisms to produce emergent behavioral states in simulations.

References:
    - Spec: specs/038-mechanism-based-simulation/spec.md
    - Data model: specs/038-mechanism-based-simulation/data-model.md
"""

from pydantic import BaseModel, Field


class UserSensitivities(BaseModel):
    """
    User sensitivities that interact with feature mechanisms.

    Each sensitivity represents how a user responds to a mechanism:
    - risk_aversion: Sensitivity to irreversible actions (high = avoids risk)
    - social_dependency: Importance of others using feature (high = follower)
    - institutional_trust_level: Trust in institutions (high = trusts institutions)
    - habit_plasticity: Ease of changing habits (high = adaptable)
    - learning_tolerance: Tolerance for learning effort (high = patient learner)
    - social_influence: Influenced by social visibility (high = conformist)

    Default value of 0.5 represents neutral sensitivity.
    """

    risk_aversion: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Sensitivity to irreversible actions (0=risk-seeking, 1=risk-averse)",
    )

    social_dependency: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Importance of others using the feature (0=independent, 1=follower)",
    )

    institutional_trust_level: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Trust in institutions (0=distrustful, 1=trusting)",
    )

    habit_plasticity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Ease of changing habits (0=rigid, 1=adaptable)",
    )

    learning_tolerance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Tolerance for learning effort (0=impatient, 1=patient)",
    )

    social_influence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Influenced by social visibility (0=independent, 1=conformist)",
    )


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: Create UserSensitivities with defaults (all 0.5)
    total_tests += 1
    try:
        sensitivities = UserSensitivities()
        if sensitivities.risk_aversion != 0.5:
            all_validation_failures.append(
                f"risk_aversion default should be 0.5: {sensitivities.risk_aversion}"
            )
        if sensitivities.social_dependency != 0.5:
            all_validation_failures.append(
                f"social_dependency default should be 0.5: {sensitivities.social_dependency}"
            )
        if sensitivities.institutional_trust_level != 0.5:
            all_validation_failures.append(
                f"institutional_trust_level default should be 0.5: "
                f"{sensitivities.institutional_trust_level}"
            )
    except Exception as e:
        all_validation_failures.append(f"Default UserSensitivities creation failed: {e}")

    # Test 2: Create UserSensitivities with all values set
    total_tests += 1
    try:
        sensitivities = UserSensitivities(
            risk_aversion=0.8,
            social_dependency=0.3,
            institutional_trust_level=0.6,
            habit_plasticity=0.4,
            learning_tolerance=0.7,
            social_influence=0.2,
        )
        if sensitivities.risk_aversion != 0.8:
            all_validation_failures.append(f"risk_aversion mismatch: {sensitivities.risk_aversion}")
        if sensitivities.social_dependency != 0.3:
            all_validation_failures.append(
                f"social_dependency mismatch: {sensitivities.social_dependency}"
            )
    except Exception as e:
        all_validation_failures.append(f"UserSensitivities with values failed: {e}")

    # Test 3: Reject value below 0
    total_tests += 1
    try:
        UserSensitivities(risk_aversion=-0.1)
        all_validation_failures.append("Should reject negative risk_aversion")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for negative value: {e}")

    # Test 4: Reject value above 1
    total_tests += 1
    try:
        UserSensitivities(social_dependency=1.5)
        all_validation_failures.append("Should reject social_dependency > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for value > 1: {e}")

    # Test 5: Edge case - boundary values (0.0 and 1.0)
    total_tests += 1
    try:
        sensitivities = UserSensitivities(
            risk_aversion=0.0,
            social_dependency=1.0,
            institutional_trust_level=0.0,
            habit_plasticity=1.0,
            learning_tolerance=0.0,
            social_influence=1.0,
        )
        if sensitivities.risk_aversion != 0.0:
            all_validation_failures.append("0.0 should be accepted for risk_aversion")
        if sensitivities.social_dependency != 1.0:
            all_validation_failures.append("1.0 should be accepted for social_dependency")
    except Exception as e:
        all_validation_failures.append(f"Boundary values test failed: {e}")

    # Test 6: Model dump produces valid dict
    total_tests += 1
    try:
        sensitivities = UserSensitivities(
            risk_aversion=0.8,
            social_dependency=0.3,
        )
        dump = sensitivities.model_dump()
        if "risk_aversion" not in dump:
            all_validation_failures.append("model_dump missing risk_aversion")
        if dump["risk_aversion"] != 0.8:
            all_validation_failures.append("model_dump risk_aversion value mismatch")
        if dump["social_dependency"] != 0.3:
            all_validation_failures.append("model_dump social_dependency value mismatch")
        if dump["institutional_trust_level"] != 0.5:
            all_validation_failures.append(
                "model_dump institutional_trust_level should default to 0.5"
            )
    except Exception as e:
        all_validation_failures.append(f"model_dump test failed: {e}")

    # Test 7: All 6 sensitivity fields exist
    total_tests += 1
    expected_fields = {
        "risk_aversion",
        "social_dependency",
        "institutional_trust_level",
        "habit_plasticity",
        "learning_tolerance",
        "social_influence",
    }
    actual_fields = set(UserSensitivities.model_fields.keys())
    if expected_fields != actual_fields:
        all_validation_failures.append(
            f"Field mismatch: expected {expected_fields}, got {actual_fields}"
        )

    # Test 8: Partial construction with keyword args
    total_tests += 1
    try:
        sensitivities = UserSensitivities(
            risk_aversion=0.9,
            learning_tolerance=0.2,
        )
        if sensitivities.risk_aversion != 0.9:
            all_validation_failures.append("risk_aversion should be 0.9")
        if sensitivities.learning_tolerance != 0.2:
            all_validation_failures.append("learning_tolerance should be 0.2")
        # Others should be default 0.5
        if sensitivities.social_dependency != 0.5:
            all_validation_failures.append("social_dependency should default to 0.5")
        if sensitivities.habit_plasticity != 0.5:
            all_validation_failures.append("habit_plasticity should default to 0.5")
    except Exception as e:
        all_validation_failures.append(f"Partial construction test failed: {e}")

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
