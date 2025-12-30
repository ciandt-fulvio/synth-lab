"""
Demographic factor mappings for synth-lab.

Maps demographic characteristics (education, disability, family composition)
to factors used for adjusting Beta distribution parameters in observable
attribute generation.

References:
    - Spec: specs/022-observable-latent-traits/spec.md (FR-005, FR-006, FR-007)
    - Research: specs/022-observable-latent-traits/research.md
"""

# Education level -> factor for digital_literacy adjustment
# Higher education -> higher factor -> shifts Beta distribution right
EDUCATION_FACTOR_MAP: dict[str, float] = {
    # Sem escolaridade formal
    "sem_escolaridade": 0.2,
    "analfabeto": 0.2,
    # Fundamental
    "fundamental_incompleto": 0.3,
    "fundamental_completo": 0.4,
    "fundamental": 0.4,
    # Médio
    "medio_incompleto": 0.5,
    "medio_completo": 0.6,
    "medio": 0.6,
    "ensino_medio": 0.6,
    # Superior
    "superior_incompleto": 0.7,
    "superior_completo": 0.8,
    "superior": 0.8,
    "graduacao": 0.8,
    # Pós-graduação
    "pos_graduacao": 0.85,
    "especializacao": 0.85,
    "mestrado": 0.9,
    "doutorado": 0.95,
    # Default
    "outro": 0.5,
    "nao_informado": 0.5,
}

# Disability type/severity -> severity factor for motor_ability adjustment
# Higher severity -> lower motor_ability
# Maps disability categories to their impact on motor/physical ability
DISABILITY_SEVERITY_MAP: dict[str, float] = {
    # Nenhuma deficiência
    "nenhuma": 0.0,
    "sem_deficiencia": 0.0,
    # Deficiência visual
    "visual_leve": 0.2,
    "visual_moderada": 0.4,
    "visual_severa": 0.7,
    "cegueira": 0.8,
    # Deficiência auditiva (menor impacto em motor_ability)
    "auditiva_leve": 0.1,
    "auditiva_moderada": 0.15,
    "auditiva_severa": 0.2,
    "surdez": 0.25,
    # Deficiência motora/física
    "motora_leve": 0.3,
    "motora_moderada": 0.5,
    "motora_severa": 0.8,
    "fisica_leve": 0.3,
    "fisica_moderada": 0.5,
    "fisica_severa": 0.8,
    # Deficiência intelectual (impacto em digital_literacy, não motor)
    "intelectual_leve": 0.1,
    "intelectual_moderada": 0.2,
    "intelectual_severa": 0.3,
    # Múltiplas deficiências
    "multipla": 0.6,
    "multipla_severa": 0.85,
    # Default
    "outra": 0.3,
    "nao_informado": 0.0,
}

# Family composition -> pressure factor for time_availability adjustment
# Higher pressure -> lower time_availability
# Maps family situations to their impact on available time
FAMILY_PRESSURE_MAP: dict[str, float] = {
    # Sem dependentes
    "sozinho": 0.1,
    "solteiro_sem_filhos": 0.1,
    "casal_sem_filhos": 0.15,
    # Com filhos pequenos (alta demanda de tempo)
    "filhos_0_3": 0.8,
    "filhos_pequenos": 0.7,
    "mae_solo_filhos_pequenos": 0.9,
    "pai_solo_filhos_pequenos": 0.9,
    # Com filhos em idade escolar
    "filhos_4_12": 0.5,
    "filhos_adolescentes": 0.4,
    # Cuidador de idosos/familiares
    "cuidador_idoso": 0.6,
    "cuidador_familiar": 0.55,
    # Família extensa
    "familia_extensa": 0.4,
    "multigeracional": 0.45,
    # Situações de alta demanda
    "multiplos_dependentes": 0.75,
    "cuidador_tempo_integral": 0.85,
    # Default
    "outro": 0.3,
    "nao_informado": 0.3,
}


def calculate_max_disability_severity(deficiencias: dict) -> float:
    """
    Calculate the maximum disability severity across all disability types.

    Returns 0.8 if ANY disability type is 'severa', 'cegueira', or 'surdez'.
    Otherwise returns the highest severity from the mapping.

    Args:
        deficiencias: Dict with visual, auditiva, motora, cognitiva sub-dicts,
                     each containing a 'tipo' key.

    Returns:
        float: Maximum severity value in [0.0, 0.8]

    Examples:
        >>> calculate_max_disability_severity({"motora": {"tipo": "severa"}})
        0.8
        >>> calculate_max_disability_severity({"visual": {"tipo": "leve"}})
        0.2
        >>> calculate_max_disability_severity({"visual": {"tipo": "nenhuma"}})
        0.0
    """
    if not deficiencias:
        return 0.0

    # Types that trigger immediate 0.8 severity
    severe_types = {"severa", "cegueira", "surdez"}

    max_severity = 0.0

    # Check each disability category
    for category in ["visual", "auditiva", "motora", "cognitiva"]:
        disability = deficiencias.get(category, {})
        tipo = disability.get("tipo", "nenhuma")

        if not tipo or tipo == "nenhuma":
            continue

        # Immediate return for severe types
        tipo_lower = tipo.lower()
        if tipo_lower in severe_types:
            return 0.8

        # Otherwise look up severity
        severity_key = f"{category}_{tipo_lower}"
        severity = DISABILITY_SEVERITY_MAP.get(severity_key, 0.0)

        # Also try just the tipo
        if severity == 0.0:
            severity = DISABILITY_SEVERITY_MAP.get(tipo_lower, 0.0)

        max_severity = max(max_severity, severity)

    return max_severity


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: EDUCATION_FACTOR_MAP has expected entries
    total_tests += 1
    required_education = ["fundamental", "medio", "superior", "pos_graduacao"]
    for key in required_education:
        if key not in EDUCATION_FACTOR_MAP:
            all_validation_failures.append(f"EDUCATION_FACTOR_MAP missing: {key}")

    # Test 2: Education factors are in [0, 1]
    total_tests += 1
    for key, value in EDUCATION_FACTOR_MAP.items():
        if not 0.0 <= value <= 1.0:
            all_validation_failures.append(f"EDUCATION_FACTOR_MAP[{key}]={value} not in [0,1]")

    # Test 3: Education factors are monotonically increasing with education level
    total_tests += 1
    expected_order = [
        ("sem_escolaridade", "fundamental"),
        ("fundamental", "medio"),
        ("medio", "superior"),
        ("superior", "mestrado"),
        ("mestrado", "doutorado"),
    ]
    for lower, higher in expected_order:
        if EDUCATION_FACTOR_MAP.get(lower, 0) >= EDUCATION_FACTOR_MAP.get(higher, 1):
            all_validation_failures.append(f"Education factor order wrong: {lower} >= {higher}")

    # Test 4: DISABILITY_SEVERITY_MAP has expected entries
    total_tests += 1
    required_disability = ["nenhuma", "visual_leve", "motora_severa"]
    for key in required_disability:
        if key not in DISABILITY_SEVERITY_MAP:
            all_validation_failures.append(f"DISABILITY_SEVERITY_MAP missing: {key}")

    # Test 5: Disability severity factors are in [0, 1]
    total_tests += 1
    for key, value in DISABILITY_SEVERITY_MAP.items():
        if not 0.0 <= value <= 1.0:
            all_validation_failures.append(f"DISABILITY_SEVERITY_MAP[{key}]={value} not in [0,1]")

    # Test 6: "nenhuma" disability has 0 severity
    total_tests += 1
    if DISABILITY_SEVERITY_MAP.get("nenhuma") != 0.0:
        all_validation_failures.append(
            f"'nenhuma' should have 0.0 severity, got {DISABILITY_SEVERITY_MAP.get('nenhuma')}"
        )

    # Test 7: FAMILY_PRESSURE_MAP has expected entries
    total_tests += 1
    required_family = ["sozinho", "filhos_pequenos", "cuidador_idoso"]
    for key in required_family:
        if key not in FAMILY_PRESSURE_MAP:
            all_validation_failures.append(f"FAMILY_PRESSURE_MAP missing: {key}")

    # Test 8: Family pressure factors are in [0, 1]
    total_tests += 1
    for key, value in FAMILY_PRESSURE_MAP.items():
        if not 0.0 <= value <= 1.0:
            all_validation_failures.append(f"FAMILY_PRESSURE_MAP[{key}]={value} not in [0,1]")

    # Test 9: "sozinho" has low pressure
    total_tests += 1
    if FAMILY_PRESSURE_MAP.get("sozinho", 1.0) > 0.3:
        all_validation_failures.append(
            f"'sozinho' should have low pressure, got {FAMILY_PRESSURE_MAP.get('sozinho')}"
        )

    # Test 10: "filhos_pequenos" has high pressure
    total_tests += 1
    if FAMILY_PRESSURE_MAP.get("filhos_pequenos", 0.0) < 0.5:
        val = FAMILY_PRESSURE_MAP.get("filhos_pequenos")
        all_validation_failures.append(f"'filhos_pequenos' should have high pressure, got {val}")

    # Test 11: calculate_max_disability_severity returns 0.8 for severe types
    total_tests += 1
    for severe_type in ["severa", "cegueira", "surdez"]:
        test_cases = [
            {"motora": {"tipo": severe_type}},
            {"visual": {"tipo": severe_type}},
            {"auditiva": {"tipo": severe_type}},
        ]
        for defic in test_cases:
            result = calculate_max_disability_severity(defic)
            if result != 0.8:
                all_validation_failures.append(
                    f"calculate_max_disability_severity({defic}) should return 0.8, got {result}"
                )

    # Test 12: calculate_max_disability_severity returns 0.0 for no disabilities
    total_tests += 1
    no_disability = {
        "visual": {"tipo": "nenhuma"},
        "auditiva": {"tipo": "nenhuma"},
        "motora": {"tipo": "nenhuma"},
        "cognitiva": {"tipo": "nenhuma"},
    }
    result = calculate_max_disability_severity(no_disability)
    if result != 0.0:
        all_validation_failures.append(
            f"calculate_max_disability_severity with no disabilities should return 0.0, got {result}"
        )

    # Test 13: calculate_max_disability_severity returns max severity for moderate
    total_tests += 1
    moderate = {
        "visual": {"tipo": "leve"},
        "motora": {"tipo": "moderada"},
    }
    result = calculate_max_disability_severity(moderate)
    # motora_moderada has severity 0.5, visual_leve has 0.2
    if result != 0.5:
        all_validation_failures.append(
            f"calculate_max_disability_severity with moderate should return 0.5, got {result}"
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
        print("Demographic factor maps ready for use")
        sys.exit(0)
