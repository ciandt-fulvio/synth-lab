"""
Testes unitários para avatar_prompt.py

Este módulo testa a construção de prompts para geração de avatares:
- Atribuição aleatória de filtros visuais
- Construção de prompts estruturados para 9 synths

Dependências: pytest
Entrada: Dados de synth mockados
Saída: Validação das funções de prompt
"""

import pytest

from synth_lab.gen_synth.avatar_prompt import (
    VISUAL_FILTERS,
    assign_random_filters,
    build_prompt,
)


class TestAssignRandomFilters:
    """Testes para função assign_random_filters() - User Story 1 (T009)"""

    def test_returns_correct_count(self):
        """Dado count=9, quando gerar filtros, então retorna lista de 9 filtros"""
        result = assign_random_filters(9)
        assert len(result) == 9

    def test_all_filters_valid(self):
        """Dado count=9, quando gerar filtros, então todos os filtros são válidos"""
        result = assign_random_filters(9)
        assert all(f in VISUAL_FILTERS for f in result)

    def test_returns_different_filters(self):
        """Dado count=100, quando gerar filtros, então usa variedade de filtros"""
        result = assign_random_filters(100)
        unique_filters = set(result)
        # Com 100 filtros, deve ter usado pelo menos 3 tipos diferentes
        assert len(unique_filters) >= 3


class TestBuildPrompt:
    """Testes para função build_prompt() - User Story 1 (T009)"""

    @pytest.fixture
    def mock_synths(self):
        """Fixture: retorna 9 synths mockados"""
        return [
            {
                "id": f"test{i:02d}",
                "demografia": {
                    "idade": 30 + i,
                    "genero_biologico": "masculino" if i % 2 == 0 else "feminino",
                    "raca_etnia": ["branco", "pardo", "preto"][i % 3],
                    "ocupacao": "engenheiro"
                }
            }
            for i in range(9)
        ]

    def test_requires_exactly_9_synths(self, mock_synths):
        """Dado lista com != 9 synths, quando construir prompt, então levanta ValueError"""
        with pytest.raises(ValueError, match="exatamente 9 synths"):
            build_prompt(mock_synths[:5])

    def test_prompt_contains_grid_layout(self, mock_synths):
        """Dado 9 synths, quando construir prompt, então contém instruções de grid 3x3"""
        result = build_prompt(mock_synths)
        # Verifica que menciona a divisão em 9 partes/3 linhas e 3 colunas
        assert "9 partes" in result or "3 linhas" in result

    def test_prompt_contains_all_positions(self, mock_synths):
        """Dado 9 synths, quando construir prompt, então contém todas as 9 posições"""
        result = build_prompt(mock_synths)
        # O prompt usa formato "1. descricao", "2. descricao", etc.
        for i in range(1, 10):
            assert f"{i}." in result

    def test_prompt_contains_demographic_data(self, mock_synths):
        """Dado 9 synths, quando construir prompt, então contém dados demográficos"""
        result = build_prompt(mock_synths)
        # Verifica que idade aparece (formato: "30 anos")
        assert "30 anos" in result
        # Verifica que gênero aparece (formato: "Homem" ou "Mulher")
        assert "Homem" in result or "Mulher" in result
        # Verifica que ocupação aparece
        assert "engenheiro" in result

    def test_prompt_contains_visual_filters(self, mock_synths):
        """Dado 9 synths, quando construir prompt, então contém filtros visuais"""
        result = build_prompt(mock_synths)
        # Pelo menos um filtro deve aparecer
        filter_found = any(f.lower() in result.lower() for f in VISUAL_FILTERS)
        assert filter_found, "Nenhum filtro visual encontrado no prompt"

    def test_prompt_length_reasonable(self, mock_synths):
        """Dado 9 synths, quando construir prompt, então tamanho é razoável (<2000 chars)"""
        result = build_prompt(mock_synths)
        # gpt-image-1 suporta prompts maiores que gpt-image-1-mini
        assert len(
            result) < 2000, f"Prompt muito longo: {len(result)} caracteres"
        # Mas deve ter conteúdo suficiente
        assert len(
            result) > 200, f"Prompt muito curto: {len(result)} caracteres"


if __name__ == "__main__":
    """
    Validação do módulo de testes.

    Este bloco verifica que:
    1. Todos os testes estão estruturados corretamente
    2. Os testes passam com a implementação atual
    """
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Executar testes com pytest
    total_tests += 1
    try:
        import pytest
        result = pytest.main([__file__, "-v", "--tb=short"])
        if result != 0:
            all_validation_failures.append(
                f"Alguns testes falharam (código: {result})")
    except ImportError as e:
        all_validation_failures.append(f"Pytest não disponível: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} checks failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print("✅ VALIDATION PASSED - All tests passed")
        sys.exit(0)
