"""
Observable label utilities for synth-lab.

Provides functions for converting numeric observable values [0,1] to
human-readable textual labels in Portuguese (pt-BR).

References:
    - Spec: specs/022-observable-latent-traits/spec.md (FR-014, US4)
    - Data model: specs/022-observable-latent-traits/data-model.md

Label Mapping:
    - [0.00, 0.20): Muito Baixo
    - [0.20, 0.40): Baixo
    - [0.40, 0.60): Médio
    - [0.60, 0.80): Alto
    - [0.80, 1.00]: Muito Alto
"""

from dataclasses import dataclass

from synth_lab.domain.constants.observable_metadata import (
    OBSERVABLE_METADATA,
    ObservableMetadata,
)
from synth_lab.domain.entities.simulation_attributes import SimulationObservables

# Label thresholds (upper bounds, exclusive except for last)
LABEL_THRESHOLDS: list[tuple[float, str]] = [
    (0.20, "Muito Baixo"),
    (0.40, "Baixo"),
    (0.60, "Médio"),
    (0.80, "Alto"),
    (1.01, "Muito Alto"),  # 1.01 to include 1.0
]


def value_to_label(value: float) -> str:
    """
    Convert a numeric value [0,1] to a textual label.

    Args:
        value: Numeric value in range [0, 1]

    Returns:
        Textual label: "Muito Baixo", "Baixo", "Médio", "Alto", or "Muito Alto"

    Raises:
        ValueError: If value is outside [0, 1] range

    Examples:
        >>> value_to_label(0.15)
        'Muito Baixo'
        >>> value_to_label(0.35)
        'Baixo'
        >>> value_to_label(0.50)
        'Médio'
        >>> value_to_label(0.75)
        'Alto'
        >>> value_to_label(0.95)
        'Muito Alto'
    """
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Value must be in [0, 1], got {value}")

    for threshold, label in LABEL_THRESHOLDS:
        if value < threshold:
            return label

    return "Muito Alto"  # Fallback for edge case


@dataclass
class ObservableWithLabel:
    """Observable attribute with formatted label information."""

    key: str
    name: str
    value: float
    label: str
    description: str


def format_observable_with_label(
    key: str, value: float, metadata: ObservableMetadata | None = None
) -> ObservableWithLabel:
    """
    Format a single observable with its label and metadata.

    Args:
        key: Observable attribute key (e.g., "digital_literacy")
        value: Numeric value in range [0, 1]
        metadata: Optional ObservableMetadata. If None, uses OBSERVABLE_METADATA.

    Returns:
        ObservableWithLabel with key, name, value, label, and description

    Raises:
        ValueError: If key is not found in OBSERVABLE_METADATA
    """
    if metadata is None:
        metadata = OBSERVABLE_METADATA.get(key)
        if metadata is None:
            raise ValueError(f"Unknown observable key: {key}")

    return ObservableWithLabel(
        key=key,
        name=metadata.name,
        value=value,
        label=value_to_label(value),
        description=metadata.description,
    )


def format_observables_with_labels(
    observables: SimulationObservables,
) -> list[ObservableWithLabel]:
    """
    Format all observables with their labels and metadata.

    Args:
        observables: SimulationObservables instance

    Returns:
        List of ObservableWithLabel for all 5 observables

    Example:
        >>> obs = SimulationObservables(
        ...     digital_literacy=0.35,
        ...     similar_tool_experience=0.42,
        ...     motor_ability=0.85,
        ...     time_availability=0.28,
        ...     domain_expertise=0.55,
        ... )
        >>> formatted = format_observables_with_labels(obs)
        >>> formatted[0].name
        'Literacia Digital'
        >>> formatted[0].label
        'Baixo'
    """
    result: list[ObservableWithLabel] = []
    obs_dict = observables.model_dump()

    for key, metadata in OBSERVABLE_METADATA.items():
        value = obs_dict.get(key, 0.0)
        result.append(format_observable_with_label(key, value, metadata))

    return result


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: value_to_label for boundary values
    total_tests += 1
    test_cases = [
        (0.00, "Muito Baixo"),
        (0.19, "Muito Baixo"),
        (0.20, "Baixo"),
        (0.39, "Baixo"),
        (0.40, "Médio"),
        (0.59, "Médio"),
        (0.60, "Alto"),
        (0.79, "Alto"),
        (0.80, "Muito Alto"),
        (1.00, "Muito Alto"),
    ]
    for value, expected in test_cases:
        result = value_to_label(value)
        if result != expected:
            all_validation_failures.append(
                f"value_to_label({value}): expected '{expected}', got '{result}'"
            )

    # Test 2: value_to_label rejects invalid values
    total_tests += 1
    try:
        value_to_label(-0.1)
        all_validation_failures.append("value_to_label should reject negative values")
    except ValueError:
        pass  # Expected

    total_tests += 1
    try:
        value_to_label(1.5)
        all_validation_failures.append("value_to_label should reject values > 1")
    except ValueError:
        pass  # Expected

    # Test 3: format_observable_with_label works
    total_tests += 1
    formatted = format_observable_with_label("digital_literacy", 0.35)
    if formatted.key != "digital_literacy":
        all_validation_failures.append(f"key mismatch: {formatted.key}")
    if formatted.name != "Literacia Digital":
        all_validation_failures.append(f"name mismatch: {formatted.name}")
    if formatted.label != "Baixo":
        all_validation_failures.append(f"label mismatch: {formatted.label}")
    if formatted.value != 0.35:
        all_validation_failures.append(f"value mismatch: {formatted.value}")

    # Test 4: format_observable_with_label rejects unknown keys
    total_tests += 1
    try:
        format_observable_with_label("unknown_key", 0.5)
        all_validation_failures.append("Should reject unknown observable key")
    except ValueError:
        pass  # Expected

    # Test 5: format_observables_with_labels returns all 5 observables
    total_tests += 1
    obs = SimulationObservables(
        digital_literacy=0.35,
        similar_tool_experience=0.42,
        motor_ability=0.85,
        time_availability=0.28,
        domain_expertise=0.55,
    )
    formatted_list = format_observables_with_labels(obs)
    if len(formatted_list) != 5:
        all_validation_failures.append(
            f"Expected 5 formatted observables, got {len(formatted_list)}"
        )

    # Test 6: Verify specific observable in formatted list
    total_tests += 1
    digital_lit = next((f for f in formatted_list if f.key == "digital_literacy"), None)
    if digital_lit is None:
        all_validation_failures.append("digital_literacy not found in formatted list")
    elif digital_lit.label != "Baixo":
        all_validation_failures.append(
            f"digital_literacy label wrong: expected 'Baixo', got '{digital_lit.label}'"
        )

    # Test 7: Verify motor_ability label
    total_tests += 1
    motor = next((f for f in formatted_list if f.key == "motor_ability"), None)
    if motor is None:
        all_validation_failures.append("motor_ability not found in formatted list")
    elif motor.label != "Muito Alto":
        all_validation_failures.append(
            f"motor_ability label wrong: expected 'Muito Alto', got '{motor.label}'"
        )

    # Test 8: All formatted observables have descriptions
    total_tests += 1
    for f in formatted_list:
        if not f.description:
            all_validation_failures.append(f"{f.key} missing description")

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Observable label utilities ready for use")
        sys.exit(0)
