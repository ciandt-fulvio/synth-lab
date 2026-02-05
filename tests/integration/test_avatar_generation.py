"""
Tests for avatar generation helper functions.

This file contains unit tests for avatar generation utility functions.

For integration testing with REAL API calls, see:
- tests/smoke/test_openai_integration.py (smoke tests with real OpenAI API)

For examples of mocked service integration tests, see:
- tests/integration/services/test_ai_services.py
- tests/integration/services/test_exploration_services.py

Dependencies: pytest
"""

import pytest


class TestAvatarGeneratorFunctions:
    """Unit tests for avatar generator helper functions."""

    def test_calculate_block_count_exact_multiple(self):
        """Test block calculation for exact multiples of 9."""
        from synth_lab.gen_synth.avatar_generator import calculate_block_count

        assert calculate_block_count(9, blocks=None) == 1
        assert calculate_block_count(18, blocks=None) == 2
        assert calculate_block_count(27, blocks=None) == 3

    def test_calculate_block_count_rounds_up(self):
        """Test block calculation rounds up for partial blocks."""
        from synth_lab.gen_synth.avatar_generator import calculate_block_count

        assert calculate_block_count(10, blocks=None) == 2
        assert calculate_block_count(19, blocks=None) == 3

    def test_calculate_block_count_override(self):
        """Test blocks parameter overrides synth count."""
        from synth_lab.gen_synth.avatar_generator import calculate_block_count

        assert calculate_block_count(9, blocks=5) == 5
        assert calculate_block_count(18, blocks=1) == 1

    def test_validate_synth_for_avatar_valid(self):
        """Test validation accepts valid synth."""
        from synth_lab.gen_synth.avatar_generator import validate_synth_for_avatar

        valid_synth = {
            "id": "test01",
            "demografia": {
                "idade": 30,
                "genero_biologico": "masculino",
                "raca_etnia": "branco",
                "ocupacao": "engenheiro",
            },
        }

        assert validate_synth_for_avatar(valid_synth) is True

    def test_validate_synth_for_avatar_missing_id(self):
        """Test validation rejects synth without id."""
        from synth_lab.gen_synth.avatar_generator import validate_synth_for_avatar

        invalid_synth = {
            "demografia": {
                "idade": 30,
                "genero_biologico": "masculino",
                "raca_etnia": "branco",
                "ocupacao": "engenheiro",
            }
        }

        assert validate_synth_for_avatar(invalid_synth) is False

    def test_validate_synth_for_avatar_missing_idade(self):
        """Test validation rejects synth without idade."""
        from synth_lab.gen_synth.avatar_generator import validate_synth_for_avatar

        invalid_synth = {
            "id": "test01",
            "demografia": {
                "genero_biologico": "masculino",
                "raca_etnia": "branco",
                "ocupacao": "engenheiro",
            },
        }

        assert validate_synth_for_avatar(invalid_synth) is False
