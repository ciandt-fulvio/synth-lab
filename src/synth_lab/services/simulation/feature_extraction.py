"""
Feature extraction utilities for UX Research analysis.

Provides helpers for extracting numpy arrays from synth outcomes
for use in ML algorithms (SHAP, etc.)

References:
    - Research: specs/017-analysis-ux-research/research.md
    - Sensitivities: specs/040-refined-sensitivities/spec.md
"""

import numpy as np
from loguru import logger

from synth_lab.domain.entities import SynthOutcome

# Default features for analysis - user sensitivities (visible to PM)
# These are the 9 psychological sensitivity dimensions that interact with mechanisms.
DEFAULT_FEATURES = [
    "risk_aversion",
    "social_dependency",
    "institutional_trust_level",
    "habit_plasticity",
    "friction_tolerance",
    "pragmatism",
    "digital_capability",
    "motor_ability",
    "subject_domain",
]

# PT-BR display names for SHAP charts
SENSITIVITY_DISPLAY_NAMES: dict[str, str] = {
    "risk_aversion": "Aversão ao Risco",
    "social_dependency": "Dependência Social",
    "institutional_trust_level": "Confiança Institucional",
    "habit_plasticity": "Plasticidade de Hábito",
    "friction_tolerance": "Tolerância à Fricção",
    "pragmatism": "Pragmatismo",
    "digital_capability": "Capacidade Digital",
    "motor_ability": "Habilidade Motora",
    "subject_domain": "Domínio do Assunto",
}


def extract_features(
    outcomes: list[SynthOutcome], features: list[str] | None = None, include_outcomes: bool = False
) -> tuple[np.ndarray, list[str], list[str]]:
    """
    Extract feature matrix from synth outcomes.

    Converts list of SynthOutcome entities into a numpy array suitable
    for scikit-learn algorithms.

    Extraction priority:
      1. sensitivities (new mechanism-based model)
      2. latent_traits (legacy)
      3. observables (legacy)

    Args:
        outcomes: List of SynthOutcome entities.
        features: Feature names to extract. Defaults to sensitivities.
        include_outcomes: If True, include adopted/not_adopted rates as features.

    Returns:
        Tuple of:
            - X: numpy array of shape (n_samples, n_features)
            - synth_ids: list of synth IDs in same order as X rows
            - feature_names: list of feature names in same order as X columns
    """
    if not outcomes:
        logger.warning("No outcomes provided for feature extraction")
        return np.array([]), [], []

    # Use default features if none specified
    if features is None:
        features = DEFAULT_FEATURES.copy()

    feature_names = features.copy()

    if include_outcomes:
        feature_names.extend(["adopted_rate", "not_adopted_rate"])

    X = []
    synth_ids = []

    for outcome in outcomes:
        row = []
        attrs = outcome.synth_attributes

        for f in features:
            value = _get_feature_value(attrs, f)
            row.append(value)

        if include_outcomes:
            row.append(outcome.adopted_rate)
            row.append(outcome.not_adopted_rate)

        X.append(row)
        synth_ids.append(outcome.synth_id)

    return np.array(X, dtype=np.float64), synth_ids, feature_names


def _get_feature_value(attrs, feature: str) -> float:
    """
    Get a feature value from SimulationAttributes, checking sensitivities first.

    Args:
        attrs: SimulationAttributes instance.
        feature: Feature name to extract.

    Returns:
        Float value (defaults to 0.5 if not found).
    """
    # 1. Check sensitivities first (new model)
    if attrs.sensitivities is not None and hasattr(attrs.sensitivities, feature):
        return float(getattr(attrs.sensitivities, feature))

    # 2. Check latent traits (legacy)
    if attrs.latent_traits is not None and hasattr(attrs.latent_traits, feature):
        return float(getattr(attrs.latent_traits, feature))

    # 3. Check observables (legacy)
    if attrs.observables is not None and hasattr(attrs.observables, feature):
        return float(getattr(attrs.observables, feature))

    logger.warning(f"Feature '{feature}' not found in synth attributes, using 0.5")
    return 0.5


def get_outcome_value(outcome: SynthOutcome, metric: str) -> float:
    """
    Get specific outcome metric value.

    Args:
        outcome: SynthOutcome entity.
        metric: One of "adopted_rate", "not_adopted_rate".

    Returns:
        The metric value as float.
    """
    if metric == "adopted_rate":
        return outcome.adopted_rate
    elif metric == "not_adopted_rate":
        return outcome.not_adopted_rate
    else:
        raise ValueError(f"Unknown metric: {metric}")


def get_attribute_value(outcome: SynthOutcome, attribute: str) -> float:
    """
    Get specific attribute value from synth.

    Args:
        outcome: SynthOutcome entity.
        attribute: Attribute name (sensitivity, latent trait, or observable).

    Returns:
        The attribute value as float.
    """
    attrs = outcome.synth_attributes

    # Check sensitivities first
    if attrs.sensitivities is not None and hasattr(attrs.sensitivities, attribute):
        return float(getattr(attrs.sensitivities, attribute))

    # Check latent traits
    if attrs.latent_traits is not None and hasattr(attrs.latent_traits, attribute):
        return float(getattr(attrs.latent_traits, attribute))

    # Check observables
    if attrs.observables is not None and hasattr(attrs.observables, attribute):
        return float(getattr(attrs.observables, attribute))

    # Check outcome fields
    if attribute == "adopted_rate":
        return outcome.adopted_rate
    elif attribute == "not_adopted_rate":
        return outcome.not_adopted_rate

    raise ValueError(f"Unknown attribute: {attribute}")


def get_available_attributes() -> dict[str, list[str]]:
    """
    Get list of available attributes for analysis.

    Returns:
        Dictionary with categories as keys and attribute lists as values.
    """
    return {
        "sensitivities": DEFAULT_FEATURES.copy(),
        "latent_traits": [
            "capability_mean",
            "trust_mean",
            "friction_tolerance_mean",
            "exploration_prob",
        ],
        "observables": [
            "digital_literacy",
            "similar_tool_experience",
            "motor_ability",
            "time_availability",
            "domain_expertise",
        ],
        "outcomes": [
            "adopted_rate",
            "not_adopted_rate",
        ],
    }


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    from synth_lab.domain.entities.simulation_attributes import (
        SimulationAttributes,
        SimulationLatentTraits,
        SimulationObservables,
    )
    from synth_lab.domain.entities.user_sensitivities import UserSensitivities

    all_validation_failures: list[str] = []
    total_tests = 0

    # Create sample outcome with sensitivities (new model)
    def create_outcome_with_sensitivities(synth_id: str, adopted: float) -> SynthOutcome:
        return SynthOutcome(
            analysis_id="ana_12345678",
            synth_id=synth_id,
            adopted_rate=adopted,
            not_adopted_rate=1.0 - adopted,
            synth_attributes=SimulationAttributes(
                sensitivities=UserSensitivities(
                    risk_aversion=0.7,
                    social_dependency=0.3,
                    institutional_trust_level=0.6,
                    habit_plasticity=0.4,
                    friction_tolerance=0.8,
                    pragmatism=0.5,
                    digital_capability=0.9,
                    motor_ability=0.6,
                    subject_domain=0.55,
                ),
            ),
        )

    # Create sample outcome with legacy attributes (no sensitivities)
    def create_outcome_legacy(synth_id: str, adopted: float) -> SynthOutcome:
        return SynthOutcome(
            analysis_id="ana_12345678",
            synth_id=synth_id,
            adopted_rate=adopted,
            not_adopted_rate=1.0 - adopted,
            synth_attributes=SimulationAttributes(
                observables=SimulationObservables(
                    digital_literacy=0.5,
                    similar_tool_experience=0.4,
                    motor_ability=0.8,
                    time_availability=0.3,
                    domain_expertise=0.6,
                ),
                latent_traits=SimulationLatentTraits(
                    capability_mean=0.55,
                    trust_mean=0.45,
                    friction_tolerance_mean=0.40,
                    exploration_prob=0.35,
                ),
            ),
        )

    outcomes_new = [
        create_outcome_with_sensitivities("synth_001", 0.40),
        create_outcome_with_sensitivities("synth_002", 0.60),
        create_outcome_with_sensitivities("synth_003", 0.30),
    ]

    outcomes_legacy = [
        create_outcome_legacy("synth_004", 0.40),
        create_outcome_legacy("synth_005", 0.60),
    ]

    # Test 1: Extract default features from sensitivities (9 features)
    total_tests += 1
    try:
        X, synth_ids, feature_names = extract_features(outcomes_new)
        if X.shape != (3, 9):
            all_validation_failures.append(f"Shape mismatch: expected (3, 9), got {X.shape}")
        if len(synth_ids) != 3:
            all_validation_failures.append(f"synth_ids length: {len(synth_ids)}")
        if feature_names != DEFAULT_FEATURES:
            all_validation_failures.append(f"feature_names mismatch: {feature_names}")
        # Check actual values
        if X[0, 0] != 0.7:  # risk_aversion
            all_validation_failures.append(f"risk_aversion value: expected 0.7, got {X[0, 0]}")
    except Exception as e:
        all_validation_failures.append(f"Default features extraction failed: {e}")

    # Test 2: Extract with include_outcomes (9 features + 2 outcomes = 11)
    total_tests += 1
    try:
        X, synth_ids, feature_names = extract_features(outcomes_new, include_outcomes=True)
        if X.shape != (3, 11):
            all_validation_failures.append(f"Shape with outcomes mismatch: {X.shape}")
        if "adopted_rate" not in feature_names:
            all_validation_failures.append("adopted_rate not in feature_names")
    except Exception as e:
        all_validation_failures.append(f"Include outcomes extraction failed: {e}")

    # Test 3: Legacy outcomes fall back to latent_traits/observables
    total_tests += 1
    try:
        X, synth_ids, feature_names = extract_features(
            outcomes_legacy, features=["capability_mean", "trust_mean"]
        )
        if X.shape != (2, 2):
            all_validation_failures.append(f"Legacy features shape: {X.shape}")
        if X[0, 0] != 0.55:  # capability_mean
            all_validation_failures.append(f"capability_mean: expected 0.55, got {X[0, 0]}")
    except Exception as e:
        all_validation_failures.append(f"Legacy features extraction failed: {e}")

    # Test 4: Empty outcomes
    total_tests += 1
    try:
        X, synth_ids, feature_names = extract_features([])
        if X.size != 0:
            all_validation_failures.append(f"Empty outcomes should return empty array: {X}")
    except Exception as e:
        all_validation_failures.append(f"Empty outcomes extraction failed: {e}")

    # Test 5: get_attribute_value - sensitivity
    total_tests += 1
    try:
        value = get_attribute_value(outcomes_new[0], "risk_aversion")
        if value != 0.7:
            all_validation_failures.append(f"get_attribute_value sensitivity: {value}")
    except Exception as e:
        all_validation_failures.append(f"get_attribute_value sensitivity failed: {e}")

    # Test 6: get_attribute_value - outcome
    total_tests += 1
    try:
        value = get_attribute_value(outcomes_new[0], "adopted_rate")
        if value != 0.40:
            all_validation_failures.append(f"get_attribute_value outcome: {value}")
    except Exception as e:
        all_validation_failures.append(f"get_attribute_value outcome failed: {e}")

    # Test 7: get_attribute_value - unknown raises
    total_tests += 1
    try:
        get_attribute_value(outcomes_new[0], "unknown_attribute")
        all_validation_failures.append("Should raise for unknown attribute")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for unknown attribute: {e}")

    # Test 8: get_available_attributes includes sensitivities
    total_tests += 1
    try:
        attrs = get_available_attributes()
        if "sensitivities" not in attrs:
            all_validation_failures.append("Missing sensitivities key")
        if "risk_aversion" not in attrs["sensitivities"]:
            all_validation_failures.append("Missing risk_aversion in sensitivities")
    except Exception as e:
        all_validation_failures.append(f"get_available_attributes failed: {e}")

    # Test 9: SENSITIVITY_DISPLAY_NAMES has all 9 entries
    total_tests += 1
    if len(SENSITIVITY_DISPLAY_NAMES) != 9:
        all_validation_failures.append(
            f"SENSITIVITY_DISPLAY_NAMES has {len(SENSITIVITY_DISPLAY_NAMES)} entries, expected 9"
        )
    for key in DEFAULT_FEATURES:
        if key not in SENSITIVITY_DISPLAY_NAMES:
            all_validation_failures.append(f"Missing display name for {key}")

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
