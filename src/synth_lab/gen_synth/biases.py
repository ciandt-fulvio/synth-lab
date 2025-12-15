"""
Behavioral biases generation module for Synth Lab.

This module generates behavioral/cognitive biases based on behavioral economics
and psychology research. Includes 7 key biases that affect decision-making.

Functions:
- generate_behavioral_biases(): Generate behavioral bias profile

Sample Input:
    biases = generate_behavioral_biases()

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
"""

from .utils import normal_distribution


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
            print(f"Test 2: All 7 biases present in output")
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
    print(f"\n{'='*60}")
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)
