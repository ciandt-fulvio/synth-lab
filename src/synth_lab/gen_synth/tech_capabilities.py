"""
Technology capabilities generation module for SynthLab.

This module generates digital literacy scores correlated with age and education.

Functions:
- generate_tech_capabilities(): Generate technology capability profile

Sample Input:
    demographics = {"idade": 32, "escolaridade": "Superior completo"}
    disabilities = {"visual": {"tipo": "nenhuma"}, ...}
    tech_caps = generate_tech_capabilities(demographics, disabilities)

Expected Output:
    {
        "alfabetizacao_digital": 75
    }

Third-party packages:
- None (uses standard library only)
"""

from typing import Any

from .utils import escolaridade_index


def generate_tech_capabilities(
    demographics: dict[str, Any], disabilities: dict[str, Any]
) -> dict[str, Any]:
    """
    Gera capacidades tecnológicas correlacionadas com idade e escolaridade.

    Technology capabilities are correlated with:
    - Age: Younger people have higher digital literacy
    - Education: Higher education correlates with better tech skills

    Args:
        demographics: Dictionary with demographic data (idade, escolaridade)
        disabilities: Dictionary with disability data (not used, kept for interface)

    Returns:
        dict[str, Any]: Technology capability profile with alfabetizacao_digital
    """
    idade = demographics["idade"]
    escolaridade = demographics["escolaridade"]

    # Alfabetização digital correlacionada negativamente com idade
    # e positivamente com escolaridade
    base_digital = 80 - (idade * 0.5)
    bonus_escolaridade = escolaridade_index(escolaridade) * 5
    alfabetizacao = max(10, min(100, int(base_digital + bonus_escolaridade)))

    return {
        "alfabetizacao_digital": alfabetizacao,
    }


if __name__ == "__main__":
    """Validation block - test with real data."""
    import random
    import sys

    print("=== Tech Capabilities Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Generate tech capabilities for young educated person
    total_tests += 1
    try:
        young_educated = {"idade": 25, "escolaridade": "Superior completo"}
        no_disabilities = {
            "visual": {"tipo": "nenhuma"},
            "auditiva": {"tipo": "nenhuma"},
            "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
            "cognitiva": {"tipo": "nenhuma"},
        }
        tech_caps = generate_tech_capabilities(young_educated, no_disabilities)

        # Verify structure - only alfabetizacao_digital
        if "alfabetizacao_digital" not in tech_caps:
            all_validation_failures.append("Missing field: alfabetizacao_digital")

        # Young educated should have high digital literacy
        if tech_caps["alfabetizacao_digital"] < 50:
            all_validation_failures.append(
                f"Young educated person should have high digital literacy, "
                f"got {tech_caps['alfabetizacao_digital']}"
            )
        else:
            print(
                f"Test 1: generate_tech_capabilities(young/educated) -> "
                f"alfabetizacao_digital={tech_caps['alfabetizacao_digital']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 1 (young educated tech caps): {str(e)}")

    # Test 2: Generate tech capabilities for old person with low education
    total_tests += 1
    try:
        old_low_edu = {"idade": 70, "escolaridade": "Fundamental incompleto"}
        no_disabilities = {
            "visual": {"tipo": "nenhuma"},
            "auditiva": {"tipo": "nenhuma"},
            "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
            "cognitiva": {"tipo": "nenhuma"},
        }
        tech_caps = generate_tech_capabilities(old_low_edu, no_disabilities)

        # Old person with low education should have lower digital literacy
        if tech_caps["alfabetizacao_digital"] > 70:
            all_validation_failures.append(
                f"Old person with low education should have lower digital literacy, "
                f"got {tech_caps['alfabetizacao_digital']}"
            )
        else:
            print(
                f"Test 2: generate_tech_capabilities(old/low edu) -> "
                f"alfabetizacao_digital={tech_caps['alfabetizacao_digital']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 2 (old low edu tech caps): {str(e)}")

    # Test 3: Batch consistency test
    total_tests += 1
    try:
        batch_errors = []
        for i in range(10):
            test_demo = {
                "idade": random.randint(18, 80),
                "escolaridade": random.choice(
                    [
                        "Sem instrução",
                        "Fundamental incompleto",
                        "Médio completo",
                        "Superior completo",
                        "Pós-graduação",
                    ]
                ),
            }
            test_disabilities = {
                "visual": {"tipo": random.choice(["nenhuma", "leve", "severa"])},
                "auditiva": {"tipo": "nenhuma"},
                "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
                "cognitiva": {"tipo": "nenhuma"},
            }
            tech_caps = generate_tech_capabilities(test_demo, test_disabilities)

            # Verify alfabetizacao_digital is in range
            if not (10 <= tech_caps["alfabetizacao_digital"] <= 100):
                batch_errors.append(
                    f"Batch {i}: alfabetizacao_digital out of range: "
                    f"{tech_caps['alfabetizacao_digital']}"
                )

        if batch_errors:
            all_validation_failures.extend(batch_errors)
        else:
            print("Test 3: Batch of 10 tech capabilities all valid")
    except Exception as e:
        all_validation_failures.append(f"Test 3 (batch consistency): {str(e)}")

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
