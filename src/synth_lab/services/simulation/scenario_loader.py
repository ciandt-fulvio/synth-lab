"""
Scenario loader service for synth-lab.

Loads predefined scenarios from JSON configuration file.

Functions:
- load_scenario: Load a specific scenario by ID
- list_scenarios: List all available scenarios

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Scenarios: data/config/scenarios.json

Sample usage:
    from synth_lab.services.simulation.scenario_loader import load_scenario, list_scenarios

    scenarios = list_scenarios()
    baseline = load_scenario("baseline")

Expected output:
    Scenario objects loaded from configuration
"""

import json
from pathlib import Path

from loguru import logger

from synth_lab.domain.entities import Scenario


def _get_scenarios_path() -> Path:
    """Get path to scenarios.json file."""
    # Navigate from this file to project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent.parent
    scenarios_path = project_root / "data" / "config" / "scenarios.json"
    return scenarios_path


def load_scenarios_from_file() -> dict[str, Scenario]:
    """
    Load all scenarios from JSON file.

    Returns:
        Dict mapping scenario IDs to Scenario objects

    Raises:
        FileNotFoundError: If scenarios.json not found
        ValueError: If JSON is invalid
    """
    scenarios_path = _get_scenarios_path()

    if not scenarios_path.exists():
        raise FileNotFoundError(
            f"Scenarios file not found: {scenarios_path}. Expected at data/config/scenarios.json"
        )

    try:
        with open(scenarios_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in scenarios file: {e}")

    # Convert dict to Scenario objects
    scenarios = {}
    for scenario_id, scenario_data in data.items():
        scenarios[scenario_id] = Scenario(**scenario_data)

    logger.info(f"Loaded {len(scenarios)} scenarios from {scenarios_path}")
    return scenarios


def list_scenarios() -> list[Scenario]:
    """
    List all available scenarios.

    Returns:
        List of Scenario objects
    """
    scenarios_dict = load_scenarios_from_file()
    return list(scenarios_dict.values())


def load_scenario(scenario_id: str) -> Scenario | None:
    """
    Load a specific scenario by ID.

    Args:
        scenario_id: ID of the scenario (e.g., "baseline", "crisis", "first-use")

    Returns:
        Scenario object if found, None otherwise
    """
    scenarios_dict = load_scenarios_from_file()
    return scenarios_dict.get(scenario_id)


if __name__ == "__main__":
    import sys

    print("=== Scenario Loader Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: List scenarios
    total_tests += 1
    try:
        scenarios = list_scenarios()
        if len(scenarios) < 3:
            all_validation_failures.append(
                f"Should have at least 3 scenarios, got {len(scenarios)}"
            )
        else:
            print(f"Test 1 PASSED: Loaded {len(scenarios)} scenarios")
    except Exception as e:
        all_validation_failures.append(f"List scenarios failed: {e}")

    # Test 2: Load baseline scenario
    total_tests += 1
    try:
        baseline = load_scenario("baseline")
        if baseline is None:
            all_validation_failures.append("Baseline scenario not found")
        elif baseline.id != "baseline":
            all_validation_failures.append(f"Baseline ID mismatch: {baseline.id}")
        else:
            print("Test 2 PASSED: Baseline scenario loaded correctly")
    except Exception as e:
        all_validation_failures.append(f"Load baseline failed: {e}")

    # Test 3: Load crisis scenario
    total_tests += 1
    try:
        crisis = load_scenario("crisis")
        if crisis is None:
            all_validation_failures.append("Crisis scenario not found")
        elif crisis.motivation_modifier <= 0:
            all_validation_failures.append(
                f"Crisis should have positive motivation modifier, got {crisis.motivation_modifier}"
            )
        else:
            print("Test 3 PASSED: Crisis scenario loaded correctly")
    except Exception as e:
        all_validation_failures.append(f"Load crisis failed: {e}")

    # Test 4: Load non-existent scenario
    total_tests += 1
    try:
        non_existent = load_scenario("non_existent_scenario")
        if non_existent is not None:
            all_validation_failures.append("Should return None for non-existent scenario")
        else:
            print("Test 4 PASSED: Correctly handles non-existent scenario")
    except Exception as e:
        all_validation_failures.append(f"Non-existent scenario test failed: {e}")

    # Test 5: Scenario has all required fields
    total_tests += 1
    try:
        baseline = load_scenario("baseline")
        if baseline:
            required_fields = [
                "id",
                "name",
                "description",
                "motivation_modifier",
                "trust_modifier",
                "friction_modifier",
                "task_criticality",
            ]
            missing = []
            for field in required_fields:
                if not hasattr(baseline, field):
                    missing.append(field)

            if missing:
                all_validation_failures.append(f"Baseline missing fields: {missing}")
            else:
                print("Test 5 PASSED: Scenario has all required fields")
    except Exception as e:
        all_validation_failures.append(f"Required fields test failed: {e}")

    # Final result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("ScenarioLoader is validated and ready for use")
        sys.exit(0)
