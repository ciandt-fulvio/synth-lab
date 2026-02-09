"""
Unit tests for the Monte Carlo simulation engine (feature_monte_carlo).

Tests Beta-sampled mechanisms, adoption probability computation, sensitivity
extraction, full simulation runs, and module constants.

References:
    - Spec: specs/040-mechanism-sensitivity-update/spec.md
    - Implementation: synth_lab/services/simulation/feature_monte_carlo.py
    - NumPy Beta: https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.beta.html
"""

import numpy as np
import pytest

from synth_lab.domain.entities.emergent_state import EmergentState
from synth_lab.domain.entities.feature_mechanisms import FeatureMechanisms
from synth_lab.domain.entities.user_sensitivities import UserSensitivities
from synth_lab.services.simulation.feature_monte_carlo import (
    _MECHANISM_FIELDS,
    _SENSITIVITY_FIELDS,
    BETA_STRENGTH,
    SimulationResults,
    SynthOutcome,
    _calculate_adoption_probability,
    _get_sensitivities,
    _sample_mechanisms,
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
        network_barrier=0.0,
        motor_barrier=0.0,
        intrinsic_appeal=0.0,
        frequency_value=0.0,
        domain_advantage=0.0,
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
            valor_intrinseco=0.8,
            friccao_operacional=0.35,
            frequencia_de_uso=0.65,
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
            valor_intrinseco=0.3,
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


# ---------------------------------------------------------------------------
# TestCalculateAdoptionProbability
# ---------------------------------------------------------------------------


class TestCalculateAdoptionProbability:
    """Tests for _calculate_adoption_probability formula."""

    def test_all_zeros_gives_base_0_5(self):
        """EmergentState with all zeros should give probability = 0.5."""
        es = _make_emergent_state()
        prob = _calculate_adoption_probability(es)
        assert prob == pytest.approx(0.5, abs=TOLERANCE)

    def test_high_barriers_reduce_probability(self):
        """8 barriers set high should push probability below 0.3."""
        es = _make_emergent_state(
            perceived_risk=0.8,
            trust_barrier=0.7,
            habit_resistance=0.6,
            learning_frustration=0.5,
            friction_burden=0.4,
            social_pressure=0.3,
            network_barrier=0.2,
            motor_barrier=0.3,
        )
        prob = _calculate_adoption_probability(es)
        assert prob < 0.3, f"Expected prob < 0.3, got {prob}"

    def test_high_appeals_increase_probability(self):
        """3 appeals set high should push probability above 0.7."""
        es = _make_emergent_state(
            intrinsic_appeal=0.9,
            frequency_value=0.8,
            domain_advantage=0.7,
        )
        prob = _calculate_adoption_probability(es)
        assert prob > 0.7, f"Expected prob > 0.7, got {prob}"

    def test_clamped_to_0_1(self):
        """Extreme values should always produce probability in [0.0, 1.0]."""
        # Very high barriers -> should clamp to 0.0
        es_low = _make_emergent_state(
            perceived_risk=1.0,
            trust_barrier=1.0,
            habit_resistance=1.0,
            learning_frustration=1.0,
            friction_burden=1.0,
            social_pressure=1.0,
            network_barrier=1.0,
            motor_barrier=1.0,
        )
        prob_low = _calculate_adoption_probability(es_low)
        assert 0.0 <= prob_low <= 1.0
        assert prob_low == pytest.approx(0.0, abs=TOLERANCE)

        # Very high appeals -> 0.5 + (1+1+0)*0.18 = 0.5 + 0.36 = 0.86
        es_high = _make_emergent_state(
            intrinsic_appeal=1.0,
            frequency_value=1.0,
        )
        prob_high = _calculate_adoption_probability(es_high)
        assert 0.0 <= prob_high <= 1.0
        assert prob_high == pytest.approx(0.86, abs=TOLERANCE)

    def test_sc005_barrier_vs_appeal_difference(self):
        """SC-005: barrier-heavy vs appeal-heavy synths differ by >= 20%.

        High barrier synth:
            8 barriers: 7 at 0.8 + motor_barrier=0.0, appeals: 2 at 0.1 + domain=0.0
            prob = 0.5 - (7*0.8+0)*0.12 + (0.1+0.1+0)*0.18
                 = 0.5 - 5.6*0.12 + 0.2*0.18
                 = 0.5 - 0.672 + 0.036
                 = -0.136  -> clamped to 0.0

        High appeal synth:
            8 barriers: 7 at 0.1 + motor_barrier=0.0, appeals: 2 at 0.9 + domain=0.0
            prob = 0.5 - (7*0.1+0)*0.12 + (0.9+0.9+0)*0.18
                 = 0.5 - 0.7*0.12 + 1.8*0.18
                 = 0.5 - 0.084 + 0.324
                 = 0.74
        """
        # High barrier synth
        es_barrier = _make_emergent_state(
            perceived_risk=0.8,
            trust_barrier=0.8,
            habit_resistance=0.8,
            learning_frustration=0.8,
            friction_burden=0.8,
            social_pressure=0.8,
            network_barrier=0.8,
            intrinsic_appeal=0.1,
            frequency_value=0.1,
        )
        prob_barrier = _calculate_adoption_probability(es_barrier)

        # High appeal synth
        es_appeal = _make_emergent_state(
            perceived_risk=0.1,
            trust_barrier=0.1,
            habit_resistance=0.1,
            learning_frustration=0.1,
            friction_burden=0.1,
            social_pressure=0.1,
            network_barrier=0.1,
            intrinsic_appeal=0.9,
            frequency_value=0.9,
        )
        prob_appeal = _calculate_adoption_probability(es_appeal)

        # Verify individual probabilities
        assert prob_barrier == pytest.approx(0.0, abs=TOLERANCE)
        assert prob_appeal == pytest.approx(0.74, abs=TOLERANCE)

        # SC-005: difference must be >= 20%
        difference = abs(prob_appeal - prob_barrier)
        assert difference >= 0.20, (
            f"SC-005 failed: |{prob_appeal} - {prob_barrier}| = {difference} < 0.20"
        )


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
        # Non-overridden fields keep the provided defaults
        assert result.social_dependency == pytest.approx(0.5, abs=TOLERANCE)

    def test_excludes_meta_from_stored(self):
        """Synth with sensitivities including '_meta' key should exclude it."""
        sens_dict = _make_sensitivities_dict(ra=0.7)
        sens_dict["_meta"] = {"source": "derived", "version": "2.0"}
        synth = {"id": "s2", "sensitivities": sens_dict}

        # Should not raise even though _meta is present
        result = _get_sensitivities(synth)
        assert isinstance(result, UserSensitivities)
        assert result.risk_aversion == pytest.approx(0.7, abs=TOLERANCE)
        # _meta should not appear as an attribute
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
        mechanisms = FeatureMechanisms(irreversibility=0.5, valor_intrinseco=0.6)

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
        mechanisms = FeatureMechanisms(irreversibility=0.5, valor_intrinseco=0.8)

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
            valor_intrinseco=0.8,
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
        """Young (low risk_aversion, high digital_capability) should adopt more.

        Given mechanisms with irreversibility=0.7 and learning_curve=0.6,
        a young user with low risk and high capability should see fewer
        barriers than an elderly user with opposite sensitivities.
        """
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
            valor_intrinseco=0.8,
            friccao_operacional=0.4,
            frequencia_de_uso=0.7,
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


# ---------------------------------------------------------------------------
# TestConstants
# ---------------------------------------------------------------------------


class TestConstants:
    """Tests for module-level constants."""

    def test_beta_strength_is_15(self):
        """BETA_STRENGTH should be 15."""
        assert BETA_STRENGTH == 15

    def test_mechanism_fields_count(self):
        """_MECHANISM_FIELDS should contain exactly 9 entries."""
        assert len(_MECHANISM_FIELDS) == 9

    def test_sensitivity_fields_count(self):
        """_SENSITIVITY_FIELDS should contain exactly 9 entries."""
        assert len(_SENSITIVITY_FIELDS) == 9
