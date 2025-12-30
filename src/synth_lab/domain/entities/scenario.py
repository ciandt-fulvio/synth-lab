"""
Scenario entities for synth-lab.

Defines models for contextual scenarios used in simulations.

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Data model: specs/016-feature-impact-simulation/data-model.md
"""

from pydantic import BaseModel, Field


class Scenario(BaseModel):
    """
    Contextual scenario that modifies synth state during simulation.

    Scenarios represent different usage contexts (e.g., normal use,
    crisis mode, first-time exploration) that affect user behavior.
    """

    id: str = Field(description="Unique scenario identifier.")

    name: str = Field(description="Display name for the scenario.")

    description: str = Field(description="Description of the scenario context.")

    # Modifiers [-0.3, +0.3]
    motivation_modifier: float = Field(
        default=0.0,
        ge=-0.3,
        le=0.3,
        description="Modifier for motivation. Range [-0.3, +0.3].",
    )

    trust_modifier: float = Field(
        default=0.0,
        ge=-0.3,
        le=0.3,
        description="Modifier for trust. Range [-0.3, +0.3].",
    )

    friction_modifier: float = Field(
        default=0.0,
        ge=-0.3,
        le=0.3,
        description="Modifier for friction tolerance. Range [-0.3, +0.3].",
    )

    # Task criticality [0, 1]
    task_criticality: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Task criticality level. Range [0, 1].",
    )


# Pre-defined scenarios
PREDEFINED_SCENARIOS: dict[str, Scenario] = {
    "baseline": Scenario(
        id="baseline",
        name="Baseline",
        description="Condicoes tipicas de uso",
        motivation_modifier=0.0,
        trust_modifier=0.0,
        friction_modifier=0.0,
        task_criticality=0.5,
    ),
    "crisis": Scenario(
        id="crisis",
        name="Crise",
        description="Urgencia, precisa resolver rapido",
        motivation_modifier=0.2,
        trust_modifier=-0.1,
        friction_modifier=-0.15,
        task_criticality=0.85,
    ),
    "first-use": Scenario(
        id="first-use",
        name="Primeiro Uso",
        description="Exploracao inicial do produto",
        motivation_modifier=0.1,
        trust_modifier=-0.2,
        friction_modifier=0.0,
        task_criticality=0.2,
    ),
}


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create valid Scenario
    total_tests += 1
    try:
        scenario = Scenario(
            id="test",
            name="Test Scenario",
            description="A test scenario",
            motivation_modifier=0.1,
            trust_modifier=-0.1,
            friction_modifier=0.0,
            task_criticality=0.5,
        )
        if scenario.id != "test":
            all_validation_failures.append(f"ID mismatch: {scenario.id}")
    except Exception as e:
        all_validation_failures.append(f"Scenario creation failed: {e}")

    # Test 2: Reject modifier out of range (too high)
    total_tests += 1
    try:
        Scenario(
            id="test",
            name="Test",
            description="Test",
            motivation_modifier=0.5,  # Too high
        )
        all_validation_failures.append("Should reject motivation_modifier > 0.3")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for high modifier: {e}")

    # Test 3: Reject modifier out of range (too low)
    total_tests += 1
    try:
        Scenario(
            id="test",
            name="Test",
            description="Test",
            trust_modifier=-0.5,  # Too low
        )
        all_validation_failures.append("Should reject trust_modifier < -0.3")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for low modifier: {e}")

    # Test 4: Reject task_criticality out of range
    total_tests += 1
    try:
        Scenario(
            id="test",
            name="Test",
            description="Test",
            task_criticality=1.5,
        )
        all_validation_failures.append("Should reject task_criticality > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for high criticality: {e}")

    # Test 5: Verify baseline scenario
    total_tests += 1
    try:
        baseline = PREDEFINED_SCENARIOS["baseline"]
        if baseline.motivation_modifier != 0.0:
            all_validation_failures.append(
                f"Baseline motivation should be 0: {baseline.motivation_modifier}"
            )
        if baseline.task_criticality != 0.5:
            all_validation_failures.append(
                f"Baseline criticality should be 0.5: {baseline.task_criticality}"
            )
    except Exception as e:
        all_validation_failures.append(f"Baseline scenario test failed: {e}")

    # Test 6: Verify crisis scenario
    total_tests += 1
    try:
        crisis = PREDEFINED_SCENARIOS["crisis"]
        if crisis.motivation_modifier != 0.2:
            all_validation_failures.append(
                f"Crisis motivation should be 0.2: {crisis.motivation_modifier}"
            )
        if crisis.task_criticality != 0.85:
            all_validation_failures.append(
                f"Crisis criticality should be 0.85: {crisis.task_criticality}"
            )
    except Exception as e:
        all_validation_failures.append(f"Crisis scenario test failed: {e}")

    # Test 7: Verify first-use scenario
    total_tests += 1
    try:
        first_use = PREDEFINED_SCENARIOS["first-use"]
        if first_use.trust_modifier != -0.2:
            all_validation_failures.append(
                f"First-use trust should be -0.2: {first_use.trust_modifier}"
            )
        if first_use.task_criticality != 0.2:
            all_validation_failures.append(
                f"First-use criticality should be 0.2: {first_use.task_criticality}"
            )
    except Exception as e:
        all_validation_failures.append(f"First-use scenario test failed: {e}")

    # Test 8: All predefined scenarios exist
    total_tests += 1
    try:
        expected_ids = {"baseline", "crisis", "first-use"}
        actual_ids = set(PREDEFINED_SCENARIOS.keys())
        if expected_ids != actual_ids:
            all_validation_failures.append(f"Expected scenarios {expected_ids}, got {actual_ids}")
    except Exception as e:
        all_validation_failures.append(f"Predefined scenarios check failed: {e}")

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
