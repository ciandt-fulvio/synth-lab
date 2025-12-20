"""
Unit tests for biases generation module (User Story 2).

Tests the generation of cognitive biases with personality coherence.

Tests cover:
- generate_biases_with_coherence function
- Bias values respect personality-derived expectations
- Bias values are within valid ranges (0-100)
"""

from synth_lab.gen_synth.biases import generate_biases_with_coherence


class TestGenerateBiasesWithCoherence:
    """Test generate_biases_with_coherence function."""

    def test_function_returns_dict(self):
        """Test that function returns a dictionary."""
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = generate_biases_with_coherence(personality)
        assert isinstance(result, dict)

    def test_function_returns_all_biases(self):
        """Test that function returns all 7 biases."""
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = generate_biases_with_coherence(personality)

        expected_biases = [
            "aversao_perda",
            "desconto_hiperbolico",
            "suscetibilidade_chamariz",
            "ancoragem",
            "vies_confirmacao",
            "vies_status_quo",
            "sobrecarga_informacao",
        ]

        for bias in expected_biases:
            assert bias in result, f"Missing bias: {bias}"

    def test_bias_values_are_integers(self):
        """Test that all bias values are integers."""
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = generate_biases_with_coherence(personality)

        for bias_name, value in result.items():
            assert isinstance(value, int), f"{bias_name} should be integer, got {type(value)}"

    def test_bias_values_in_valid_range(self):
        """Test that all bias values are in valid range (0-100)."""
        personality = {
            "abertura": 80,
            "conscienciosidade": 20,
            "extroversao": 75,
            "amabilidade": 30,
            "neuroticismo": 85,
        }
        result = generate_biases_with_coherence(personality)

        for bias_name, value in result.items():
            assert 0 <= value <= 100, f"{bias_name} out of range: {value}"

    def test_high_conscienciosidade_produces_coherent_biases(self):
        """
        Test that high conscientiousness produces:
        - High vies_status_quo (70-90)
        - Low desconto_hiperbolico (10-30)
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 85,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }

        # Test multiple samples to account for randomness
        for _ in range(10):
            result = generate_biases_with_coherence(personality)

            # vies_status_quo should be high (70-90)
            assert 70 <= result["vies_status_quo"] <= 90, (
                f"vies_status_quo should be 70-90 for high conscientiousness, "
                f"got {result['vies_status_quo']}"
            )

            # desconto_hiperbolico should be low (10-30)
            assert 10 <= result["desconto_hiperbolico"] <= 30, (
                f"desconto_hiperbolico should be 10-30 for high conscientiousness, "
                f"got {result['desconto_hiperbolico']}"
            )

    def test_high_neuroticismo_produces_coherent_biases(self):
        """
        Test that high neuroticism produces:
        - High aversao_perda (70-95)
        - High sobrecarga_informacao (60-85)
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 85,
        }

        # Test multiple samples to account for randomness
        for _ in range(10):
            result = generate_biases_with_coherence(personality)

            # aversao_perda should be high (70-95)
            assert 70 <= result["aversao_perda"] <= 95, (
                f"aversao_perda should be 70-95 for high neuroticism, "
                f"got {result['aversao_perda']}"
            )

            # sobrecarga_informacao should be high (60-85)
            assert 60 <= result["sobrecarga_informacao"] <= 85, (
                f"sobrecarga_informacao should be 60-85 for high neuroticism, "
                f"got {result['sobrecarga_informacao']}"
            )

    def test_high_abertura_produces_coherent_biases(self):
        """
        Test that high openness produces:
        - Low vies_confirmacao (10-35)
        - Low sobrecarga_informacao (15-40)
        """
        personality = {
            "abertura": 85,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }

        # Test multiple samples to account for randomness
        for _ in range(10):
            result = generate_biases_with_coherence(personality)

            # vies_confirmacao should be low (10-35)
            assert 10 <= result["vies_confirmacao"] <= 35, (
                f"vies_confirmacao should be 10-35 for high openness, "
                f"got {result['vies_confirmacao']}"
            )

            # sobrecarga_informacao should be low (15-40)
            assert 15 <= result["sobrecarga_informacao"] <= 40, (
                f"sobrecarga_informacao should be 15-40 for high openness, "
                f"got {result['sobrecarga_informacao']}"
            )

    def test_low_amabilidade_produces_coherent_biases(self):
        """
        Test that low agreeableness produces:
        - High vies_confirmacao (65-90)
        - High ancoragem (60-85)
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 20,
            "neuroticismo": 50,
        }

        # Test multiple samples to account for randomness
        for _ in range(10):
            result = generate_biases_with_coherence(personality)

            # vies_confirmacao should be high (65-90)
            assert 65 <= result["vies_confirmacao"] <= 90, (
                f"vies_confirmacao should be 65-90 for low agreeableness, "
                f"got {result['vies_confirmacao']}"
            )

            # ancoragem should be high (60-85)
            assert 60 <= result["ancoragem"] <= 85, (
                f"ancoragem should be 60-85 for low agreeableness, "
                f"got {result['ancoragem']}"
            )

    def test_high_extroversao_produces_coherent_biases(self):
        """
        Test that high extraversion produces:
        - Moderate-High desconto_hiperbolico (50-80)
        - Low sobrecarga_informacao (20-45)
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 85,
            "amabilidade": 50,
            "neuroticismo": 50,
        }

        # Test multiple samples to account for randomness
        for _ in range(10):
            result = generate_biases_with_coherence(personality)

            # desconto_hiperbolico should be moderate-high (50-80)
            assert 50 <= result["desconto_hiperbolico"] <= 80, (
                f"desconto_hiperbolico should be 50-80 for high extraversion, "
                f"got {result['desconto_hiperbolico']}"
            )

            # sobrecarga_informacao should be low (20-45)
            assert 20 <= result["sobrecarga_informacao"] <= 45, (
                f"sobrecarga_informacao should be 20-45 for high extraversion, "
                f"got {result['sobrecarga_informacao']}"
            )

    def test_biases_have_variety_with_same_personality(self):
        """
        Test that multiple calls with same personality produce varied bias values
        (due to randomness within coherence constraints).
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }

        # Generate 20 samples
        samples = [generate_biases_with_coherence(personality) for _ in range(20)]

        # Check that aversao_perda varies across samples
        aversao_values = {s["aversao_perda"] for s in samples}
        assert len(aversao_values) >= 5, (
            f"aversao_perda should have variety across samples, "
            f"got only {len(aversao_values)} unique values"
        )

    def test_extreme_personality_produces_extreme_biases(self):
        """
        Test that extreme personality values produce biases
        at the appropriate extremes.
        """
        # Extreme low personality
        low_personality = {
            "abertura": 10,
            "conscienciosidade": 10,
            "extroversao": 10,
            "amabilidade": 10,
            "neuroticismo": 10,
        }

        # Extreme high personality
        high_personality = {
            "abertura": 90,
            "conscienciosidade": 90,
            "extroversao": 90,
            "amabilidade": 90,
            "neuroticismo": 90,
        }

        # Generate biases for both
        low_result = generate_biases_with_coherence(low_personality)
        high_result = generate_biases_with_coherence(high_personality)

        # Both should have valid values
        for bias_name, value in low_result.items():
            assert 0 <= value <= 100, f"Low personality {bias_name} out of range: {value}"

        for bias_name, value in high_result.items():
            assert 0 <= value <= 100, f"High personality {bias_name} out of range: {value}"

        # At least some biases should differ significantly between extremes
        differences = [
            abs(high_result[bias] - low_result[bias])
            for bias in low_result.keys()
        ]
        assert max(differences) >= 30, (
            "Extreme personalities should produce significantly different biases"
        )

    def test_moderate_personality_produces_moderate_biases(self):
        """
        Test that moderate personality values (40-60) produce
        moderate bias values with natural variation.
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }

        # Generate multiple samples
        samples = [generate_biases_with_coherence(personality) for _ in range(50)]

        # Check that average bias values are roughly centered around 50
        avg_aversao = sum(s["aversao_perda"] for s in samples) / len(samples)
        avg_desconto = sum(s["desconto_hiperbolico"] for s in samples) / len(samples)

        # Averages should be reasonably centered (35-65 range)
        assert 35 <= avg_aversao <= 65, f"Average aversao_perda should be moderate: {avg_aversao}"
        assert 35 <= avg_desconto <= 65, f"Average desconto_hiperbolico should be moderate: {avg_desconto}"

    def test_batch_consistency(self):
        """Test that batch generation produces consistently valid results."""
        personality = {
            "abertura": 70,
            "conscienciosidade": 60,
            "extroversao": 40,
            "amabilidade": 55,
            "neuroticismo": 45,
        }

        # Generate 30 samples
        for i in range(30):
            result = generate_biases_with_coherence(personality)

            # Verify all required biases present
            assert len(result) == 7, f"Batch {i}: Expected 7 biases, got {len(result)}"

            # Verify all values in range
            for bias_name, value in result.items():
                assert 0 <= value <= 100, (
                    f"Batch {i}: {bias_name} out of range: {value}"
                )
