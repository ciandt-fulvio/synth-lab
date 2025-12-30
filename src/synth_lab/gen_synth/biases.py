"""
Behavioral biases generation module for SynthLab.

This module generates behavioral/cognitive biases based on behavioral economics
and psychology research. Includes 7 key biases that affect decision-making.

Functions:
- generate_behavioral_biases(): Generate behavioral bias profile (deprecated)
- get_coherence_expectations(personality): Get expected bias ranges from personality
- generate_biases_with_coherence(personality): Generate biases coherent with personality

Sample Input:
    biases = generate_behavioral_biases()
    # OR with coherence:
    personality = {"abertura": 80, "conscienciosidade": 70, ...}
    biases = generate_biases_with_coherence(personality)

Expected Output:
    {
        "aversao_perda": 65,
        "desconto_hiperbolico": 48,
        "suscetibilidade_chamariz": 52,
        "ancoragem": 58,
        "vies_confirmacao": 62,
        "vies_status_quo": 55,
        "sobrecarga_informacao": 47
    }

Third-party packages:
- None (uses standard library only)

Behavioral biases explained:
- aversao_perda: Loss aversion (losses feel worse than equivalent gains)
- desconto_hiperbolico: Hyperbolic discounting (prefer immediate rewards)
- suscetibilidade_chamariz: Decoy effect susceptibility
- ancoragem: Anchoring bias (reliance on first information)
- vies_confirmacao: Confirmation bias
- vies_status_quo: Status quo bias (preference for current state)
- sobrecarga_informacao: Information overload susceptibility

Personality-Bias Coherence Rules (User Story 2):
Based on psychological research linking Big Five personality traits to cognitive biases.
See spec.md FR-003 for complete mapping definitions.
"""

from .utils import normal_distribution

# Personality-Bias Coherence Rules (User Story 2)
# Maps Big Five personality traits to expected cognitive bias ranges
# Format: (trait_name, trait_range, bias_name, bias_range)
COHERENCE_RULES = [
    # High Conscientiousness (70-100)
    ("conscienciosidade", (70, 100), "vies_status_quo", (70, 90)),
    ("conscienciosidade", (70, 100), "desconto_hiperbolico", (10, 30)),
    # Low Conscientiousness (0-30)
    ("conscienciosidade", (0, 30), "vies_status_quo", (10, 35)),
    ("conscienciosidade", (0, 30), "desconto_hiperbolico", (60, 85)),
    # High Neuroticism (70-100)
    ("neuroticismo", (70, 100), "aversao_perda", (70, 95)),
    ("neuroticismo", (70, 100), "sobrecarga_informacao", (60, 85)),
    # Low Neuroticism (0-30)
    ("neuroticismo", (0, 30), "aversao_perda", (10, 35)),
    ("neuroticismo", (0, 30), "sobrecarga_informacao", (15, 40)),
    # High Openness (70-100)
    ("abertura", (70, 100), "vies_confirmacao", (10, 35)),
    ("abertura", (70, 100), "sobrecarga_informacao", (15, 40)),
    # Low Openness (0-30)
    ("abertura", (0, 30), "vies_confirmacao", (60, 85)),
    ("abertura", (0, 30), "vies_status_quo", (60, 85)),
    # High Agreeableness (70-100)
    ("amabilidade", (70, 100), "vies_confirmacao", (15, 40)),
    ("amabilidade", (70, 100), "ancoragem", (40, 60)),
    # Low Agreeableness (0-30)
    ("amabilidade", (0, 30), "vies_confirmacao", (65, 90)),
    ("amabilidade", (0, 30), "ancoragem", (60, 85)),
    # High Extraversion (70-100)
    ("extroversao", (70, 100), "desconto_hiperbolico", (50, 80)),
    ("extroversao", (70, 100), "sobrecarga_informacao", (20, 45)),
    # Low Extraversion (0-30)
    ("extroversao", (0, 30), "desconto_hiperbolico", (20, 50)),
    ("extroversao", (0, 30), "sobrecarga_informacao", (45, 70)),
]


def get_coherence_expectations(personality: dict[str, int]) -> dict[str, dict[str, int]]:
    """
    Calcula os ranges esperados para cada viés baseado na personalidade Big Five.

    Para cada viés cognitivo, determina os valores mínimo e máximo esperados
    baseado nos traços de personalidade e nas regras de coerência definidas.

    Quando múltiplas regras afetam o mesmo viés (conflito), usa média ponderada
    dos ranges para criar um compromisso entre as regras.

    Args:
        personality: Dictionary com os 5 traços Big Five (0-100 scale)

    Returns:
        dict[str, dict[str, int]]: Para cada viés, retorna {"min": X, "max": Y}

    Example:
        >>> personality = {"abertura": 85, "conscienciosidade": 70, ...}
        >>> expectations = get_coherence_expectations(personality)
        >>> expectations["vies_confirmacao"]
        {"min": 10, "max": 35}  # Low due to high openness
    """
    # Default ranges for biases (moderate, allow natural variation)
    # Used when no specific rule applies or as fallback
    default_ranges = {
        "aversao_perda": {"min": 30, "max": 70},
        "desconto_hiperbolico": {"min": 30, "max": 70},
        "suscetibilidade_chamariz": {"min": 30, "max": 70},
        "ancoragem": {"min": 30, "max": 70},
        "vies_confirmacao": {"min": 30, "max": 70},
        "vies_status_quo": {"min": 30, "max": 70},
        "sobrecarga_informacao": {"min": 30, "max": 70},
    }

    # Accumulate applicable rules for each bias
    bias_constraints: dict[str, list[tuple[int, int]]] = {
        bias: [] for bias in default_ranges.keys()
    }

    # Check each rule and collect applicable constraints
    for trait_name, trait_range, bias_name, bias_range in COHERENCE_RULES:
        trait_value = personality.get(trait_name, 50)
        trait_min, trait_max = trait_range

        # Check if this rule applies to current personality
        if trait_min <= trait_value <= trait_max:
            bias_constraints[bias_name].append(bias_range)

    # Calculate final expectations for each bias
    expectations = {}
    for bias_name, constraints in bias_constraints.items():
        if not constraints:
            # No specific rule applies, use default
            expectations[bias_name] = default_ranges[bias_name].copy()
        elif len(constraints) == 1:
            # Single rule applies, use it directly
            bias_min, bias_max = constraints[0]
            expectations[bias_name] = {"min": bias_min, "max": bias_max}
        else:
            # Multiple rules apply, use weighted average
            # This handles cases like sobrecarga_informacao affected by
            # multiple traits (neuroticismo, abertura, extroversao)
            avg_min = sum(c[0] for c in constraints) // len(constraints)
            avg_max = sum(c[1] for c in constraints) // len(constraints)

            # Check if rules reinforce or conflict
            # Rules reinforce if all push in same direction (all high or all low)
            all_high = all(c[0] >= 50 for c in constraints)  # All push high
            all_low = all(c[1] <= 50 for c in constraints)  # All push low
            reinforce = all_high or all_low

            # For reinforcing rules, use the averaged range as-is
            # For conflicting rules, ensure wider range (at least 30 points) for natural variation
            if not reinforce and avg_max - avg_min < 30:
                # Widen the range to allow natural variation when rules conflict
                midpoint = (avg_min + avg_max) // 2
                avg_min = max(0, midpoint - 15)
                avg_max = min(100, midpoint + 15)

            expectations[bias_name] = {"min": avg_min, "max": avg_max}

    return expectations


def generate_biases_with_coherence(personality: dict[str, int]) -> dict[str, int]:
    """
    Gera vieses comportamentais coerentes com a personalidade Big Five.

    Em vez de usar distribuição normal centrada em 50 para todos,
    usa ranges específicos derivados dos traços de personalidade para
    garantir coerência psicológica.

    Args:
        personality: Dictionary com os 5 traços Big Five (0-100 scale)

    Returns:
        dict[str, int]: Dictionary com 7 vieses comportamentais (0-100 scale)
                       com valores coerentes com a personalidade

    Example:
        >>> personality = {"abertura": 85, "conscienciosidade": 20, ...}
        >>> biases = generate_biases_with_coherence(personality)
        >>> biases["vies_confirmacao"]  # Low due to high openness
        25
        >>> biases["desconto_hiperbolico"]  # High due to low conscientiousness
        70
    """
    # Get expected ranges for each bias based on personality
    expectations = get_coherence_expectations(personality)

    # Generate bias values within expected ranges
    biases = {}
    for bias_name, expectation in expectations.items():
        bias_min = expectation["min"]
        bias_max = expectation["max"]

        # Calculate mean and std for this bias's expected range
        mean = (bias_min + bias_max) / 2
        # Std is roughly 1/4 of the range (95% of values within range)
        std = (bias_max - bias_min) / 4

        # Generate value using normal distribution within expected range
        value = normal_distribution(mean, std, bias_min, bias_max)
        biases[bias_name] = value

    return biases


def generate_behavioral_biases() -> dict[str, int]:
    """
    Gera 7 vieses comportamentais com Normal(μ=50, σ=20).

    These biases affect decision-making and are measured on a 0-100 scale
    where higher values indicate stronger susceptibility to the bias.

    Returns:
        dict[str, int]: Dictionary with 7 behavioral biases (0-100 scale)
    """
    return {
        "aversao_perda": normal_distribution(50, 20, 0, 100),
        "desconto_hiperbolico": normal_distribution(50, 20, 0, 100),
        "suscetibilidade_chamariz": normal_distribution(50, 20, 0, 100),
        "ancoragem": normal_distribution(50, 20, 0, 100),
        "vies_confirmacao": normal_distribution(50, 20, 0, 100),
        "vies_status_quo": normal_distribution(50, 20, 0, 100),
        "sobrecarga_informacao": normal_distribution(50, 20, 0, 100),
    }


if __name__ == "__main__":
    """Validation block - test with real data."""
    import sys

    print("=== Behavioral Biases Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Generate behavioral biases
    total_tests += 1
    try:
        biases = generate_behavioral_biases()

        required_biases = [
            "aversao_perda",
            "desconto_hiperbolico",
            "suscetibilidade_chamariz",
            "ancoragem",
            "vies_confirmacao",
            "vies_status_quo",
            "sobrecarga_informacao",
        ]

        for bias in required_biases:
            if bias not in biases:
                all_validation_failures.append(f"Missing bias: {bias}")
            elif not (0 <= biases[bias] <= 100):
                all_validation_failures.append(f"Bias {bias} out of range: {biases[bias]}")

        if not all_validation_failures:
            print(
                f"Test 1: generate_behavioral_biases() -> "
                f"aversao_perda={biases['aversao_perda']}, "
                f"ancoragem={biases['ancoragem']}, "
                f"vies_confirmacao={biases['vies_confirmacao']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 1 (generate_behavioral_biases): {str(e)}")

    # Test 2: Verify all 7 biases are present
    total_tests += 1
    try:
        biases = generate_behavioral_biases()
        if len(biases) != 7:
            all_validation_failures.append(f"Expected 7 biases, got {len(biases)}")
        else:
            print("Test 2: All 7 biases present in output")
    except Exception as e:
        all_validation_failures.append(f"Test 2 (bias count): {str(e)}")

    # Test 3: Verify distribution is centered around 50
    total_tests += 1
    try:
        samples = [generate_behavioral_biases() for _ in range(100)]
        avg_aversao_perda = sum(s["aversao_perda"] for s in samples) / len(samples)

        # Average should be roughly around 50 (allow 40-60 range for 100 samples)
        if not (40 <= avg_aversao_perda <= 60):
            all_validation_failures.append(
                f"Distribution not centered: avg aversao_perda={avg_aversao_perda} (expected 40-60)"
            )
        else:
            print(f"Test 3: Distribution centered around mean -> avg={avg_aversao_perda:.1f}")
    except Exception as e:
        all_validation_failures.append(f"Test 3 (distribution center): {str(e)}")

    # Test 4: Verify biases have variety (not all the same value)
    total_tests += 1
    try:
        biases = generate_behavioral_biases()
        unique_values = len(set(biases.values()))

        # With 7 biases and normal distribution, should have some variety
        if unique_values < 3:
            all_validation_failures.append(
                f"Biases lack variety: only {unique_values} unique values"
            )
        else:
            print(f"Test 4: Biases have variety -> {unique_values} unique values")
    except Exception as e:
        all_validation_failures.append(f"Test 4 (bias variety): {str(e)}")

    # Test 5: Verify each bias independently varies
    total_tests += 1
    try:
        bias_ranges = {
            "aversao_perda": set(),
            "desconto_hiperbolico": set(),
            "suscetibilidade_chamariz": set(),
            "ancoragem": set(),
            "vies_confirmacao": set(),
            "vies_status_quo": set(),
            "sobrecarga_informacao": set(),
        }

        for _ in range(50):
            biases = generate_behavioral_biases()
            for bias_name, value in biases.items():
                bias_ranges[bias_name].add(value)

        # Each bias should have at least 10 different values in 50 samples
        for bias_name, values in bias_ranges.items():
            if len(values) < 10:
                all_validation_failures.append(
                    f"Bias {bias_name} lacks variety: only {len(values)} unique values in 50 samples"
                )

        if not any(f.startswith("Test 5") for f in all_validation_failures):
            print(
                f"Test 5: Each bias varies independently -> "
                f"aversao_perda has {len(bias_ranges['aversao_perda'])} values, "
                f"ancoragem has {len(bias_ranges['ancoragem'])} values"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 5 (individual bias variety): {str(e)}")

    # Test 6: Batch consistency test
    total_tests += 1
    try:
        batch_errors = []
        for i in range(20):
            biases = generate_behavioral_biases()

            # Verify each bias is in valid range
            for bias_name, value in biases.items():
                if not (0 <= value <= 100):
                    batch_errors.append(f"Batch {i}: {bias_name} out of range: {value}")

            # Verify we have exactly 7 biases
            if len(biases) != 7:
                batch_errors.append(f"Batch {i}: Expected 7 biases, got {len(biases)}")

        if batch_errors:
            all_validation_failures.extend(batch_errors)
        else:
            print("Test 6: Batch of 20 bias profiles all valid")
    except Exception as e:
        all_validation_failures.append(f"Test 6 (batch consistency): {str(e)}")

    # Final validation result
    print(f"\n{'=' * 60}")
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)
