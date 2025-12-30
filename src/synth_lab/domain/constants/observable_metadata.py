"""
Observable attribute metadata for synth-lab.

Defines names, descriptions, and display information for observable
attributes in Portuguese (pt-BR) for PM-facing interfaces.

References:
    - Spec: specs/022-observable-latent-traits/spec.md (FR-014)
    - Data model: specs/022-observable-latent-traits/data-model.md
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ObservableMetadata:
    """Metadata for an observable attribute."""

    key: str
    name: str
    description: str


OBSERVABLE_METADATA: dict[str, ObservableMetadata] = {
    "digital_literacy": ObservableMetadata(
        key="digital_literacy",
        name="Literacia Digital",
        description="Familiaridade com tecnologia e interfaces digitais",
    ),
    "similar_tool_experience": ObservableMetadata(
        key="similar_tool_experience",
        name="Experiência com Ferramentas Similares",
        description="Uso prévio de ferramentas ou produtos parecidos",
    ),
    "motor_ability": ObservableMetadata(
        key="motor_ability",
        name="Capacidade Motora",
        description="Habilidade física para interação com dispositivos",
    ),
    "time_availability": ObservableMetadata(
        key="time_availability",
        name="Disponibilidade de Tempo",
        description="Tempo típico disponível para uso do produto",
    ),
    "domain_expertise": ObservableMetadata(
        key="domain_expertise",
        name="Conhecimento do Domínio",
        description="Expertise na área de atuação do produto",
    ),
}


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: All 5 observables are defined
    total_tests += 1
    expected_keys = {
        "digital_literacy",
        "similar_tool_experience",
        "motor_ability",
        "time_availability",
        "domain_expertise",
    }
    actual_keys = set(OBSERVABLE_METADATA.keys())
    if actual_keys != expected_keys:
        all_validation_failures.append(f"Expected keys {expected_keys}, got {actual_keys}")

    # Test 2: All metadata have required fields
    total_tests += 1
    for key, meta in OBSERVABLE_METADATA.items():
        if not meta.key:
            all_validation_failures.append(f"{key}: missing key")
        if not meta.name:
            all_validation_failures.append(f"{key}: missing name")
        if not meta.description:
            all_validation_failures.append(f"{key}: missing description")

    # Test 3: Key matches dict key
    total_tests += 1
    for key, meta in OBSERVABLE_METADATA.items():
        if meta.key != key:
            all_validation_failures.append(f"Key mismatch: dict key={key}, meta.key={meta.key}")

    # Test 4: Names are in Portuguese
    total_tests += 1
    portuguese_indicators = [
        "Literacia",
        "Experiência",
        "Capacidade",
        "Disponibilidade",
        "Conhecimento",
    ]
    found_portuguese = False
    for meta in OBSERVABLE_METADATA.values():
        for indicator in portuguese_indicators:
            if indicator in meta.name:
                found_portuguese = True
                break
        if found_portuguese:
            break
    if not found_portuguese:
        all_validation_failures.append("Names should be in Portuguese")

    # Test 5: Metadata is immutable (frozen dataclass)
    total_tests += 1
    try:
        meta = OBSERVABLE_METADATA["digital_literacy"]
        meta.name = "Test"  # type: ignore
        all_validation_failures.append("ObservableMetadata should be immutable")
    except Exception:
        pass  # Expected - frozen dataclass

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Observable metadata ready for use")
        sys.exit(0)
