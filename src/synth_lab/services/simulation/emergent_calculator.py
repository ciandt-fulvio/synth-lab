"""
Emergent state calculator for synth-lab.

Computes 9 emergent behavioral states from 9 feature mechanisms x 7 user
sensitivities interactions. Each state represents a barrier or appeal that
modifies user adoption behavior during Monte Carlo simulations.

9 Emergent States (per spec FR-010):

    Resistance barriers (mechanism x (1 - sensitivity)):
        trust_barrier        = institutional_trust x (1 - institutional_trust_level)
        habit_resistance     = habit_displacement x (1 - habit_plasticity)
        learning_frustration = learning_curve x (1 - digital_capability)
        friction_burden      = friccao_operacional x (1 - friction_tolerance)
        network_barrier      = network_effect x (1 - social_dependency)

    Affinity barriers (mechanism x sensitivity):
        perceived_risk  = irreversibility x risk_aversion
        social_pressure = social_visibility x social_dependency

    Appeals (mechanism x sensitivity):
        intrinsic_appeal = valor_intrinseco x pragmatism
        frequency_value  = frequencia_de_uso x pragmatism

References:
    - Spec: specs/040-emergent-state-expansion/spec.md
    - FR-010: 9-state emergent formulas
    - Replaces: mechanism_interaction.py (4-delta model)

Sample input:
    mechanisms = FeatureMechanisms(irreversibility=0.9, institutional_trust=0.8)
    sensitivities = UserSensitivities(risk_aversion=0.8, institutional_trust_level=0.6)

Expected output:
    EmergentState(
        perceived_risk=0.72,   # 0.9 x 0.8
        trust_barrier=0.32,    # 0.8 x (1 - 0.6)
        ...
    )
"""

from synth_lab.domain.entities.emergent_state import EmergentState, InteractionContribution
from synth_lab.domain.entities.feature_mechanisms import FeatureMechanisms
from synth_lab.domain.entities.user_sensitivities import UserSensitivities

# 9 interaction pairs: (mechanism_field, sensitivity_field, formula_type)
# formula_type: "affinity" = mech x sens, "resistance" = mech x (1 - sens)
INTERACTION_PAIRS: list[tuple[str, str, str]] = [
    # Affinity barriers
    ("irreversibility", "risk_aversion", "affinity"),
    ("social_visibility", "social_dependency", "affinity"),
    # Resistance barriers
    ("institutional_trust", "institutional_trust_level", "resistance"),
    ("habit_displacement", "habit_plasticity", "resistance"),
    ("learning_curve", "digital_capability", "resistance"),
    ("friccao_operacional", "friction_tolerance", "resistance"),
    ("network_effect", "social_dependency", "resistance"),
    # Appeals (same formula as affinity: mech x sens)
    ("valor_intrinseco", "pragmatism", "affinity"),
    ("frequencia_de_uso", "pragmatism", "affinity"),
]


def calculate_emergent_state(
    mechanisms: FeatureMechanisms,
    sensitivities: UserSensitivities,
) -> EmergentState:
    """
    Calculate 9 emergent states from mechanism x sensitivity interactions.

    Uses FR-010 formulas:
        - Resistance: mechanism x (1 - sensitivity) -- high sensitivity reduces barrier
        - Affinity: mechanism x sensitivity -- high sensitivity increases barrier/appeal

    Args:
        mechanisms: Feature structural mechanisms (9 floats in [0, 1]).
        sensitivities: User psychological sensitivities (7 floats in [0, 1]).

    Returns:
        EmergentState with 7 barriers, 2 appeals, top contributors, and raw interactions.

    Example:
        >>> mechanisms = FeatureMechanisms(irreversibility=0.9, network_effect=0.7)
        >>> sensitivities = UserSensitivities(risk_aversion=0.8, social_dependency=0.3)
        >>> state = calculate_emergent_state(mechanisms, sensitivities)
        >>> state.perceived_risk
        0.72  # 0.9 x 0.8
        >>> state.network_barrier
        0.49  # 0.7 x (1 - 0.3)
    """
    # Calculate all 9 raw interactions
    raw_interactions: dict[str, float] = {}

    for mech_name, sens_name, formula_type in INTERACTION_PAIRS:
        mech_value = getattr(mechanisms, mech_name)
        sens_value = getattr(sensitivities, sens_name)

        if formula_type == "resistance":
            product = mech_value * (1 - sens_value)
        else:  # affinity or appeal
            product = mech_value * sens_value

        key = f"{mech_name}_{sens_name}"
        raw_interactions[key] = round(product, 10)

    # Calculate the 9 emergent states using explicit FR-010 formulas
    # Affinity barriers
    perceived_risk = mechanisms.irreversibility * sensitivities.risk_aversion
    social_pressure = mechanisms.social_visibility * sensitivities.social_dependency

    # Resistance barriers
    trust_barrier = mechanisms.institutional_trust * (1 - sensitivities.institutional_trust_level)
    habit_resistance = mechanisms.habit_displacement * (1 - sensitivities.habit_plasticity)
    learning_frustration = mechanisms.learning_curve * (1 - sensitivities.digital_capability)
    friction_burden = mechanisms.friccao_operacional * (1 - sensitivities.friction_tolerance)
    network_barrier = mechanisms.network_effect * (1 - sensitivities.social_dependency)

    # Appeals
    intrinsic_appeal = mechanisms.valor_intrinseco * sensitivities.pragmatism
    frequency_value = mechanisms.frequencia_de_uso * sensitivities.pragmatism

    # Extract top 3 contributors sorted by product descending (non-zero only)
    top_contributors = _get_top_contributors(raw_interactions, top_n=3)

    return EmergentState(
        perceived_risk=perceived_risk,
        trust_barrier=trust_barrier,
        habit_resistance=habit_resistance,
        learning_frustration=learning_frustration,
        friction_burden=friction_burden,
        social_pressure=social_pressure,
        network_barrier=network_barrier,
        intrinsic_appeal=intrinsic_appeal,
        frequency_value=frequency_value,
        top_contributors=top_contributors,
        raw_interactions=raw_interactions,
    )


def _get_top_contributors(
    raw_interactions: dict[str, float],
    top_n: int = 3,
) -> list[InteractionContribution]:
    """
    Extract top N interactions sorted by product value descending.

    Only includes non-zero contributions. Uses INTERACTION_PAIRS to correctly
    split compound key names (e.g. "friccao_operacional_friction_tolerance").

    Args:
        raw_interactions: Dictionary of "mechanism_sensitivity" -> product.
        top_n: Number of top contributors to return.

    Returns:
        List of InteractionContribution sorted by product descending.
    """
    # Build a lookup from key -> (mechanism, sensitivity) for correct splitting
    key_lookup: dict[str, tuple[str, str]] = {
        f"{mech}_{sens}": (mech, sens) for mech, sens, _ in INTERACTION_PAIRS
    }

    contributions: list[InteractionContribution] = []

    for key, product in raw_interactions.items():
        if product <= 0:
            continue

        pair = key_lookup.get(key)
        if pair is None:
            continue  # Skip malformed keys

        mechanism, sensitivity = pair
        contributions.append(
            InteractionContribution(
                mechanism=mechanism,
                sensitivity=sensitivity,
                product=product,
            )
        )

    contributions.sort(key=lambda c: c.product, reverse=True)
    return contributions[:top_n]


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    TOLERANCE = 0.0001

    # Test 1: Basic calculation with known values (verify each formula)
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(
            irreversibility=0.9,
            network_effect=0.7,
            institutional_trust=0.8,
            habit_displacement=0.4,
            learning_curve=0.5,
            social_visibility=0.3,
            valor_intrinseco=0.6,
            friccao_operacional=0.2,
            frequencia_de_uso=0.85,
        )
        sensitivities = UserSensitivities(
            risk_aversion=0.8,
            social_dependency=0.3,
            institutional_trust_level=0.6,
            habit_plasticity=0.5,
            friction_tolerance=0.7,
            pragmatism=0.9,
            digital_capability=0.4,
        )
        state = calculate_emergent_state(mechanisms, sensitivities)

        # Verify each of the 9 formulas
        expected = {
            # Affinity barriers: mech x sens
            "perceived_risk": 0.9 * 0.8,  # 0.72
            "social_pressure": 0.3 * 0.3,  # 0.09
            # Resistance barriers: mech x (1 - sens)
            "trust_barrier": 0.8 * (1 - 0.6),  # 0.32
            "habit_resistance": 0.4 * (1 - 0.5),  # 0.20
            "learning_frustration": 0.5 * (1 - 0.4),  # 0.30
            "friction_burden": 0.2 * (1 - 0.7),  # 0.06
            "network_barrier": 0.7 * (1 - 0.3),  # 0.49
            # Appeals: mech x sens
            "intrinsic_appeal": 0.6 * 0.9,  # 0.54
            "frequency_value": 0.85 * 0.9,  # 0.765
        }

        for field_name, expected_val in expected.items():
            actual_val = getattr(state, field_name)
            if abs(actual_val - expected_val) > TOLERANCE:
                all_validation_failures.append(
                    f"Basic calc {field_name}: expected {expected_val}, got {actual_val}"
                )
    except Exception as e:
        all_validation_failures.append(f"Basic calculation test failed: {e}")

    # Test 2: Zero mechanisms -> all states zero (regardless of sensitivities)
    total_tests += 1
    try:
        all_state_fields = [
            "perceived_risk",
            "trust_barrier",
            "habit_resistance",
            "learning_frustration",
            "friction_burden",
            "social_pressure",
            "network_barrier",
            "intrinsic_appeal",
            "frequency_value",
        ]
        # Case A: all zeros
        mechanisms = FeatureMechanisms()  # All 0.0
        sensitivities = UserSensitivities(
            risk_aversion=0.0,
            social_dependency=0.0,
            institutional_trust_level=0.0,
            habit_plasticity=0.0,
            friction_tolerance=0.0,
            pragmatism=0.0,
            digital_capability=0.0,
        )
        state = calculate_emergent_state(mechanisms, sensitivities)
        for fn in all_state_fields:
            if getattr(state, fn) != 0.0:
                all_validation_failures.append(f"All zeros {fn}: got {getattr(state, fn)}")
        for key, val in state.raw_interactions.items():
            if val != 0.0:
                all_validation_failures.append(f"All zeros raw[{key}]: got {val}")
        if len(state.top_contributors) != 0:
            all_validation_failures.append(
                f"All zeros: expected 0 contributors, got {len(state.top_contributors)}"
            )
        # Case B: zero mechanisms, non-zero sensitivities -> still all zero
        sensitivities_b = UserSensitivities(
            risk_aversion=0.9,
            social_dependency=0.8,
            institutional_trust_level=0.7,
            habit_plasticity=0.6,
            friction_tolerance=0.5,
            pragmatism=0.4,
            digital_capability=0.3,
        )
        state_b = calculate_emergent_state(FeatureMechanisms(), sensitivities_b)
        for fn in all_state_fields:
            if getattr(state_b, fn) != 0.0:
                all_validation_failures.append(
                    f"Zero mechs/non-zero sens {fn}: got {getattr(state_b, fn)}"
                )
    except Exception as e:
        all_validation_failures.append(f"Zero mechanisms test failed: {e}")

    # Test 3: Max values (all 1.0) -> correct products
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(
            irreversibility=1.0,
            network_effect=1.0,
            institutional_trust=1.0,
            habit_displacement=1.0,
            learning_curve=1.0,
            social_visibility=1.0,
            valor_intrinseco=1.0,
            friccao_operacional=1.0,
            frequencia_de_uso=1.0,
        )
        sensitivities = UserSensitivities(
            risk_aversion=1.0,
            social_dependency=1.0,
            institutional_trust_level=1.0,
            habit_plasticity=1.0,
            friction_tolerance=1.0,
            pragmatism=1.0,
            digital_capability=1.0,
        )
        state = calculate_emergent_state(mechanisms, sensitivities)

        # Affinity: 1.0 x 1.0 = 1.0
        max_affinity = {
            "perceived_risk": 1.0,  # 1.0 x 1.0
            "social_pressure": 1.0,  # 1.0 x 1.0
            "intrinsic_appeal": 1.0,  # 1.0 x 1.0
            "frequency_value": 1.0,  # 1.0 x 1.0
        }
        # Resistance: 1.0 x (1 - 1.0) = 0.0
        max_resistance = {
            "trust_barrier": 0.0,  # 1.0 x (1 - 1.0)
            "habit_resistance": 0.0,  # 1.0 x (1 - 1.0)
            "learning_frustration": 0.0,  # 1.0 x (1 - 1.0)
            "friction_burden": 0.0,  # 1.0 x (1 - 1.0)
            "network_barrier": 0.0,  # 1.0 x (1 - 1.0)
        }

        for field_name, expected_val in {**max_affinity, **max_resistance}.items():
            actual_val = getattr(state, field_name)
            if abs(actual_val - expected_val) > TOLERANCE:
                all_validation_failures.append(
                    f"Max values {field_name}: expected {expected_val}, got {actual_val}"
                )
    except Exception as e:
        all_validation_failures.append(f"Max values test failed: {e}")

    # Test 4: Top contributors are sorted by product descending
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(
            irreversibility=0.9,  # 0.9 x 0.9 = 0.81
            valor_intrinseco=0.8,  # 0.8 x 0.7 = 0.56
            network_effect=0.5,  # 0.5 x (1 - 0.2) = 0.40
            habit_displacement=0.3,  # 0.3 x (1 - 0.5) = 0.15
            social_visibility=0.1,  # 0.1 x 0.2 = 0.02
        )
        sensitivities = UserSensitivities(
            risk_aversion=0.9,
            pragmatism=0.7,
            social_dependency=0.2,
            habit_plasticity=0.5,
        )
        state = calculate_emergent_state(mechanisms, sensitivities)

        if len(state.top_contributors) != 3:
            all_validation_failures.append(
                f"Top contributors count: expected 3, got {len(state.top_contributors)}"
            )
        else:
            # Verify sorted descending
            products = [c.product for c in state.top_contributors]
            if products != sorted(products, reverse=True):
                all_validation_failures.append(
                    f"Top contributors not sorted descending: {products}"
                )

            # First should be irreversibility x risk_aversion = 0.81
            if state.top_contributors[0].mechanism != "irreversibility":
                all_validation_failures.append(
                    f"Top contributor mechanism: expected 'irreversibility', "
                    f"got '{state.top_contributors[0].mechanism}'"
                )
            if abs(state.top_contributors[0].product - 0.81) > TOLERANCE:
                all_validation_failures.append(
                    f"Top contributor product: expected 0.81, "
                    f"got {state.top_contributors[0].product}"
                )

            # Second should be valor_intrinseco x pragmatism = 0.56
            if state.top_contributors[1].mechanism != "valor_intrinseco":
                all_validation_failures.append(
                    f"Second contributor mechanism: expected 'valor_intrinseco', "
                    f"got '{state.top_contributors[1].mechanism}'"
                )
    except Exception as e:
        all_validation_failures.append(f"Top contributors test failed: {e}")

    # Test 5: raw_interactions has exactly 9 keys
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(irreversibility=0.5, valor_intrinseco=0.3)
        sensitivities = UserSensitivities()
        state = calculate_emergent_state(mechanisms, sensitivities)

        expected_keys = {
            "irreversibility_risk_aversion",
            "social_visibility_social_dependency",
            "institutional_trust_institutional_trust_level",
            "habit_displacement_habit_plasticity",
            "learning_curve_digital_capability",
            "friccao_operacional_friction_tolerance",
            "network_effect_social_dependency",
            "valor_intrinseco_pragmatism",
            "frequencia_de_uso_pragmatism",
        }
        actual_keys = set(state.raw_interactions.keys())

        if len(actual_keys) != 9:
            all_validation_failures.append(
                f"raw_interactions should have 9 keys, got {len(actual_keys)}"
            )
        if expected_keys != actual_keys:
            missing = expected_keys - actual_keys
            extra = actual_keys - expected_keys
            all_validation_failures.append(
                f"raw_interactions keys mismatch. Missing: {missing}, Extra: {extra}"
            )
    except Exception as e:
        all_validation_failures.append(f"raw_interactions keys test failed: {e}")

    # Test 6: Default sensitivities (0.5) produce expected intermediate values
    total_tests += 1
    try:
        mechanisms = FeatureMechanisms(
            irreversibility=1.0,
            institutional_trust=1.0,
            habit_displacement=1.0,
            learning_curve=1.0,
            friccao_operacional=1.0,
            network_effect=1.0,
            social_visibility=1.0,
            valor_intrinseco=1.0,
            frequencia_de_uso=1.0,
        )
        sensitivities = UserSensitivities()  # All defaults (0.5)
        state = calculate_emergent_state(mechanisms, sensitivities)

        # Affinity: 1.0 x 0.5 = 0.5
        # Resistance: 1.0 x (1 - 0.5) = 0.5
        all_fields = [
            "perceived_risk",
            "trust_barrier",
            "habit_resistance",
            "learning_frustration",
            "friction_burden",
            "social_pressure",
            "network_barrier",
            "intrinsic_appeal",
            "frequency_value",
        ]
        for field_name in all_fields:
            actual_val = getattr(state, field_name)
            if abs(actual_val - 0.5) > TOLERANCE:
                all_validation_failures.append(
                    f"Default sensitivity {field_name}: expected 0.5, got {actual_val}"
                )
    except Exception as e:
        all_validation_failures.append(f"Default sensitivities test failed: {e}")

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
