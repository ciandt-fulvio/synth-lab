"""
Unit tests for emergent state calculator.

Tests the 11-state emergent formula system where feature mechanisms interact
with user sensitivities to produce barriers and appeals.

Changes from previous version:
    - perceived_risk uses non-linear formula: 1 - (1-irrev)*(1-risk_aversion)
    - network_effect is now an appeal (network_bonus) instead of a barrier
    - 7 barriers + 4 appeals = 11 emergent states

References:
    - Implementation: synth_lab/services/simulation/emergent_calculator.py
"""

import pytest

from synth_lab.domain.entities.feature_mechanisms import FeatureMechanisms
from synth_lab.domain.entities.user_sensitivities import UserSensitivities
from synth_lab.services.simulation.emergent_calculator import (
    INTERACTION_PAIRS,
    _get_top_contributors,
    calculate_emergent_state,
)

TOLERANCE = 1e-4


class TestCalculateEmergentState:
    """Tests for calculate_emergent_state with known mechanism x sensitivity values."""

    def test_known_values_all_11_formulas(self):
        """Verify each of the 11 emergent states with hand-calculated products."""
        mechanisms = FeatureMechanisms(
            irreversibility=0.9,
            social_visibility=0.3,
            institutional_trust=0.8,
            habit_displacement=0.4,
            learning_curve=0.5,
            operational_friction=0.2,
            network_effect=0.7,
            intrinsic_value=0.6,
            frequency_of_use=0.85,
        )
        sensitivities = UserSensitivities(
            risk_aversion=0.8,
            social_dependency=0.3,
            institutional_trust_level=0.6,
            habit_plasticity=0.5,
            digital_capability=0.4,
            friction_tolerance=0.7,
            pragmatism=0.9,
            motor_ability=0.6,
            subject_domain=0.7,
        )

        state = calculate_emergent_state(mechanisms, sensitivities)

        # Non-linear barrier: 1 - (1-0.9)*(1-0.8) = 1 - 0.1*0.2 = 0.98
        assert state.perceived_risk == pytest.approx(0.98, abs=TOLERANCE)

        # Affinity barrier
        assert state.social_pressure == pytest.approx(0.09, abs=TOLERANCE)

        # Resistance barriers: mech x (1 - sens)
        assert state.trust_barrier == pytest.approx(0.32, abs=TOLERANCE)
        assert state.habit_resistance == pytest.approx(0.20, abs=TOLERANCE)
        assert state.learning_frustration == pytest.approx(0.30, abs=TOLERANCE)
        assert state.friction_burden == pytest.approx(0.06, abs=TOLERANCE)
        assert state.motor_barrier == pytest.approx(0.08, abs=TOLERANCE)

        # Appeals: mech x sens
        assert state.intrinsic_appeal == pytest.approx(0.54, abs=TOLERANCE)
        assert state.frequency_value == pytest.approx(0.765, abs=TOLERANCE)
        assert state.domain_advantage == pytest.approx(0.42, abs=TOLERANCE)
        assert state.network_bonus == pytest.approx(0.21, abs=TOLERANCE)

    def test_zero_mechanisms_produce_all_zero_states(self):
        """All mechanisms=0.0 with arbitrary sensitivities produces all-zero states.

        Note: perceived_risk with non-linear formula: 1 - (1-0)*(1-sens) = sens.
        But when irreversibility=0.0, the raw product stays 0.0 in raw_interactions,
        and the emergent state uses the non-linear formula directly.
        """
        mechanisms = FeatureMechanisms()  # All default to 0.0
        sensitivities = UserSensitivities(
            risk_aversion=0.9,
            social_dependency=0.8,
            institutional_trust_level=0.7,
            habit_plasticity=0.6,
            friction_tolerance=0.5,
            pragmatism=0.4,
            digital_capability=0.3,
        )

        state = calculate_emergent_state(mechanisms, sensitivities)

        # Non-linear perceived_risk: 1 - (1-0)*(1-0.9) = 0.9 (NOT zero!)
        assert state.perceived_risk == pytest.approx(0.9, abs=TOLERANCE)

        # All other states should be 0.0 (mechanism=0 zeroes the product)
        zero_fields = [
            "trust_barrier", "habit_resistance", "learning_frustration",
            "friction_burden", "social_pressure", "motor_barrier",
            "intrinsic_appeal", "frequency_value", "domain_advantage",
            "network_bonus",
        ]
        for field_name in zero_fields:
            assert getattr(state, field_name) == pytest.approx(0.0, abs=TOLERANCE), (
                f"{field_name} should be 0.0 when all mechanisms are zero"
            )

    def test_max_values_affinity_and_resistance(self):
        """All mechanisms=1.0 and all sensitivities=1.0.

        Affinity types produce 1.0 (1 x 1).
        Resistance types produce 0.0 (1 x (1-1)).
        Non-linear perceived_risk: 1 - (1-1)(1-1) = 1.0.
        """
        mechanisms = FeatureMechanisms(
            irreversibility=1.0,
            social_visibility=1.0,
            institutional_trust=1.0,
            habit_displacement=1.0,
            learning_curve=1.0,
            operational_friction=1.0,
            network_effect=1.0,
            intrinsic_value=1.0,
            frequency_of_use=1.0,
        )
        sensitivities = UserSensitivities(
            risk_aversion=1.0,
            social_dependency=1.0,
            institutional_trust_level=1.0,
            habit_plasticity=1.0,
            friction_tolerance=1.0,
            pragmatism=1.0,
            digital_capability=1.0,
            motor_ability=1.0,
            subject_domain=1.0,
        )

        state = calculate_emergent_state(mechanisms, sensitivities)

        # Affinity/Non-linear types -> 1.0
        assert state.perceived_risk == pytest.approx(1.0, abs=TOLERANCE)
        assert state.social_pressure == pytest.approx(1.0, abs=TOLERANCE)
        assert state.intrinsic_appeal == pytest.approx(1.0, abs=TOLERANCE)
        assert state.frequency_value == pytest.approx(1.0, abs=TOLERANCE)
        assert state.domain_advantage == pytest.approx(1.0, abs=TOLERANCE)
        assert state.network_bonus == pytest.approx(1.0, abs=TOLERANCE)

        # Resistance types -> 0.0
        assert state.trust_barrier == pytest.approx(0.0, abs=TOLERANCE)
        assert state.habit_resistance == pytest.approx(0.0, abs=TOLERANCE)
        assert state.learning_frustration == pytest.approx(0.0, abs=TOLERANCE)
        assert state.friction_burden == pytest.approx(0.0, abs=TOLERANCE)
        assert state.motor_barrier == pytest.approx(0.0, abs=TOLERANCE)

    def test_default_sensitivities_produce_expected_values(self):
        """All mechanisms=1.0 with default sensitivities (0.5).

        Affinity: 1.0 x 0.5 = 0.5.
        Resistance: 1.0 x (1 - 0.5) = 0.5.
        Non-linear perceived_risk: 1 - (1-1.0)*(1-0.5) = 1.0.
        """
        mechanisms = FeatureMechanisms(
            irreversibility=1.0,
            social_visibility=1.0,
            institutional_trust=1.0,
            habit_displacement=1.0,
            learning_curve=1.0,
            operational_friction=1.0,
            network_effect=1.0,
            intrinsic_value=1.0,
            frequency_of_use=1.0,
        )
        sensitivities = UserSensitivities()  # All defaults = 0.5

        state = calculate_emergent_state(mechanisms, sensitivities)

        # perceived_risk is non-linear: 1 - (1-1.0)*(1-0.5) = 1.0
        assert state.perceived_risk == pytest.approx(1.0, abs=TOLERANCE)

        # All other states should be 0.5
        half_fields = [
            "trust_barrier", "habit_resistance", "learning_frustration",
            "friction_burden", "social_pressure", "motor_barrier",
            "intrinsic_appeal", "frequency_value", "domain_advantage",
            "network_bonus",
        ]
        for field_name in half_fields:
            assert getattr(state, field_name) == pytest.approx(0.5, abs=TOLERANCE), (
                f"{field_name} should be 0.5 with all mechanisms=1.0 and default sensitivities"
            )

    def test_non_linear_perceived_risk_values(self):
        """Verify non-linear perceived_risk formula with specific values.

        Formula: perceived_risk = 1 - (1 - irreversibility) * (1 - risk_aversion)
        """
        test_cases = [
            # (irreversibility, risk_aversion, expected_perceived_risk)
            (0.9, 0.8, 0.98),  # Both high -> approaches 1.0
            (0.5, 0.5, 0.75),  # Both medium -> significant risk
            (0.3, 0.2, 0.44),  # Both low -> still moderate
            (0.0, 0.9, 0.90),  # Zero irreversibility, high aversion -> still 0.9
            (0.9, 0.0, 0.90),  # High irreversibility, zero aversion -> still 0.9
            (0.0, 0.0, 0.00),  # Both zero -> zero risk
        ]
        for irrev, risk_av, expected in test_cases:
            mechanisms = FeatureMechanisms(irreversibility=irrev)
            sensitivities = UserSensitivities(risk_aversion=risk_av)
            state = calculate_emergent_state(mechanisms, sensitivities)
            assert state.perceived_risk == pytest.approx(expected, abs=TOLERANCE), (
                f"irrev={irrev}, risk_av={risk_av}: "
                f"expected {expected}, got {state.perceived_risk}"
            )

    def test_raw_interactions_has_11_keys(self):
        """Verify raw_interactions contains exactly the expected 11 compound keys."""
        mechanisms = FeatureMechanisms(irreversibility=0.5, intrinsic_value=0.3)
        sensitivities = UserSensitivities()

        state = calculate_emergent_state(mechanisms, sensitivities)

        expected_keys = {
            "irreversibility_risk_aversion",
            "social_visibility_social_dependency",
            "institutional_trust_institutional_trust_level",
            "habit_displacement_habit_plasticity",
            "learning_curve_digital_capability",
            "operational_friction_friction_tolerance",
            "network_effect_social_dependency",
            "operational_friction_motor_ability",
            "intrinsic_value_pragmatism",
            "frequency_of_use_pragmatism",
            "intrinsic_value_subject_domain",
        }
        assert set(state.raw_interactions.keys()) == expected_keys
        assert len(state.raw_interactions) == 11

    def test_network_bonus_is_affinity(self):
        """network_bonus = network_effect x social_dependency (affinity formula)."""
        mechanisms = FeatureMechanisms(network_effect=0.8)
        sensitivities = UserSensitivities(social_dependency=0.6)
        state = calculate_emergent_state(mechanisms, sensitivities)
        assert state.network_bonus == pytest.approx(0.48, abs=TOLERANCE)


class TestTopContributors:
    """Tests for _get_top_contributors extraction and sorting."""

    def test_sorted_descending_by_product(self):
        """Top contributors are returned sorted by product value descending."""
        mechanisms = FeatureMechanisms(
            irreversibility=0.9,   # non-linear perceived_risk, raw=0.9*0.9=0.81
            intrinsic_value=0.8,  # 0.8 x 0.7 = 0.56
            network_effect=0.5,    # 0.5 x 0.2 = 0.10 (affinity)
            habit_displacement=0.3,  # 0.3 x (1 - 0.5) = 0.15
            social_visibility=0.1,   # 0.1 x 0.2 = 0.02
        )
        sensitivities = UserSensitivities(
            risk_aversion=0.9,
            pragmatism=0.7,
            social_dependency=0.2,
            habit_plasticity=0.5,
        )

        state = calculate_emergent_state(mechanisms, sensitivities)
        products = [c.product for c in state.top_contributors]

        assert products == sorted(products, reverse=True)

    def test_top_3_by_default(self):
        """Only 3 contributors returned by default."""
        mechanisms = FeatureMechanisms(
            irreversibility=0.9,
            social_visibility=0.3,
            institutional_trust=0.8,
            habit_displacement=0.4,
            learning_curve=0.5,
            operational_friction=0.2,
            network_effect=0.7,
            intrinsic_value=0.6,
            frequency_of_use=0.85,
        )
        sensitivities = UserSensitivities(
            risk_aversion=0.8,
            social_dependency=0.3,
            institutional_trust_level=0.6,
            habit_plasticity=0.5,
            digital_capability=0.4,
            friction_tolerance=0.7,
            pragmatism=0.9,
        )

        state = calculate_emergent_state(mechanisms, sensitivities)

        assert len(state.top_contributors) == 3

    def test_zero_products_excluded(self):
        """Zero-value interactions are excluded from top_contributors."""
        mechanisms = FeatureMechanisms()  # All 0.0
        sensitivities = UserSensitivities(
            risk_aversion=0.9,
            social_dependency=0.8,
            pragmatism=0.7,
        )

        state = calculate_emergent_state(mechanisms, sensitivities)

        assert len(state.top_contributors) == 0

    def test_contributor_fields_correct(self):
        """Each InteractionContribution has correct mechanism, sensitivity, product."""
        mechanisms = FeatureMechanisms(irreversibility=0.9)
        sensitivities = UserSensitivities(risk_aversion=0.8)

        state = calculate_emergent_state(mechanisms, sensitivities)

        # raw_interactions stores the simple product (0.9*0.8=0.72)
        # even though perceived_risk uses non-linear formula
        top = state.top_contributors[0]
        assert top.mechanism == "irreversibility"
        assert top.sensitivity == "risk_aversion"
        assert top.product == pytest.approx(0.72, abs=TOLERANCE)

    def test_get_top_contributors_custom_n(self):
        """_get_top_contributors respects the top_n parameter."""
        raw_interactions = {
            "irreversibility_risk_aversion": 0.72,
            "social_visibility_social_dependency": 0.09,
            "institutional_trust_institutional_trust_level": 0.32,
            "habit_displacement_habit_plasticity": 0.20,
            "learning_curve_digital_capability": 0.30,
            "operational_friction_friction_tolerance": 0.06,
            "network_effect_social_dependency": 0.49,
            "intrinsic_value_pragmatism": 0.54,
            "frequency_of_use_pragmatism": 0.765,
        }

        top_5 = _get_top_contributors(raw_interactions, top_n=5)
        assert len(top_5) == 5

        top_1 = _get_top_contributors(raw_interactions, top_n=1)
        assert len(top_1) == 1
        assert top_1[0].product == pytest.approx(0.765, abs=TOLERANCE)


class TestInteractionPairs:
    """Tests for the INTERACTION_PAIRS constant structure."""

    def test_has_11_pairs(self):
        """INTERACTION_PAIRS contains exactly 11 tuples."""
        assert len(INTERACTION_PAIRS) == 11

    def test_formula_types(self):
        """Correct distribution of formula types: 6 affinity, 5 resistance.

        6 affinity = 1 non-linear barrier (perceived_risk) + 1 affinity barrier
                     + 4 appeals (intrinsic_appeal, frequency_value, domain_advantage, network_bonus)
        5 resistance = trust, habit, learning, friction, motor barriers
        """
        affinity_count = sum(1 for _, _, ft in INTERACTION_PAIRS if ft == "affinity")
        resistance_count = sum(1 for _, _, ft in INTERACTION_PAIRS if ft == "resistance")

        assert affinity_count == 6
        assert resistance_count == 5

    def test_all_mechanism_fields_used(self):
        """All 9 mechanism field names appear in INTERACTION_PAIRS."""
        expected_mechanisms = {
            "irreversibility",
            "social_visibility",
            "institutional_trust",
            "habit_displacement",
            "learning_curve",
            "operational_friction",
            "network_effect",
            "intrinsic_value",
            "frequency_of_use",
        }

        actual_mechanisms = {mech for mech, _, _ in INTERACTION_PAIRS}

        assert actual_mechanisms == expected_mechanisms

    def test_each_tuple_has_3_elements(self):
        """Each pair is a (mechanism_field, sensitivity_field, formula_type) tuple."""
        for pair in INTERACTION_PAIRS:
            assert len(pair) == 3
            mech, sens, formula = pair
            assert isinstance(mech, str)
            assert isinstance(sens, str)
            assert formula in ("affinity", "resistance")

    def test_sensitivity_fields_are_valid(self):
        """All sensitivity field names in INTERACTION_PAIRS exist on UserSensitivities."""
        valid_sensitivity_fields = set(UserSensitivities.model_fields.keys())

        for _, sens_field, _ in INTERACTION_PAIRS:
            assert sens_field in valid_sensitivity_fields, (
                f"Sensitivity field '{sens_field}' not found in UserSensitivities"
            )

    def test_mechanism_fields_are_valid(self):
        """All mechanism field names in INTERACTION_PAIRS exist on FeatureMechanisms."""
        valid_mechanism_fields = set(FeatureMechanisms.model_fields.keys())

        for mech_field, _, _ in INTERACTION_PAIRS:
            assert mech_field in valid_mechanism_fields, (
                f"Mechanism field '{mech_field}' not found in FeatureMechanisms"
            )

    def test_network_effect_is_affinity(self):
        """network_effect should be affinity type (appeal), not resistance."""
        network_pair = [p for p in INTERACTION_PAIRS if p[0] == "network_effect"]
        assert len(network_pair) == 1
        assert network_pair[0][2] == "affinity"
