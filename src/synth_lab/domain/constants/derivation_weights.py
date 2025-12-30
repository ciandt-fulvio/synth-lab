"""
Derivation Weights for Latent Trait Calculation.

This module defines the weights used to derive latent traits from observable
attributes. The weights are documented with rationale for each value.

References:
    - Spec: specs/022-observable-latent-traits/spec.md (FR-007, US5)
    - Research: specs/022-observable-latent-traits/research.md
    - Data model: specs/022-observable-latent-traits/data-model.md

Sample usage:
    from synth_lab.domain.constants.derivation_weights import DERIVATION_WEIGHTS

    cap_weights = DERIVATION_WEIGHTS["capability_mean"]
    # {'digital_literacy': 0.40, 'similar_tool_experience': 0.35, ...}

Expected output:
    Dictionary with weights summing to 1.0 for each latent trait
"""

from typing import TypedDict


class CapabilityWeights(TypedDict):
    """Weights for capability_mean derivation."""

    digital_literacy: float
    similar_tool_experience: float
    motor_ability: float
    domain_expertise: float


class TrustWeights(TypedDict):
    """Weights for trust_mean derivation."""

    similar_tool_experience: float
    digital_literacy: float


class FrictionToleranceWeights(TypedDict):
    """Weights for friction_tolerance_mean derivation."""

    time_availability: float
    digital_literacy: float
    similar_tool_experience: float


class ExplorationWeights(TypedDict):
    """Weights for exploration_prob derivation."""

    digital_literacy: float
    novelty_preference: float  # Derived from (1 - similar_tool_experience)
    time_availability: float


class DerivationWeightsType(TypedDict):
    """Complete derivation weights structure."""

    capability_mean: CapabilityWeights
    trust_mean: TrustWeights
    friction_tolerance_mean: FrictionToleranceWeights
    exploration_prob: ExplorationWeights


# =============================================================================
# DERIVATION WEIGHTS
# =============================================================================
#
# These weights define how observable attributes contribute to each latent trait.
# All weights within a trait MUST sum to 1.0 to ensure latent values remain in [0,1].
#
# Rationale for each trait:
#
# CAPABILITY_MEAN: User's ability to successfully complete digital tasks
# - digital_literacy (0.40): Primary driver - tech skills directly affect capability
# - similar_tool_experience (0.35): Prior experience with similar tools helps success
# - motor_ability (0.15): Physical ability affects interaction speed and accuracy
# - domain_expertise (0.10): Domain knowledge helps understand context but less critical
#
# TRUST_MEAN: User's trust in digital systems and willingness to rely on them
# - similar_tool_experience (0.60): Past success builds trust in similar tools
# - digital_literacy (0.40): Understanding technology reduces fear and increases trust
#
# FRICTION_TOLERANCE_MEAN: User's patience with obstacles and errors
# - time_availability (0.40): More time = more patience for friction
# - digital_literacy (0.35): Tech-savvy users understand errors better, tolerate more
# - similar_tool_experience (0.25): Experience helps calibrate expectations
#
# EXPLORATION_PROB: Probability user will try new features/approaches
# - digital_literacy (0.50): Tech-savvy users more likely to explore
# - novelty_preference (0.30): Less experience = more novelty seeking (1 - exp)
# - time_availability (0.20): More time = more exploration
#
# =============================================================================

DERIVATION_WEIGHTS: DerivationWeightsType = {
    # ==========================================================================
    # CAPABILITY_MEAN
    # ==========================================================================
    # User's ability to successfully complete digital tasks.
    # Formula: 0.40*dl + 0.35*exp + 0.15*motor + 0.10*domain
    # Sum: 0.40 + 0.35 + 0.15 + 0.10 = 1.00
    "capability_mean": {
        "digital_literacy": 0.40,  # Primary driver: tech skills
        "similar_tool_experience": 0.35,  # Prior experience with similar tools
        "motor_ability": 0.15,  # Physical ability for interaction
        "domain_expertise": 0.10,  # Domain knowledge (context understanding)
    },
    # ==========================================================================
    # TRUST_MEAN
    # ==========================================================================
    # User's trust in digital systems and willingness to rely on them.
    # Formula: 0.60*exp + 0.40*dl
    # Sum: 0.60 + 0.40 = 1.00
    "trust_mean": {
        "similar_tool_experience": 0.60,  # Past success builds trust
        "digital_literacy": 0.40,  # Understanding reduces fear
    },
    # ==========================================================================
    # FRICTION_TOLERANCE_MEAN
    # ==========================================================================
    # User's patience with obstacles and errors during task completion.
    # Formula: 0.40*time + 0.35*dl + 0.25*exp
    # Sum: 0.40 + 0.35 + 0.25 = 1.00
    "friction_tolerance_mean": {
        "time_availability": 0.40,  # More time = more patience
        "digital_literacy": 0.35,  # Tech-savvy tolerate errors better
        "similar_tool_experience": 0.25,  # Experience calibrates expectations
    },
    # ==========================================================================
    # EXPLORATION_PROB
    # ==========================================================================
    # Probability that user will try new features or approaches.
    # Formula: 0.50*dl + 0.30*(1-exp) + 0.20*time
    # Note: (1-exp) represents novelty preference - less experience means more
    # willingness to try new things (no established habits to break).
    # Sum: 0.50 + 0.30 + 0.20 = 1.00
    "exploration_prob": {
        "digital_literacy": 0.50,  # Tech-savvy explore more
        "novelty_preference": 0.30,  # Calculated as (1 - similar_tool_experience)
        "time_availability": 0.20,  # More time = more exploration
    },
}


def validate_derivation_weights() -> tuple[bool, list[str]]:
    """
    Validate that all weight sets sum to 1.0.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    for trait_name, weights in DERIVATION_WEIGHTS.items():
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            errors.append(f"{trait_name} weights sum to {total}, expected 1.0")

    return (len(errors) == 0, errors)


if __name__ == "__main__":
    import sys

    print("=== Derivation Weights Validation ===\n")

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: All weights exist
    total_tests += 1
    try:
        expected_traits = [
            "capability_mean",
            "trust_mean",
            "friction_tolerance_mean",
            "exploration_prob",
        ]
        for trait in expected_traits:
            if trait not in DERIVATION_WEIGHTS:
                all_validation_failures.append(f"Missing trait: {trait}")
        print("Test 1 PASSED: All expected traits exist")
    except Exception as e:
        all_validation_failures.append(f"Traits existence test failed: {e}")

    # Test 2: All weights sum to 1.0
    total_tests += 1
    try:
        is_valid, errors = validate_derivation_weights()
        if not is_valid:
            all_validation_failures.extend(errors)
        else:
            print("Test 2 PASSED: All weights sum to 1.0")
    except Exception as e:
        all_validation_failures.append(f"Weight sum validation failed: {e}")

    # Test 3: Capability weights are correct
    total_tests += 1
    try:
        cap = DERIVATION_WEIGHTS["capability_mean"]
        if cap["digital_literacy"] != 0.40:
            all_validation_failures.append(
                f"capability digital_literacy should be 0.40, got {cap['digital_literacy']}"
            )
        if cap["similar_tool_experience"] != 0.35:
            actual = cap["similar_tool_experience"]
            all_validation_failures.append(
                f"capability similar_tool_experience: expected 0.35, got {actual}"
            )
        if cap["motor_ability"] != 0.15:
            all_validation_failures.append(
                f"capability motor_ability should be 0.15, got {cap['motor_ability']}"
            )
        if cap["domain_expertise"] != 0.10:
            all_validation_failures.append(
                f"capability domain_expertise should be 0.10, got {cap['domain_expertise']}"
            )
        print("Test 3 PASSED: Capability weights are correct")
    except Exception as e:
        all_validation_failures.append(f"Capability weights test failed: {e}")

    # Test 4: Trust weights are correct
    total_tests += 1
    try:
        trust = DERIVATION_WEIGHTS["trust_mean"]
        if trust["similar_tool_experience"] != 0.60:
            actual = trust["similar_tool_experience"]
            all_validation_failures.append(
                f"trust similar_tool_experience: expected 0.60, got {actual}"
            )
        if trust["digital_literacy"] != 0.40:
            all_validation_failures.append(
                f"trust digital_literacy should be 0.40, got {trust['digital_literacy']}"
            )
        print("Test 4 PASSED: Trust weights are correct")
    except Exception as e:
        all_validation_failures.append(f"Trust weights test failed: {e}")

    # Test 5: Friction tolerance weights are correct
    total_tests += 1
    try:
        friction = DERIVATION_WEIGHTS["friction_tolerance_mean"]
        if friction["time_availability"] != 0.40:
            all_validation_failures.append(
                f"friction time_availability should be 0.40, got {friction['time_availability']}"
            )
        if friction["digital_literacy"] != 0.35:
            all_validation_failures.append(
                f"friction digital_literacy should be 0.35, got {friction['digital_literacy']}"
            )
        if friction["similar_tool_experience"] != 0.25:
            actual = friction["similar_tool_experience"]
            all_validation_failures.append(
                f"friction similar_tool_experience: expected 0.25, got {actual}"
            )
        print("Test 5 PASSED: Friction tolerance weights are correct")
    except Exception as e:
        all_validation_failures.append(f"Friction tolerance weights test failed: {e}")

    # Test 6: Exploration weights are correct
    total_tests += 1
    try:
        exp = DERIVATION_WEIGHTS["exploration_prob"]
        if exp["digital_literacy"] != 0.50:
            all_validation_failures.append(
                f"exploration digital_literacy should be 0.50, got {exp['digital_literacy']}"
            )
        if exp["novelty_preference"] != 0.30:
            all_validation_failures.append(
                f"exploration novelty_preference should be 0.30, got {exp['novelty_preference']}"
            )
        if exp["time_availability"] != 0.20:
            all_validation_failures.append(
                f"exploration time_availability should be 0.20, got {exp['time_availability']}"
            )
        print("Test 6 PASSED: Exploration weights are correct")
    except Exception as e:
        all_validation_failures.append(f"Exploration weights test failed: {e}")

    # Final validation result
    print()
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Derivation weights are correctly defined")
        sys.exit(0)
