"""
Feature mechanisms entities for synth-lab.

Defines models for feature structural mechanisms that interact with user
sensitivities to produce emergent behavioral states in simulations.

References:
    - Spec: specs/040-mechanism-expansion/spec.md
    - Data model: specs/038-mechanism-based-simulation/data-model.md
"""

from pydantic import BaseModel, Field


class FeatureMechanisms(BaseModel):
    """
    Feature mechanisms that interact with user sensitivities.

    Each mechanism represents a structural property of the feature:
    - irreversibility: Actions cannot be undone (0=reversible, 1=permanent)
    - network_effect: Value depends on others using it (0=individual, 1=requires network)
    - institutional_trust: Requires trust in institution (0=peer, 1=institutional)
    - habit_displacement: Replaces existing habits (0=additive, 1=replacement)
    - learning_curve: Requires learning new skills (0=intuitive, 1=complex)
    - social_visibility: Usage is visible to others (0=private, 1=public)
    - valor_intrinseco: Real improvement in user's life (0=cosmetic, 1=transformative)
    - friccao_operacional: Operational friction/steps/errors in usage (0=none, 1=extreme)
    - frequencia_de_uso: Expected usage frequency (0=rare, 1=daily or more)

    Default value of 0.0 represents mechanism not present.
    """

    irreversibility: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which actions are permanent/irreversible",
    )
    network_effect: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which value depends on others using it",
    )
    institutional_trust: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which feature requires trust in institution",
    )
    habit_displacement: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which feature replaces existing habits",
    )
    learning_curve: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which feature requires learning new skills",
    )
    social_visibility: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which usage is visible to others",
    )
    valor_intrinseco: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Real improvement in user's life (0=cosmetic, 1=transformative)",
    )
    friccao_operacional: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Operational friction/steps/errors in usage (0=none, 1=extreme)",
    )
    frequencia_de_uso: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Expected usage frequency (0=rare, 1=daily or more)",
    )

    def has_any_mechanism(self) -> bool:
        """Check if any mechanism is non-zero."""
        return any(
            [
                self.irreversibility > 0,
                self.network_effect > 0,
                self.institutional_trust > 0,
                self.habit_displacement > 0,
                self.learning_curve > 0,
                self.social_visibility > 0,
                self.valor_intrinseco > 0,
                self.friccao_operacional > 0,
                self.frequencia_de_uso > 0,
            ]
        )


ALL_9_FIELDS = {
    "irreversibility",
    "network_effect",
    "institutional_trust",
    "habit_displacement",
    "learning_curve",
    "social_visibility",
    "valor_intrinseco",
    "friccao_operacional",
    "frequencia_de_uso",
}

if __name__ == "__main__":
    import sys

    failures: list[str] = []
    total_tests = 0

    # Test 1: Default creation (all 0.0)
    total_tests += 1
    try:
        m = FeatureMechanisms()
        for f in ALL_9_FIELDS:
            if getattr(m, f) != 0.0:
                failures.append(f"{f} default should be 0.0, got {getattr(m, f)}")
        if m.has_any_mechanism():
            failures.append("has_any_mechanism should be False for defaults")
    except Exception as e:
        failures.append(f"Default creation failed: {e}")

    # Test 2: Full creation with all 9 values
    total_tests += 1
    try:
        vals = dict(
            irreversibility=0.9,
            network_effect=0.7,
            institutional_trust=0.8,
            habit_displacement=0.4,
            learning_curve=0.5,
            social_visibility=0.3,
            valor_intrinseco=0.6,
            friccao_operacional=0.2,
            frequencia_de_uso=0.85,
        )
        m = FeatureMechanisms(**vals)
        for k, v in vals.items():
            if getattr(m, k) != v:
                failures.append(f"{k} mismatch: expected {v}, got {getattr(m, k)}")
        if not m.has_any_mechanism():
            failures.append("has_any_mechanism should be True with all values set")
    except Exception as e:
        failures.append(f"Full creation failed: {e}")

    # Test 3: Backward compat - only original 6 fields, new fields default 0.0
    total_tests += 1
    try:
        m = FeatureMechanisms(
            irreversibility=0.9,
            network_effect=0.7,
            institutional_trust=0.8,
            habit_displacement=0.4,
            learning_curve=0.5,
            social_visibility=0.3,
        )
        for f in ("valor_intrinseco", "friccao_operacional", "frequencia_de_uso"):
            if getattr(m, f) != 0.0:
                failures.append(f"Backward compat: {f} should default to 0.0, got {getattr(m, f)}")
    except Exception as e:
        failures.append(f"Backward compatibility test failed: {e}")

    # Test 4: Reject value below 0 (original field)
    total_tests += 1
    try:
        FeatureMechanisms(irreversibility=-0.1)
        failures.append("Should reject negative irreversibility")
    except ValueError:
        pass

    # Test 5: Reject value above 1 (original field)
    total_tests += 1
    try:
        FeatureMechanisms(network_effect=1.5)
        failures.append("Should reject network_effect > 1")
    except ValueError:
        pass

    # Test 6: Reject new field below 0
    total_tests += 1
    try:
        FeatureMechanisms(valor_intrinseco=-0.5)
        failures.append("Should reject negative valor_intrinseco")
    except ValueError:
        pass

    # Test 7: Reject new field above 1
    total_tests += 1
    try:
        FeatureMechanisms(frequencia_de_uso=2.0)
        failures.append("Should reject frequencia_de_uso > 1")
    except ValueError:
        pass

    # Test 8: Boundary values (0.0 and 1.0 accepted)
    total_tests += 1
    try:
        m = FeatureMechanisms(
            irreversibility=0.0,
            network_effect=1.0,
            institutional_trust=0.0,
            habit_displacement=1.0,
            learning_curve=0.0,
            social_visibility=1.0,
            valor_intrinseco=0.0,
            friccao_operacional=1.0,
            frequencia_de_uso=0.0,
        )
        if m.network_effect != 1.0:
            failures.append("1.0 should be accepted for network_effect")
        if m.friccao_operacional != 1.0:
            failures.append("1.0 should be accepted for friccao_operacional")
        if not m.has_any_mechanism():
            failures.append("has_any_mechanism should be True with some 1.0 values")
    except Exception as e:
        failures.append(f"Boundary values test failed: {e}")

    # Test 9: has_any_mechanism detects each new field individually
    total_tests += 1
    try:
        for field, val in [
            ("valor_intrinseco", 0.1),
            ("friccao_operacional", 0.3),
            ("frequencia_de_uso", 0.5),
        ]:
            m = FeatureMechanisms(**{field: val})
            if not m.has_any_mechanism():
                failures.append(f"has_any_mechanism should be True with {field}={val}")
    except Exception as e:
        failures.append(f"has_any_mechanism new fields test failed: {e}")

    # Test 10: model_dump has all 9 fields with correct values
    total_tests += 1
    try:
        m = FeatureMechanisms(irreversibility=0.9, network_effect=0.7, valor_intrinseco=0.6)
        dump = m.model_dump()
        if set(dump.keys()) != ALL_9_FIELDS:
            failures.append(f"model_dump keys mismatch: {set(dump.keys())} != {ALL_9_FIELDS}")
        checks = {
            "irreversibility": 0.9,
            "network_effect": 0.7,
            "valor_intrinseco": 0.6,
            "institutional_trust": 0.0,
            "friccao_operacional": 0.0,
            "frequencia_de_uso": 0.0,
        }
        for k, expected in checks.items():
            if dump[k] != expected:
                failures.append(f"model_dump {k}: expected {expected}, got {dump[k]}")
    except Exception as e:
        failures.append(f"model_dump test failed: {e}")

    # Test 11: Field count is exactly 9
    total_tests += 1
    actual_fields = set(FeatureMechanisms.model_fields.keys())
    if actual_fields != ALL_9_FIELDS:
        failures.append(f"Field set mismatch: expected {ALL_9_FIELDS}, got {actual_fields}")
    if len(actual_fields) != 9:
        failures.append(f"Field count should be 9, got {len(actual_fields)}")

    # Final result
    if failures:
        print(f"VALIDATION FAILED - {len(failures)} of {total_tests} tests failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
