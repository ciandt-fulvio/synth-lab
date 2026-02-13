"""
Integration tests for the full simulation-sensitivity pipeline.

Verifies that the complete pipeline works end-to-end:
    demographics -> sensitivities -> emergent states -> adoption probability -> simulation results

Changes from previous version:
    - perceived_risk uses non-linear formula: 1 - (1-irrev)*(1-risk_aversion)
    - network_effect is now an appeal (network_bonus) instead of a barrier
    - Sigmoid probability function instead of linear
    - Gating mechanisms based on feature_types

Modules under test:
    - synth_lab.services.sensitivity_deriver.derive_sensitivities
    - synth_lab.services.simulation.emergent_calculator.calculate_emergent_state
    - synth_lab.services.simulation.feature_monte_carlo.run_simulation

References:
    - Sensitivity rules: src/synth_lab/config/sensitivity_rules.yaml
"""

import pytest

from synth_lab.domain.entities.feature_mechanisms import FeatureMechanisms
from synth_lab.domain.entities.user_sensitivities import UserSensitivities
from synth_lab.services.sensitivity_deriver import derive_sensitivities
from synth_lab.services.simulation.emergent_calculator import calculate_emergent_state
from synth_lab.services.simulation.feature_monte_carlo import run_simulation


@pytest.mark.integration
class TestSimulationSensitivityIntegration:
    """End-to-end integration tests for the simulation-sensitivity pipeline."""

    def test_full_pipeline_demographics_to_adoption(self):
        """Full pipeline: pre-computed sensitivities -> emergent -> adoption.

        Creates 2 synth dicts with pre-computed sensitivities representing:
        - Young tech-savvy (high digital_capability, high motor_ability)
        - Elderly low-tech (low digital_capability, lower motor_ability)
        """
        young_tech = {
            "id": "young_tech",
            "sensitivities": {
                "risk_aversion": 0.35,
                "social_dependency": 0.55,
                "institutional_trust_level": 0.55,
                "habit_plasticity": 0.65,
                "friction_tolerance": 0.60,
                "pragmatism": 0.55,
                "digital_capability": 0.80,
                "motor_ability": 0.95,
                "subject_domain": 0.50,
            },
        }
        elderly_low_tech = {
            "id": "elderly_low_tech",
            "sensitivities": {
                "risk_aversion": 0.65,
                "social_dependency": 0.35,
                "institutional_trust_level": 0.60,
                "habit_plasticity": 0.30,
                "friction_tolerance": 0.35,
                "pragmatism": 0.55,
                "digital_capability": 0.25,
                "motor_ability": 0.75,
                "subject_domain": 0.50,
            },
        }

        mechanisms = FeatureMechanisms(
            irreversibility=0.7,
            network_effect=0.5,
            institutional_trust=0.6,
            habit_displacement=0.5,
            learning_curve=0.6,
            social_visibility=0.3,
            intrinsic_value=0.8,
            operational_friction=0.4,
            frequency_of_use=0.7,
        )

        results = run_simulation(
            [young_tech, elderly_low_tech],
            mechanisms,
            n_executions=500,
            seed=42,
        )

        assert len(results.outcomes) == 2

        young_outcome = results.outcomes[0]
        elderly_outcome = results.outcomes[1]

        # Young tech-savvy should have higher adoption rate than elderly
        assert young_outcome.adoption_rate > elderly_outcome.adoption_rate, (
            f"Young tech ({young_outcome.adoption_rate}) should have higher adoption "
            f"than elderly ({elderly_outcome.adoption_rate})"
        )

        # All rates must be in valid range [0, 1]
        for outcome in results.outcomes:
            assert 0.0 <= outcome.adoption_rate <= 1.0
            assert 0.0 <= outcome.mean_probability <= 1.0

        assert 0.0 <= results.aggregate_adoption_rate <= 1.0

    def test_pre_computed_sensitivities_skip_derivation(self):
        """Synths with pre-computed sensitivities should work without demographics."""
        synth_with_sensitivities = {
            "id": "pre_computed",
            "sensitivities": {
                "risk_aversion": 0.3,
                "social_dependency": 0.5,
                "institutional_trust_level": 0.6,
                "habit_plasticity": 0.7,
                "friction_tolerance": 0.8,
                "pragmatism": 0.6,
                "digital_capability": 0.9,
                "motor_ability": 0.85,
                "subject_domain": 0.7,
            },
        }

        mechanisms = FeatureMechanisms(
            irreversibility=0.5,
            intrinsic_value=0.7,
            learning_curve=0.4,
        )

        results = run_simulation(
            [synth_with_sensitivities],
            mechanisms,
            n_executions=200,
            seed=42,
        )

        assert len(results.outcomes) == 1
        assert results.outcomes[0].synth_id == "pre_computed"
        assert 0.0 <= results.outcomes[0].adoption_rate <= 1.0
        assert results.n_synths == 1
        assert results.n_executions == 200

    def test_emergent_states_match_formulas(self):
        """Verify emergent states match documented formulas.

        Derives sensitivities for a known demographic profile, then verifies:
        - perceived_risk = 1 - (1 - irreversibility) * (1 - risk_aversion)  [non-linear]
        - intrinsic_appeal = intrinsic_value x pragmatism
        """
        synth = {
            "id": "test",
            "demografia": {
                "idade": 30,
                "escolaridade": "Superior completo",
                "localizacao": {"regiao": "Sudeste"},
            },
        }

        derived = derive_sensitivities(synth)
        sensitivities = UserSensitivities(
            **{k: v for k, v in derived.items() if k != "_meta"}
        )

        mechanisms = FeatureMechanisms(
            irreversibility=0.8,
            intrinsic_value=0.7,
        )

        state = calculate_emergent_state(mechanisms, sensitivities)

        # perceived_risk = 1 - (1 - 0.8) * (1 - risk_aversion) [non-linear]
        expected_perceived_risk = 1.0 - (1.0 - 0.8) * (1.0 - derived["risk_aversion"])
        assert state.perceived_risk == pytest.approx(expected_perceived_risk, abs=1e-6), (
            f"perceived_risk: expected {expected_perceived_risk}, got {state.perceived_risk}. "
            f"Formula: 1 - (1-0.8) * (1-{derived['risk_aversion']})"
        )

        # intrinsic_appeal = intrinsic_value x pragmatism (appeal formula)
        expected_intrinsic_appeal = 0.7 * derived["pragmatism"]
        assert state.intrinsic_appeal == pytest.approx(
            expected_intrinsic_appeal, abs=1e-6
        )

        # trust_barrier = institutional_trust x (1 - institutional_trust_level)
        # mechanisms.institutional_trust defaults to 0.0, so trust_barrier should be 0.0
        assert state.trust_barrier == pytest.approx(0.0, abs=1e-6)

        # network_bonus = network_effect x social_dependency
        # mechanisms.network_effect defaults to 0.0, so network_bonus should be 0.0
        assert state.network_bonus == pytest.approx(0.0, abs=1e-6)

    def test_deterministic_sensitivities_produce_consistent_results(self):
        """Same demographics + same seed -> same sensitivities. Same seed -> same simulation."""
        demo_data = {
            "demografia": {
                "idade": 40,
                "escolaridade": "Superior completo",
                "localizacao": {"regiao": "Sudeste"},
            },
        }

        # Derive sensitivities twice with same seed -> should be identical
        derived_1 = derive_sensitivities(demo_data, seed=42)
        derived_2 = derive_sensitivities(demo_data, seed=42)

        sensitivity_fields = [
            "risk_aversion", "social_dependency", "institutional_trust_level",
            "habit_plasticity", "friction_tolerance", "pragmatism",
            "digital_capability", "motor_ability", "subject_domain",
        ]
        for field in sensitivity_fields:
            assert derived_1[field] == derived_2[field]

        # Pre-compute sensitivities so simulation is fully deterministic
        synth_with_sens = {
            "id": "deterministic",
            "sensitivities": {k: v for k, v in derived_1.items() if k != "_meta"},
        }

        mechanisms = FeatureMechanisms(
            irreversibility=0.6,
            intrinsic_value=0.7,
            network_effect=0.4,
            habit_displacement=0.3,
        )

        results_1 = run_simulation([synth_with_sens], mechanisms, n_executions=300, seed=42)
        results_2 = run_simulation([synth_with_sens], mechanisms, n_executions=300, seed=42)

        assert results_1.outcomes[0].adoption_rate == results_2.outcomes[0].adoption_rate
        assert results_1.outcomes[0].mean_probability == results_2.outcomes[0].mean_probability
        assert results_1.aggregate_adoption_rate == results_2.aggregate_adoption_rate

    def test_feature_types_gating_affects_financial_features(self):
        """Financial feature with low-trust synths should have lower adoption with gates."""
        low_trust_synth = {
            "id": "low_trust",
            "sensitivities": {
                "risk_aversion": 0.7,
                "social_dependency": 0.5,
                "institutional_trust_level": 0.2,  # Low trust
                "habit_plasticity": 0.5,
                "friction_tolerance": 0.5,
                "pragmatism": 0.6,
                "digital_capability": 0.7,
                "motor_ability": 0.8,
                "subject_domain": 0.5,
            },
        }

        mechanisms = FeatureMechanisms(
            irreversibility=0.8,
            institutional_trust=0.9,
            intrinsic_value=0.6,
        )

        # Without feature_types (no gates)
        results_no_gate = run_simulation(
            [low_trust_synth], mechanisms, n_executions=500, seed=42,
        )
        # With financial feature_types (trust + risk gates)
        results_financial = run_simulation(
            [low_trust_synth], mechanisms, n_executions=500, seed=42,
            feature_types=["financial"],
        )

        # Financial gate should reduce adoption for low-trust users
        assert results_financial.outcomes[0].adoption_rate <= results_no_gate.outcomes[0].adoption_rate
