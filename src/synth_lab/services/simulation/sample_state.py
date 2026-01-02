"""
User state sampling for Monte Carlo simulation.

Samples user state from latent traits with noise and scenario modifiers.

Functions:
- sample_user_state(): Sample user state with noise and scenario effects

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Research: specs/016-feature-impact-simulation/research.md

Sample usage:
    from synth_lab.services.simulation.sample_state import sample_user_state
    import numpy as np

    rng = np.random.default_rng(seed=42)
    latent_traits = {"capability_mean": 0.6, "trust_mean": 0.5, ...}
    scenario = {"trust_modifier": -0.1, "friction_modifier": 0.1, ...}
    state = sample_user_state(latent_traits, scenario, sigma=0.1, rng=rng)

Expected output:
    UserState with capability, trust, friction_tolerance, explores values
"""

import numpy as np
from numpy.random import Generator
from pydantic import BaseModel, Field


class UserState(BaseModel):
    """
    Sampled user state for a single simulation execution.

    All values are in [0, 1] range after clamping.
    """

    capability: float = Field(ge=0.0, le=1.0, description="User capability level")
    trust: float = Field(ge=0.0, le=1.0, description="User trust level")
    friction_tolerance: float = Field(ge=0.0, le=1.0, description="Tolerance for friction")
    explores: bool = Field(description="Whether user explores the feature")
    motivation: float = Field(ge=0.0, le=1.0, description="User motivation level")


def sample_user_state(
    latent_traits: dict[str, float],
    scenario: dict[str, float],
    sigma: float,
    rng: Generator) -> UserState:
    """
    Sample user state from latent traits with noise and scenario modifiers.

    This function:
    1. Samples values from Normal(mean, sigma) for each latent trait
    2. Applies scenario modifiers (trust, friction)
    3. Samples exploration based on exploration_prob
    4. Calculates motivation from scenario

    Args:
        latent_traits: Dict with capability_mean, trust_mean, friction_tolerance_mean,
                       exploration_prob
        scenario: Dict with trust_modifier, friction_modifier, motivation_modifier,
                  task_criticality
        sigma: Standard deviation for Normal noise
        rng: NumPy random generator for reproducibility

    Returns:
        UserState with sampled values

    Notes:
        - All continuous values are clamped to [0, 1]
        - Exploration is sampled as Bernoulli(exploration_prob)
        - Motivation = base + motivation_modifier, where base comes from task_criticality
    """
    # Extract latent traits
    capability_mean = latent_traits.get("capability_mean", 0.5)
    trust_mean = latent_traits.get("trust_mean", 0.5)
    friction_mean = latent_traits.get("friction_tolerance_mean", 0.5)
    exploration_prob = latent_traits.get("exploration_prob", 0.5)

    # Extract scenario modifiers
    trust_modifier = scenario.get("trust_modifier", 0.0)
    friction_modifier = scenario.get("friction_modifier", 0.0)
    motivation_modifier = scenario.get("motivation_modifier", 0.0)
    task_criticality = scenario.get("task_criticality", 0.5)

    # Sample from Normal distributions with noise
    capability_raw = rng.normal(capability_mean, sigma)
    trust_raw = rng.normal(trust_mean, sigma)
    friction_raw = rng.normal(friction_mean, sigma)

    # Apply scenario modifiers
    trust_adjusted = trust_raw + trust_modifier
    friction_adjusted = friction_raw + friction_modifier

    # Clamp to [0, 1]
    capability = float(np.clip(capability_raw, 0.0, 1.0))
    trust = float(np.clip(trust_adjusted, 0.0, 1.0))
    friction_tolerance = float(np.clip(friction_adjusted, 0.0, 1.0))

    # Sample exploration as Bernoulli
    explores = bool(rng.random() < exploration_prob)

    # Calculate motivation
    # Base motivation from task criticality, adjusted by scenario
    base_motivation = task_criticality
    motivation = float(np.clip(base_motivation + motivation_modifier, 0.0, 1.0))

    return UserState(
        capability=capability,
        trust=trust,
        friction_tolerance=friction_tolerance,
        explores=explores,
        motivation=motivation)


def sample_user_states_batch(
    latent_traits_batch: list[dict[str, float]],
    scenario: dict[str, float],
    sigma: float,
    rng: Generator) -> list[UserState]:
    """
    Sample user states for a batch of synths.

    Args:
        latent_traits_batch: List of latent traits dicts
        scenario: Scenario modifiers (same for all)
        sigma: Standard deviation for Normal noise
        rng: NumPy random generator

    Returns:
        List of UserState instances
    """
    return [sample_user_state(traits, scenario, sigma, rng) for traits in latent_traits_batch]


if __name__ == "__main__":
    import sys

    print("=== Sample State Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Basic sampling
    total_tests += 1
    try:
        rng = np.random.default_rng(seed=42)
        latent_traits = {
            "capability_mean": 0.6,
            "trust_mean": 0.5,
            "friction_tolerance_mean": 0.4,
            "exploration_prob": 0.5,
        }
        scenario = {
            "trust_modifier": 0.0,
            "friction_modifier": 0.0,
            "motivation_modifier": 0.0,
            "task_criticality": 0.5,
        }

        state = sample_user_state(latent_traits, scenario, sigma=0.1, rng=rng)

        if not 0.0 <= state.capability <= 1.0:
            all_validation_failures.append(f"Capability out of range: {state.capability}")
        if not 0.0 <= state.trust <= 1.0:
            all_validation_failures.append(f"Trust out of range: {state.trust}")
        if not 0.0 <= state.friction_tolerance <= 1.0:
            all_validation_failures.append(
                f"Friction tolerance out of range: {state.friction_tolerance}"
            )
        if not isinstance(state.explores, bool):
            all_validation_failures.append(f"Explores should be bool: {type(state.explores)}")
        print(f"Test 1 PASSED: Basic sampling (capability={state.capability:.3f})")
    except Exception as e:
        all_validation_failures.append(f"Basic sampling failed: {e}")

    # Test 2: Reproducibility with same seed
    total_tests += 1
    try:
        rng1 = np.random.default_rng(seed=42)
        rng2 = np.random.default_rng(seed=42)

        state1 = sample_user_state(latent_traits, scenario, sigma=0.1, rng=rng1)
        state2 = sample_user_state(latent_traits, scenario, sigma=0.1, rng=rng2)

        if state1.capability != state2.capability:
            all_validation_failures.append("Reproducibility failed: capability differs")
        if state1.trust != state2.trust:
            all_validation_failures.append("Reproducibility failed: trust differs")
        else:
            print("Test 2 PASSED: Reproducibility with same seed")
    except Exception as e:
        all_validation_failures.append(f"Reproducibility test failed: {e}")

    # Test 3: Scenario modifiers affect output
    total_tests += 1
    try:
        rng = np.random.default_rng(seed=42)
        scenario_crisis = {
            "trust_modifier": -0.2,
            "friction_modifier": -0.15,
            "motivation_modifier": 0.2,
            "task_criticality": 0.85,
        }

        state_baseline = sample_user_state(
            latent_traits, scenario, sigma=0.1, rng=np.random.default_rng(seed=42)
        )
        state_crisis = sample_user_state(
            latent_traits, scenario_crisis, sigma=0.1, rng=np.random.default_rng(seed=42)
        )

        # Crisis should have lower trust (modifier is -0.2)
        if state_crisis.trust >= state_baseline.trust:
            all_validation_failures.append(
                f"Crisis should have lower trust: {state_crisis.trust} >= {state_baseline.trust}"
            )
        # Crisis should have higher motivation
        if state_crisis.motivation <= state_baseline.motivation:
            all_validation_failures.append(
                f"Crisis should have higher motivation: {state_crisis.motivation} <= {state_baseline.motivation}"
            )
        else:
            print("Test 3 PASSED: Scenario modifiers affect output")
    except Exception as e:
        all_validation_failures.append(f"Scenario modifiers test failed: {e}")

    # Test 4: Clamping works
    total_tests += 1
    try:
        rng = np.random.default_rng(seed=42)
        extreme_scenario = {
            "trust_modifier": -1.0,  # Very negative
            "friction_modifier": 1.0,  # Very positive
            "motivation_modifier": 0.0,
            "task_criticality": 0.5,
        }

        state = sample_user_state(latent_traits, extreme_scenario, sigma=0.1, rng=rng)

        # Values should be clamped to [0, 1]
        if state.trust < 0.0 or state.trust > 1.0:
            all_validation_failures.append(f"Trust not clamped: {state.trust}")
        if state.friction_tolerance < 0.0 or state.friction_tolerance > 1.0:
            all_validation_failures.append(
                f"Friction tolerance not clamped: {state.friction_tolerance}"
            )
        else:
            print("Test 4 PASSED: Clamping works correctly")
    except Exception as e:
        all_validation_failures.append(f"Clamping test failed: {e}")

    # Test 5: Exploration probability
    total_tests += 1
    try:
        # With exploration_prob = 1.0, should always explore
        traits_always_explore = {**latent_traits, "exploration_prob": 1.0}
        rng = np.random.default_rng(seed=42)

        explores_count = sum(
            sample_user_state(traits_always_explore, scenario, sigma=0.1, rng=rng).explores
            for _ in range(100)
        )

        if explores_count != 100:
            all_validation_failures.append(
                f"With prob=1.0, should always explore: {explores_count}/100"
            )

        # With exploration_prob = 0.0, should never explore
        traits_never_explore = {**latent_traits, "exploration_prob": 0.0}
        rng = np.random.default_rng(seed=42)

        explores_count = sum(
            sample_user_state(traits_never_explore, scenario, sigma=0.1, rng=rng).explores
            for _ in range(100)
        )

        if explores_count != 0:
            all_validation_failures.append(
                f"With prob=0.0, should never explore: {explores_count}/100"
            )
        else:
            print("Test 5 PASSED: Exploration probability works correctly")
    except Exception as e:
        all_validation_failures.append(f"Exploration probability test failed: {e}")

    # Test 6: Batch sampling
    total_tests += 1
    try:
        rng = np.random.default_rng(seed=42)
        traits_batch = [latent_traits] * 10

        states = sample_user_states_batch(traits_batch, scenario, sigma=0.1, rng=rng)

        if len(states) != 10:
            all_validation_failures.append(f"Expected 10 states, got {len(states)}")
        else:
            print("Test 6 PASSED: Batch sampling works")
    except Exception as e:
        all_validation_failures.append(f"Batch sampling failed: {e}")

    # Final result
    print()
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
