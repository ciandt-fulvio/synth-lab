"""
Integration tests for avatar generation.

Tests the avatar generation workflow with real OpenAI API
(when API key is available) and error handling.

Dependencies: pytest, Pillow
Input: Synth data with demographics
Output: Validation of avatar generation workflow
"""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.mark.slow
class TestRealOpenAIIntegration:
    """
    Integration tests with real OpenAI API - User Story 1 (T042)

    CAUTION: These tests make real OpenAI API calls and incur costs.
    Run only when needed: pytest -m slow
    """

    @pytest.fixture
    def real_synths(self):
        """Fixture: returns real synths for testing"""
        return [
            {
                "id": f"real{i:02d}",
                "demografia": {
                    "idade": 25 + (i * 5),
                    "genero_biologico": "masculino" if i % 2 == 0 else "feminino",
                    "raca_etnia": ["branco", "pardo", "preto"][i % 3],
                    "ocupacao": ["engenheiro", "professor", "médico"][i % 3]
                }
            }
            for i in range(9)
        ]

    @pytest.fixture
    def temp_avatar_dir(self):
        """Fixture: temporary directory for avatars"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_real_api_single_block(self, real_synths, temp_avatar_dir):
        """
        SLOW TEST: Tests real generation of 1 block via OpenAI API

        Estimated cost: ~$0.02
        Estimated time: 5-10 seconds
        """
        import os

        from synth_lab.gen_synth.avatar_generator import generate_avatars

        # Check if API key is configured
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not configured - skipping real API test")

        # Generate real avatars
        result = generate_avatars(
            real_synths,
            blocks=None,
            avatar_dir=temp_avatar_dir,
            api_key=api_key
        )

        # Verifications
        assert len(result) == 9, f"Expected 9 avatars, got {len(result)}"

        # Verify all files were created
        for path in result:
            assert Path(path).exists(), f"Avatar not created: {path}"

            # Verify it's a valid PNG
            from PIL import Image
            img = Image.open(path)
            assert img.width == 341 or img.height == 341, f"Incorrect dimension: {img.size}"

    def test_real_api_error_handling(self, temp_avatar_dir):
        """
        SLOW TEST: Tests error handling with invalid API key
        """
        from synth_lab.gen_synth.avatar_generator import generate_avatars

        invalid_synths = [{
            "id": "test01",
            "demografia": {
                "idade": 30,
                "genero_biologico": "masculino",
                "raca_etnia": "branco",
                "ocupacao": "teste"
            }
        }] * 9

        # Should fail with invalid API key
        with pytest.raises(Exception):  # ValueError or AuthenticationError
            generate_avatars(
                invalid_synths,
                blocks=None,
                avatar_dir=temp_avatar_dir,
                api_key="sk-invalid-key-for-testing"
            )


class TestAvatarGeneratorFunctions:
    """Tests for avatar generator helper functions"""

    def test_calculate_block_count_exact_multiple(self):
        """Test block calculation for exact multiples of 9"""
        from synth_lab.gen_synth.avatar_generator import calculate_block_count

        assert calculate_block_count(9, blocks=None) == 1
        assert calculate_block_count(18, blocks=None) == 2
        assert calculate_block_count(27, blocks=None) == 3

    def test_calculate_block_count_rounds_up(self):
        """Test block calculation rounds up for partial blocks"""
        from synth_lab.gen_synth.avatar_generator import calculate_block_count

        assert calculate_block_count(10, blocks=None) == 2
        assert calculate_block_count(19, blocks=None) == 3

    def test_calculate_block_count_override(self):
        """Test blocks parameter overrides synth count"""
        from synth_lab.gen_synth.avatar_generator import calculate_block_count

        assert calculate_block_count(9, blocks=5) == 5
        assert calculate_block_count(18, blocks=1) == 1

    def test_validate_synth_for_avatar_valid(self):
        """Test validation accepts valid synth"""
        from synth_lab.gen_synth.avatar_generator import validate_synth_for_avatar

        valid_synth = {
            "id": "test01",
            "demografia": {
                "idade": 30,
                "genero_biologico": "masculino",
                "raca_etnia": "branco",
                "ocupacao": "engenheiro"
            }
        }

        assert validate_synth_for_avatar(valid_synth) is True

    def test_validate_synth_for_avatar_missing_id(self):
        """Test validation rejects synth without id"""
        from synth_lab.gen_synth.avatar_generator import validate_synth_for_avatar

        invalid_synth = {
            "demografia": {
                "idade": 30,
                "genero_biologico": "masculino",
                "raca_etnia": "branco",
                "ocupacao": "engenheiro"
            }
        }

        assert validate_synth_for_avatar(invalid_synth) is False

    def test_validate_synth_for_avatar_missing_idade(self):
        """Test validation rejects synth without idade"""
        from synth_lab.gen_synth.avatar_generator import validate_synth_for_avatar

        invalid_synth = {
            "id": "test01",
            "demografia": {
                "genero_biologico": "masculino",
                "raca_etnia": "branco",
                "ocupacao": "engenheiro"
            }
        }

        assert validate_synth_for_avatar(invalid_synth) is False
