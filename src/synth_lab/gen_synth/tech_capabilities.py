"""
Technology capabilities generation module for Synth Lab.

This module generates technology-related capabilities including digital literacy,
device usage, accessibility preferences, and platform familiarity.

Functions:
- generate_tech_capabilities(): Generate complete technology capability profile

Sample Input:
    demographics = {"idade": 32, "escolaridade": "Superior completo"}
    disabilities = {"visual": {"tipo": "nenhuma"}, ...}
    tech_caps = generate_tech_capabilities(demographics, disabilities)

Expected Output:
    {
        "alfabetizacao_digital": 75,
        "dispositivos": {
            "principal": "smartphone",
            "qualidade": "novo"
        },
        "preferencias_acessibilidade": {
            "zoom_fonte": 100,
            "alto_contraste": False
        },
        "velocidade_digitacao": 60,
        "frequencia_internet": "diária",
        "familiaridade_plataformas": {
            "e_commerce": 72,
            "banco_digital": 68,
            "redes_sociais": 85
        }
    }

Third-party packages:
- None (uses standard library only)
"""

import random
from typing import Any

from .utils import escolaridade_index, normal_distribution, weighted_choice


def generate_tech_capabilities(
    demographics: dict[str, Any], disabilities: dict[str, Any]
) -> dict[str, Any]:
    """
    Gera capacidades tecnológicas correlacionadas com idade e escolaridade.

    Technology capabilities are correlated with:
    - Age: Younger people have higher digital literacy
    - Education: Higher education correlates with better tech skills
    - Disabilities: Visual impairments affect accessibility preferences

    Args:
        demographics: Dictionary with demographic data (idade, escolaridade)
        disabilities: Dictionary with disability data

    Returns:
        dict[str, Any]: Complete technology capability profile
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
        "dispositivos": {
            "principal": random.choice(["smartphone", "computador", "tablet"]),
            "qualidade": weighted_choice(
                {"novo": 0.3, "intermediário": 0.5, "antigo": 0.2}
            ),
        },
        "preferencias_acessibilidade": {
            "zoom_fonte": (
                100
                if disabilities["visual"]["tipo"] == "nenhuma"
                else random.randint(120, 200)
            ),
            "alto_contraste": disabilities["visual"]["tipo"] in ["severa", "cegueira"],
        },
        "velocidade_digitacao": max(10, min(120, 70 - idade // 2)),
        "frequencia_internet": random.choice(["diária", "semanal", "mensal", "rara"]),
        "familiaridade_plataformas": {
            "e_commerce": normal_distribution(50, 25, 0, 100),
            "banco_digital": normal_distribution(50, 25, 0, 100),
            "redes_sociais": normal_distribution(60, 25, 0, 100),
        },
    }


if __name__ == "__main__":
    """Validation block - test with real data."""
    import sys

    from .config import load_config_data

    print("=== Tech Capabilities Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Load config
    try:
        config = load_config_data()
    except Exception as e:
        print(f"Failed to load config: {e}")
        sys.exit(1)

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

        # Verify structure
        required_fields = [
            "alfabetizacao_digital",
            "dispositivos",
            "preferencias_acessibilidade",
            "velocidade_digitacao",
            "frequencia_internet",
            "familiaridade_plataformas",
        ]
        for field in required_fields:
            if field not in tech_caps:
                all_validation_failures.append(f"Missing field: {field}")

        # Young educated should have high digital literacy
        if tech_caps["alfabetizacao_digital"] < 50:
            all_validation_failures.append(
                f"Young educated person should have high digital literacy, "
                f"got {tech_caps['alfabetizacao_digital']}"
            )

        # No disabilities should have normal font zoom (100)
        if tech_caps["preferencias_acessibilidade"]["zoom_fonte"] != 100:
            all_validation_failures.append(
                f"No visual disability should have zoom_fonte=100, "
                f"got {tech_caps['preferencias_acessibilidade']['zoom_fonte']}"
            )

        # No disabilities should have alto_contraste=False
        if tech_caps["preferencias_acessibilidade"]["alto_contraste"] is not False:
            all_validation_failures.append(
                "No visual disability should have alto_contraste=False"
            )

        if not any(f.startswith("Test 1") for f in all_validation_failures):
            print(
                f"Test 1: generate_tech_capabilities(young/educated) -> "
                f"alfabetizacao_digital={tech_caps['alfabetizacao_digital']}, "
                f"velocidade_digitacao={tech_caps['velocidade_digitacao']}"
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

        # Old person should have lower typing speed
        if tech_caps["velocidade_digitacao"] > 50:
            all_validation_failures.append(
                f"Old person should have lower typing speed, "
                f"got {tech_caps['velocidade_digitacao']}"
            )

        if not any(f.startswith("Test 2") for f in all_validation_failures):
            print(
                f"Test 2: generate_tech_capabilities(old/low edu) -> "
                f"alfabetizacao_digital={tech_caps['alfabetizacao_digital']}, "
                f"velocidade_digitacao={tech_caps['velocidade_digitacao']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 2 (old low edu tech caps): {str(e)}")

    # Test 3: Generate tech capabilities for person with visual disability
    total_tests += 1
    try:
        middle_aged = {"idade": 45, "escolaridade": "Médio completo"}
        visual_disability = {
            "visual": {"tipo": "severa"},
            "auditiva": {"tipo": "nenhuma"},
            "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
            "cognitiva": {"tipo": "nenhuma"},
        }
        tech_caps = generate_tech_capabilities(middle_aged, visual_disability)

        # Severe visual disability should have high zoom_fonte
        if tech_caps["preferencias_acessibilidade"]["zoom_fonte"] < 120:
            all_validation_failures.append(
                f"Severe visual disability should have zoom_fonte >= 120, "
                f"got {tech_caps['preferencias_acessibilidade']['zoom_fonte']}"
            )

        # Severe visual disability should have alto_contraste=True
        if tech_caps["preferencias_acessibilidade"]["alto_contraste"] is not True:
            all_validation_failures.append(
                "Severe visual disability should have alto_contraste=True"
            )

        if not any(f.startswith("Test 3") for f in all_validation_failures):
            print(
                f"Test 3: generate_tech_capabilities(visual disability) -> "
                f"zoom_fonte={tech_caps['preferencias_acessibilidade']['zoom_fonte']}, "
                f"alto_contraste={tech_caps['preferencias_acessibilidade']['alto_contraste']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 3 (visual disability tech caps): {str(e)}")

    # Test 4: Verify device structure
    total_tests += 1
    try:
        test_demo = {"idade": 35, "escolaridade": "Superior completo"}
        no_disabilities = {
            "visual": {"tipo": "nenhuma"},
            "auditiva": {"tipo": "nenhuma"},
            "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
            "cognitiva": {"tipo": "nenhuma"},
        }
        tech_caps = generate_tech_capabilities(test_demo, no_disabilities)

        if "principal" not in tech_caps["dispositivos"]:
            all_validation_failures.append("Missing principal in dispositivos")
        elif tech_caps["dispositivos"]["principal"] not in ["smartphone", "computador", "tablet"]:
            all_validation_failures.append(
                f"Invalid principal device: {tech_caps['dispositivos']['principal']}"
            )

        if "qualidade" not in tech_caps["dispositivos"]:
            all_validation_failures.append("Missing qualidade in dispositivos")
        elif tech_caps["dispositivos"]["qualidade"] not in ["novo", "intermediário", "antigo"]:
            all_validation_failures.append(
                f"Invalid qualidade: {tech_caps['dispositivos']['qualidade']}"
            )

        if not any(f.startswith("Test 4") for f in all_validation_failures):
            print(
                f"Test 4: Device structure valid -> "
                f"{tech_caps['dispositivos']['principal']}, {tech_caps['dispositivos']['qualidade']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 4 (device structure): {str(e)}")

    # Test 5: Verify platform familiarity ranges
    total_tests += 1
    try:
        test_demo = {"idade": 40, "escolaridade": "Médio completo"}
        no_disabilities = {
            "visual": {"tipo": "nenhuma"},
            "auditiva": {"tipo": "nenhuma"},
            "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
            "cognitiva": {"tipo": "nenhuma"},
        }
        tech_caps = generate_tech_capabilities(test_demo, no_disabilities)

        familiaridade = tech_caps["familiaridade_plataformas"]
        if not (0 <= familiaridade["e_commerce"] <= 100):
            all_validation_failures.append(
                f"e_commerce familiarity out of range: {familiaridade['e_commerce']}"
            )
        if not (0 <= familiaridade["banco_digital"] <= 100):
            all_validation_failures.append(
                f"banco_digital familiarity out of range: {familiaridade['banco_digital']}"
            )
        if not (0 <= familiaridade["redes_sociais"] <= 100):
            all_validation_failures.append(
                f"redes_sociais familiarity out of range: {familiaridade['redes_sociais']}"
            )

        if not any(f.startswith("Test 5") for f in all_validation_failures):
            print(
                f"Test 5: Platform familiarity in range -> "
                f"e_commerce={familiaridade['e_commerce']}, "
                f"banco={familiaridade['banco_digital']}, "
                f"redes={familiaridade['redes_sociais']}"
            )
    except Exception as e:
        all_validation_failures.append(f"Test 5 (platform familiarity): {str(e)}")

    # Test 6: Batch consistency test
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

            # Verify velocidade_digitacao is in range
            if not (10 <= tech_caps["velocidade_digitacao"] <= 120):
                batch_errors.append(
                    f"Batch {i}: velocidade_digitacao out of range: "
                    f"{tech_caps['velocidade_digitacao']}"
                )

            # Verify zoom_fonte consistency with visual disability
            if test_disabilities["visual"]["tipo"] == "nenhuma":
                if tech_caps["preferencias_acessibilidade"]["zoom_fonte"] != 100:
                    batch_errors.append(
                        f"Batch {i}: No visual disability should have zoom_fonte=100, "
                        f"got {tech_caps['preferencias_acessibilidade']['zoom_fonte']}"
                    )

        if batch_errors:
            all_validation_failures.extend(batch_errors)
        else:
            print("Test 6: Batch of 10 tech capabilities all valid")
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
