"""
User sensitivities entities for synth-lab.

Defines models for user psychological sensitivities that interact with feature
mechanisms to produce emergent behavioral states in simulations.

References:
    - Spec: specs/040-refined-sensitivities/spec.md
    - Data model: specs/040-refined-sensitivities/data-model.md
"""

from pydantic import BaseModel, Field


class UserSensitivities(BaseModel):
    """
    User sensitivities that interact with feature mechanisms.

    Each sensitivity represents how a user responds to a mechanism:
    - risk_aversion: Sensitivity to irreversible actions (high = avoids risk)
    - institutional_trust_level: Trust in institutions (high = trusts institutions)
    - friction_tolerance: Tolerance for complex processes (high = tolerates friction)
    - digital_capability: Digital technical ability (high = digitally capable)

    Default value of 0.5 represents neutral sensitivity.
    """

    risk_aversion: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Sensitivity to irreversible actions (0=risk-seeking, 1=risk-averse)",
    )

    institutional_trust_level: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Trust in institutions (0=distrustful, 1=trusting)",
    )

    friction_tolerance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Tolerance for complex processes (0=impatient, 1=tolerant)",
    )

    digital_capability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Digital technical ability (0=low capability, 1=high capability)",
    )


if __name__ == "__main__":
    import sys

    ALL_FIELDS = [
        "risk_aversion",
        "institutional_trust_level",
        "friction_tolerance",
        "digital_capability",
    ]

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: Create UserSensitivities with defaults (all 0.5)
    total_tests += 1
    try:
        sensitivities = UserSensitivities()
        for field in ALL_FIELDS:
            val = getattr(sensitivities, field)
            if val != 0.5:
                all_validation_failures.append(f"{field} default should be 0.5, got {val}")
    except Exception as e:
        all_validation_failures.append(f"Default UserSensitivities creation failed: {e}")

    # Test 2: Create UserSensitivities with all values set
    total_tests += 1
    try:
        values = {
            "risk_aversion": 0.8,
            "institutional_trust_level": 0.6,
            "friction_tolerance": 0.7,
            "digital_capability": 0.2,
        }
        sensitivities = UserSensitivities(**values)
        for field, expected in values.items():
            actual = getattr(sensitivities, field)
            if actual != expected:
                all_validation_failures.append(
                    f"{field} mismatch: expected {expected}, got {actual}"
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
        UserSensitivities(institutional_trust_level=1.5)
        all_validation_failures.append("Should reject institutional_trust_level > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for value > 1: {e}")

    # Test 5: Edge case - boundary values (0.0 and 1.0)
    total_tests += 1
    try:
        boundary = {
            "risk_aversion": 0.0,
            "institutional_trust_level": 1.0,
            "friction_tolerance": 0.0,
            "digital_capability": 1.0,
        }
        sensitivities = UserSensitivities(**boundary)
        for field, expected in boundary.items():
            actual = getattr(sensitivities, field)
            if actual != expected:
                all_validation_failures.append(f"Boundary {expected} not accepted for {field}")
    except Exception as e:
        all_validation_failures.append(f"Boundary values test failed: {e}")

    # Test 6: Model dump produces valid dict with defaults
    total_tests += 1
    try:
        sensitivities = UserSensitivities(risk_aversion=0.8, friction_tolerance=0.3)
        dump = sensitivities.model_dump()
        expected_dump = {
            "risk_aversion": 0.8,
            "institutional_trust_level": 0.5,
            "friction_tolerance": 0.3,
            "digital_capability": 0.5,
        }
        for field, expected in expected_dump.items():
            if dump.get(field) != expected:
                all_validation_failures.append(
                    f"model_dump {field}: expected {expected}, got {dump.get(field)}"
                )
    except Exception as e:
        all_validation_failures.append(f"model_dump test failed: {e}")

    # Test 7: All 4 sensitivity fields exist
    total_tests += 1
    expected_fields = set(ALL_FIELDS)
    actual_fields = set(UserSensitivities.model_fields.keys())
    if expected_fields != actual_fields:
        all_validation_failures.append(
            f"Field mismatch: expected {expected_fields}, got {actual_fields}"
        )

    # Test 8: Partial construction with keyword args
    total_tests += 1
    try:
        sensitivities = UserSensitivities(risk_aversion=0.9, friction_tolerance=0.2)
        checks = {
            "risk_aversion": 0.9,
            "friction_tolerance": 0.2,
            "institutional_trust_level": 0.5,
            "digital_capability": 0.5,
        }
        for field, expected in checks.items():
            actual = getattr(sensitivities, field)
            if actual != expected:
                all_validation_failures.append(
                    f"Partial: {field} should be {expected}, got {actual}"
                )
    except Exception as e:
        all_validation_failures.append(f"Partial construction test failed: {e}")

    # Test 9: Reject out-of-range for fields
    total_tests += 1
    for field_name, bad_value in [
        ("friction_tolerance", -0.5),
        ("digital_capability", 2.0),
        ("institutional_trust_level", -0.1),
        ("risk_aversion", 1.5),
    ]:
        try:
            UserSensitivities(**{field_name: bad_value})
            all_validation_failures.append(f"Should reject {field_name}={bad_value}")
        except ValueError:
            pass  # Expected
        except Exception as e:
            all_validation_failures.append(f"Unexpected error for {field_name}={bad_value}: {e}")

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
