"""
Simulation Attributes Generator for synth-lab.

Generates observable attributes and derives latent traits for Monte Carlo
feature impact simulations.

Functions:
- generate_observables(): Generate observable attributes using Beta distributions
- derive_latent_traits(): Derive latent traits from observables
- generate_simulation_attributes(): Main function to generate all simulation attributes
- digital_literacy_to_alfabetizacao_digital(): Translate digital_literacy [0,1] to [0,100]
- motor_ability_from_disability(): Derive motor_ability from disability type

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Data model: specs/016-feature-impact-simulation/data-model.md
    - Research: specs/016-feature-impact-simulation/research.md

Sample usage:
    from synth_lab.gen_synth.simulation_attributes import generate_simulation_attributes
    import numpy as np

    rng = np.random.default_rng(seed=42)
    deficiencias = {"motora": {"tipo": "nenhuma"}}
    attrs = generate_simulation_attributes(rng, deficiencias)
    print(attrs["observables"]["digital_literacy"])

Expected output:
    SimulationAttributes with all fields in [0, 1] range
"""

from typing import Any

import numpy as np
from numpy.random import Generator

from synth_lab.domain.entities import (
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables,
)


# Motor ability mapping from disability type
MOTOR_ABILITY_MAP: dict[str, float] = {
    "nenhuma": 1.0,
    "leve": 0.8,
    "moderada": 0.5,
    "severa": 0.2,
}


def motor_ability_from_disability(tipo: str) -> float:
    """
    Derive motor_ability from disability type.

    Args:
        tipo: Disability type ('nenhuma', 'leve', 'moderada', 'severa')

    Returns:
        Motor ability value in [0, 1]

    Examples:
        >>> motor_ability_from_disability("nenhuma")
        1.0
        >>> motor_ability_from_disability("severa")
        0.2
    """
    return MOTOR_ABILITY_MAP.get(tipo, 1.0)


def digital_literacy_to_alfabetizacao_digital(dl: float) -> int:
    """
    Translate digital_literacy [0,1] to alfabetizacao_digital [0,100].

    Args:
        dl: Digital literacy value in [0, 1]

    Returns:
        Alphabetization digital value in [0, 100]

    Examples:
        >>> digital_literacy_to_alfabetizacao_digital(0.35)
        35
        >>> digital_literacy_to_alfabetizacao_digital(0.857)
        86
    """
    return int(round(dl * 100))


def generate_observables(
    rng: Generator,
    deficiencias: dict[str, Any],
) -> SimulationObservables:
    """
    Generate observable attributes using Beta distributions.

    Args:
        rng: NumPy random generator for reproducibility
        deficiencias: Disabilities dict with 'motora.tipo'

    Returns:
        SimulationObservables with all fields in [0, 1]

    Notes:
        - digital_literacy: Beta(2,4) -> skewed toward low-medium values
        - similar_tool_experience: Beta(3,3) -> symmetric
        - time_availability: Beta(2,3) -> skewed toward low values
        - domain_expertise: Beta(3,3) -> symmetric
        - motor_ability: derived from deficiencias.motora.tipo
    """
    # Generate via Beta distributions
    digital_literacy = float(rng.beta(2, 4))
    similar_tool_experience = float(rng.beta(3, 3))
    time_availability = float(rng.beta(2, 3))
    domain_expertise = float(rng.beta(3, 3))

    # Derive motor_ability from disabilities
    motora_tipo = deficiencias.get("motora", {}).get("tipo", "nenhuma")
    motor_ability = motor_ability_from_disability(motora_tipo)

    return SimulationObservables(
        digital_literacy=digital_literacy,
        similar_tool_experience=similar_tool_experience,
        motor_ability=motor_ability,
        time_availability=time_availability,
        domain_expertise=domain_expertise,
    )


def derive_latent_traits(observables: SimulationObservables) -> SimulationLatentTraits:
    """
    Derive latent traits from observable attributes.

    Args:
        observables: Observable attributes

    Returns:
        SimulationLatentTraits with all fields in [0, 1]

    Formulas:
        - capability_mean: 0.40*dl + 0.35*exp + 0.15*motor + 0.10*domain
        - trust_mean: 0.60*exp + 0.40*dl
        - friction_tolerance_mean: 0.40*time + 0.35*dl + 0.25*exp
        - exploration_prob: 0.50*dl + 0.30*(1-exp) + 0.20*time
    """
    dl = observables.digital_literacy
    exp = observables.similar_tool_experience
    motor = observables.motor_ability
    time = observables.time_availability
    domain = observables.domain_expertise

    # Calculate latent traits using weighted formulas
    capability_mean = 0.40 * dl + 0.35 * exp + 0.15 * motor + 0.10 * domain
    trust_mean = 0.60 * exp + 0.40 * dl
    friction_tolerance_mean = 0.40 * time + 0.35 * dl + 0.25 * exp
    exploration_prob = 0.50 * dl + 0.30 * (1 - exp) + 0.20 * time

    # Ensure all values are in [0, 1] (should already be due to weighted sum)
    capability_mean = max(0.0, min(1.0, capability_mean))
    trust_mean = max(0.0, min(1.0, trust_mean))
    friction_tolerance_mean = max(0.0, min(1.0, friction_tolerance_mean))
    exploration_prob = max(0.0, min(1.0, exploration_prob))

    return SimulationLatentTraits(
        capability_mean=capability_mean,
        trust_mean=trust_mean,
        friction_tolerance_mean=friction_tolerance_mean,
        exploration_prob=exploration_prob,
    )


def generate_simulation_attributes(
    rng: Generator,
    deficiencias: dict[str, Any],
) -> SimulationAttributes:
    """
    Generate complete simulation attributes for a synth.

    This is the main entry point for simulation attribute generation.
    It generates observables using Beta distributions and derives
    latent traits from them.

    Args:
        rng: NumPy random generator for reproducibility
        deficiencias: Disabilities dict with 'motora.tipo'

    Returns:
        SimulationAttributes with observables and latent_traits

    Example:
        >>> import numpy as np
        >>> rng = np.random.default_rng(seed=42)
        >>> deficiencias = {"motora": {"tipo": "nenhuma"}}
        >>> attrs = generate_simulation_attributes(rng, deficiencias)
        >>> 0 <= attrs.observables.digital_literacy <= 1
        True
    """
    observables = generate_observables(rng, deficiencias)
    latent_traits = derive_latent_traits(observables)

    return SimulationAttributes(
        observables=observables,
        latent_traits=latent_traits,
    )


def validate_simulation_attributes(attrs: SimulationAttributes) -> tuple[bool, list[str]]:
    """
    Validate that all simulation attributes are in valid range.

    Args:
        attrs: SimulationAttributes to validate

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Validate observables
    for field, value in attrs.observables.model_dump().items():
        if not 0.0 <= value <= 1.0:
            errors.append(f"Observable {field} out of range: {value}")

    # Validate latent traits
    for field, value in attrs.latent_traits.model_dump().items():
        if not 0.0 <= value <= 1.0:
            errors.append(f"Latent trait {field} out of range: {value}")

    return (len(errors) == 0, errors)


if __name__ == "__main__":
    import sys

    print("=== Simulation Attributes Generator Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: motor_ability_from_disability
    total_tests += 1
    try:
        if motor_ability_from_disability("nenhuma") != 1.0:
            all_validation_failures.append("motor_ability: 'nenhuma' should be 1.0")
        if motor_ability_from_disability("leve") != 0.8:
            all_validation_failures.append("motor_ability: 'leve' should be 0.8")
        if motor_ability_from_disability("moderada") != 0.5:
            all_validation_failures.append("motor_ability: 'moderada' should be 0.5")
        if motor_ability_from_disability("severa") != 0.2:
            all_validation_failures.append("motor_ability: 'severa' should be 0.2")
        if motor_ability_from_disability("unknown") != 1.0:
            all_validation_failures.append("motor_ability: unknown should default to 1.0")
        print("Test 1 PASSED: motor_ability_from_disability")
    except Exception as e:
        all_validation_failures.append(f"motor_ability_from_disability failed: {e}")

    # Test 2: digital_literacy_to_alfabetizacao_digital
    total_tests += 1
    try:
        if digital_literacy_to_alfabetizacao_digital(0.0) != 0:
            all_validation_failures.append("dl_to_ad: 0.0 should be 0")
        if digital_literacy_to_alfabetizacao_digital(1.0) != 100:
            all_validation_failures.append("dl_to_ad: 1.0 should be 100")
        if digital_literacy_to_alfabetizacao_digital(0.35) != 35:
            all_validation_failures.append("dl_to_ad: 0.35 should be 35")
        if digital_literacy_to_alfabetizacao_digital(0.857) != 86:
            all_validation_failures.append("dl_to_ad: 0.857 should round to 86")
        print("Test 2 PASSED: digital_literacy_to_alfabetizacao_digital")
    except Exception as e:
        all_validation_failures.append(f"digital_literacy_to_alfabetizacao_digital failed: {e}")

    # Test 3: generate_observables with seed
    total_tests += 1
    try:
        rng = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "nenhuma"}}
        obs = generate_observables(rng, deficiencias)

        # All values should be in [0, 1]
        for field, value in obs.model_dump().items():
            if not 0.0 <= value <= 1.0:
                all_validation_failures.append(f"Observable {field} out of range: {value}")

        if obs.motor_ability != 1.0:
            all_validation_failures.append(
                f"motor_ability should be 1.0 for 'nenhuma': {obs.motor_ability}"
            )
        print(f"Test 3 PASSED: generate_observables (digital_literacy={obs.digital_literacy:.3f})")
    except Exception as e:
        all_validation_failures.append(f"generate_observables failed: {e}")

    # Test 4: generate_observables with motor disability
    total_tests += 1
    try:
        rng = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "severa"}}
        obs = generate_observables(rng, deficiencias)

        if obs.motor_ability != 0.2:
            all_validation_failures.append(
                f"motor_ability should be 0.2 for 'severa': {obs.motor_ability}"
            )
        print(f"Test 4 PASSED: motor_ability with disability (value={obs.motor_ability})")
    except Exception as e:
        all_validation_failures.append(f"generate_observables with disability failed: {e}")

    # Test 5: derive_latent_traits formulas
    total_tests += 1
    try:
        # Use known values for testing formula correctness
        obs = SimulationObservables(
            digital_literacy=0.5,
            similar_tool_experience=0.5,
            motor_ability=1.0,
            time_availability=0.5,
            domain_expertise=0.5,
        )
        traits = derive_latent_traits(obs)

        # capability_mean = 0.40*0.5 + 0.35*0.5 + 0.15*1.0 + 0.10*0.5 = 0.575
        expected_capability = 0.575
        if abs(traits.capability_mean - expected_capability) > 0.001:
            all_validation_failures.append(
                f"capability_mean mismatch: expected {expected_capability}, got {traits.capability_mean}"
            )

        # trust_mean = 0.60*0.5 + 0.40*0.5 = 0.5
        expected_trust = 0.5
        if abs(traits.trust_mean - expected_trust) > 0.001:
            all_validation_failures.append(
                f"trust_mean mismatch: expected {expected_trust}, got {traits.trust_mean}"
            )

        # friction_tolerance_mean = 0.40*0.5 + 0.35*0.5 + 0.25*0.5 = 0.5
        expected_friction = 0.5
        if abs(traits.friction_tolerance_mean - expected_friction) > 0.001:
            all_validation_failures.append(
                f"friction_tolerance mismatch: expected {expected_friction}, got {traits.friction_tolerance_mean}"
            )

        # exploration_prob = 0.50*0.5 + 0.30*(1-0.5) + 0.20*0.5 = 0.25 + 0.15 + 0.1 = 0.5
        expected_exploration = 0.5
        if abs(traits.exploration_prob - expected_exploration) > 0.001:
            all_validation_failures.append(
                f"exploration_prob mismatch: expected {expected_exploration}, got {traits.exploration_prob}"
            )

        print("Test 5 PASSED: derive_latent_traits formulas correct")
    except Exception as e:
        all_validation_failures.append(f"derive_latent_traits failed: {e}")

    # Test 6: generate_simulation_attributes complete flow
    total_tests += 1
    try:
        rng = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "leve"}}
        attrs = generate_simulation_attributes(rng, deficiencias)

        # Validate all fields
        is_valid, errors = validate_simulation_attributes(attrs)
        if not is_valid:
            all_validation_failures.extend(errors)
        else:
            print(f"Test 6 PASSED: generate_simulation_attributes (9 attributes valid)")
    except Exception as e:
        all_validation_failures.append(f"generate_simulation_attributes failed: {e}")

    # Test 7: Reproducibility with same seed
    total_tests += 1
    try:
        rng1 = np.random.default_rng(seed=42)
        rng2 = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "nenhuma"}}

        attrs1 = generate_simulation_attributes(rng1, deficiencias)
        attrs2 = generate_simulation_attributes(rng2, deficiencias)

        if attrs1.observables.digital_literacy != attrs2.observables.digital_literacy:
            all_validation_failures.append(
                "Reproducibility failed: same seed should produce same values"
            )
        print("Test 7 PASSED: Reproducibility with same seed")
    except Exception as e:
        all_validation_failures.append(f"Reproducibility test failed: {e}")

    # Test 8: Generate many samples to verify Beta distribution behavior
    total_tests += 1
    try:
        rng = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "nenhuma"}}

        samples = []
        for _ in range(100):
            obs = generate_observables(rng, deficiencias)
            samples.append(obs.digital_literacy)

        mean_dl = sum(samples) / len(samples)
        # Beta(2,4) has mean = 2/(2+4) = 0.333
        if not 0.2 <= mean_dl <= 0.5:
            all_validation_failures.append(
                f"Beta distribution check: mean should be ~0.33, got {mean_dl}"
            )
        print(f"Test 8 PASSED: Beta distribution behavior (mean={mean_dl:.3f})")
    except Exception as e:
        all_validation_failures.append(f"Beta distribution test failed: {e}")

    # Final validation result
    print()
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
