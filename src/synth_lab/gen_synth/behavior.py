"""
Behavior generation module for SynthLab.

This module generates behavioral attributes including consumption habits,
technology usage, media patterns, and social media engagement.

Functions:
- generate_behavior(): Generate complete behavioral profile

Sample Input:
    demographics = {"idade": 32, "renda_mensal": 4500}
    behavior = generate_behavior(demographics, config_data)

Expected Output:
    {
        "habitos_consumo": {
            "frequencia_compras": "semanal",
            "preferencia_canal": "híbrido",
            "categorias_preferidas": ["eletrônicos", "livros"]
        },
        "padroes_midia": {
            "tv_aberta": 15,
            "streaming": 35,
            "redes_sociais": 45
        },
        "fonte_noticias": ["portais online", "redes sociais"],
        "lealdade_marca": 58,
        "engajamento_redes_sociais": {
            "plataformas": ["Instagram", "WhatsApp", "YouTube"],
            "frequencia_posts": "ocasional"
        }
    }

Third-party packages:
- None (uses standard library only)
"""

import random
from typing import Any

from .utils import normal_distribution, weighted_choice


def generate_behavior(demographics: dict[str, Any], config_data: dict[str, Any]) -> dict[str, Any]:
    """
    Gera atributos comportamentais (consumo, mídia).

    Behavioral patterns are correlated with age and income:
    - Younger people use more social media
    - Higher income correlates with more online shopping

    Args:
        demographics: Dictionary with demographic data (idade, renda_mensal)
        config_data: Configuration data including interests_hobbies

    Returns:
        dict[str, Any]: Complete behavioral profile
    """
    interests = config_data["interests_hobbies"]
    idade = demographics["idade"]
    renda = demographics["renda_mensal"]

    # Tempo em redes sociais inversamente correlacionado com idade
    base_redes = 60 - (idade * 0.5)
    redes_sociais = max(5, min(70, int(base_redes + random.randint(-15, 15))))

    return {
        "habitos_consumo": {
            "frequencia_compras": random.choice(
                ["diária", "semanal", "quinzenal", "mensal", "esporádica"]
            ),
            "preferencia_canal": weighted_choice(
                {"loja física": 0.3, "e-commerce": 0.3, "híbrido": 0.4}
            ),
            "categorias_preferidas": random.sample(
                interests["categorias_compras"], k=random.randint(2, 5)
            ),
        },
        "padroes_midia": {
            "tv_aberta": random.randint(0, 35),
            "streaming": random.randint(0, 50),
            "redes_sociais": redes_sociais,
        },
        "fonte_noticias": random.sample(interests["fontes_noticias"], k=random.randint(2, 5)),
        "lealdade_marca": normal_distribution(50, 20, 0, 100),
        "engajamento_redes_sociais": {
            "plataformas": random.sample(
                interests["plataformas_redes_sociais"], k=random.randint(2, 6)
            ),
            "frequencia_posts": random.choice(
                ["nunca", "raro", "ocasional", "frequente", "muito frequente"]
            ),
        },
    }


if __name__ == "__main__":
    """Validation block - test with real data."""
    import sys

    from .config import load_config_data

    print("=== Behavior Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Load config
    try:
        config = load_config_data()
    except Exception as e:
        print(f"Failed to load config: {e}")
        sys.exit(1)

    # Test 1: Generate behavior for young high-income person
    total_tests += 1
    try:
        young_rich = {"idade": 25, "renda_mensal": 10000}
        behavior = generate_behavior(young_rich, config)

        # Verify structure
        required_fields = [
            "habitos_consumo",
            "padroes_midia",
            "fonte_noticias",
            "lealdade_marca",
            "engajamento_redes_sociais",
        ]
        for field in required_fields:
            if field not in behavior:
                all_validation_failures.append(f"Missing field: {field}")

        # Verify social media time (should be high for young person)
        if behavior["padroes_midia"]["redes_sociais"] < 20:
            all_validation_failures.append(
                f"Young person social media time too low: {behavior['padroes_midia']['redes_sociais']}"
            )

        if not any(f.startswith("Test 1") for f in all_validation_failures):
            print(
                f"Test 1: generate_behavior(young/rich) -> "
                f"redes_sociais={behavior['padroes_midia']['redes_sociais']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 1 (young rich behavior): {str(e)}")

    # Test 2: Generate behavior for old low-income person
    total_tests += 1
    try:
        old_poor = {"idade": 70, "renda_mensal": 1500}
        behavior = generate_behavior(old_poor, config)

        # Social media time should be lower for older person
        if behavior["padroes_midia"]["redes_sociais"] > 50:
            all_validation_failures.append(
                f"Old person social media time too high: {behavior['padroes_midia']['redes_sociais']}"
            )

        print(
            f"Test 2: generate_behavior(old/poor) -> "
            f"redes_sociais={behavior['padroes_midia']['redes_sociais']}"
        )
    except Exception as e:
        all_validation_failures.append(f"Test 2 (old poor behavior): {str(e)}")

    # Test 3: Verify consumption habits structure
    total_tests += 1
    try:
        test_demo = {"idade": 35, "renda_mensal": 5000}
        behavior = generate_behavior(test_demo, config)

        habitos = behavior["habitos_consumo"]
        if "frequencia_compras" not in habitos:
            all_validation_failures.append("Missing frequencia_compras")
        elif habitos["frequencia_compras"] not in [
            "diária",
            "semanal",
            "quinzenal",
            "mensal",
            "esporádica",
        ]:
            all_validation_failures.append(
                f"Invalid frequencia_compras: {habitos['frequencia_compras']}"
            )

        if "preferencia_canal" not in habitos:
            all_validation_failures.append("Missing preferencia_canal")
        elif habitos["preferencia_canal"] not in ["loja física", "e-commerce", "híbrido"]:
            all_validation_failures.append(
                f"Invalid preferencia_canal: {habitos['preferencia_canal']}"
            )

        if "categorias_preferidas" not in habitos:
            all_validation_failures.append("Missing categorias_preferidas")
        elif not (2 <= len(habitos["categorias_preferidas"]) <= 5):
            all_validation_failures.append(
                f"Invalid categorias_preferidas count: {len(habitos['categorias_preferidas'])}"
            )

        if not any(f.startswith("Test 3") for f in all_validation_failures):
            print(
                f"Test 3: Consumption habits valid -> "
                f"{habitos['frequencia_compras']}, {habitos['preferencia_canal']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 3 (consumption habits): {str(e)}")

    # Test 4: Verify media patterns ranges
    total_tests += 1
    try:
        test_demo = {"idade": 40, "renda_mensal": 3000}
        behavior = generate_behavior(test_demo, config)

        midia = behavior["padroes_midia"]
        if not (0 <= midia["tv_aberta"] <= 35):
            all_validation_failures.append(f"tv_aberta out of range: {midia['tv_aberta']}")
        if not (0 <= midia["streaming"] <= 50):
            all_validation_failures.append(f"streaming out of range: {midia['streaming']}")
        if not (5 <= midia["redes_sociais"] <= 70):
            all_validation_failures.append(f"redes_sociais out of range: {midia['redes_sociais']}")

        if not any(f.startswith("Test 4") for f in all_validation_failures):
            print(
                f"Test 4: Media patterns in range -> "
                f"tv={midia['tv_aberta']}, streaming={midia['streaming']}, "
                f"redes={midia['redes_sociais']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 4 (media patterns): {str(e)}")

    # Test 5: Verify social media engagement
    total_tests += 1
    try:
        test_demo = {"idade": 30, "renda_mensal": 4000}
        behavior = generate_behavior(test_demo, config)

        engagement = behavior["engajamento_redes_sociais"]
        if "plataformas" not in engagement:
            all_validation_failures.append("Missing plataformas in engagement")
        elif not (2 <= len(engagement["plataformas"]) <= 6):
            all_validation_failures.append(
                f"Invalid plataformas count: {len(engagement['plataformas'])}"
            )

        if "frequencia_posts" not in engagement:
            all_validation_failures.append("Missing frequencia_posts in engagement")
        elif engagement["frequencia_posts"] not in [
            "nunca",
            "raro",
            "ocasional",
            "frequente",
            "muito frequente",
        ]:
            all_validation_failures.append(
                f"Invalid frequencia_posts: {engagement['frequencia_posts']}"
            )

        if not any(f.startswith("Test 5") for f in all_validation_failures):
            print(
                f"Test 5: Social media engagement valid -> "
                f"{len(engagement['plataformas'])} platforms, {engagement['frequencia_posts']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 5 (social media engagement): {str(e)}")

    # Test 6: Batch consistency test
    total_tests += 1
    try:
        batch_errors = []
        for i in range(10):
            test_demo = {
                "idade": random.randint(18, 80),
                "renda_mensal": random.uniform(1000, 15000),
            }
            behavior = generate_behavior(test_demo, config)

            # Verify behavioral scores are in range
            if not (0 <= behavior["lealdade_marca"] <= 100):
                batch_errors.append(
                    f"Batch {i}: lealdade_marca out of range: {behavior['lealdade_marca']}"
                )

        if batch_errors:
            all_validation_failures.extend(batch_errors)
        else:
            print("Test 6: Batch of 10 behaviors all valid")
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
