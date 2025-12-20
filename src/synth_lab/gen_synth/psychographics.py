"""
Psychographics generation module for Synth Lab.

This module generates psychographic attributes including Big Five personality traits,
values, interests, hobbies, and cognitive contracts.

Functions:
- generate_big_five(): Generate Big Five personality traits
- generate_cognitive_contract(): Generate cognitive contract for interview behavior
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
        "contrato_cognitivo": {
            "tipo": "factual",
            "perfil_cognitivo": "responde só ao que foi perguntado, evita abstrações",
            "regras": [...],
            "efeito_esperado": "respostas secas, muito factuais"
        }
    }

Third-party packages:
- None (uses standard library only)
"""

import random
from typing import Any

from .utils import normal_distribution

# Definição dos 6 contratos cognitivos
COGNITIVE_CONTRACTS = {
    "factual": {
        "tipo": "factual",
        "perfil_cognitivo": "responde só ao que foi perguntado, evita abstrações",
        "regras": [
            "Proibido dar opinião geral",
            "Proibido usar termos abstratos ('experiência', 'usabilidade', 'fluido')",
            "Sempre relatar um evento específico",
            "Respostas curtas e diretas",
            "Se não lembrar, dizer 'não lembro direito'",
        ],
        "efeito_esperado": "respostas secas, muito factuais, ótimas para detectar pontos objetivos de fricção",
    },
    "narrador": {
        "tipo": "narrador",
        "perfil_cognitivo": "responde contando histórias, se perde no meio",
        "regras": [
            "Responder sempre com uma narrativa",
            "Pode misturar eventos",
            "Pode se contradizer levemente",
            "Ordem temporal imperfeita",
            "Detalhes irrelevantes são permitidos",
        ],
        "efeito_esperado": "respostas ricas em contexto, mas que exigem análise para extrair insights",
    },
    "desconfiado": {
        "tipo": "desconfiado",
        "perfil_cognitivo": "suspeita da entrevista e do sistema",
        "regras": [
            "Evitar respostas longas",
            "Minimizar problemas ('não foi tão ruim assim')",
            "Demonstrar cautela ao responder",
            "Pode questionar a pergunta",
            "Não se aprofundar espontaneamente",
        ],
        "efeito_esperado": "respostas evasivas que revelam desconfiança ou experiências negativas não verbalizadas",
    },
    "racionalizador": {
        "tipo": "racionalizador",
        "perfil_cognitivo": "primeiro relata, depois tenta explicar",
        "regras": [
            "Primeiro turno: só descrever o que aconteceu",
            "Explicações só se perguntado explicitamente",
            "Pode reformular respostas anteriores",
            "Racionalização imperfeita",
        ],
        "efeito_esperado": "ótimo para observar construção de sentido pós-fato",
    },
    "impaciente": {
        "tipo": "impaciente",
        "perfil_cognitivo": "pouca tolerância, responde rápido e mal",
        "regras": [
            "Respostas curtas",
            "Pode ignorar parte da pergunta",
            "Pode demonstrar irritação leve",
            "Não elabora sem follow-up direto",
        ],
        "efeito_esperado": "abandono, desistência, respostas truncadas - simula usuários impacientes",
    },
    "esforçado_confuso": {
        "tipo": "esforçado_confuso",
        "perfil_cognitivo": "quer ajudar, mas não sabe explicar bem",
        "regras": [
            "Tenta responder tudo",
            "Usa exemplos simples",
            "Pode se confundir ao explicar",
            "Pode concordar com o entrevistador",
        ],
        "efeito_esperado": "respostas longas, mas pouco precisas — muito realista",
    },
}


def generate_cognitive_contract() -> dict[str, Any]:
    """
    Gera um contrato cognitivo sorteado aleatoriamente com chances iguais.

    O contrato cognitivo define como o synth se comporta em entrevistas,
    simulando diferentes padrões de resposta humana.

    Returns:
        dict: Contrato cognitivo com tipo, perfil, regras e efeito esperado
    """
    tipo = random.choice(list(COGNITIVE_CONTRACTS.keys()))
    return COGNITIVE_CONTRACTS[tipo].copy()


def generate_big_five() -> dict[str, int]:
    """
    Gera traços de personalidade Big Five com distribuição baseada em dados brasileiros.

    Big Five personality traits are the most scientifically validated
    personality model, measuring: Openness, Conscientiousness, Extraversion,
    Agreeableness, and Neuroticism.

    Distribuição baseada em: International Sexuality Description Project (Brazil)
    - Abertura (Openness): μ=49.16, σ=9.37
    - Conscienciosidade (Conscientiousness): μ=45.38, σ=9.28
    - Extroversao (Extraversion): μ=45.89, σ=9.36
    - Amabilidade (Agreeableness): μ=45.86, σ=8.82
    - Neuroticismo (Neuroticism): μ=53.14, σ=9.07

    Returns:
        dict[str, int]: Dictionary with 5 personality traits (0-100 scale)
    """
    return {
        "abertura": normal_distribution(49.16, 9.37, 0, 100),
        "conscienciosidade": normal_distribution(45.38, 9.28, 0, 100),
        "extroversao": normal_distribution(45.89, 9.36, 0, 100),
        "amabilidade": normal_distribution(45.86, 8.82, 0, 100),
        "neuroticismo": normal_distribution(53.14, 9.07, 0, 100),
    }


def generate_psychographics(
    big_five: dict[str, int], config_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Gera atributos psicográficos (interesses, contrato cognitivo).

    Correlações implementadas:
    - Interesses correlacionados com abertura (1-4 itens)
    - Contrato cognitivo sorteado com chances iguais

    Args:
        big_five: Dictionary with Big Five personality traits
        config_data: Configuration data including interests/hobbies

    Returns:
        dict[str, Any]: Complete psychographic profile
    """
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

    # Contrato cognitivo (sorteado com chances iguais entre 6 tipos)
    contrato_cognitivo = generate_cognitive_contract()

    return {
        "personalidade_big_five": big_five,
        "interesses": interesses_list,
        "contrato_cognitivo": contrato_cognitivo,
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
        if "contrato_cognitivo" not in psycho:
            all_validation_failures.append("Psychographics missing contrato_cognitivo")
        else:
            cc = psycho["contrato_cognitivo"]
            if "tipo" not in cc or "perfil_cognitivo" not in cc or "regras" not in cc:
                all_validation_failures.append(
                    f"Contrato cognitivo missing required fields: {cc.keys()}"
                )

        if not any(f.startswith("Test 2") for f in all_validation_failures):
            print(
                f"Test 2: generate_psychographics(low openness) -> "
                f"{len(psycho['interesses'])} interesses, contrato={psycho['contrato_cognitivo']['tipo']}"
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

    # Test 4: Verify cognitive contract generation
    total_tests += 1
    try:
        contract = generate_cognitive_contract()
        valid_types = ["factual", "narrador", "desconfiado", "racionalizador", "impaciente", "esforçado_confuso"]

        if contract["tipo"] not in valid_types:
            all_validation_failures.append(
                f"Cognitive contract invalid type: {contract['tipo']}"
            )
        if not isinstance(contract["regras"], list) or len(contract["regras"]) < 1:
            all_validation_failures.append(
                f"Cognitive contract regras should be non-empty list: {contract['regras']}"
            )
        if "perfil_cognitivo" not in contract or not contract["perfil_cognitivo"]:
            all_validation_failures.append("Cognitive contract missing perfil_cognitivo")

        if not any("Test 4" in f for f in all_validation_failures):
            print(f"Test 4: generate_cognitive_contract() -> tipo={contract['tipo']}")
    except Exception as e:
        all_validation_failures.append(f"Test 4 (cognitive contract generation): {str(e)}")

    # Test 5: Verify cognitive contract distribution (should be roughly equal)
    total_tests += 1
    try:
        contract_counts = {t: 0 for t in COGNITIVE_CONTRACTS.keys()}

        for _ in range(60):  # 60 samples for 6 types = ~10 per type expected
            contract = generate_cognitive_contract()
            contract_counts[contract["tipo"]] += 1

        # Should have at least 3 different types in 60 samples (very high probability)
        types_with_values = sum(1 for v in contract_counts.values() if v > 0)
        if types_with_values < 3:
            all_validation_failures.append(
                f"Cognitive contract distribution too narrow: {contract_counts}"
            )
        else:
            print(f"Test 5: Cognitive contract distribution across {types_with_values} types: {contract_counts}")
    except Exception as e:
        all_validation_failures.append(f"Test 5 (cognitive contract distribution): {str(e)}")

    # Test 6: Batch consistency test
    total_tests += 1
    try:
        batch_errors = []
        valid_types = list(COGNITIVE_CONTRACTS.keys())
        for i in range(10):
            big_five = generate_big_five()
            psycho = generate_psychographics(big_five, config)

            # Verify all required fields
            if len(psycho["interesses"]) < 1 or len(psycho["interesses"]) > 4:
                batch_errors.append(
                    f"Batch {i}: interesses should be 1-4: {len(psycho['interesses'])}"
                )
            if "contrato_cognitivo" not in psycho:
                batch_errors.append(f"Batch {i}: missing contrato_cognitivo")
            elif psycho["contrato_cognitivo"]["tipo"] not in valid_types:
                batch_errors.append(
                    f"Batch {i}: invalid contrato_cognitivo tipo: {psycho['contrato_cognitivo']['tipo']}"
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
