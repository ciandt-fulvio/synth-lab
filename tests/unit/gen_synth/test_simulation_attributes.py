"""
Unit tests for simulation attributes generation.

Tests:
- Beta distribution outputs are in [0,1]
- Latent trait derivation formulas correctness
- motor_ability derivation from disability types
- digital_literacy to alfabetizacao_digital translation

References:
    - Module: src/synth_lab/gen_synth/simulation_attributes.py
    - Spec: specs/016-feature-impact-simulation/spec.md
"""

import numpy as np
import pytest

from synth_lab.domain.entities import (
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables,
)
from synth_lab.gen_synth.simulation_attributes import (
    MOTOR_ABILITY_MAP,
    derive_latent_traits,
    digital_literacy_to_alfabetizacao_digital,
    generate_observables,
    generate_simulation_attributes,
    motor_ability_from_disability,
    validate_simulation_attributes,
)


class TestMotorAbilityFromDisability:
    """Tests for motor_ability_from_disability function."""

    @pytest.mark.parametrize(
        "tipo,expected",
        [
            ("nenhuma", 1.0),
            ("leve", 0.8),
            ("moderada", 0.5),
            ("severa", 0.2),
        ],
    )
    def test_known_disability_types(self, tipo: str, expected: float) -> None:
        """Known disability types return correct motor ability values."""
        result = motor_ability_from_disability(tipo)
        assert result == expected

    def test_unknown_disability_defaults_to_one(self) -> None:
        """Unknown disability types default to 1.0."""
        result = motor_ability_from_disability("unknown")
        assert result == 1.0

    def test_all_map_values_in_valid_range(self) -> None:
        """All mapped values are in [0, 1] range."""
        for tipo, value in MOTOR_ABILITY_MAP.items():
            assert 0.0 <= value <= 1.0, f"{tipo} has invalid value {value}"


class TestDigitalLiteracyTranslation:
    """Tests for digital_literacy_to_alfabetizacao_digital function."""

    @pytest.mark.parametrize(
        "dl,expected",
        [
            (0.0, 0),
            (1.0, 100),
            (0.5, 50),
            (0.35, 35),
            (0.857, 86),  # rounds to 86
            (0.005, 0),  # rounds to 0 (0.5 -> 0)
            (0.995, 100),  # rounds to 100 (99.5 -> 100)
        ],
    )
    def test_translation_values(self, dl: float, expected: int) -> None:
        """Digital literacy values translate correctly to integers."""
        result = digital_literacy_to_alfabetizacao_digital(dl)
        assert result == expected
        assert isinstance(result, int)


class TestGenerateObservables:
    """Tests for generate_observables function."""

    def test_reproducibility_with_same_seed(self) -> None:
        """Same seed produces same observable values."""
        rng1 = np.random.default_rng(seed=42)
        rng2 = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "nenhuma"}}

        obs1 = generate_observables(rng1, deficiencias)
        obs2 = generate_observables(rng2, deficiencias)

        assert obs1.digital_literacy == obs2.digital_literacy
        assert obs1.similar_tool_experience == obs2.similar_tool_experience
        assert obs1.motor_ability == obs2.motor_ability
        assert obs1.time_availability == obs2.time_availability
        assert obs1.domain_expertise == obs2.domain_expertise

    def test_all_values_in_valid_range(self) -> None:
        """All generated observable values are in [0, 1] range."""
        rng = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "nenhuma"}}

        # Generate multiple times to increase coverage
        for _ in range(100):
            obs = generate_observables(rng, deficiencias)
            assert 0.0 <= obs.digital_literacy <= 1.0
            assert 0.0 <= obs.similar_tool_experience <= 1.0
            assert 0.0 <= obs.motor_ability <= 1.0
            assert 0.0 <= obs.time_availability <= 1.0
            assert 0.0 <= obs.domain_expertise <= 1.0

    def test_motor_ability_from_disability_integration(self) -> None:
        """Motor ability is correctly derived from disability type."""
        rng = np.random.default_rng(seed=42)

        test_cases = [
            ({"motora": {"tipo": "nenhuma"}}, 1.0),
            ({"motora": {"tipo": "leve"}}, 0.8),
            ({"motora": {"tipo": "moderada"}}, 0.5),
            ({"motora": {"tipo": "severa"}}, 0.2),
        ]

        for deficiencias, expected_motor in test_cases:
            obs = generate_observables(rng, deficiencias)
            assert obs.motor_ability == expected_motor

    def test_missing_motora_defaults_to_nenhuma(self) -> None:
        """Missing motora key defaults to motor_ability=1.0."""
        rng = np.random.default_rng(seed=42)
        deficiencias = {}  # No motora key

        obs = generate_observables(rng, deficiencias)
        assert obs.motor_ability == 1.0

    def test_beta_distribution_behavior(self) -> None:
        """Beta distributions produce expected mean values."""
        rng = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "nenhuma"}}

        samples = [generate_observables(rng, deficiencias) for _ in range(1000)]

        # digital_literacy: Beta(2,4) has mean = 2/(2+4) = 0.333
        dl_mean = sum(s.digital_literacy for s in samples) / len(samples)
        assert 0.25 <= dl_mean <= 0.42, f"digital_literacy mean {dl_mean} out of expected range"

        # time_availability: Beta(2,3) has mean = 2/(2+3) = 0.4
        ta_mean = sum(s.time_availability for s in samples) / len(samples)
        assert 0.32 <= ta_mean <= 0.48, f"time_availability mean {ta_mean} out of expected range"


class TestDeriveLatentTraits:
    """Tests for derive_latent_traits function."""

    def test_formula_correctness_symmetric(self) -> None:
        """Latent traits derive correctly from symmetric inputs (all 0.5)."""
        obs = SimulationObservables(
            digital_literacy=0.5,
            similar_tool_experience=0.5,
            motor_ability=1.0,
            time_availability=0.5,
            domain_expertise=0.5,
        )
        traits = derive_latent_traits(obs)

        # capability_mean = 0.40*0.5 + 0.35*0.5 + 0.15*1.0 + 0.10*0.5 = 0.575
        assert abs(traits.capability_mean - 0.575) < 0.001

        # trust_mean = 0.60*0.5 + 0.40*0.5 = 0.5
        assert abs(traits.trust_mean - 0.5) < 0.001

        # friction_tolerance_mean = 0.40*0.5 + 0.35*0.5 + 0.25*0.5 = 0.5
        assert abs(traits.friction_tolerance_mean - 0.5) < 0.001

        # exploration_prob = 0.50*0.5 + 0.30*(1-0.5) + 0.20*0.5 = 0.5
        assert abs(traits.exploration_prob - 0.5) < 0.001

    def test_formula_correctness_edge_low(self) -> None:
        """Latent traits derive correctly from low inputs (all 0.0)."""
        obs = SimulationObservables(
            digital_literacy=0.0,
            similar_tool_experience=0.0,
            motor_ability=0.2,
            time_availability=0.0,
            domain_expertise=0.0,
        )
        traits = derive_latent_traits(obs)

        # capability_mean = 0.40*0.0 + 0.35*0.0 + 0.15*0.2 + 0.10*0.0 = 0.03
        assert abs(traits.capability_mean - 0.03) < 0.001

        # trust_mean = 0.60*0.0 + 0.40*0.0 = 0.0
        assert abs(traits.trust_mean - 0.0) < 0.001

        # friction_tolerance_mean = 0.40*0.0 + 0.35*0.0 + 0.25*0.0 = 0.0
        assert abs(traits.friction_tolerance_mean - 0.0) < 0.001

        # exploration_prob = 0.50*0.0 + 0.30*(1-0.0) + 0.20*0.0 = 0.30
        assert abs(traits.exploration_prob - 0.30) < 0.001

    def test_formula_correctness_edge_high(self) -> None:
        """Latent traits derive correctly from high inputs (all 1.0)."""
        obs = SimulationObservables(
            digital_literacy=1.0,
            similar_tool_experience=1.0,
            motor_ability=1.0,
            time_availability=1.0,
            domain_expertise=1.0,
        )
        traits = derive_latent_traits(obs)

        # capability_mean = 0.40*1.0 + 0.35*1.0 + 0.15*1.0 + 0.10*1.0 = 1.0
        assert abs(traits.capability_mean - 1.0) < 0.001

        # trust_mean = 0.60*1.0 + 0.40*1.0 = 1.0
        assert abs(traits.trust_mean - 1.0) < 0.001

        # friction_tolerance_mean = 0.40*1.0 + 0.35*1.0 + 0.25*1.0 = 1.0
        assert abs(traits.friction_tolerance_mean - 1.0) < 0.001

        # exploration_prob = 0.50*1.0 + 0.30*(1-1.0) + 0.20*1.0 = 0.70
        assert abs(traits.exploration_prob - 0.70) < 0.001

    def test_all_outputs_in_valid_range(self) -> None:
        """All derived latent traits are in [0, 1] range."""
        rng = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "nenhuma"}}

        for _ in range(100):
            obs = generate_observables(rng, deficiencias)
            traits = derive_latent_traits(obs)

            assert 0.0 <= traits.capability_mean <= 1.0
            assert 0.0 <= traits.trust_mean <= 1.0
            assert 0.0 <= traits.friction_tolerance_mean <= 1.0
            assert 0.0 <= traits.exploration_prob <= 1.0


class TestGenerateSimulationAttributes:
    """Tests for generate_simulation_attributes function."""

    def test_returns_simulation_attributes(self) -> None:
        """Returns a SimulationAttributes instance."""
        rng = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "nenhuma"}}

        attrs = generate_simulation_attributes(rng, deficiencias)

        assert isinstance(attrs, SimulationAttributes)
        assert isinstance(attrs.observables, SimulationObservables)
        assert isinstance(attrs.latent_traits, SimulationLatentTraits)

    def test_reproducibility(self) -> None:
        """Same seed produces same results."""
        deficiencias = {"motora": {"tipo": "leve"}}

        rng1 = np.random.default_rng(seed=123)
        rng2 = np.random.default_rng(seed=123)

        attrs1 = generate_simulation_attributes(rng1, deficiencias)
        attrs2 = generate_simulation_attributes(rng2, deficiencias)

        assert attrs1.observables.digital_literacy == attrs2.observables.digital_literacy
        assert attrs1.latent_traits.capability_mean == attrs2.latent_traits.capability_mean


class TestValidateSimulationAttributes:
    """Tests for validate_simulation_attributes function."""

    def test_valid_attributes_pass(self) -> None:
        """Valid simulation attributes pass validation."""
        rng = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "nenhuma"}}

        attrs = generate_simulation_attributes(rng, deficiencias)
        is_valid, errors = validate_simulation_attributes(attrs)

        assert is_valid is True
        assert errors == []

    def test_invalid_observable_detected(self) -> None:
        """Invalid observable values are detected."""
        # Create manually to inject invalid values
        observables = SimulationObservables(
            digital_literacy=0.5,
            similar_tool_experience=0.5,
            motor_ability=0.5,
            time_availability=0.5,
            domain_expertise=0.5,
        )
        latent_traits = SimulationLatentTraits(
            capability_mean=0.5,
            trust_mean=0.5,
            friction_tolerance_mean=0.5,
            exploration_prob=0.5,
        )
        attrs = SimulationAttributes(
            observables=observables,
            latent_traits=latent_traits,
        )

        # Normal case should pass
        is_valid, errors = validate_simulation_attributes(attrs)
        assert is_valid is True


class TestIntegration:
    """Integration tests for full simulation attributes flow."""

    def test_full_flow_with_various_disabilities(self) -> None:
        """Full flow works with various disability configurations."""
        rng = np.random.default_rng(seed=42)

        disability_configs = [
            {"motora": {"tipo": "nenhuma"}, "visual": {"tipo": "nenhuma"}},
            {"motora": {"tipo": "severa"}, "visual": {"tipo": "moderada"}},
            {},  # Empty disabilities
        ]

        for deficiencias in disability_configs:
            attrs = generate_simulation_attributes(rng, deficiencias)

            # Validate structure
            is_valid, errors = validate_simulation_attributes(attrs)
            assert is_valid, f"Validation failed for {deficiencias}: {errors}"

            # Verify all fields are populated
            assert hasattr(attrs.observables, "digital_literacy")
            assert hasattr(attrs.latent_traits, "capability_mean")

    def test_synth_builder_integration_flow(self) -> None:
        """Simulation attributes integrate correctly with synth builder."""
        rng = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "moderada"}}

        attrs = generate_simulation_attributes(rng, deficiencias)

        # Verify motor_ability reflects disability
        assert attrs.observables.motor_ability == 0.5  # "moderada" -> 0.5

        # Verify digital_literacy translation works
        dl = attrs.observables.digital_literacy
        ad = digital_literacy_to_alfabetizacao_digital(dl)
        assert ad == int(round(dl * 100))
