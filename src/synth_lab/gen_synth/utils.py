"""
Utility functions for SynthLab.

Common helper functions used across the synth generation system.
"""

import random
import string

# Escolaridade order for comparison
ESCOLARIDADE_ORDEM = [
    "Sem instrução",
    "Fundamental incompleto",
    "Fundamental completo",
    "Médio incompleto",
    "Médio completo",
    "Superior incompleto",
    "Superior completo",
    "Pós-graduação",
]


def gerar_id(tamanho: int = 6) -> str:
    """
    Gera um ID alfanumérico aleatório de tamanho especificado.

    Args:
        tamanho: Tamanho do ID (padrão: 6 caracteres)

    Returns:
        str: ID alfanumérico único
    """
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=tamanho))


def weighted_choice(options: dict[str, float]) -> str:
    """Seleciona uma opção baseada em pesos/probabilidades."""
    choices = list(options.keys())
    weights = list(options.values())
    return random.choices(choices, weights=weights, k=1)[0]


def normal_distribution(
    mean: float = 50, std: float = 15, min_val: int = 0, max_val: int = 100
) -> int:
    """Gera valor de distribuição normal limitado entre min_val e max_val."""
    value = random.gauss(mean, std)
    return max(min_val, min(max_val, round(value)))


def escolaridade_index(escolaridade: str) -> int:
    """Retorna o índice da escolaridade na ordem hierárquica."""
    try:
        return ESCOLARIDADE_ORDEM.index(escolaridade)
    except ValueError:
        return 0


def escolaridade_compativel(escolaridade: str, escolaridade_minima: str) -> bool:
    """Verifica se a escolaridade é compatível (maior ou igual) à mínima exigida."""
    return escolaridade_index(escolaridade) >= escolaridade_index(escolaridade_minima)


if __name__ == "__main__":
    """Validation with real data."""
    print("=== Utils Module Validation ===\n")

    # Test ID generation
    id1 = gerar_id()
    id2 = gerar_id()
    assert len(id1) == 6, f"ID length should be 6, got {len(id1)}"
    assert id1 != id2, "IDs should be unique"
    print(f"✓ gerar_id() works: {id1}, {id2}")

    # Test weighted choice
    options = {"A": 0.7, "B": 0.3}
    result = weighted_choice(options)
    assert result in ["A", "B"], f"Result should be A or B, got {result}"
    print(f"✓ weighted_choice() works: {result}")

    # Test normal distribution
    val = normal_distribution(50, 15, 0, 100)
    assert 0 <= val <= 100, f"Value should be in [0,100], got {val}"
    print(f"✓ normal_distribution() works: {val}")

    # Test escolaridade functions
    assert escolaridade_index("Superior completo") == 6
    assert escolaridade_compativel(
        "Superior completo", "Médio completo") is True
    assert escolaridade_compativel(
        "Médio completo", "Superior completo") is False
    print("✓ escolaridade functions work correctly")

    print("\n✓ All validations passed")
