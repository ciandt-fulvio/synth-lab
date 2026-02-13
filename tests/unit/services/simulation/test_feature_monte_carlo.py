"""
Unit tests for the Monte Carlo simulation engine (feature_monte_carlo).

Tests Beta-sampled mechanisms, sigmoid adoption probability, sensitivity
extraction, gating mechanisms, full simulation runs, and module constants.

References:
    - Implementation: synth_lab/services/simulation/feature_monte_carlo.py
    - NumPy Beta: https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.beta.html
"""

import math

import numpy as np
import pytest

from synth_lab.domain.entities.emergent_state import EmergentState
from synth_lab.domain.entities.feature_mechanisms import FeatureMechanisms
from synth_lab.domain.entities.user_sensitivities import UserSensitivities
from synth_lab.services.simulation.feature_monte_carlo import (
    _MECHANISM_FIELDS,
    _SENSITIVITY_FIELDS,
    BETA_STRENGTH_DEFAULT,
    BETA_STRENGTH_MAP,
    GATE_TYPE_MAP,
    _INTERCEPT,
    _APPEAL_WEIGHT,
    _BARRIER_WEIGHT,
    SimulationResults,
    SynthOutcome,
    _apply_gates,
    _calculate_adoption_probability,
    _get_sensitivities,
    _sample_mechanisms,
    _sigmoid,
    run_simulation,
)

TOLERANCE = 1e-4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sensitivities_dict(
    ra=0.5, sd=0.5, it=0.5, hp=0.5, ft=0.5, pr=0.5, dc=0.5, ma=0.5, dom=0.5
):
    """Compact helper for sensitivities dict."""
    return {
        "risk_aversion": ra,
        "social_dependency": sd,
        "institutional_trust_level": it,
        "habit_plasticity": hp,
        "friction_tolerance": ft,
        "pragmatism": pr,
        "digital_capability": dc,
        "motor_ability": ma,
        "subject_domain": dom,
    }


def _make_emergent_state(**kw):
    """Build EmergentState with defaults=0.0."""
    defaults = dict(
        perceived_risk=0.0,
        trust_barrier=0.0,
        habit_resistance=0.0,
        learning_frustration=0.0,
        friction_burden=0.0,
        social_pressure=0.0,
        motor_barrier=0.0,
        intrinsic_appeal=0.0,
        frequency_value=0.0,
        domain_advantage=0.0,
        network_bonus=0.0,
    )
    defaults.update(kw)
    return EmergentState(**defaults)


# ---------------------------------------------------------------------------
# TestSampleMechanisms
# ---------------------------------------------------------------------------


class TestSampleMechanisms:
    """Tests for _sample_mechanisms Beta-distribution sampling."""

    def test_mean_zero_stays_zero(self):
        """Mechanisms with irreversibility=0.0 should stay exactly 0.0."""
        rng = np.random.default_rng(42)
        mechanisms = FeatureMechanisms(irreversibility=0.0)
        sampled = _sample_mechanisms(mechanisms, rng)
        assert sampled.irreversibility == 0.0

    def test_mean_one_stays_one(self):
        """Mechanisms with irreversibility=1.0 should stay exactly 1.0."""
        rng = np.random.default_rng(42)
        mechanisms = FeatureMechanisms(irreversibility=1.0)
        sampled = _sample_mechanisms(mechanisms, rng)
        assert sampled.irreversibility == 1.0

    def test_mean_half_samples_around_half(self):
        """200 samples with mean=0.5 should average within (0.3, 0.7)."""
        rng = np.random.default_rng(42)
        mechanisms = FeatureMechanisms(irreversibility=0.5)
        samples = [
            _sample_mechanisms(mechanisms, rng).irreversibility for _ in range(200)
        ]
        avg = sum(samples) / len(samples)
        assert 0.3 < avg < 0.7, f"Average {avg:.4f} outside (0.3, 0.7)"

    def test_all_9_fields_sampled(self):
        """All 9 mechanism fields should receive values in [0, 1]."""
        rng = np.random.default_rng(42)
        mechanisms = FeatureMechanisms(
            irreversibility=0.5,
            network_effect=0.3,
            institutional_trust=0.7,
            habit_displacement=0.4,
            learning_curve=0.6,
            social_visibility=0.2,
            intrinsic_value=0.8,
            operational_friction=0.35,
            frequency_of_use=0.65,
        )
        sampled = _sample_mechanisms(mechanisms, rng)

        for field_name in _MECHANISM_FIELDS:
            value = getattr(sampled, field_name)
            assert 0.0 <= value <= 1.0, (
                f"{field_name}={value} outside [0, 1]"
            )

    def test_reproducibility_with_same_seed(self):
        """Same rng seed should produce identical sampled values."""
        mechanisms = FeatureMechanisms(
            irreversibility=0.5,
            network_effect=0.7,
            intrinsic_value=0.3,
        )

        rng_a = np.random.default_rng(99)
        sampled_a = _sample_mechanisms(mechanisms, rng_a)

        rng_b = np.random.default_rng(99)
        sampled_b = _sample_mechanisms(mechanisms, rng_b)

        for field_name in _MECHANISM_FIELDS:
            val_a = getattr(sampled_a, field_name)
            val_b = getattr(sampled_b, field_name)
            assert val_a == pytest.approx(val_b, abs=TOLERANCE), (
                f"{field_name}: {val_a} != {val_b}"
            )

    def test_per_mechanism_beta_strength(self):
        """Verify that different mechanisms use different Beta concentrations.

        institutional_trust (strength=30) should have tighter distribution
        than intrinsic_value (strength=6).
        """
        rng_trust = np.random.default_rng(42)
        rng_value = np.random.default_rng(42)

        mechs_trust = FeatureMechanisms(institutional_trust=0.5)
        mechs_value = FeatureMechanisms(intrinsic_value=0.5)

        trust_samples = [
            _sample_mechanisms(mechs_trust, rng_trust).institutional_trust
            for _ in range(500)
        ]
        value_samples = [
            _sample_mechanisms(mechs_value, rng_value).intrinsic_value
            for _ in range(500)
        ]

        trust_std = np.std(trust_samples)
        value_std = np.std(value_samples)

        # intrinsic_value (strength=6) should have higher variance than
        # institutional_trust (strength=30)
        assert value_std > trust_std, (
            f"intrinsic_value std ({value_std:.4f}) should be > "
            f"institutional_trust std ({trust_std:.4f})"
        )


# ---------------------------------------------------------------------------
# TestCalculateAdoptionProbability
# ---------------------------------------------------------------------------


class TestCalculateAdoptionProbability:
    """Tests for _calculate_adoption_probability sigmoid formula."""

    def test_all_zeros_gives_sigmoid_of_intercept(self):
        """EmergentState with all zeros should give sigmoid(INTERCEPT)."""
        es = _make_emergent_state()
        prob = _calculate_adoption_probability(es)
        expected = _sigmoid(_INTERCEPT)  # sigmoid(-0.2) ≈ 0.4502
        assert prob == pytest.approx(expected, abs=TOLERANCE)

    def test_high_barriers_reduce_probability(self):
        """7 barriers set high should push probability very low."""
        es = _make_emergent_state(
            perceived_risk=0.8,
            trust_barrier=0.7,
            habit_resistance=0.6,
            learning_frustration=0.5,
            friction_burden=0.4,
            social_pressure=0.3,
            motor_barrier=0.3,
        )
        prob = _calculate_adoption_probability(es)
        assert prob < 0.15, f"Expected prob < 0.15, got {prob}"

    def test_high_appeals_increase_probability(self):
        """4 appeals set high should push probability above 0.7."""
        es = _make_emergent_state(
            intrinsic_appeal=0.9,
            frequency_value=0.8,
            domain_advantage=0.7,
            network_bonus=0.5,
        )
        prob = _calculate_adoption_probability(es)
        assert prob > 0.7, f"Expected prob > 0.7, got {prob}"

    def test_sigmoid_always_in_0_1(self):
        """Extreme values should always produce probability in (0, 1)."""
        # Very high barriers
        es_low = _make_emergent_state(
            perceived_risk=1.0,
            trust_barrier=1.0,
            habit_resistance=1.0,
            learning_frustration=1.0,
            friction_burden=1.0,
            social_pressure=1.0,
            motor_barrier=1.0,
        )
        prob_low = _calculate_adoption_probability(es_low)
        assert 0.0 < prob_low < 1.0  # sigmoid never reaches 0 or 1

        # Very high appeals
        es_high = _make_emergent_state(
            intrinsic_appeal=1.0,
            frequency_value=1.0,
            domain_advantage=1.0,
            network_bonus=1.0,
        )
        prob_high = _calculate_adoption_probability(es_high)
        assert 0.0 < prob_high < 1.0

    def test_barrier_heavy_vs_appeal_heavy_difference(self):
        """Barrier-heavy vs appeal-heavy synths differ by >= 20%."""
        es_barrier = _make_emergent_state(
            perceived_risk=0.8,
            trust_barrier=0.8,
            habit_resistance=0.8,
            learning_frustration=0.8,
            friction_burden=0.8,
            social_pressure=0.8,
            motor_barrier=0.8,
            intrinsic_appeal=0.1,
            frequency_value=0.1,
        )
        prob_barrier = _calculate_adoption_probability(es_barrier)

        es_appeal = _make_emergent_state(
            perceived_risk=0.1,
            trust_barrier=0.1,
            habit_resistance=0.1,
            learning_frustration=0.1,
            friction_burden=0.1,
            social_pressure=0.1,
            motor_barrier=0.1,
            intrinsic_appeal=0.9,
            frequency_value=0.9,
            network_bonus=0.5,
        )
        prob_appeal = _calculate_adoption_probability(es_appeal)

        difference = abs(prob_appeal - prob_barrier)
        assert difference >= 0.20, (
            f"|{prob_appeal} - {prob_barrier}| = {difference} < 0.20"
        )

    def test_sigmoid_function_correctness(self):
        """Verify _sigmoid produces correct output for known inputs."""
        assert _sigmoid(0.0) == pytest.approx(0.5, abs=TOLERANCE)
        assert _sigmoid(100.0) == pytest.approx(1.0, abs=TOLERANCE)
        assert _sigmoid(-100.0) == pytest.approx(0.0, abs=TOLERANCE)
        assert _sigmoid(1.0) == pytest.approx(1.0 / (1.0 + math.exp(-1.0)), abs=TOLERANCE)


# ---------------------------------------------------------------------------
# TestGatingMechanisms
# ---------------------------------------------------------------------------


class TestGatingMechanisms:
    """Tests for _apply_gates gating mechanisms."""

    def test_no_gates_without_feature_types(self):
        """Without feature_types, prob should be unchanged."""
        es = _make_emergent_state(trust_barrier=0.8, perceived_risk=0.9)
        prob = 0.5
        gated = _apply_gates(prob, es, feature_types=None)
        assert gated == pytest.approx(0.5, abs=TOLERANCE)

    def test_no_gates_with_empty_feature_types(self):
        """Empty feature_types list should not apply any gates."""
        es = _make_emergent_state(trust_barrier=0.8)
        prob = 0.5
        gated = _apply_gates(prob, es, feature_types=[])
        assert gated == pytest.approx(0.5, abs=TOLERANCE)

    def test_trust_gate_low_trust_reduces_prob(self):
        """Financial feature with low trust should significantly reduce prob."""
        es = _make_emergent_state(trust_barrier=0.8)  # trust_level ≈ 0.2
        prob = 0.6
        gated = _apply_gates(prob, es, feature_types=["financial"])
        assert gated < prob, f"Trust gate should reduce prob: {gated} >= {prob}"

    def test_trust_gate_high_trust_preserves_prob(self):
        """Financial feature with high trust should mostly preserve prob."""
        es = _make_emergent_state(trust_barrier=0.1)  # trust_level ≈ 0.9
        prob = 0.6
        gated = _apply_gates(prob, es, feature_types=["financial"])
        assert gated >= prob * 0.8, (
            f"High trust should preserve most of prob: {gated} < {prob * 0.8}"
        )

    def test_risk_gate_high_risk_reduces_prob(self):
        """Identity feature with high perceived_risk should reduce prob."""
        es = _make_emergent_state(perceived_risk=0.95)
        prob = 0.6
        gated = _apply_gates(prob, es, feature_types=["identity"])
        assert gated < prob

    def test_value_gate_low_value_reduces_prob(self):
        """Aesthetic feature with low intrinsic_appeal should reduce prob."""
        es = _make_emergent_state(intrinsic_appeal=0.05)
        prob = 0.6
        gated = _apply_gates(prob, es, feature_types=["aesthetic"])
        assert gated < prob

    def test_value_gate_high_value_preserves_prob(self):
        """Aesthetic feature with high intrinsic_appeal should mostly preserve prob."""
        es = _make_emergent_state(intrinsic_appeal=0.8)
        prob = 0.6
        gated = _apply_gates(prob, es, feature_types=["aesthetic"])
        assert gated >= prob * 0.8

    def test_unrelated_feature_type_no_gate(self):
        """Feature type not in any gate map should not apply gates."""
        es = _make_emergent_state(trust_barrier=0.9, perceived_risk=0.9)
        prob = 0.5
        gated = _apply_gates(prob, es, feature_types=["communication"])
        assert gated == pytest.approx(0.5, abs=TOLERANCE)

    def test_multiple_gates_can_stack(self):
        """Financial + identity activates both trust and risk gates."""
        es = _make_emergent_state(trust_barrier=0.7, perceived_risk=0.9)
        prob = 0.6
        gated = _apply_gates(prob, es, feature_types=["financial", "identity"])
        # Both gates should reduce prob significantly
        assert gated < prob * 0.5


# ---------------------------------------------------------------------------
# TestGetSensitivities
# ---------------------------------------------------------------------------


class TestGetSensitivities:
    """Tests for _get_sensitivities extraction from synth data."""

    def test_uses_stored_sensitivities(self):
        """Synth with 'sensitivities' key should return those values."""
        sens_dict = _make_sensitivities_dict(ra=0.8, dc=0.3)
        synth = {"id": "s1", "sensitivities": sens_dict}
        result = _get_sensitivities(synth)

        assert isinstance(result, UserSensitivities)
        assert result.risk_aversion == pytest.approx(0.8, abs=TOLERANCE)
        assert result.digital_capability == pytest.approx(0.3, abs=TOLERANCE)
        assert result.social_dependency == pytest.approx(0.5, abs=TOLERANCE)

    def test_excludes_meta_from_stored(self):
        """Synth with sensitivities including '_meta' key should exclude it."""
        sens_dict = _make_sensitivities_dict(ra=0.7)
        sens_dict["_meta"] = {"source": "derived", "version": "2.0"}
        synth = {"id": "s2", "sensitivities": sens_dict}

        result = _get_sensitivities(synth)
        assert isinstance(result, UserSensitivities)
        assert result.risk_aversion == pytest.approx(0.7, abs=TOLERANCE)
        assert not hasattr(result, "_meta")


# ---------------------------------------------------------------------------
# TestRunSimulation
# ---------------------------------------------------------------------------


class TestRunSimulation:
    """Tests for the full run_simulation Monte Carlo engine."""

    def test_basic_simulation_structure(self):
        """2 synths, 100 executions should produce correct structure."""
        synths = [
            {"id": "s1", "sensitivities": _make_sensitivities_dict()},
            {"id": "s2", "sensitivities": _make_sensitivities_dict(ra=0.7)},
        ]
        mechanisms = FeatureMechanisms(irreversibility=0.5, intrinsic_value=0.6)

        results = run_simulation(synths, mechanisms, n_executions=100, seed=42)

        assert isinstance(results, SimulationResults)
        assert results.n_synths == 2
        assert results.n_executions == 100
        assert len(results.outcomes) == 2
        for outcome in results.outcomes:
            assert isinstance(outcome, SynthOutcome)
            assert outcome.n_executions == 100

    def test_reproducibility_same_seed(self):
        """Same inputs + same seed should produce identical results."""
        synths = [
            {"id": "repro", "sensitivities": _make_sensitivities_dict(ra=0.6, dc=0.7)},
        ]
        mechanisms = FeatureMechanisms(irreversibility=0.5, intrinsic_value=0.8)

        r1 = run_simulation(synths, mechanisms, n_executions=200, seed=99)
        r2 = run_simulation(synths, mechanisms, n_executions=200, seed=99)

        assert r1.outcomes[0].adoption_rate == r2.outcomes[0].adoption_rate
        assert r1.outcomes[0].mean_probability == r2.outcomes[0].mean_probability
        assert r1.aggregate_adoption_rate == r2.aggregate_adoption_rate

    def test_adoption_rate_in_0_1_range(self):
        """All adoption_rates and aggregate should be in [0, 1]."""
        synths = [
            {"id": f"s{i}", "sensitivities": _make_sensitivities_dict()}
            for i in range(5)
        ]
        mechanisms = FeatureMechanisms(
            irreversibility=0.7,
            learning_curve=0.6,
            intrinsic_value=0.8,
        )

        results = run_simulation(synths, mechanisms, n_executions=100, seed=42)

        for outcome in results.outcomes:
            assert 0.0 <= outcome.adoption_rate <= 1.0, (
                f"{outcome.synth_id}: adoption_rate={outcome.adoption_rate}"
            )
            assert 0.0 <= outcome.mean_probability <= 1.0, (
                f"{outcome.synth_id}: mean_probability={outcome.mean_probability}"
            )
        assert 0.0 <= results.aggregate_adoption_rate <= 1.0

    def test_young_vs_elderly_adoption(self):
        """Young (low risk_aversion, high digital_capability) should adopt more."""
        young = {
            "id": "young_tech",
            "sensitivities": _make_sensitivities_dict(
                ra=0.3, sd=0.6, hp=0.8, ft=0.7, pr=0.7, dc=0.9,
            ),
        }
        elderly = {
            "id": "elderly_user",
            "sensitivities": _make_sensitivities_dict(
                ra=0.9, sd=0.3, it=0.4, hp=0.2, ft=0.2, pr=0.4, dc=0.2,
            ),
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
            [young, elderly], mechanisms, n_executions=500, seed=42
        )

        young_outcome = results.outcomes[0]
        elderly_outcome = results.outcomes[1]

        assert young_outcome.synth_id == "young_tech"
        assert elderly_outcome.synth_id == "elderly_user"
        assert young_outcome.adoption_rate > elderly_outcome.adoption_rate, (
            f"Young ({young_outcome.adoption_rate}) should have higher adoption "
            f"than elderly ({elderly_outcome.adoption_rate})"
        )

    def test_synth_id_preserved(self):
        """synth['id'] should appear in outcome.synth_id."""
        synths = [
            {"id": "custom_id_abc", "sensitivities": _make_sensitivities_dict()},
        ]
        mechanisms = FeatureMechanisms(irreversibility=0.5)

        results = run_simulation(synths, mechanisms, n_executions=10, seed=42)

        assert results.outcomes[0].synth_id == "custom_id_abc"

    def test_feature_types_passed_to_gates(self):
        """feature_types param should affect simulation results for financial features."""
        synths = [
            {"id": "s1", "sensitivities": _make_sensitivities_dict(
                ra=0.5, it=0.3,  # Low trust
            )},
        ]
        mechanisms = FeatureMechanisms(
            irreversibility=0.7,
            institutional_trust=0.8,
            intrinsic_value=0.6,
        )

        # Without gates
        results_no_gate = run_simulation(
            synths, mechanisms, n_executions=500, seed=42
        )
        # With financial gate (low trust should reduce adoption)
        results_with_gate = run_simulation(
            synths, mechanisms, n_executions=500, seed=42,
            feature_types=["financial"],
        )

        # Financial gate should reduce adoption rate for low-trust synths
        assert results_with_gate.outcomes[0].adoption_rate <= results_no_gate.outcomes[0].adoption_rate


# ---------------------------------------------------------------------------
# TestConstants
# ---------------------------------------------------------------------------


class TestConstants:
    """Tests for module-level constants."""

    def test_beta_strength_default_is_15(self):
        """BETA_STRENGTH_DEFAULT should be 15."""
        assert BETA_STRENGTH_DEFAULT == 15

    def test_beta_strength_map_has_9_entries(self):
        """BETA_STRENGTH_MAP should have entries for all 9 mechanisms."""
        assert len(BETA_STRENGTH_MAP) == 9

    def test_beta_strength_map_values_positive(self):
        """All Beta strength values should be positive integers."""
        for name, strength in BETA_STRENGTH_MAP.items():
            assert isinstance(strength, int), f"{name}: {strength} is not int"
            assert strength > 0, f"{name}: {strength} <= 0"

    def test_mechanism_fields_count(self):
        """_MECHANISM_FIELDS should contain exactly 9 entries."""
        assert len(_MECHANISM_FIELDS) == 9

    def test_sensitivity_fields_count(self):
        """_SENSITIVITY_FIELDS should contain exactly 9 entries."""
        assert len(_SENSITIVITY_FIELDS) == 9

    def test_gate_type_map_structure(self):
        """GATE_TYPE_MAP should have 3 gate types with valid lists."""
        assert len(GATE_TYPE_MAP) == 3
        assert "trust_gate" in GATE_TYPE_MAP
        assert "risk_gate" in GATE_TYPE_MAP
        assert "value_gate" in GATE_TYPE_MAP
        for gate_name, types in GATE_TYPE_MAP.items():
            assert isinstance(types, list)
            assert len(types) > 0
