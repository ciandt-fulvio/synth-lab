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
- generate_observables_correlated(): Generate observables correlated with demographics

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Spec: specs/022-observable-latent-traits/spec.md (FR-005, FR-006, FR-007)
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

from synth_lab.domain.constants.demographic_factors import (
    DISABILITY_SEVERITY_MAP,
    EDUCATION_FACTOR_MAP,
    FAMILY_PRESSURE_MAP,
    calculate_max_disability_severity,
)
from synth_lab.domain.constants.derivation_weights import DERIVATION_WEIGHTS
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


def _normalize_education(escolaridade: str | None) -> str:
    """
    Normalize education string to match EDUCATION_FACTOR_MAP keys.

    Args:
        escolaridade: Raw education string from synth

    Returns:
        Normalized key for EDUCATION_FACTOR_MAP
    """
    if not escolaridade:
        return "nao_informado"

    # Normalize: lowercase, replace spaces with underscores
    normalized = escolaridade.lower().strip()
    normalized = normalized.replace(" ", "_")
    normalized = normalized.replace("ã", "a").replace("é", "e").replace("í", "i")

    # Direct match first
    if normalized in EDUCATION_FACTOR_MAP:
        return normalized

    # Try partial matches
    if "doutorado" in normalized:
        return "doutorado"
    if "mestrado" in normalized:
        return "mestrado"
    if "pos" in normalized or "especializacao" in normalized:
        return "pos_graduacao"
    if "superior" in normalized:
        if "incompleto" in normalized:
            return "superior_incompleto"
        return "superior"
    if "graduacao" in normalized:
        return "graduacao"
    if "medio" in normalized or "ensino_medio" in normalized:
        if "incompleto" in normalized:
            return "medio_incompleto"
        return "medio"
    if "fundamental" in normalized:
        if "incompleto" in normalized:
            return "fundamental_incompleto"
        return "fundamental"
    if "sem" in normalized or "analfabeto" in normalized:
        return "sem_escolaridade"

    return "nao_informado"


def _normalize_disability(deficiencias: dict[str, Any]) -> str:
    """
    Extract normalized disability key from deficiencias dict.

    Focuses on motor/physical disability for motor_ability calculation.

    Args:
        deficiencias: Disabilities dict

    Returns:
        Normalized key for DISABILITY_SEVERITY_MAP
    """
    if not deficiencias:
        return "nenhuma"

    # Check motor disability first
    motora = deficiencias.get("motora", {})
    motora_tipo = motora.get("tipo", "nenhuma")

    if motora_tipo and motora_tipo != "nenhuma":
        # Map to severity key
        severity_key = f"motora_{motora_tipo.lower()}"
        if severity_key in DISABILITY_SEVERITY_MAP:
            return severity_key
        # Try without prefix
        if motora_tipo.lower() in DISABILITY_SEVERITY_MAP:
            return motora_tipo.lower()

    # Check visual disability (affects digital interaction)
    visual = deficiencias.get("visual", {})
    visual_tipo = visual.get("tipo", "nenhuma")

    if visual_tipo and visual_tipo != "nenhuma":
        severity_key = f"visual_{visual_tipo.lower()}"
        if severity_key in DISABILITY_SEVERITY_MAP:
            return severity_key

    return "nenhuma"


def _normalize_family_composition(composicao_familiar: dict[str, Any] | None) -> str:
    """
    Normalize family composition to match FAMILY_PRESSURE_MAP keys.

    Args:
        composicao_familiar: Family composition dict with 'tipo'

    Returns:
        Normalized key for FAMILY_PRESSURE_MAP
    """
    if not composicao_familiar:
        return "nao_informado"

    tipo = composicao_familiar.get("tipo", "")
    if not tipo:
        return "nao_informado"

    # Normalize
    normalized = tipo.lower().strip()
    normalized = normalized.replace(" ", "_")

    # Direct match
    if normalized in FAMILY_PRESSURE_MAP:
        return normalized

    # Partial matches
    if "unipessoal" in normalized or "sozinho" in normalized:
        return "sozinho"
    if "casal" in normalized:
        if "sem_filhos" in normalized:
            return "casal_sem_filhos"
        if "filhos" in normalized:
            return "filhos_4_12"  # Default assumption
    if "monoparental" in normalized:
        return "mae_solo_filhos_pequenos"  # Conservative estimate
    if "multigeracional" in normalized:
        return "multigeracional"

    return "outro"


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


def generate_observables_correlated(
    rng: Generator,
    deficiencias: dict[str, Any],
    escolaridade: str | None = None,
    composicao_familiar: dict[str, Any] | None = None,
    idade: int | None = None,
) -> SimulationObservables:
    """
    Generate observable attributes correlated with demographics.

    Uses demographic factors to shift Beta distribution parameters,
    producing values that correlate with education level, disability
    status, family composition, and age.

    Args:
        rng: NumPy random generator for reproducibility
        deficiencias: Disabilities dict with 'motora.tipo', 'visual.tipo'
        escolaridade: Education level string (e.g., 'Superior completo')
        composicao_familiar: Family composition dict with 'tipo'
        idade: Age in years (affects time_availability)

    Returns:
        SimulationObservables with all fields in [0, 1]

    Notes:
        - digital_literacy: Shifts right with higher education
        - motor_ability: Derived from disability severity and age
          Formula: max(0.1, (1.0 - disability_severity) - (0.2 * age_motor_factor))
          age_motor_factor: <30 -> 0.0, 30-60 -> 0.3, >60 -> 0.6
        - time_availability: Shifts left with higher family pressure, adjusted by age
        - similar_tool_experience: Correlation with education
        - domain_expertise: Base Beta distribution (no shift)

    Example:
        >>> rng = np.random.default_rng(42)
        >>> deficiencias = {"motora": {"tipo": "nenhuma"}}
        >>> obs = generate_observables_correlated(
        ...     rng, deficiencias,
        ...     escolaridade="Doutorado",
        ...     composicao_familiar={"tipo": "sozinho"},
        ... )
        >>> obs.digital_literacy > 0.5  # Higher with higher education
        True
    """
    # Get education factor (shifts digital_literacy right)
    edu_key = _normalize_education(escolaridade)
    edu_factor = EDUCATION_FACTOR_MAP.get(edu_key, 0.5)

    # Get max disability severity across all disability types (affects motor_ability)
    # Returns 0.8 if any disability is 'severa', 'cegueira', or 'surdez'
    disability_severity = calculate_max_disability_severity(deficiencias)

    # Get family pressure (affects time_availability)
    family_key = _normalize_family_composition(composicao_familiar)
    family_pressure = FAMILY_PRESSURE_MAP.get(family_key, 0.3)

    # Age factor for time_availability (elderly have more time, young parents less)
    age_time_factor = 0.5  # Default neutral
    if idade is not None:
        if idade < 30:
            age_time_factor = 0.4  # Less time (building career)
        elif idade > 60:
            age_time_factor = 0.7  # More time (retired or less obligations)
        else:
            age_time_factor = 0.5  # Middle ground

    # Age factor for motor_ability (older = reduced motor ability)
    age_motor_factor = 0.0  # Default: young, no reduction
    if idade is not None:
        if idade < 30:
            age_motor_factor = 0.0  # Young: no reduction
        elif idade <= 60:
            age_motor_factor = 0.3  # Middle age: slight reduction
        else:
            age_motor_factor = 0.6  # Elderly: more reduction

    # Generate digital_literacy with education-shifted Beta
    # Higher education -> shift alpha up (more probability toward 1)
    dl_alpha = 2 + edu_factor * 3  # Range: 2-5
    dl_beta = 4 - edu_factor * 2  # Range: 2-4
    digital_literacy = float(rng.beta(dl_alpha, max(1.5, dl_beta)))

    # Generate similar_tool_experience (correlated with education too)
    exp_alpha = 2 + edu_factor * 2  # Range: 2-4
    exp_beta = 3
    similar_tool_experience = float(rng.beta(exp_alpha, exp_beta))

    # Calculate motor_ability from disability and age
    # Formula: max(0.1, (1.0 - disability_severity) - (0.2 * age_motor_factor))
    motor_ability = max(0.1, (1.0 - disability_severity) - (0.2 * age_motor_factor))

    # Generate time_availability (inversely related to family pressure)
    # Higher pressure -> lower time availability
    time_alpha = 2 + (1 - family_pressure) * 2 + age_time_factor  # Range: 2-5
    time_beta = 3 + family_pressure * 2  # Range: 3-5
    time_availability = float(rng.beta(time_alpha, time_beta))

    # Generate domain_expertise (neutral, uncorrelated)
    domain_expertise = float(rng.beta(3, 3))

    # Ensure all values are in [0, 1]
    digital_literacy = max(0.0, min(1.0, digital_literacy))
    similar_tool_experience = max(0.0, min(1.0, similar_tool_experience))
    motor_ability = max(0.0, min(1.0, motor_ability))
    time_availability = max(0.0, min(1.0, time_availability))
    domain_expertise = max(0.0, min(1.0, domain_expertise))

    return SimulationObservables(
        digital_literacy=digital_literacy,
        similar_tool_experience=similar_tool_experience,
        motor_ability=motor_ability,
        time_availability=time_availability,
        domain_expertise=domain_expertise,
    )


def derive_latent_traits(observables: SimulationObservables) -> SimulationLatentTraits:
    """
    Derive latent traits from observable attributes using documented formulas.

    This function transforms the 5 observable attributes into 4 latent traits
    that drive Monte Carlo simulation behavior. The derivation uses weighted
    sums where weights are defined in DERIVATION_WEIGHTS.

    Args:
        observables: Observable attributes (digital_literacy, similar_tool_experience,
                     motor_ability, time_availability, domain_expertise)

    Returns:
        SimulationLatentTraits with all fields in [0, 1]

    Derivation Formulas:
        Each latent trait is a weighted sum of observables. All weights sum to 1.0
        to ensure output remains in [0, 1] when inputs are in [0, 1].

        1. CAPABILITY_MEAN: User's ability to successfully complete digital tasks
           Formula: 0.40*dl + 0.35*exp + 0.15*motor + 0.10*domain
           - digital_literacy (0.40): Primary driver - tech skills directly affect success
           - similar_tool_experience (0.35): Prior experience with similar tools
           - motor_ability (0.15): Physical ability affects interaction speed/accuracy
           - domain_expertise (0.10): Domain knowledge helps context understanding

        2. TRUST_MEAN: User's trust in digital systems and willingness to rely on them
           Formula: 0.60*exp + 0.40*dl
           - similar_tool_experience (0.60): Past success builds trust in similar tools
           - digital_literacy (0.40): Understanding technology reduces fear

        3. FRICTION_TOLERANCE_MEAN: User's patience with obstacles and errors
           Formula: 0.40*time + 0.35*dl + 0.25*exp
           - time_availability (0.40): More time = more patience for friction
           - digital_literacy (0.35): Tech-savvy users understand errors better
           - similar_tool_experience (0.25): Experience calibrates expectations

        4. EXPLORATION_PROB: Probability user will try new features/approaches
           Formula: 0.50*dl + 0.30*(1-exp) + 0.20*time
           - digital_literacy (0.50): Tech-savvy users explore more
           - novelty_preference (0.30): Less experience = more novelty seeking
             Note: Uses (1 - exp) because users without established habits
             are more willing to try new approaches
           - time_availability (0.20): More time = more exploration

    Example:
        >>> obs = SimulationObservables(
        ...     digital_literacy=0.5,
        ...     similar_tool_experience=0.5,
        ...     motor_ability=1.0,
        ...     time_availability=0.5,
        ...     domain_expertise=0.5,
        ... )
        >>> traits = derive_latent_traits(obs)
        >>> traits.capability_mean  # 0.40*0.5 + 0.35*0.5 + 0.15*1.0 + 0.10*0.5 = 0.575
        0.575

    References:
        - Weights defined in: synth_lab/domain/constants/derivation_weights.py
        - Spec: specs/022-observable-latent-traits/spec.md (FR-007)
    """
    # Extract observable values for readability
    dl = observables.digital_literacy
    exp = observables.similar_tool_experience
    motor = observables.motor_ability
    time = observables.time_availability
    domain = observables.domain_expertise

    # Get weights from centralized constants
    cap_w = DERIVATION_WEIGHTS["capability_mean"]
    trust_w = DERIVATION_WEIGHTS["trust_mean"]
    friction_w = DERIVATION_WEIGHTS["friction_tolerance_mean"]
    explore_w = DERIVATION_WEIGHTS["exploration_prob"]

    # =========================================================================
    # CAPABILITY_MEAN: User's ability to complete digital tasks
    # =========================================================================
    # Weighted sum: digital_literacy contributes most (40%), followed by
    # similar_tool_experience (35%), motor_ability (15%), domain_expertise (10%)
    capability_mean = (
        cap_w["digital_literacy"] * dl
        + cap_w["similar_tool_experience"] * exp
        + cap_w["motor_ability"] * motor
        + cap_w["domain_expertise"] * domain
    )

    # =========================================================================
    # TRUST_MEAN: User's trust in digital systems
    # =========================================================================
    # Past success with similar tools (60%) is the primary trust builder.
    # Digital literacy (40%) helps users understand what the system is doing.
    trust_mean = trust_w["similar_tool_experience"] * exp + trust_w["digital_literacy"] * dl

    # =========================================================================
    # FRICTION_TOLERANCE_MEAN: User's patience with obstacles
    # =========================================================================
    # Time availability (40%) is key - busy users abandon frustrated tasks.
    # Digital literacy (35%) helps users recover from errors independently.
    # Experience (25%) sets realistic expectations about friction.
    friction_tolerance_mean = (
        friction_w["time_availability"] * time
        + friction_w["digital_literacy"] * dl
        + friction_w["similar_tool_experience"] * exp
    )

    # =========================================================================
    # EXPLORATION_PROB: Probability of trying new features
    # =========================================================================
    # Digital literacy (50%) is the main driver - tech-savvy users explore more.
    # Novelty preference (30%) uses INVERSE of experience: users without
    # established habits are more willing to try new approaches.
    # Time availability (20%) allows exploration when user isn't rushed.
    novelty_preference = 1.0 - exp  # Less experience = more novelty seeking
    exploration_prob = (
        explore_w["digital_literacy"] * dl
        + explore_w["novelty_preference"] * novelty_preference
        + explore_w["time_availability"] * time
    )

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
            actual = traits.capability_mean
            all_validation_failures.append(
                f"capability_mean mismatch: expected {expected_capability}, got {actual}"
            )

        # trust_mean = 0.60*0.5 + 0.40*0.5 = 0.5
        expected_trust = 0.5
        if abs(traits.trust_mean - expected_trust) > 0.001:
            all_validation_failures.append(
                f"trust_mean: expected {expected_trust}, got {traits.trust_mean}"
            )

        # friction_tolerance_mean = 0.40*0.5 + 0.35*0.5 + 0.25*0.5 = 0.5
        expected_friction = 0.5
        if abs(traits.friction_tolerance_mean - expected_friction) > 0.001:
            actual = traits.friction_tolerance_mean
            all_validation_failures.append(
                f"friction_tolerance mismatch: expected {expected_friction}, got {actual}"
            )

        # exploration_prob = 0.50*0.5 + 0.30*(1-0.5) + 0.20*0.5 = 0.5
        expected_exploration = 0.5
        if abs(traits.exploration_prob - expected_exploration) > 0.001:
            actual = traits.exploration_prob
            all_validation_failures.append(
                f"exploration_prob mismatch: expected {expected_exploration}, got {actual}"
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
            print("Test 6 PASSED: generate_simulation_attributes (9 attributes valid)")
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

    # Test 9: _normalize_education
    total_tests += 1
    try:
        assert _normalize_education("Doutorado") == "doutorado"
        assert _normalize_education("Superior completo") == "superior_completo"
        assert _normalize_education("Superior") == "superior"
        assert _normalize_education("Ensino Médio") == "ensino_medio"
        assert _normalize_education("Médio completo") == "medio_completo"
        assert _normalize_education("Fundamental incompleto") == "fundamental_incompleto"
        assert _normalize_education(None) == "nao_informado"
        assert _normalize_education("") == "nao_informado"
        print("Test 9 PASSED: _normalize_education")
    except AssertionError as e:
        all_validation_failures.append(f"_normalize_education failed: {e}")
    except Exception as e:
        all_validation_failures.append(f"_normalize_education error: {e}")

    # Test 10: _normalize_disability
    total_tests += 1
    try:
        assert _normalize_disability({"motora": {"tipo": "severa"}}) == "motora_severa"
        assert _normalize_disability({"visual": {"tipo": "leve"}}) == "visual_leve"
        assert _normalize_disability({}) == "nenhuma"
        assert _normalize_disability(None) == "nenhuma"
        print("Test 10 PASSED: _normalize_disability")
    except AssertionError as e:
        all_validation_failures.append(f"_normalize_disability failed: {e}")
    except Exception as e:
        all_validation_failures.append(f"_normalize_disability error: {e}")

    # Test 11: _normalize_family_composition
    total_tests += 1
    try:
        assert _normalize_family_composition({"tipo": "sozinho"}) == "sozinho"
        assert _normalize_family_composition({"tipo": "casal sem filhos"}) == "casal_sem_filhos"
        assert _normalize_family_composition(None) == "nao_informado"
        print("Test 11 PASSED: _normalize_family_composition")
    except AssertionError as e:
        all_validation_failures.append(f"_normalize_family_composition failed: {e}")
    except Exception as e:
        all_validation_failures.append(f"_normalize_family_composition error: {e}")

    # Test 12: generate_observables_correlated - high education
    total_tests += 1
    try:
        rng = np.random.default_rng(seed=42)
        deficiencias = {"motora": {"tipo": "nenhuma"}}

        # Generate 50 samples with high education
        high_edu_samples = []
        for _ in range(50):
            obs = generate_observables_correlated(rng, deficiencias, escolaridade="Doutorado")
            high_edu_samples.append(obs.digital_literacy)

        # Generate 50 samples with low education
        rng = np.random.default_rng(seed=42)
        low_edu_samples = []
        for _ in range(50):
            obs = generate_observables_correlated(rng, deficiencias, escolaridade="Fundamental")
            low_edu_samples.append(obs.digital_literacy)

        mean_high = sum(high_edu_samples) / len(high_edu_samples)
        mean_low = sum(low_edu_samples) / len(low_edu_samples)

        if mean_high <= mean_low:
            all_validation_failures.append(
                f"High education should have higher digital_literacy: "
                f"high={mean_high:.3f}, low={mean_low:.3f}"
            )
        print(
            f"Test 12 PASSED: generate_observables_correlated education effect "
            f"(high={mean_high:.3f}, low={mean_low:.3f})"
        )
    except Exception as e:
        all_validation_failures.append(
            f"generate_observables_correlated education test failed: {e}"
        )

    # Test 13: generate_observables_correlated - motor disability
    total_tests += 1
    try:
        rng = np.random.default_rng(seed=42)

        # No disability
        obs_no_disability = generate_observables_correlated(rng, {"motora": {"tipo": "nenhuma"}})

        # Severe disability
        obs_severe = generate_observables_correlated(rng, {"motora": {"tipo": "severa"}})

        if obs_no_disability.motor_ability <= obs_severe.motor_ability:
            all_validation_failures.append(
                f"No disability should have higher motor_ability: "
                f"no={obs_no_disability.motor_ability:.3f}, "
                f"severe={obs_severe.motor_ability:.3f}"
            )
        print(
            f"Test 13 PASSED: generate_observables_correlated disability effect "
            f"(no_disability={obs_no_disability.motor_ability:.3f}, "
            f"severe={obs_severe.motor_ability:.3f})"
        )
    except Exception as e:
        all_validation_failures.append(
            f"generate_observables_correlated disability test failed: {e}"
        )

    # Test 14: generate_observables_correlated - family pressure
    total_tests += 1
    try:
        rng = np.random.default_rng(seed=42)
        deficiencias = {}

        # Low pressure (sozinho)
        low_pressure_samples = []
        for _ in range(30):
            obs = generate_observables_correlated(
                rng, deficiencias, composicao_familiar={"tipo": "sozinho"}
            )
            low_pressure_samples.append(obs.time_availability)

        # High pressure (mae_solo_filhos_pequenos)
        rng = np.random.default_rng(seed=42)
        high_pressure_samples = []
        for _ in range(30):
            obs = generate_observables_correlated(
                rng, deficiencias, composicao_familiar={"tipo": "monoparental"}
            )
            high_pressure_samples.append(obs.time_availability)

        mean_low = sum(low_pressure_samples) / len(low_pressure_samples)
        mean_high = sum(high_pressure_samples) / len(high_pressure_samples)

        if mean_low <= mean_high:
            all_validation_failures.append(
                f"Low family pressure should have higher time_availability: "
                f"low_pressure={mean_low:.3f}, high_pressure={mean_high:.3f}"
            )
        print(
            f"Test 14 PASSED: generate_observables_correlated family pressure effect "
            f"(low_pressure={mean_low:.3f}, high_pressure={mean_high:.3f})"
        )
    except Exception as e:
        all_validation_failures.append(
            f"generate_observables_correlated family pressure test failed: {e}"
        )

    # Test 15 [T050]: derive_latent_traits with various known values
    total_tests += 1
    try:
        # Test with extreme values (all zeros)
        obs_zeros = SimulationObservables(
            digital_literacy=0.0,
            similar_tool_experience=0.0,
            motor_ability=0.0,
            time_availability=0.0,
            domain_expertise=0.0,
        )
        traits_zeros = derive_latent_traits(obs_zeros)

        # All zeros should produce specific values based on formulas
        # capability = 0.40*0 + 0.35*0 + 0.15*0 + 0.10*0 = 0
        if traits_zeros.capability_mean != 0.0:
            all_validation_failures.append(
                f"T050: All-zeros capability_mean should be 0.0, got {traits_zeros.capability_mean}"
            )
        # trust = 0.60*0 + 0.40*0 = 0
        if traits_zeros.trust_mean != 0.0:
            all_validation_failures.append(
                f"T050: All-zeros trust_mean should be 0.0, got {traits_zeros.trust_mean}"
            )
        # friction = 0.40*0 + 0.35*0 + 0.25*0 = 0
        if traits_zeros.friction_tolerance_mean != 0.0:
            actual = traits_zeros.friction_tolerance_mean
            all_validation_failures.append(
                f"T050: All-zeros friction_tolerance should be 0.0, got {actual}"
            )
        # exploration = 0.50*0 + 0.30*(1-0) + 0.20*0 = 0.30
        if abs(traits_zeros.exploration_prob - 0.30) > 0.001:
            actual = traits_zeros.exploration_prob
            all_validation_failures.append(
                f"T050: All-zeros exploration_prob should be 0.30, got {actual}"
            )

        # Test with all ones
        obs_ones = SimulationObservables(
            digital_literacy=1.0,
            similar_tool_experience=1.0,
            motor_ability=1.0,
            time_availability=1.0,
            domain_expertise=1.0,
        )
        traits_ones = derive_latent_traits(obs_ones)

        # capability = 0.40*1 + 0.35*1 + 0.15*1 + 0.10*1 = 1.0
        if abs(traits_ones.capability_mean - 1.0) > 0.001:
            all_validation_failures.append(
                f"T050: All-ones capability_mean should be 1.0, got {traits_ones.capability_mean}"
            )
        # trust = 0.60*1 + 0.40*1 = 1.0
        if abs(traits_ones.trust_mean - 1.0) > 0.001:
            all_validation_failures.append(
                f"T050: All-ones trust_mean should be 1.0, got {traits_ones.trust_mean}"
            )
        # friction = 0.40*1 + 0.35*1 + 0.25*1 = 1.0
        if abs(traits_ones.friction_tolerance_mean - 1.0) > 0.001:
            actual = traits_ones.friction_tolerance_mean
            all_validation_failures.append(
                f"T050: All-ones friction_tolerance should be 1.0, got {actual}"
            )
        # exploration = 0.50*1 + 0.30*(1-1) + 0.20*1 = 0.70
        if abs(traits_ones.exploration_prob - 0.70) > 0.001:
            actual = traits_ones.exploration_prob
            all_validation_failures.append(
                f"T050: All-ones exploration_prob should be 0.70, got {actual}"
            )

        print("Test 15 PASSED: derive_latent_traits with extreme values [T050]")
    except Exception as e:
        all_validation_failures.append(f"T050 derive_latent_traits extreme values test failed: {e}")

    # Test 16 [T051]: Verify formulas match DERIVATION_WEIGHTS constants
    total_tests += 1
    try:
        # Verify each weight individually by setting only one observable to 1.0
        # This tests that the weights are correctly applied

        # Test digital_literacy weight in capability_mean
        obs_dl_only = SimulationObservables(
            digital_literacy=1.0,
            similar_tool_experience=0.0,
            motor_ability=0.0,
            time_availability=0.0,
            domain_expertise=0.0,
        )
        traits_dl = derive_latent_traits(obs_dl_only)
        expected_cap_dl = DERIVATION_WEIGHTS["capability_mean"]["digital_literacy"]
        if abs(traits_dl.capability_mean - expected_cap_dl) > 0.001:
            all_validation_failures.append(
                f"T051: capability_mean with only dl=1 should be {expected_cap_dl}, "
                f"got {traits_dl.capability_mean}"
            )

        # Test similar_tool_experience weight in trust_mean
        obs_exp_only = SimulationObservables(
            digital_literacy=0.0,
            similar_tool_experience=1.0,
            motor_ability=0.0,
            time_availability=0.0,
            domain_expertise=0.0,
        )
        traits_exp = derive_latent_traits(obs_exp_only)
        expected_trust_exp = DERIVATION_WEIGHTS["trust_mean"]["similar_tool_experience"]
        if abs(traits_exp.trust_mean - expected_trust_exp) > 0.001:
            all_validation_failures.append(
                f"T051: trust_mean with only exp=1 should be {expected_trust_exp}, "
                f"got {traits_exp.trust_mean}"
            )

        # Test time_availability weight in friction_tolerance_mean
        obs_time_only = SimulationObservables(
            digital_literacy=0.0,
            similar_tool_experience=0.0,
            motor_ability=0.0,
            time_availability=1.0,
            domain_expertise=0.0,
        )
        traits_time = derive_latent_traits(obs_time_only)
        expected_ft = DERIVATION_WEIGHTS["friction_tolerance_mean"]["time_availability"]
        actual_ft = traits_time.friction_tolerance_mean
        if abs(actual_ft - expected_ft) > 0.001:
            all_validation_failures.append(
                f"T051: friction_tolerance with time=1: expected {expected_ft}, got {actual_ft}"
            )

        # Verify weight sums = 1.0 for each trait (from DERIVATION_WEIGHTS)
        for trait_name, weights in DERIVATION_WEIGHTS.items():
            weight_sum = sum(weights.values())
            if abs(weight_sum - 1.0) > 0.001:
                all_validation_failures.append(
                    f"T051: {trait_name} weights should sum to 1.0, got {weight_sum}"
                )

        print("Test 16 PASSED: Formulas match DERIVATION_WEIGHTS [T051]")
    except Exception as e:
        all_validation_failures.append(f"T051 formula verification test failed: {e}")

    # Test 17 [US5]: Verify exploration_prob novelty preference calculation
    total_tests += 1
    try:
        # High experience should mean LOW exploration (established habits)
        obs_high_exp = SimulationObservables(
            digital_literacy=0.5,
            similar_tool_experience=1.0,  # Very experienced
            motor_ability=1.0,
            time_availability=0.5,
            domain_expertise=0.5,
        )
        traits_high_exp = derive_latent_traits(obs_high_exp)

        # Low experience should mean HIGH exploration (novelty seeking)
        obs_low_exp = SimulationObservables(
            digital_literacy=0.5,
            similar_tool_experience=0.0,  # No experience
            motor_ability=1.0,
            time_availability=0.5,
            domain_expertise=0.5,
        )
        traits_low_exp = derive_latent_traits(obs_low_exp)

        # Low experience should have HIGHER exploration probability
        if traits_low_exp.exploration_prob <= traits_high_exp.exploration_prob:
            all_validation_failures.append(
                f"US5: Low experience should have higher exploration_prob: "
                f"low_exp={traits_low_exp.exploration_prob:.3f}, "
                f"high_exp={traits_high_exp.exploration_prob:.3f}"
            )

        # Verify the exact difference is 0.30 (novelty_preference weight)
        expected_diff = DERIVATION_WEIGHTS["exploration_prob"]["novelty_preference"]
        actual_diff = traits_low_exp.exploration_prob - traits_high_exp.exploration_prob
        if abs(actual_diff - expected_diff) > 0.001:
            all_validation_failures.append(
                f"US5: Exploration difference should be {expected_diff}, got {actual_diff}"
            )

        print(
            f"Test 17 PASSED: Novelty preference calculation "
            f"(low_exp={traits_low_exp.exploration_prob:.3f}, "
            f"high_exp={traits_high_exp.exploration_prob:.3f})"
        )
    except Exception as e:
        all_validation_failures.append(f"US5 novelty preference test failed: {e}")

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
