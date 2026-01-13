"""
Group configuration defaults for synth-lab.

Contains IBGE-based default distributions for demographic attributes
used in synth group creation. Also includes education level expansion
ratios for converting 4-level UI selections to 8-level internal representation.

References:
    - Spec: specs/030-custom-synth-groups/spec.md
    - Data model: specs/030-custom-synth-groups/data-model.md
"""

from typing import TypedDict


# Type definitions for group configuration
class IdadeDistribution(TypedDict):
    """Age distribution weights (must sum to 1.0)."""

    faixa_15_29: float  # 15-29 years
    faixa_30_44: float  # 30-44 years
    faixa_45_59: float  # 45-59 years
    faixa_60_plus: float  # 60+ years


class EscolaridadeDistribution(TypedDict):
    """Education distribution weights (must sum to 1.0)."""

    sem_instrucao: float
    fundamental: float  # Will be expanded to incompleto/completo
    medio: float  # Will be expanded to incompleto/completo
    superior: float  # Will be expanded to incompleto/completo/pos


class SeveridadeDistribution(TypedDict):
    """Disability severity distribution weights (must sum to 1.0)."""

    nenhuma: float
    leve: float
    moderada: float
    severa: float
    total: float


class DeficienciasConfig(TypedDict):
    """Disability configuration."""

    taxa_com_deficiencia: float  # 0.0 to 1.0
    distribuicao_severidade: SeveridadeDistribution


class ComposicaoFamiliarDistribution(TypedDict):
    """Family composition distribution weights (must sum to 1.0)."""

    unipessoal: float
    casal_sem_filhos: float
    casal_com_filhos: float
    monoparental: float
    multigeracional: float


class DomainExpertiseConfig(TypedDict):
    """Beta distribution parameters for domain expertise."""

    alpha: float  # Shape parameter (> 0)
    beta: float  # Shape parameter (> 0)


class GroupDistributions(TypedDict):
    """All distribution configurations."""

    idade: dict[str, float]
    escolaridade: dict[str, float]
    deficiencias: DeficienciasConfig
    composicao_familiar: dict[str, float]
    domain_expertise: DomainExpertiseConfig


class GroupConfig(TypedDict):
    """Complete group configuration."""

    n_synths: int
    distributions: GroupDistributions


# =============================================================================
# IBGE Default Values
# =============================================================================

# Default age distribution based on IBGE 2022 Census
DEFAULT_IDADE_DISTRIBUTION: dict[str, float] = {
    "15-29": 0.26,
    "30-44": 0.27,
    "45-59": 0.24,
    "60+": 0.23,
}

# Default education distribution based on IBGE 2022 Census
DEFAULT_ESCOLARIDADE_DISTRIBUTION: dict[str, float] = {
    "sem_instrucao": 0.068,
    "fundamental": 0.329,
    "medio": 0.314,
    "superior": 0.289,
}

# Default severity distribution (uniform)
DEFAULT_SEVERIDADE_DISTRIBUTION: SeveridadeDistribution = {
    "nenhuma": 0.20,
    "leve": 0.20,
    "moderada": 0.20,
    "severa": 0.20,
    "total": 0.20,
}

# Default disability configuration (IBGE rate: 8.4%)
DEFAULT_DEFICIENCIAS_CONFIG: DeficienciasConfig = {
    "taxa_com_deficiencia": 0.084,
    "distribuicao_severidade": DEFAULT_SEVERIDADE_DISTRIBUTION,
}

# Default family composition based on IBGE 2022 Census
DEFAULT_COMPOSICAO_FAMILIAR_DISTRIBUTION: dict[str, float] = {
    "unipessoal": 0.15,
    "casal_sem_filhos": 0.20,
    "casal_com_filhos": 0.35,
    "monoparental": 0.18,
    "multigeracional": 0.12,
}

# Default domain expertise (regular distribution)
DEFAULT_DOMAIN_EXPERTISE_CONFIG: DomainExpertiseConfig = {
    "alpha": 3.0,
    "beta": 3.0,
}

# Complete default group configuration
DEFAULT_GROUP_CONFIG: GroupConfig = {
    "n_synths": 500,
    "distributions": {
        "idade": DEFAULT_IDADE_DISTRIBUTION,
        "escolaridade": DEFAULT_ESCOLARIDADE_DISTRIBUTION,
        "deficiencias": DEFAULT_DEFICIENCIAS_CONFIG,
        "composicao_familiar": DEFAULT_COMPOSICAO_FAMILIAR_DISTRIBUTION,
        "domain_expertise": DEFAULT_DOMAIN_EXPERTISE_CONFIG,
    },
}


# =============================================================================
# Education Level Expansion Ratios
# =============================================================================

# Ratios for expanding 4-level UI education to 8-level display representation
# Based on IBGE 2022 Census data
# Keys use display names to match ibge_distributions.json format
ESCOLARIDADE_EXPANSION_RATIOS: dict[str, dict[str, float]] = {
    # "Fundamental" expands to incomplete/complete
    "fundamental": {
        "Fundamental incompleto": 0.763,  # 76.3%
        "Fundamental completo": 0.237,  # 23.7%
    },
    # "Médio" expands to incomplete/complete
    "medio": {
        "Médio incompleto": 0.134,  # 13.4%
        "Médio completo": 0.866,  # 86.6%
    },
    # "Superior" expands to incomplete/complete/pos_graduacao
    "superior": {
        "Superior incompleto": 0.183,  # 18.3%
        "Superior completo": 0.606,  # 60.6%
        "Pós-graduação": 0.211,  # 21.1%
    },
}


# =============================================================================
# Domain Expertise Presets
# =============================================================================

# Preset configurations for domain expertise levels
DOMAIN_EXPERTISE_PRESETS: dict[str, DomainExpertiseConfig] = {
    "baixo": {"alpha": 2.0, "beta": 5.0},  # Mean ~0.29
    "regular": {"alpha": 3.0, "beta": 3.0},  # Mean ~0.50
    "alto": {"alpha": 5.0, "beta": 2.0},  # Mean ~0.71
}

# Disability rate threshold for severity distribution switching
# Below this rate: uniform distribution
# Above this rate: weighted toward severe
DISABILITY_RATE_THRESHOLD = 0.08

# Weighted severity distribution (used when rate > threshold)
WEIGHTED_SEVERIDADE_DISTRIBUTION: SeveridadeDistribution = {
    "nenhuma": 0.0,
    "leve": 0.10,
    "moderada": 0.25,
    "severa": 0.30,
    "total": 0.35,
}


def expand_education_distribution(
    four_level_dist: dict[str, float],
) -> dict[str, float]:
    """
    Expand 4-level UI education distribution to 8-level display representation.

    Args:
        four_level_dist: Distribution with keys: sem_instrucao, fundamental, medio, superior

    Returns:
        Distribution with display keys matching ibge_distributions.json format:
        "Sem instrução", "Fundamental incompleto", "Fundamental completo",
        "Médio incompleto", "Médio completo", "Superior incompleto",
        "Superior completo", "Pós-graduação"
    """
    result: dict[str, float] = {}

    # sem_instrucao passes through with display name
    result["Sem instrução"] = four_level_dist.get("sem_instrucao", 0.0)

    # Expand fundamental
    fundamental_total = four_level_dist.get("fundamental", 0.0)
    for sub_level, ratio in ESCOLARIDADE_EXPANSION_RATIOS["fundamental"].items():
        result[sub_level] = fundamental_total * ratio

    # Expand medio
    medio_total = four_level_dist.get("medio", 0.0)
    for sub_level, ratio in ESCOLARIDADE_EXPANSION_RATIOS["medio"].items():
        result[sub_level] = medio_total * ratio

    # Expand superior
    superior_total = four_level_dist.get("superior", 0.0)
    for sub_level, ratio in ESCOLARIDADE_EXPANSION_RATIOS["superior"].items():
        result[sub_level] = superior_total * ratio

    return result


def get_severity_distribution_for_rate(rate: float) -> SeveridadeDistribution:
    """
    Get the appropriate severity distribution based on disability rate.

    Args:
        rate: Disability rate (0.0 to 1.0)

    Returns:
        Severity distribution dict (uniform if rate <= 8%, weighted if > 8%)
    """
    if rate <= DISABILITY_RATE_THRESHOLD:
        return DEFAULT_SEVERIDADE_DISTRIBUTION.copy()
    return WEIGHTED_SEVERIDADE_DISTRIBUTION.copy()


# Mapping from internal keys (underscores) to display names (spaces)
COMPOSICAO_FAMILIAR_KEY_MAP: dict[str, str] = {
    "unipessoal": "unipessoal",
    "casal_sem_filhos": "casal sem filhos",
    "casal_com_filhos": "casal com filhos",
    "monoparental": "monoparental",
    "multigeracional": "multigeracional",
    "outros": "outros",
}


def normalize_composicao_familiar_distribution(
    internal_dist: dict[str, float],
) -> dict[str, float]:
    """
    Convert family composition distribution from internal keys to display names.

    Args:
        internal_dist: Distribution with internal keys (e.g., "casal_sem_filhos")

    Returns:
        Distribution with display keys matching ibge_distributions.json format
        (e.g., "casal sem filhos")
    """
    result: dict[str, float] = {}
    for key, value in internal_dist.items():
        display_key = COMPOSICAO_FAMILIAR_KEY_MAP.get(key, key)
        result[display_key] = value
    return result


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: Default age distribution sums to 1.0
    total_tests += 1
    idade_sum = sum(DEFAULT_IDADE_DISTRIBUTION.values())
    if abs(idade_sum - 1.0) > 0.01:
        all_validation_failures.append(f"Age distribution sums to {idade_sum}, expected 1.0")

    # Test 2: Default education distribution sums to 1.0
    total_tests += 1
    escolaridade_sum = sum(DEFAULT_ESCOLARIDADE_DISTRIBUTION.values())
    if abs(escolaridade_sum - 1.0) > 0.01:
        all_validation_failures.append(
            f"Education distribution sums to {escolaridade_sum}, expected 1.0"
        )

    # Test 3: Default family composition sums to 1.0
    total_tests += 1
    familia_sum = sum(DEFAULT_COMPOSICAO_FAMILIAR_DISTRIBUTION.values())
    if abs(familia_sum - 1.0) > 0.01:
        all_validation_failures.append(f"Family composition sums to {familia_sum}, expected 1.0")

    # Test 4: Default severity distribution sums to 1.0
    total_tests += 1
    severidade_sum = sum(DEFAULT_SEVERIDADE_DISTRIBUTION.values())
    if abs(severidade_sum - 1.0) > 0.01:
        all_validation_failures.append(
            f"Severity distribution sums to {severidade_sum}, expected 1.0"
        )

    # Test 5: Education expansion preserves total probability
    total_tests += 1
    expanded = expand_education_distribution(DEFAULT_ESCOLARIDADE_DISTRIBUTION)
    expanded_sum = sum(expanded.values())
    if abs(expanded_sum - 1.0) > 0.01:
        all_validation_failures.append(f"Expanded education sums to {expanded_sum}, expected 1.0")

    # Test 6: Education expansion has correct keys (display names)
    total_tests += 1
    expected_keys = {
        "Sem instrução",
        "Fundamental incompleto",
        "Fundamental completo",
        "Médio incompleto",
        "Médio completo",
        "Superior incompleto",
        "Superior completo",
        "Pós-graduação",
    }
    if set(expanded.keys()) != expected_keys:
        all_validation_failures.append(f"Expanded education has wrong keys: {set(expanded.keys())}")

    # Test 7: Expansion ratios sum to 1.0 for each level
    total_tests += 1
    for level, ratios in ESCOLARIDADE_EXPANSION_RATIOS.items():
        ratio_sum = sum(ratios.values())
        if abs(ratio_sum - 1.0) > 0.01:
            all_validation_failures.append(
                f"Expansion ratios for {level} sum to {ratio_sum}, expected 1.0"
            )

    # Test 8: Domain expertise presets have valid alpha/beta
    total_tests += 1
    for name, config in DOMAIN_EXPERTISE_PRESETS.items():
        if config["alpha"] <= 0 or config["beta"] <= 0:
            all_validation_failures.append(f"Preset {name} has invalid alpha/beta: {config}")

    # Test 9: Severity distribution for low rate returns uniform
    total_tests += 1
    low_rate_dist = get_severity_distribution_for_rate(0.05)
    if low_rate_dist != DEFAULT_SEVERIDADE_DISTRIBUTION:
        all_validation_failures.append(
            f"Low rate should return uniform distribution: {low_rate_dist}"
        )

    # Test 10: Severity distribution for high rate returns weighted
    total_tests += 1
    high_rate_dist = get_severity_distribution_for_rate(0.50)
    if high_rate_dist["total"] != 0.35:
        all_validation_failures.append(
            f"High rate should return weighted distribution: {high_rate_dist}"
        )

    # Test 11: DEFAULT_GROUP_CONFIG has all required keys
    total_tests += 1
    required_dist_keys = {
        "idade",
        "escolaridade",
        "deficiencias",
        "composicao_familiar",
        "domain_expertise",
    }
    config_dist_keys = set(DEFAULT_GROUP_CONFIG["distributions"].keys())
    if config_dist_keys != required_dist_keys:
        missing = required_dist_keys - config_dist_keys
        all_validation_failures.append(f"DEFAULT_GROUP_CONFIG missing keys: {missing}")

    # Test 12: DEFAULT_GROUP_CONFIG n_synths is 500
    total_tests += 1
    if DEFAULT_GROUP_CONFIG["n_synths"] != 500:
        all_validation_failures.append(
            f"DEFAULT_GROUP_CONFIG n_synths should be 500, got {DEFAULT_GROUP_CONFIG['n_synths']}"
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
        print("Group defaults ready for use")
        sys.exit(0)
