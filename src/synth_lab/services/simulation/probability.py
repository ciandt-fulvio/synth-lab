"""
Probability calculations for Monte Carlo simulation.

Functions for calculating attempt and success probabilities based on
user state and feature scorecard.

Functions:
- sigmoid(): Logistic sigmoid function
- calculate_p_attempt(): Probability user attempts the feature
- calculate_p_success(): Probability of success given attempt
- sample_outcome(): Sample outcome based on probabilities

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Research: specs/016-feature-impact-simulation/research.md

Sample usage:
    from synth_lab.services.simulation.probability import calculate_p_attempt, sample_outcome
    import numpy as np

    rng = np.random.default_rng(seed=42)
    p_attempt = calculate_p_attempt(user_state, scorecard_scores)
    p_success = calculate_p_success(user_state, scorecard_scores)
    outcome = sample_outcome(p_attempt, p_success, rng)

Expected output:
    outcome: "did_not_try", "failed", or "success"
"""

from typing import Literal

import numpy as np
from numpy.random import Generator

from synth_lab.services.simulation.sample_state import UserState

# Type alias for outcomes
Outcome = Literal["did_not_try", "failed", "success"]


def sigmoid(x: float) -> float:
    """
    Logistic sigmoid function.

    Maps any real number to (0, 1) range.

    Args:
        x: Input value

    Returns:
        float: sigmoid(x) in (0, 1)

    Examples:
        >>> sigmoid(0)
        0.5
        >>> sigmoid(10)  # doctest: +ELLIPSIS
        0.999...
        >>> sigmoid(-10)  # doctest: +ELLIPSIS
        0.0000...
    """
    # Use numpy's implementation for numerical stability
    return float(1.0 / (1.0 + np.exp(-x)))


def calculate_p_attempt(
    user_state: UserState,
    scorecard_scores: dict[str, float]) -> float:
    """
    Calculate probability that user attempts the feature.

    Formula:
        logit = w_motivation * motivation
              + w_trust * trust
              - w_risk * perceived_risk
              - w_effort * initial_effort
              + w_explore * explores
              + intercept

        P(attempt) = sigmoid(logit)

    Args:
        user_state: Sampled user state
        scorecard_scores: Dict with perceived_risk, initial_effort scores

    Returns:
        float: Probability of attempt in [0, 1]

    Notes:
        - Higher motivation and trust increase attempt probability
        - Higher risk and effort decrease attempt probability
        - Explorers are more likely to attempt
    """
    # Extract user state
    motivation = user_state.motivation
    trust = user_state.trust
    explores = float(user_state.explores)

    # Extract scorecard scores (0 = best, 1 = worst)
    perceived_risk = scorecard_scores.get("perceived_risk", 0.5)
    initial_effort = scorecard_scores.get("initial_effort", 0.5)

    # Weights (from research.md calibration)
    w_motivation = 2.0
    w_trust = 1.5
    w_risk = 2.0
    w_effort = 1.5
    w_explore = 1.0
    intercept = 0.0

    # Calculate logit
    logit = (
        w_motivation * motivation
        + w_trust * trust
        - w_risk * perceived_risk
        - w_effort * initial_effort
        + w_explore * explores
        + intercept
    )

    return sigmoid(logit)


def calculate_p_success(
    user_state: UserState,
    scorecard_scores: dict[str, float]) -> float:
    """
    Calculate probability of success given user attempted.

    Formula:
        logit = w_capability * capability
              + w_friction * friction_tolerance
              - w_complexity * complexity
              - w_ttv * time_to_value
              + intercept

        P(success|attempt) = sigmoid(logit)

    Args:
        user_state: Sampled user state
        scorecard_scores: Dict with complexity, time_to_value scores

    Returns:
        float: Probability of success in [0, 1]

    Notes:
        - Higher capability and friction tolerance increase success
        - Higher complexity and time_to_value decrease success
    """
    # Extract user state
    capability = user_state.capability
    friction_tolerance = user_state.friction_tolerance

    # Extract scorecard scores (0 = best, 1 = worst)
    complexity = scorecard_scores.get("complexity", 0.5)
    time_to_value = scorecard_scores.get("time_to_value", 0.5)

    # Weights (from research.md calibration)
    w_capability = 2.5
    w_friction = 1.5
    w_complexity = 2.0
    w_ttv = 1.5
    intercept = 0.0

    # Calculate logit
    logit = (
        w_capability * capability
        + w_friction * friction_tolerance
        - w_complexity * complexity
        - w_ttv * time_to_value
        + intercept
    )

    return sigmoid(logit)


def sample_outcome(
    p_attempt: float,
    p_success: float,
    rng: Generator) -> Outcome:
    """
    Sample outcome based on attempt and success probabilities.

    Decision tree:
    1. Sample Bernoulli(p_attempt) -> if false, return "did_not_try"
    2. Sample Bernoulli(p_success) -> if false, return "failed"
    3. Return "success"

    Args:
        p_attempt: Probability of attempting
        p_success: Probability of success given attempt
        rng: NumPy random generator

    Returns:
        Outcome: "did_not_try", "failed", or "success"
    """
    # First, check if user attempts
    if rng.random() >= p_attempt:
        return "did_not_try"

    # User attempted, check if successful
    if rng.random() >= p_success:
        return "failed"

    return "success"


def calculate_outcome_probabilities(
    user_state: UserState,
    scorecard_scores: dict[str, float]) -> dict[str, float]:
    """
    Calculate exact outcome probabilities (no sampling).

    Args:
        user_state: Sampled user state
        scorecard_scores: Dict with all dimension scores

    Returns:
        Dict with p_did_not_try, p_failed, p_success

    Notes:
        - p_did_not_try = 1 - p_attempt
        - p_failed = p_attempt * (1 - p_success)
        - p_success = p_attempt * p_success
        - Sum should equal 1.0
    """
    p_attempt = calculate_p_attempt(user_state, scorecard_scores)
    p_success_given_attempt = calculate_p_success(user_state, scorecard_scores)

    p_did_not_try = 1.0 - p_attempt
    p_failed = p_attempt * (1.0 - p_success_given_attempt)
    p_success = p_attempt * p_success_given_attempt

    return {
        "p_did_not_try": p_did_not_try,
        "p_failed": p_failed,
        "p_success": p_success,
    }


if __name__ == "__main__":
    import sys

    print("=== Probability Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Sigmoid basic properties
    total_tests += 1
    try:
        if abs(sigmoid(0) - 0.5) > 0.001:
            all_validation_failures.append(f"sigmoid(0) should be 0.5: {sigmoid(0)}")
        if sigmoid(10) < 0.999:
            all_validation_failures.append(f"sigmoid(10) should be ~1: {sigmoid(10)}")
        if sigmoid(-10) > 0.001:
            all_validation_failures.append(f"sigmoid(-10) should be ~0: {sigmoid(-10)}")
        print("Test 1 PASSED: Sigmoid basic properties")
    except Exception as e:
        all_validation_failures.append(f"Sigmoid test failed: {e}")

    # Test 2: P_attempt increases with motivation
    total_tests += 1
    try:
        scorecard = {"perceived_risk": 0.5, "initial_effort": 0.5}

        state_low_motivation = UserState(
            capability=0.5,
            trust=0.5,
            friction_tolerance=0.5,
            explores=False,
            motivation=0.2)
        state_high_motivation = UserState(
            capability=0.5,
            trust=0.5,
            friction_tolerance=0.5,
            explores=False,
            motivation=0.8)

        p_low = calculate_p_attempt(state_low_motivation, scorecard)
        p_high = calculate_p_attempt(state_high_motivation, scorecard)

        if p_high <= p_low:
            all_validation_failures.append(
                f"Higher motivation should increase p_attempt: {p_high} <= {p_low}"
            )
        else:
            print(
                f"Test 2 PASSED: P_attempt increases with motivation ({p_low:.3f} -> {p_high:.3f})"
            )
    except Exception as e:
        all_validation_failures.append(f"P_attempt motivation test failed: {e}")

    # Test 3: P_success increases with capability
    total_tests += 1
    try:
        scorecard = {"complexity": 0.5, "time_to_value": 0.5}

        state_low_cap = UserState(
            capability=0.2,
            trust=0.5,
            friction_tolerance=0.5,
            explores=False,
            motivation=0.5)
        state_high_cap = UserState(
            capability=0.8,
            trust=0.5,
            friction_tolerance=0.5,
            explores=False,
            motivation=0.5)

        p_low = calculate_p_success(state_low_cap, scorecard)
        p_high = calculate_p_success(state_high_cap, scorecard)

        if p_high <= p_low:
            all_validation_failures.append(
                f"Higher capability should increase p_success: {p_high} <= {p_low}"
            )
        else:
            print(
                f"Test 3 PASSED: P_success increases with capability ({p_low:.3f} -> {p_high:.3f})"
            )
    except Exception as e:
        all_validation_failures.append(f"P_success capability test failed: {e}")

    # Test 4: Higher risk decreases p_attempt
    total_tests += 1
    try:
        state = UserState(
            capability=0.5,
            trust=0.5,
            friction_tolerance=0.5,
            explores=False,
            motivation=0.5)

        p_low_risk = calculate_p_attempt(state, {"perceived_risk": 0.2, "initial_effort": 0.5})
        p_high_risk = calculate_p_attempt(state, {"perceived_risk": 0.8, "initial_effort": 0.5})

        if p_high_risk >= p_low_risk:
            all_validation_failures.append(
                f"Higher risk should decrease p_attempt: {p_high_risk} >= {p_low_risk}"
            )
        else:
            print(
                f"Test 4 PASSED: Higher risk decreases p_attempt ({p_low_risk:.3f} -> {p_high_risk:.3f})"
            )
    except Exception as e:
        all_validation_failures.append(f"Risk effect test failed: {e}")

    # Test 5: Sample outcome distribution
    total_tests += 1
    try:
        rng = np.random.default_rng(seed=42)

        # Sample many outcomes
        outcomes = []
        for _ in range(1000):
            outcome = sample_outcome(0.7, 0.8, rng)
            outcomes.append(outcome)

        # Count outcomes
        counts = {
            "did_not_try": outcomes.count("did_not_try"),
            "failed": outcomes.count("failed"),
            "success": outcomes.count("success"),
        }

        # Expected: ~30% did_not_try, ~14% failed (0.7*0.2), ~56% success (0.7*0.8)
        if counts["did_not_try"] < 200 or counts["did_not_try"] > 400:
            all_validation_failures.append(f"did_not_try count unexpected: {counts['did_not_try']}")
        if counts["success"] < 400 or counts["success"] > 700:
            all_validation_failures.append(f"success count unexpected: {counts['success']}")
        else:
            print(f"Test 5 PASSED: Sample outcome distribution ({counts})")
    except Exception as e:
        all_validation_failures.append(f"Sample outcome test failed: {e}")

    # Test 6: Outcome probabilities sum to 1
    total_tests += 1
    try:
        state = UserState(
            capability=0.5,
            trust=0.5,
            friction_tolerance=0.5,
            explores=True,
            motivation=0.5)
        scorecard = {
            "complexity": 0.4,
            "initial_effort": 0.3,
            "perceived_risk": 0.2,
            "time_to_value": 0.5,
        }

        probs = calculate_outcome_probabilities(state, scorecard)
        total = probs["p_did_not_try"] + probs["p_failed"] + probs["p_success"]

        if abs(total - 1.0) > 0.0001:
            all_validation_failures.append(f"Probabilities should sum to 1: {total}")
        else:
            print(f"Test 6 PASSED: Outcome probabilities sum to 1.0 ({probs})")
    except Exception as e:
        all_validation_failures.append(f"Outcome probabilities test failed: {e}")

    # Test 7: Explores increases p_attempt
    total_tests += 1
    try:
        scorecard = {"perceived_risk": 0.5, "initial_effort": 0.5}

        state_no_explore = UserState(
            capability=0.5,
            trust=0.5,
            friction_tolerance=0.5,
            explores=False,
            motivation=0.5)
        state_explore = UserState(
            capability=0.5,
            trust=0.5,
            friction_tolerance=0.5,
            explores=True,
            motivation=0.5)

        p_no = calculate_p_attempt(state_no_explore, scorecard)
        p_yes = calculate_p_attempt(state_explore, scorecard)

        if p_yes <= p_no:
            all_validation_failures.append(f"Explores should increase p_attempt: {p_yes} <= {p_no}")
        else:
            print(f"Test 7 PASSED: Explores increases p_attempt ({p_no:.3f} -> {p_yes:.3f})")
    except Exception as e:
        all_validation_failures.append(f"Explores effect test failed: {e}")

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
