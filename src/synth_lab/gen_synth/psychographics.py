"""
Psychographics generation module for Synth Lab.

This module generates psychographic attributes including Big Five personality traits,
values, interests, hobbies, political and religious inclinations.

Functions:
- generate_big_five(): Generate Big Five personality traits
- generate_psychographics(): Generate complete psychographic profile

Sample Input:
    big_five = generate_big_five()
    psycho = generate_psychographics(big_five, config_data)

Expected Output:
    {
        "personalidade_big_five": {
            "abertura": 65,
            "conscienciosidade": 72,
            "extroversao": 45,
            "amabilidade": 58,
            "neuroticismo": 42
        },
        "interesses": ["tecnologia", "esportes"],  # 1-4 itens, correlacionado com abertura
        "inclinacao_politica": 45,  # Correlacionado com religião
        "inclinacao_religiosa": "católico"  # Católicos/evangélicos tendem à direita
    }

Third-party packages:
- None (uses standard library only)
"""

import random
from typing import Any

from .utils import normal_distribution, weighted_choice


def generate_big_five() -> dict[str, int]:
    """
    Gera traços de personalidade Big Five com distribuição Normal(μ=50, σ=15).

    Big Five personality traits are the most scientifically validated
    personality model, measuring: Openness, Conscientiousness, Extraversion,
    Agreeableness, and Neuroticism.

    Returns:
        dict[str, int]: Dictionary with 5 personality traits (0-100 scale)
    """
    return {
        "abertura": normal_distribution(50, 15, 0, 100),
        "conscienciosidade": normal_distribution(50, 15, 0, 100),
        "extroversao": normal_distribution(50, 15, 0, 100),
        "amabilidade": normal_distribution(50, 15, 0, 100),
        "neuroticismo": normal_distribution(50, 15, 0, 100),
    }


def generate_psychographics(
    big_five: dict[str, int], config_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Gera atributos psicográficos (interesses, política, religião).

    Correlações implementadas:
    - Católicos e evangélicos têm maior probabilidade de serem de direita
    - Interesses correlacionados com abertura (1-4 itens)

    Args:
        big_five: Dictionary with Big Five personality traits
        config_data: Configuration data including IBGE and interests/hobbies

    Returns:
        dict[str, Any]: Complete psychographic profile
    """
    ibge = config_data["ibge"]
    interests = config_data["interests_hobbies"]

    # Interesses (1-4 itens, correlacionados com abertura)
    # Abertura baixa (0-40): 1-2 interesses
    # Abertura média (41-70): 2-3 interesses
    # Abertura alta (71-100): 3-4 interesses
    if big_five["abertura"] <= 40:
        num_interesses = random.randint(1, 2)
    elif big_five["abertura"] <= 70:
        num_interesses = random.randint(2, 3)
    else:
        num_interesses = random.randint(3, 4)

    interesses_list = random.sample(interests["interesses"], k=num_interesses)

    # Inclinação religiosa primeiro (afeta política)
    inclinacao_religiosa = weighted_choice(ibge["religiao"])

    # Inclinação política correlacionada com religião
    # Católicos e evangélicos têm maior probabilidade de serem de direita
    if inclinacao_religiosa in ["católico", "evangélico"]:
        # 60% direita, 20% centro, 10% esquerda, 10% outros
        categoria_weights = {
            "direita": 0.60,
            "centro": 0.20,
            "esquerda": 0.10,
            "neutro": 0.05,
            "nao_sabe": 0.05,
        }
        categoria = weighted_choice(categoria_weights)
    else:
        # Usa distribuição normal do IBGE para outras religiões
        distribuicao = ibge["inclinacao_politica_distribuicao"]
        categoria = weighted_choice(distribuicao)

    # Gera valor numérico baseado na categoria
    if categoria == "esquerda":
        inclinacao_politica = random.randint(-100, -20)
    elif categoria == "direita":
        inclinacao_politica = random.randint(20, 100)
    elif categoria == "centro":
        inclinacao_politica = random.randint(-20, 20)
    elif categoria == "neutro":
        inclinacao_politica = random.randint(-10, 10)
    else:  # nao_sabe
        inclinacao_politica = 0

    return {
        "personalidade_big_five": big_five,
        "interesses": interesses_list,
        "inclinacao_politica": inclinacao_politica,
        "inclinacao_religiosa": inclinacao_religiosa,
    }


if __name__ == "__main__":
    """Validation block - test with real data."""
    import sys

    from .config import load_config_data

    print("=== Psychographics Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Load config
    try:
        config = load_config_data()
    except Exception as e:
        print(f"Failed to load config: {e}")
        sys.exit(1)

    # Test 1: Generate Big Five traits
    total_tests += 1
    try:
        big_five = generate_big_five()
        required_traits = ["abertura", "conscienciosidade", "extroversao", "amabilidade", "neuroticismo"]
        for trait in required_traits:
            if trait not in big_five:
                all_validation_failures.append(f"Big Five missing trait: {trait}")
            elif not (0 <= big_five[trait] <= 100):
                all_validation_failures.append(
                    f"Big Five trait {trait} out of range: {big_five[trait]}"
                )
        if not all_validation_failures:
            print(
                f"Test 1: generate_big_five() -> abertura={big_five['abertura']}, "
                f"extroversao={big_five['extroversao']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 1 (generate_big_five): {str(e)}")

    # Test 2: Generate psychographics with low openness
    total_tests += 1
    try:
        low_openness = {
            "abertura": 20,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        psycho = generate_psychographics(low_openness, config)

        if "personalidade_big_five" not in psycho:
            all_validation_failures.append("Psychographics missing personalidade_big_five")
        if "interesses" not in psycho or len(psycho["interesses"]) < 1 or len(psycho["interesses"]) > 4:
            all_validation_failures.append(
                f"Psychographics interesses should be 1-4: {psycho.get('interesses')}"
            )
        if "inclinacao_politica" not in psycho:
            all_validation_failures.append("Psychographics missing inclinacao_politica")
        elif not (-100 <= psycho["inclinacao_politica"] <= 100):
            all_validation_failures.append(
                f"Inclinacao politica out of range: {psycho['inclinacao_politica']}"
            )
        if "inclinacao_religiosa" not in psycho:
            all_validation_failures.append("Psychographics missing inclinacao_religiosa")

        if not any(f.startswith("Test 2") for f in all_validation_failures):
            print(
                f"Test 2: generate_psychographics(low openness) -> "
                f"{len(psycho['interesses'])} interesses, politica={psycho['inclinacao_politica']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 2 (psychographics low openness): {str(e)}")

    # Test 3: Generate psychographics with high openness
    total_tests += 1
    try:
        high_openness = {
            "abertura": 90,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        psycho = generate_psychographics(high_openness, config)

        # High openness should correlate with more interests (3-4 range)
        num_interests = len(psycho["interesses"])
        if num_interests < 3:
            all_validation_failures.append(
                f"High openness should have 3-4 interests, got {num_interests}"
            )
        else:
            print(
                f"Test 3: generate_psychographics(high openness) -> "
                f"{num_interests} interesses (expected 3-4)"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 3 (psychographics high openness): {str(e)}")

    # Test 4: Verify political inclination categories
    total_tests += 1
    try:
        test_big_five = generate_big_five()
        political_counts = {
            "esquerda": 0,
            "direita": 0,
            "centro": 0,
            "neutro": 0,
            "nao_sabe": 0,
        }

        for _ in range(50):
            psycho = generate_psychographics(test_big_five, config)
            pol = psycho["inclinacao_politica"]
            if pol < -20:
                political_counts["esquerda"] += 1
            elif pol > 20:
                political_counts["direita"] += 1
            elif -20 <= pol <= 20 and pol != 0:
                political_counts["centro"] += 1
            elif pol == 0:
                political_counts["nao_sabe"] += 1
            else:
                political_counts["neutro"] += 1

        # Should have some distribution across categories
        categories_with_values = sum(1 for v in political_counts.values() if v > 0)
        if categories_with_values < 2:
            all_validation_failures.append(
                f"Political distribution too narrow: {political_counts}"
            )
        else:
            print(f"Test 4: Political distribution across {categories_with_values} categories")
    except Exception as e:
        all_validation_failures.append(f"Test 4 (political distribution): {str(e)}")

    # Test 5: Verify religious inclination
    total_tests += 1
    try:
        test_big_five = generate_big_five()
        religious_values = set()
        for _ in range(20):
            psycho = generate_psychographics(test_big_five, config)
            religious_values.add(psycho["inclinacao_religiosa"])

        # Should have at least 2 different religious values in 20 samples
        if len(religious_values) < 2:
            all_validation_failures.append(
                f"Religious distribution too narrow: {religious_values}"
            )
        else:
            print(f"Test 5: Religious distribution has {len(religious_values)} different values")
    except Exception as e:
        all_validation_failures.append(f"Test 5 (religious distribution): {str(e)}")

    # Test 6: Batch consistency test
    total_tests += 1
    try:
        batch_errors = []
        for i in range(10):
            big_five = generate_big_five()
            psycho = generate_psychographics(big_five, config)

            # Verify all required fields
            if len(psycho["interesses"]) < 1 or len(psycho["interesses"]) > 4:
                batch_errors.append(
                    f"Batch {i}: interesses should be 1-4: {len(psycho['interesses'])}"
                )
            if not (-100 <= psycho["inclinacao_politica"] <= 100):
                batch_errors.append(
                    f"Batch {i}: inclinacao_politica out of range: {psycho['inclinacao_politica']}"
                )

        if batch_errors:
            all_validation_failures.extend(batch_errors)
        else:
            print("Test 6: Batch of 10 psychographics all valid")
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
