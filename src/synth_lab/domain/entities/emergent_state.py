"""
Emergent state entities for synth-lab.

Defines models for emergent behavioral states calculated from mechanism × sensitivity
interactions during Monte Carlo simulations.

References:
    - Spec: specs/038-mechanism-based-simulation/spec.md
    - Data model: specs/038-mechanism-based-simulation/data-model.md
"""

from dataclasses import dataclass, field


@dataclass
class InteractionContribution:
    """
    Single mechanism × sensitivity interaction contribution.

    Used for explainability to show which interactions had the most impact
    on the emergent state.
    """

    mechanism: str
    """Name of the mechanism (e.g., 'irreversibility')."""

    sensitivity: str
    """Name of the sensitivity (e.g., 'risk_aversion')."""

    product: float
    """mechanism_value × sensitivity_value."""


@dataclass
class EmergentState:
    """
    Emergent behavioral state from mechanism × sensitivity interactions.

    Calculated per user per simulation execution.
    Modifies effective scorecard dimensions.
    """

    perceived_risk_delta: float
    """Change to perceived risk from irreversibility × risk_aversion."""

    initial_effort_delta: float
    """Change to initial effort from habit_displacement + learning_curve interactions."""

    trust_barrier: float
    """Barrier from institutional_trust × (1 - institutional_trust_level)."""

    social_barrier: float
    """Barrier from network_effect × (1 - social_dependency)."""

    top_contributors: list[InteractionContribution] = field(default_factory=list)
    """Top interactions sorted by product value (typically top 3)."""

    raw_interactions: dict[str, float] = field(default_factory=dict)
    """All mechanism_sensitivity products for full explainability."""


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: Create InteractionContribution
    total_tests += 1
    try:
        contribution = InteractionContribution(
            mechanism="irreversibility",
            sensitivity="risk_aversion",
            product=0.72,
        )
        if contribution.mechanism != "irreversibility":
            all_validation_failures.append(f"mechanism mismatch: {contribution.mechanism}")
        if contribution.sensitivity != "risk_aversion":
            all_validation_failures.append(f"sensitivity mismatch: {contribution.sensitivity}")
        if contribution.product != 0.72:
            all_validation_failures.append(f"product mismatch: {contribution.product}")
    except Exception as e:
        all_validation_failures.append(f"InteractionContribution creation failed: {e}")

    # Test 2: Create EmergentState with minimal data
    total_tests += 1
    try:
        state = EmergentState(
            perceived_risk_delta=0.15,
            initial_effort_delta=0.08,
            trust_barrier=0.32,
            social_barrier=0.49,
        )
        if state.perceived_risk_delta != 0.15:
            all_validation_failures.append(
                f"perceived_risk_delta mismatch: {state.perceived_risk_delta}"
            )
        if state.initial_effort_delta != 0.08:
            all_validation_failures.append(
                f"initial_effort_delta mismatch: {state.initial_effort_delta}"
            )
        if state.trust_barrier != 0.32:
            all_validation_failures.append(f"trust_barrier mismatch: {state.trust_barrier}")
        if state.social_barrier != 0.49:
            all_validation_failures.append(f"social_barrier mismatch: {state.social_barrier}")
        if state.top_contributors != []:
            all_validation_failures.append("top_contributors should default to empty list")
        if state.raw_interactions != {}:
            all_validation_failures.append("raw_interactions should default to empty dict")
    except Exception as e:
        all_validation_failures.append(f"EmergentState minimal creation failed: {e}")

    # Test 3: Create EmergentState with full data
    total_tests += 1
    try:
        contributors = [
            InteractionContribution("irreversibility", "risk_aversion", 0.72),
            InteractionContribution("network_effect", "social_dependency", 0.36),
            InteractionContribution("learning_curve", "learning_tolerance", 0.16),
        ]
        raw = {
            "irreversibility_risk_aversion": 0.72,
            "network_effect_social_dependency": 0.36,
            "learning_curve_learning_tolerance": 0.16,
        }
        state = EmergentState(
            perceived_risk_delta=0.15,
            initial_effort_delta=0.08,
            trust_barrier=0.32,
            social_barrier=0.49,
            top_contributors=contributors,
            raw_interactions=raw,
        )
        if len(state.top_contributors) != 3:
            all_validation_failures.append(
                f"top_contributors count mismatch: {len(state.top_contributors)}"
            )
        if state.top_contributors[0].product != 0.72:
            all_validation_failures.append("First contributor product should be 0.72")
        if "irreversibility_risk_aversion" not in state.raw_interactions:
            all_validation_failures.append("raw_interactions missing expected key")
    except Exception as e:
        all_validation_failures.append(f"EmergentState full creation failed: {e}")

    # Test 4: Zero values should be valid
    total_tests += 1
    try:
        state = EmergentState(
            perceived_risk_delta=0.0,
            initial_effort_delta=0.0,
            trust_barrier=0.0,
            social_barrier=0.0,
        )
        if state.perceived_risk_delta != 0.0:
            all_validation_failures.append("Zero perceived_risk_delta should be valid")
    except Exception as e:
        all_validation_failures.append(f"Zero values test failed: {e}")

    # Test 5: Negative values should be valid (deltas can be negative)
    total_tests += 1
    try:
        state = EmergentState(
            perceived_risk_delta=-0.1,
            initial_effort_delta=-0.05,
            trust_barrier=0.0,
            social_barrier=0.0,
        )
        if state.perceived_risk_delta != -0.1:
            all_validation_failures.append("Negative perceived_risk_delta should be valid")
    except Exception as e:
        all_validation_failures.append(f"Negative values test failed: {e}")

    # Test 6: InteractionContribution with edge values
    total_tests += 1
    try:
        contribution = InteractionContribution(
            mechanism="habit_displacement",
            sensitivity="habit_plasticity",
            product=0.0,
        )
        if contribution.product != 0.0:
            all_validation_failures.append("Zero product should be valid")

        contribution2 = InteractionContribution(
            mechanism="social_visibility",
            sensitivity="social_influence",
            product=1.0,
        )
        if contribution2.product != 1.0:
            all_validation_failures.append("Product of 1.0 should be valid")
    except Exception as e:
        all_validation_failures.append(f"Edge values test failed: {e}")

    # Test 7: Empty top_contributors list
    total_tests += 1
    try:
        state = EmergentState(
            perceived_risk_delta=0.15,
            initial_effort_delta=0.08,
            trust_barrier=0.32,
            social_barrier=0.49,
            top_contributors=[],
            raw_interactions={},
        )
        if state.top_contributors != []:
            all_validation_failures.append("Empty top_contributors should work")
        if state.raw_interactions != {}:
            all_validation_failures.append("Empty raw_interactions should work")
    except Exception as e:
        all_validation_failures.append(f"Empty lists test failed: {e}")

    # Test 8: Verify all fields exist on EmergentState
    total_tests += 1
    expected_fields = {
        "perceived_risk_delta",
        "initial_effort_delta",
        "trust_barrier",
        "social_barrier",
        "top_contributors",
        "raw_interactions",
    }
    actual_fields = {f.name for f in EmergentState.__dataclass_fields__.values()}
    if expected_fields != actual_fields:
        all_validation_failures.append(
            f"EmergentState field mismatch: expected {expected_fields}, got {actual_fields}"
        )

    # Test 9: Verify all fields exist on InteractionContribution
    total_tests += 1
    expected_contrib_fields = {"mechanism", "sensitivity", "product"}
    actual_contrib_fields = {f.name for f in InteractionContribution.__dataclass_fields__.values()}
    if expected_contrib_fields != actual_contrib_fields:
        all_validation_failures.append(
            f"InteractionContribution field mismatch: expected {expected_contrib_fields}, "
            f"got {actual_contrib_fields}"
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
