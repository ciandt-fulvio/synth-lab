"""
Mechanism interaction service for synth-lab.

.. deprecated:: 040-mechanism-sensitivity-update
    This module is replaced by ``emergent_calculator.py`` which implements
    the new 9-state emergent model (7 barriers + 2 appeals). Kept for
    reference and backward compatibility. Do not use for new code.

Calculates emergent behavioral states from mechanism × sensitivity interactions.
These emergent states modify effective scorecard dimensions during simulation.

References:
    - Spec: specs/038-mechanism-based-simulation/spec.md (original)
    - Superseded by: specs/040-mechanism-sensitivity-update/spec.md
    - Data model: specs/038-mechanism-based-simulation/data-model.md

Original Interaction Formula (4 deltas):
    perceived_risk_delta = irreversibility × risk_aversion
    initial_effort_delta = habit_displacement × (1 - habit_plasticity)
                         + learning_curve × (1 - digital_capability)
    trust_barrier = institutional_trust × (1 - institutional_trust_level)
    social_barrier = network_effect × (1 - social_dependency)
"""

from synth_lab.domain.entities.emergent_state import EmergentState, InteractionContribution
from synth_lab.domain.entities.feature_mechanisms import FeatureMechanisms
from synth_lab.domain.entities.user_sensitivities import UserSensitivities

# Mechanism-sensitivity interaction pairs
INTERACTION_PAIRS = [
    ("irreversibility", "risk_aversion"),
    ("network_effect", "social_dependency"),
    ("institutional_trust", "institutional_trust_level"),
    ("habit_displacement", "habit_plasticity"),
    ("learning_curve", "digital_capability"),
    ("social_visibility", "social_dependency"),
]


def calculate_emergent_state(
    mechanisms: FeatureMechanisms,
    sensitivities: UserSensitivities,
) -> EmergentState:
    """
    Calculate emergent state from mechanism × sensitivity interactions.

    Args:
        mechanisms: Feature structural mechanisms.
        sensitivities: User psychological sensitivities.

    Returns:
        EmergentState with computed deltas and contributors.

    Example:
        >>> mechanisms = FeatureMechanisms(irreversibility=0.9, network_effect=0.7)
        >>> sensitivities = UserSensitivities(risk_aversion=0.8, social_dependency=0.3)
        >>> state = calculate_emergent_state(mechanisms, sensitivities)
        >>> state.perceived_risk_delta
        0.72  # 0.9 × 0.8
    """
    # Calculate all raw interactions
    raw_interactions: dict[str, float] = {}

    for mech_name, sens_name in INTERACTION_PAIRS:
        mech_value = getattr(mechanisms, mech_name)
        sens_value = getattr(sensitivities, sens_name)

        # For barriers, we use (1 - sensitivity) for some interactions
        # to represent resistance (high sensitivity = low barrier)
        if mech_name in ("irreversibility", "social_visibility"):
            # These directly multiply with sensitivity
            product = mech_value * sens_value
        else:
            # For barriers, high sensitivity reduces the barrier
            product = mech_value * (1 - sens_value)

        key = f"{mech_name}_{sens_name}"
        raw_interactions[key] = product

    # Calculate emergent deltas
    perceived_risk_delta = mechanisms.irreversibility * sensitivities.risk_aversion

    initial_effort_delta = (
        mechanisms.habit_displacement * (1 - sensitivities.habit_plasticity)
        + mechanisms.learning_curve * (1 - sensitivities.digital_capability)
    )

    trust_barrier = mechanisms.institutional_trust * (1 - sensitivities.institutional_trust_level)

    social_barrier = mechanisms.network_effect * (1 - sensitivities.social_dependency)

    # Get top contributors
    top_contributors = get_top_contributors(raw_interactions, top_n=3)

    return EmergentState(
        perceived_risk_delta=perceived_risk_delta,
        initial_effort_delta=initial_effort_delta,
        trust_barrier=trust_barrier,
        social_barrier=social_barrier,
        top_contributors=top_contributors,
        raw_interactions=raw_interactions,
    )


def get_top_contributors(
    raw_interactions: dict[str, float],
    top_n: int = 3,
) -> list[InteractionContribution]:
    """
    Get top N interactions sorted by product value.

    Args:
        raw_interactions: Dictionary of mechanism_sensitivity -> product.
        top_n: Number of top contributors to return.

    Returns:
        List of InteractionContribution sorted by product descending.
    """
    contributions = []

    for key, product in raw_interactions.items():
        if product > 0:  # Only include non-zero contributions
            parts = key.split("_", 1)
            if len(parts) == 2:
                mechanism, sensitivity = parts[0], parts[1]
            else:
                # Handle keys like "network_effect_social_dependency"
                for mech_name, sens_name in INTERACTION_PAIRS:
                    expected_key = f"{mech_name}_{sens_name}"
                    if key == expected_key:
                        mechanism, sensitivity = mech_name, sens_name
                        break
                else:
                    continue  # Skip malformed keys

            contributions.append(
                InteractionContribution(
                    mechanism=mechanism,
                    sensitivity=sensitivity,
                    product=product,
                )
            )

    # Sort by product descending and return top N
    contributions.sort(key=lambda c: c.product, reverse=True)
    return contributions[:top_n]


def calculate_effective_scores(
    base_scores: dict[str, float],
    emergent_state: EmergentState,
) -> dict[str, float]:
    """
    Apply emergent state deltas to base scorecard scores.

    Args:
        base_scores: Dictionary with keys 'complexity', 'initial_effort',
                    'perceived_risk', 'time_to_value'.
        emergent_state: Calculated emergent state from mechanism interactions.

    Returns:
        Modified scores with deltas applied, clamped to [0, 1].

    Example:
        >>> base_scores = {'perceived_risk': 0.3, 'initial_effort': 0.4, ...}
        >>> effective = calculate_effective_scores(base_scores, emergent_state)
        >>> effective['perceived_risk']  # 0.3 + perceived_risk_delta (clamped)
    """
    effective = base_scores.copy()

    # Apply perceived_risk_delta
    if "perceived_risk" in effective:
        effective["perceived_risk"] = _clamp(
            effective["perceived_risk"] + emergent_state.perceived_risk_delta
        )

    # Apply initial_effort_delta
    if "initial_effort" in effective:
        effective["initial_effort"] = _clamp(
            effective["initial_effort"] + emergent_state.initial_effort_delta
        )

    # Trust barrier affects perceived_risk
    if "perceived_risk" in effective:
        effective["perceived_risk"] = _clamp(
            effective["perceived_risk"] + emergent_state.trust_barrier
        )

    # Social barrier affects complexity (harder to adopt without network)
    if "complexity" in effective:
        effective["complexity"] = _clamp(
            effective["complexity"] + emergent_state.social_barrier
        )

    return effective


def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp value to [min_val, max_val] range."""
    return max(min_val, min(max_val, value))


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: Basic calculation
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
        sensitivities = UserSensitivities(
            risk_aversion=0.8,
            social_dependency=0.3,
            institutional_trust_level=0.6,
            habit_plasticity=0.5,
            digital_capability=0.7,
            pragmatism=0.5,
            friction_tolerance=0.5,
        )
        state = calculate_emergent_state(mechanisms, sensitivities)

        # perceived_risk_delta = 0.9 × 0.8 = 0.72
        expected_risk = 0.72
        if abs(state.perceived_risk_delta - expected_risk) > 0.001:
            all_validation_failures.append(
                f"perceived_risk_delta: expected {expected_risk}, got {state.perceived_risk_delta}"
            )

        # trust_barrier = 0.8 × (1 - 0.6) = 0.8 × 0.4 = 0.32
        expected_trust = 0.32
        if abs(state.trust_barrier - expected_trust) > 0.001:
            all_validation_failures.append(
                f"trust_barrier: expected {expected_trust}, got {state.trust_barrier}"
            )

        # social_barrier = 0.7 × (1 - 0.3) = 0.7 × 0.7 = 0.49
        expected_social = 0.49
        if abs(state.social_barrier - expected_social) > 0.001:
            all_validation_failures.append(
                f"social_barrier: expected {expected_social}, got {state.social_barrier}"
            )

    except Exception as e:
        all_validation_failures.append(f"Basic calculation failed: {e}")

    # Test 2: Zero mechanisms produce zero deltas
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms()  # All zeros
        sensitivities = UserSensitivities(risk_aversion=0.9)  # High sensitivity
        state = calculate_emergent_state(mechanisms, sensitivities)

        if state.perceived_risk_delta != 0.0:
            all_validation_failures.append(
                f"Zero mechanisms should produce zero deltas: {state.perceived_risk_delta}"
            )
    except Exception as e:
        all_validation_failures.append(f"Zero mechanisms test failed: {e}")

    # Test 3: Top contributors are sorted by product
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(
            irreversibility=0.9,  # Will produce highest
            network_effect=0.3,
            learning_curve=0.5,
        )
        sensitivities = UserSensitivities(
            risk_aversion=0.9,  # 0.9 × 0.9 = 0.81
            social_dependency=0.1,  # 0.3 × 0.9 = 0.27
            digital_capability=0.3,  # 0.5 × 0.7 = 0.35
        )
        state = calculate_emergent_state(mechanisms, sensitivities)

        if len(state.top_contributors) == 0:
            all_validation_failures.append("Should have top contributors")
        elif state.top_contributors[0].mechanism != "irreversibility":
            all_validation_failures.append(
                f"Top contributor should be irreversibility: {state.top_contributors[0].mechanism}"
            )
    except Exception as e:
        all_validation_failures.append(f"Top contributors test failed: {e}")

    # Test 4: Same scores different mechanisms produce >15% variance
    total_tests += 1
    try:
        # High-mechanism feature
        high_mech = FeatureMechanisms(
            irreversibility=0.9,
            network_effect=0.8,
            institutional_trust=0.7,
        )
        # Low-mechanism feature
        low_mech = FeatureMechanisms(
            irreversibility=0.1,
            network_effect=0.1,
            institutional_trust=0.1,
        )
        # High-sensitivity user
        high_sens = UserSensitivities(
            risk_aversion=0.9,
            social_dependency=0.2,
            institutional_trust_level=0.3,
        )

        state_high = calculate_emergent_state(high_mech, high_sens)
        state_low = calculate_emergent_state(low_mech, high_sens)

        # Calculate total impact difference
        high_impact = (
            state_high.perceived_risk_delta
            + state_high.trust_barrier
            + state_high.social_barrier
        )
        low_impact = (
            state_low.perceived_risk_delta + state_low.trust_barrier + state_low.social_barrier
        )

        variance = abs(high_impact - low_impact)
        # SC-001: Must show >15% variance
        if variance < 0.15:
            all_validation_failures.append(
                f"Same-score features with different mechanisms should show >15% variance: {variance}"
            )
    except Exception as e:
        all_validation_failures.append(f"Variance test failed: {e}")

    # Test 5: Effective scores are clamped to [0, 1]
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(
            irreversibility=1.0,
            habit_displacement=1.0,
            learning_curve=1.0,
        )
        sensitivities = UserSensitivities(
            risk_aversion=1.0,
            habit_plasticity=0.0,
            digital_capability=0.0,
        )
        state = calculate_emergent_state(mechanisms, sensitivities)

        base_scores = {
            "perceived_risk": 0.8,  # + 1.0 delta would be 1.8
            "initial_effort": 0.9,  # + 2.0 delta would be 2.9
            "complexity": 0.5,
            "time_to_value": 0.5,
        }

        effective = calculate_effective_scores(base_scores, state)

        if effective["perceived_risk"] > 1.0:
            all_validation_failures.append(
                f"perceived_risk should be clamped: {effective['perceived_risk']}"
            )
        if effective["initial_effort"] > 1.0:
            all_validation_failures.append(
                f"initial_effort should be clamped: {effective['initial_effort']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Clamping test failed: {e}")

    # Test 6: Raw interactions dict has all expected keys
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(irreversibility=0.5)
        sensitivities = UserSensitivities()
        state = calculate_emergent_state(mechanisms, sensitivities)

        expected_keys = {
            "irreversibility_risk_aversion",
            "network_effect_social_dependency",
            "institutional_trust_institutional_trust_level",
            "habit_displacement_habit_plasticity",
            "learning_curve_digital_capability",
            "social_visibility_social_dependency",
        }
        actual_keys = set(state.raw_interactions.keys())

        if expected_keys != actual_keys:
            all_validation_failures.append(
                f"raw_interactions keys mismatch: expected {expected_keys}, got {actual_keys}"
            )
    except Exception as e:
        all_validation_failures.append(f"Raw interactions test failed: {e}")

    # Test 7: Initial effort delta calculation
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(habit_displacement=0.6, learning_curve=0.4)
        sensitivities = UserSensitivities(habit_plasticity=0.2, digital_capability=0.3)
        state = calculate_emergent_state(mechanisms, sensitivities)

        # habit_displacement × (1 - habit_plasticity) = 0.6 × 0.8 = 0.48
        # learning_curve × (1 - digital_capability) = 0.4 × 0.7 = 0.28
        # Total = 0.48 + 0.28 = 0.76
        expected_effort = 0.76
        if abs(state.initial_effort_delta - expected_effort) > 0.001:
            all_validation_failures.append(
                f"initial_effort_delta: expected {expected_effort}, got {state.initial_effort_delta}"
            )
    except Exception as e:
        all_validation_failures.append(f"Initial effort calculation test failed: {e}")

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
