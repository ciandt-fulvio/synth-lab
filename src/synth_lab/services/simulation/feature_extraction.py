"""
Feature extraction utilities for UX Research analysis.

Provides helpers for extracting numpy arrays from synth outcomes
for use in ML algorithms (clustering, SHAP, etc.)

References:
    - Research: specs/017-analysis-ux-research/research.md
"""

import numpy as np
from loguru import logger

from synth_lab.domain.entities import SynthOutcome

# Default features for analysis (all available attributes)
# Includes both observables (visible to PM) and latent traits (simulation-derived)
DEFAULT_FEATURES = [
    # Observables - visible user characteristics
    "digital_literacy",
    "similar_tool_experience",
    "motor_ability",
    "time_availability",
    "domain_expertise",
    # Latent traits - simulation-derived values
    "capability_mean",
    "trust_mean",
    "friction_tolerance_mean",
    "exploration_prob",
]


def extract_features(
    outcomes: list[SynthOutcome],
    features: list[str] | None = None,
    include_outcomes: bool = False,
) -> tuple[np.ndarray, list[str], list[str]]:
    """
    Extract feature matrix from synth outcomes.

    Converts list of SynthOutcome entities into a numpy array suitable
    for scikit-learn algorithms.

    Args:
        outcomes: List of SynthOutcome entities.
        features: Feature names to extract. Defaults to latent traits.
        include_outcomes: If True, include success/failed rates as features.

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
        feature_names.extend(["success_rate", "failed_rate", "did_not_try_rate"])

    X = []
    synth_ids = []

    for outcome in outcomes:
        row = []
        attrs = outcome.synth_attributes.latent_traits
        observables = outcome.synth_attributes.observables

        for f in features:
            # Try latent traits first
            if hasattr(attrs, f):
                row.append(getattr(attrs, f))
            # Then try observables
            elif hasattr(observables, f):
                row.append(getattr(observables, f))
            else:
                logger.warning(f"Feature '{f}' not found in synth attributes, using 0.0")
                row.append(0.0)

        if include_outcomes:
            row.append(outcome.success_rate)
            row.append(outcome.failed_rate)
            row.append(outcome.did_not_try_rate)

        X.append(row)
        synth_ids.append(outcome.synth_id)

    return np.array(X, dtype=np.float64), synth_ids, feature_names


def get_outcome_value(outcome: SynthOutcome, metric: str) -> float:
    """
    Get specific outcome metric value.

    Args:
        outcome: SynthOutcome entity.
        metric: One of "success_rate", "failed_rate", "did_not_try_rate".

    Returns:
        The metric value as float.
    """
    if metric == "success_rate":
        return outcome.success_rate
    elif metric == "failed_rate":
        return outcome.failed_rate
    elif metric == "did_not_try_rate":
        return outcome.did_not_try_rate
    else:
        raise ValueError(f"Unknown metric: {metric}")


def get_attribute_value(outcome: SynthOutcome, attribute: str) -> float:
    """
    Get specific attribute value from synth.

    Args:
        outcome: SynthOutcome entity.
        attribute: Attribute name (latent trait or observable).

    Returns:
        The attribute value as float.
    """
    # Check latent traits
    attrs = outcome.synth_attributes.latent_traits
    if hasattr(attrs, attribute):
        return getattr(attrs, attribute)

    # Check observables
    observables = outcome.synth_attributes.observables
    if hasattr(observables, attribute):
        return getattr(observables, attribute)

    # Check outcome fields
    if attribute == "success_rate":
        return outcome.success_rate
    elif attribute == "failed_rate":
        return outcome.failed_rate
    elif attribute == "did_not_try_rate":
        return outcome.did_not_try_rate
    elif attribute == "attempt_rate":
        return 1.0 - outcome.did_not_try_rate

    raise ValueError(f"Unknown attribute: {attribute}")


def get_available_attributes() -> dict[str, list[str]]:
    """
    Get list of available attributes for analysis.

    Returns:
        Dictionary with categories as keys and attribute lists as values.
    """
    return {
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
            "success_rate",
            "failed_rate",
            "did_not_try_rate",
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

    all_validation_failures: list[str] = []
    total_tests = 0

    # Create sample outcomes for tests
    def create_outcome(synth_id: str, success: float, failed: float) -> SynthOutcome:
        return SynthOutcome(
            analysis_id="ana_12345678",
            synth_id=synth_id,
            success_rate=success,
            failed_rate=failed,
            did_not_try_rate=1.0 - success - failed,
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

    outcomes = [
        create_outcome("synth_001", 0.40, 0.35),
        create_outcome("synth_002", 0.60, 0.25),
        create_outcome("synth_003", 0.30, 0.45),
    ]

    # Test 1: Extract default features (9 features: 5 observables + 4 latent traits)
    total_tests += 1
    try:
        X, synth_ids, feature_names = extract_features(outcomes)
        if X.shape != (3, 9):
            all_validation_failures.append(f"Shape mismatch: expected (3, 9), got {X.shape}")
        if len(synth_ids) != 3:
            all_validation_failures.append(f"synth_ids length: {len(synth_ids)}")
        if feature_names != DEFAULT_FEATURES:
            all_validation_failures.append(f"feature_names mismatch: {feature_names}")
    except Exception as e:
        all_validation_failures.append(f"Default features extraction failed: {e}")

    # Test 2: Extract with include_outcomes (9 features + 3 outcomes = 12)
    total_tests += 1
    try:
        X, synth_ids, feature_names = extract_features(outcomes, include_outcomes=True)
        if X.shape != (3, 12):
            all_validation_failures.append(f"Shape with outcomes mismatch: {X.shape}")
        if "success_rate" not in feature_names:
            all_validation_failures.append("success_rate not in feature_names")
    except Exception as e:
        all_validation_failures.append(f"Include outcomes extraction failed: {e}")

    # Test 3: Extract specific features
    total_tests += 1
    try:
        X, synth_ids, feature_names = extract_features(
            outcomes, features=["capability_mean", "trust_mean"]
        )
        if X.shape != (3, 2):
            all_validation_failures.append(f"Specific features shape: {X.shape}")
        if feature_names != ["capability_mean", "trust_mean"]:
            all_validation_failures.append(f"Specific feature_names: {feature_names}")
    except Exception as e:
        all_validation_failures.append(f"Specific features extraction failed: {e}")

    # Test 4: Extract observable feature
    total_tests += 1
    try:
        X, _, feature_names = extract_features(outcomes, features=["digital_literacy"])
        if X.shape != (3, 1):
            all_validation_failures.append(f"Observable feature shape: {X.shape}")
        # Check value is 0.5 as defined above
        if not np.allclose(X[:, 0], [0.5, 0.5, 0.5]):
            all_validation_failures.append(f"Observable values incorrect: {X[:, 0]}")
    except Exception as e:
        all_validation_failures.append(f"Observable feature extraction failed: {e}")

    # Test 5: Empty outcomes
    total_tests += 1
    try:
        X, synth_ids, feature_names = extract_features([])
        if X.size != 0:
            all_validation_failures.append(f"Empty outcomes should return empty array: {X}")
        if synth_ids != []:
            all_validation_failures.append(f"Empty outcomes synth_ids: {synth_ids}")
    except Exception as e:
        all_validation_failures.append(f"Empty outcomes extraction failed: {e}")

    # Test 6: get_outcome_value
    total_tests += 1
    try:
        value = get_outcome_value(outcomes[0], "success_rate")
        if value != 0.40:
            all_validation_failures.append(f"get_outcome_value mismatch: {value}")
    except Exception as e:
        all_validation_failures.append(f"get_outcome_value failed: {e}")

    # Test 7: get_attribute_value - latent trait
    total_tests += 1
    try:
        value = get_attribute_value(outcomes[0], "capability_mean")
        if value != 0.55:
            all_validation_failures.append(f"get_attribute_value latent: {value}")
    except Exception as e:
        all_validation_failures.append(f"get_attribute_value latent failed: {e}")

    # Test 8: get_attribute_value - observable
    total_tests += 1
    try:
        value = get_attribute_value(outcomes[0], "digital_literacy")
        if value != 0.5:
            all_validation_failures.append(f"get_attribute_value observable: {value}")
    except Exception as e:
        all_validation_failures.append(f"get_attribute_value observable failed: {e}")

    # Test 9: get_attribute_value - outcome
    total_tests += 1
    try:
        value = get_attribute_value(outcomes[0], "success_rate")
        if value != 0.40:
            all_validation_failures.append(f"get_attribute_value outcome: {value}")
    except Exception as e:
        all_validation_failures.append(f"get_attribute_value outcome failed: {e}")

    # Test 10: get_attribute_value - unknown raises
    total_tests += 1
    try:
        get_attribute_value(outcomes[0], "unknown_attribute")
        all_validation_failures.append("Should raise for unknown attribute")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for unknown attribute: {e}")

    # Test 11: get_available_attributes
    total_tests += 1
    try:
        attrs = get_available_attributes()
        if "latent_traits" not in attrs:
            all_validation_failures.append("Missing latent_traits key")
        if "capability_mean" not in attrs["latent_traits"]:
            all_validation_failures.append("Missing capability_mean in latent_traits")
    except Exception as e:
        all_validation_failures.append(f"get_available_attributes failed: {e}")

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
