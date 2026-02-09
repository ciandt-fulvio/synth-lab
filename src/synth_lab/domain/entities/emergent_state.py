"""
Emergent state entities for synth-lab.

Defines models for emergent behavioral states calculated from mechanism x sensitivity
interactions during Monte Carlo simulations. Each state represents a barrier or appeal
that modifies user adoption behavior.

11 Emergent States:
    Barriers (8):
        - perceived_risk: irreversibility x risk_aversion (Affinity)
        - trust_barrier: institutional_trust x (1 - institutional_trust_level) (Resistance)
        - habit_resistance: habit_displacement x (1 - habit_plasticity) (Resistance)
        - learning_frustration: learning_curve x (1 - digital_capability) (Resistance)
        - friction_burden: friccao_operacional x (1 - friction_tolerance) (Resistance)
        - social_pressure: social_visibility x social_dependency (Affinity)
        - network_barrier: network_effect x (1 - social_dependency) (Resistance)
        - motor_barrier: friccao_operacional x (1 - motor_ability) (Resistance)

    Appeals (3):
        - intrinsic_appeal: valor_intrinseco x pragmatism (Appeal)
        - frequency_value: frequencia_de_uso x pragmatism (Appeal)
        - domain_advantage: valor_intrinseco x subject_domain (Appeal)

References:
    - Spec: specs/040-emergent-state-expansion/spec.md
"""

from dataclasses import dataclass, field


@dataclass
class InteractionContribution:
    """
    Single mechanism x sensitivity interaction contribution.

    Used for explainability to show which interactions had the most impact
    on the emergent state.
    """

    mechanism: str
    """Name of the mechanism (e.g., 'irreversibility')."""

    sensitivity: str
    """Name of the sensitivity (e.g., 'risk_aversion')."""

    product: float
    """mechanism_value x sensitivity_value."""


@dataclass
class EmergentState:
    """
    Emergent behavioral state from mechanism x sensitivity interactions.

    Calculated per user per simulation execution.
    Contains 8 barriers and 3 appeals that modify adoption behavior.

    Barriers (higher = harder to adopt):
        perceived_risk = irreversibility x risk_aversion
        trust_barrier = institutional_trust x (1 - institutional_trust_level)
        habit_resistance = habit_displacement x (1 - habit_plasticity)
        learning_frustration = learning_curve x (1 - digital_capability)
        friction_burden = friccao_operacional x (1 - friction_tolerance)
        social_pressure = social_visibility x social_dependency
        network_barrier = network_effect x (1 - social_dependency)
        motor_barrier = friccao_operacional x (1 - motor_ability)

    Appeals (higher = easier to adopt):
        intrinsic_appeal = valor_intrinseco x pragmatism
        frequency_value = frequencia_de_uso x pragmatism
        domain_advantage = valor_intrinseco x subject_domain
    """

    # --- Barriers (7) ---

    perceived_risk: float
    """Barrier from irreversibility x risk_aversion (Affinity type)."""

    trust_barrier: float
    """Barrier from institutional_trust x (1 - institutional_trust_level) (Resistance type)."""

    habit_resistance: float
    """Barrier from habit_displacement x (1 - habit_plasticity) (Resistance type)."""

    learning_frustration: float
    """Barrier from learning_curve x (1 - digital_capability) (Resistance type)."""

    friction_burden: float
    """Barrier from friccao_operacional x (1 - friction_tolerance) (Resistance type)."""

    social_pressure: float
    """Barrier from social_visibility x social_dependency (Affinity type)."""

    network_barrier: float
    """Barrier from network_effect x (1 - social_dependency) (Resistance type)."""

    motor_barrier: float
    """Barrier from friccao_operacional x (1 - motor_ability) (Resistance type)."""

    # --- Appeals (3) ---

    intrinsic_appeal: float
    """Appeal from valor_intrinseco x pragmatism (Appeal type)."""

    frequency_value: float
    """Appeal from frequencia_de_uso x pragmatism (Appeal type)."""

    domain_advantage: float
    """Appeal from valor_intrinseco x subject_domain (Appeal type)."""

    # --- Metadata ---

    top_contributors: list[InteractionContribution] = field(default_factory=list)
    """Top interactions sorted by product value (typically top 3)."""

    raw_interactions: dict[str, float] = field(default_factory=dict)
    """All 11 mechanism x sensitivity products for full explainability."""


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

    # Test 2: Create EmergentState with minimal data (all 11 states)
    total_tests += 1
    try:
        state = EmergentState(
            perceived_risk=0.15,
            trust_barrier=0.32,
            habit_resistance=0.20,
            learning_frustration=0.45,
            friction_burden=0.10,
            social_pressure=0.28,
            network_barrier=0.49,
            motor_barrier=0.12,
            intrinsic_appeal=0.65,
            frequency_value=0.40,
            domain_advantage=0.35,
        )
        if state.perceived_risk != 0.15:
            all_validation_failures.append(f"perceived_risk mismatch: {state.perceived_risk}")
        if state.trust_barrier != 0.32:
            all_validation_failures.append(f"trust_barrier mismatch: {state.trust_barrier}")
        if state.habit_resistance != 0.20:
            all_validation_failures.append(f"habit_resistance mismatch: {state.habit_resistance}")
        if state.learning_frustration != 0.45:
            all_validation_failures.append(
                f"learning_frustration mismatch: {state.learning_frustration}"
            )
        if state.friction_burden != 0.10:
            all_validation_failures.append(f"friction_burden mismatch: {state.friction_burden}")
        if state.social_pressure != 0.28:
            all_validation_failures.append(f"social_pressure mismatch: {state.social_pressure}")
        if state.network_barrier != 0.49:
            all_validation_failures.append(f"network_barrier mismatch: {state.network_barrier}")
        if state.motor_barrier != 0.12:
            all_validation_failures.append(f"motor_barrier mismatch: {state.motor_barrier}")
        if state.intrinsic_appeal != 0.65:
            all_validation_failures.append(f"intrinsic_appeal mismatch: {state.intrinsic_appeal}")
        if state.frequency_value != 0.40:
            all_validation_failures.append(f"frequency_value mismatch: {state.frequency_value}")
        if state.domain_advantage != 0.35:
            all_validation_failures.append(f"domain_advantage mismatch: {state.domain_advantage}")
        if state.top_contributors != []:
            all_validation_failures.append("top_contributors should default to empty list")
        if state.raw_interactions != {}:
            all_validation_failures.append("raw_interactions should default to empty dict")
    except Exception as e:
        all_validation_failures.append(f"EmergentState minimal creation failed: {e}")

    # Test 3: Create EmergentState with full data (states + contributors + raw_interactions)
    total_tests += 1
    try:
        contributors = [
            InteractionContribution("irreversibility", "risk_aversion", 0.72),
            InteractionContribution("valor_intrinseco", "pragmatism", 0.65),
            InteractionContribution("network_effect", "social_dependency", 0.49),
        ]
        raw = {
            "irreversibility_risk_aversion": 0.72,
            "institutional_trust_institutional_trust_level": 0.32,
            "habit_displacement_habit_plasticity": 0.20,
            "learning_curve_digital_capability": 0.45,
            "friccao_operacional_friction_tolerance": 0.10,
            "social_visibility_social_dependency": 0.28,
            "network_effect_social_dependency": 0.49,
            "friccao_operacional_motor_ability": 0.12,
            "valor_intrinseco_pragmatism": 0.65,
            "frequencia_de_uso_pragmatism": 0.40,
            "valor_intrinseco_subject_domain": 0.35,
        }
        state = EmergentState(
            perceived_risk=0.72,
            trust_barrier=0.32,
            habit_resistance=0.20,
            learning_frustration=0.45,
            friction_burden=0.10,
            social_pressure=0.28,
            network_barrier=0.49,
            motor_barrier=0.12,
            intrinsic_appeal=0.65,
            frequency_value=0.40,
            domain_advantage=0.35,
            top_contributors=contributors,
            raw_interactions=raw,
        )
        if len(state.top_contributors) != 3:
            all_validation_failures.append(
                f"top_contributors count mismatch: {len(state.top_contributors)}"
            )
        if state.top_contributors[0].product != 0.72:
            all_validation_failures.append("First contributor product should be 0.72")
        if len(state.raw_interactions) != 11:
            all_validation_failures.append(
                f"raw_interactions should have 11 keys, got {len(state.raw_interactions)}"
            )
        if "irreversibility_risk_aversion" not in state.raw_interactions:
            all_validation_failures.append("raw_interactions missing expected key")
        if "valor_intrinseco_pragmatism" not in state.raw_interactions:
            all_validation_failures.append("raw_interactions missing appeal key")
    except Exception as e:
        all_validation_failures.append(f"EmergentState full creation failed: {e}")

    # Test 4: Zero values should be valid
    total_tests += 1
    try:
        state = EmergentState(
            perceived_risk=0.0,
            trust_barrier=0.0,
            habit_resistance=0.0,
            learning_frustration=0.0,
            friction_burden=0.0,
            social_pressure=0.0,
            network_barrier=0.0,
            motor_barrier=0.0,
            intrinsic_appeal=0.0,
            frequency_value=0.0,
            domain_advantage=0.0,
        )
        for field_name in [
            "perceived_risk",
            "trust_barrier",
            "habit_resistance",
            "learning_frustration",
            "friction_burden",
            "social_pressure",
            "network_barrier",
            "motor_barrier",
            "intrinsic_appeal",
            "frequency_value",
            "domain_advantage",
        ]:
            if getattr(state, field_name) != 0.0:
                all_validation_failures.append(f"Zero {field_name} should be valid")
    except Exception as e:
        all_validation_failures.append(f"Zero values test failed: {e}")

    # Test 5: Field existence check (11 state fields + 2 metadata fields = 13 total)
    total_tests += 1
    expected_fields = {
        # 8 barriers
        "perceived_risk",
        "trust_barrier",
        "habit_resistance",
        "learning_frustration",
        "friction_burden",
        "social_pressure",
        "network_barrier",
        "motor_barrier",
        # 3 appeals
        "intrinsic_appeal",
        "frequency_value",
        "domain_advantage",
        # 2 metadata
        "top_contributors",
        "raw_interactions",
    }
    actual_fields = {f.name for f in EmergentState.__dataclass_fields__.values()}
    if expected_fields != actual_fields:
        all_validation_failures.append(
            f"EmergentState field mismatch: expected {expected_fields}, got {actual_fields}"
        )
    if len(actual_fields) != 13:
        all_validation_failures.append(
            f"EmergentState should have 13 fields, got {len(actual_fields)}"
        )

    # Test 6: Verify InteractionContribution fields unchanged
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
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
