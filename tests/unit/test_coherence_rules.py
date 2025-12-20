"""
Unit tests for personality-bias coherence rules (User Story 2).

Tests the mapping between Big Five personality traits and cognitive biases
to ensure psychologically realistic and consistent behavior patterns.

Tests cover:
- get_coherence_expectations function
- 10 personality-bias mappings as defined in spec.md
- Edge cases with moderate trait values (40-60)
- Conflicting rules when multiple traits affect the same bias
"""

from synth_lab.gen_synth.biases import get_coherence_expectations


class TestGetCoherenceExpectations:
    """Test get_coherence_expectations function."""

    def test_function_returns_dict(self):
        """Test that function returns a dictionary."""
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)
        assert isinstance(result, dict)

    def test_function_returns_all_biases(self):
        """Test that function returns expectations for all 7 biases."""
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

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

    def test_expectations_have_valid_ranges(self):
        """Test that expectations have min and max values in valid range."""
        personality = {
            "abertura": 80,
            "conscienciosidade": 80,
            "extroversao": 80,
            "amabilidade": 80,
            "neuroticismo": 20,
        }
        result = get_coherence_expectations(personality)

        for bias_name, expectation in result.items():
            assert "min" in expectation, f"{bias_name} missing 'min'"
            assert "max" in expectation, f"{bias_name} missing 'max'"
            assert 0 <= expectation["min"] <= 100, f"{bias_name} min out of range"
            assert 0 <= expectation["max"] <= 100, f"{bias_name} max out of range"
            assert expectation["min"] <= expectation["max"], f"{bias_name} min > max"


class TestPersonalityBiasMappings:
    """Test the 10 personality-bias mappings from FR-003."""

    def test_high_conscienciosidade_biases(self):
        """
        High Conscienciosidade (70-100) → High vies_status_quo (70-90),
        Low desconto_hiperbolico (10-30)
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 85,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

        # vies_status_quo should be high (70-90)
        assert result["vies_status_quo"]["min"] >= 70
        assert result["vies_status_quo"]["max"] <= 90

        # desconto_hiperbolico should be low (10-30)
        assert result["desconto_hiperbolico"]["min"] >= 10
        assert result["desconto_hiperbolico"]["max"] <= 30

    def test_low_conscienciosidade_biases(self):
        """
        Low Conscienciosidade (0-30) → Low vies_status_quo (10-35),
        High desconto_hiperbolico (60-85)
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 20,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

        # vies_status_quo should be low (10-35)
        assert result["vies_status_quo"]["min"] >= 10
        assert result["vies_status_quo"]["max"] <= 35

        # desconto_hiperbolico should be high (60-85)
        assert result["desconto_hiperbolico"]["min"] >= 60
        assert result["desconto_hiperbolico"]["max"] <= 85

    def test_high_neuroticismo_biases(self):
        """
        High Neuroticismo (70-100) → High aversao_perda (70-95),
        High sobrecarga_informacao (60-85)
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 85,
        }
        result = get_coherence_expectations(personality)

        # aversao_perda should be high (70-95)
        assert result["aversao_perda"]["min"] >= 70
        assert result["aversao_perda"]["max"] <= 95

        # sobrecarga_informacao should be high (60-85)
        assert result["sobrecarga_informacao"]["min"] >= 60
        assert result["sobrecarga_informacao"]["max"] <= 85

    def test_low_neuroticismo_biases(self):
        """
        Low Neuroticismo (0-30) → Low aversao_perda (10-35),
        Low sobrecarga_informacao (15-40)
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 20,
        }
        result = get_coherence_expectations(personality)

        # aversao_perda should be low (10-35)
        assert result["aversao_perda"]["min"] >= 10
        assert result["aversao_perda"]["max"] <= 35

        # sobrecarga_informacao should be low (15-40)
        assert result["sobrecarga_informacao"]["min"] >= 15
        assert result["sobrecarga_informacao"]["max"] <= 40

    def test_high_abertura_biases(self):
        """
        High Abertura (70-100) → Low vies_confirmacao (10-35),
        Low sobrecarga_informacao (15-40)
        """
        personality = {
            "abertura": 85,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

        # vies_confirmacao should be low (10-35)
        assert result["vies_confirmacao"]["min"] >= 10
        assert result["vies_confirmacao"]["max"] <= 35

        # sobrecarga_informacao should be low (15-40)
        assert result["sobrecarga_informacao"]["min"] >= 15
        assert result["sobrecarga_informacao"]["max"] <= 40

    def test_low_abertura_biases(self):
        """
        Low Abertura (0-30) → High vies_confirmacao (60-85),
        High vies_status_quo (60-85)
        """
        personality = {
            "abertura": 20,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

        # vies_confirmacao should be high (60-85)
        assert result["vies_confirmacao"]["min"] >= 60
        assert result["vies_confirmacao"]["max"] <= 85

        # vies_status_quo should be high (60-85)
        assert result["vies_status_quo"]["min"] >= 60
        assert result["vies_status_quo"]["max"] <= 85

    def test_high_amabilidade_biases(self):
        """
        High Amabilidade (70-100) → Low vies_confirmacao (15-40),
        Moderate ancoragem (40-60)
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 85,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

        # vies_confirmacao should be low (15-40)
        assert result["vies_confirmacao"]["min"] >= 15
        assert result["vies_confirmacao"]["max"] <= 40

        # ancoragem should be moderate (40-60)
        assert result["ancoragem"]["min"] >= 40
        assert result["ancoragem"]["max"] <= 60

    def test_low_amabilidade_biases(self):
        """
        Low Amabilidade (0-30) → High vies_confirmacao (65-90),
        High ancoragem (60-85)
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 20,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

        # vies_confirmacao should be high (65-90)
        assert result["vies_confirmacao"]["min"] >= 65
        assert result["vies_confirmacao"]["max"] <= 90

        # ancoragem should be high (60-85)
        assert result["ancoragem"]["min"] >= 60
        assert result["ancoragem"]["max"] <= 85

    def test_high_extroversao_biases(self):
        """
        High Extroversao (70-100) → Moderate-High desconto_hiperbolico (50-80),
        Low sobrecarga_informacao (20-45)
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 85,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

        # desconto_hiperbolico should be moderate-high (50-80)
        assert result["desconto_hiperbolico"]["min"] >= 50
        assert result["desconto_hiperbolico"]["max"] <= 80

        # sobrecarga_informacao should be low (20-45)
        assert result["sobrecarga_informacao"]["min"] >= 20
        assert result["sobrecarga_informacao"]["max"] <= 45

    def test_low_extroversao_biases(self):
        """
        Low Extroversao (0-30) → Low-Moderate desconto_hiperbolico (20-50),
        Moderate sobrecarga_informacao (45-70)
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 20,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

        # desconto_hiperbolico should be low-moderate (20-50)
        assert result["desconto_hiperbolico"]["min"] >= 20
        assert result["desconto_hiperbolico"]["max"] <= 50

        # sobrecarga_informacao should be moderate (45-70)
        assert result["sobrecarga_informacao"]["min"] >= 45
        assert result["sobrecarga_informacao"]["max"] <= 70


class TestEdgeCases:
    """Test edge cases with moderate trait values (T037)."""

    def test_moderate_personality_values(self):
        """
        Test that moderate personality values (40-60) result in
        moderate bias expectations with wider acceptable ranges.
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

        # For moderate personalities, bias ranges should be broader
        # and centered around 50 (allowing for natural variation)
        for bias_name, expectation in result.items():
            range_width = expectation["max"] - expectation["min"]

            # Moderate traits should allow wider ranges (at least 20 points)
            assert range_width >= 20, (
                f"{bias_name} range too narrow for moderate personality: "
                f"{expectation['min']}-{expectation['max']}"
            )

    def test_all_moderate_traits_provide_defaults(self):
        """
        Test that when all traits are moderate, the function returns
        default expectations for all biases.
        """
        personality = {
            "abertura": 45,
            "conscienciosidade": 55,
            "extroversao": 50,
            "amabilidade": 48,
            "neuroticismo": 52,
        }
        result = get_coherence_expectations(personality)

        assert len(result) == 7, "Should return expectations for all 7 biases"


class TestConflictingRules:
    """Test scenarios where multiple traits affect the same bias (T038)."""

    def test_conflicting_sobrecarga_informacao(self):
        """
        Test sobrecarga_informacao when:
        - High Neuroticismo (70-100) → High sobrecarga_informacao (60-85)
        - High Abertura (70-100) → Low sobrecarga_informacao (15-40)
        - High Extroversao (70-100) → Low sobrecarga_informacao (20-45)

        Expected: System should use weighted averaging or prioritization.
        """
        personality = {
            "abertura": 80,  # → Low sobrecarga_informacao
            "conscienciosidade": 50,
            "extroversao": 80,  # → Low sobrecarga_informacao
            "amabilidade": 50,
            "neuroticismo": 80,  # → High sobrecarga_informacao
        }
        result = get_coherence_expectations(personality)

        # Result should be a compromise, not extreme in either direction
        # Acceptable range should be moderate (30-70)
        sobrecarga = result["sobrecarga_informacao"]
        assert sobrecarga["min"] >= 20, "Min should not be too low with conflicting rules"
        assert sobrecarga["max"] <= 80, "Max should not be too high with conflicting rules"

    def test_conflicting_vies_confirmacao(self):
        """
        Test vies_confirmacao when:
        - High Abertura (70-100) → Low vies_confirmacao (10-35)
        - Low Amabilidade (0-30) → High vies_confirmacao (65-90)

        Expected: System should handle conflict gracefully.
        """
        personality = {
            "abertura": 80,  # → Low vies_confirmacao
            "conscienciosidade": 50,
            "extroversao": 50,
            "amabilidade": 20,  # → High vies_confirmacao
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

        # Result should be moderate when rules conflict
        vies_conf = result["vies_confirmacao"]
        assert vies_conf["min"] >= 10, "Min should respect some lower bound"
        assert vies_conf["max"] <= 90, "Max should respect some upper bound"
        # Range should be reasonably wide to accommodate conflict
        assert (vies_conf["max"] - vies_conf["min"]) >= 30

    def test_conflicting_desconto_hiperbolico(self):
        """
        Test desconto_hiperbolico when:
        - High Conscienciosidade (70-100) → Low desconto_hiperbolico (10-30)
        - High Extroversao (70-100) → Moderate-High desconto_hiperbolico (50-80)

        Expected: System should handle conflict gracefully.
        """
        personality = {
            "abertura": 50,
            "conscienciosidade": 85,  # → Low desconto_hiperbolico
            "extroversao": 85,  # → Moderate-High desconto_hiperbolico
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

        # Result should be moderate when rules conflict
        desconto = result["desconto_hiperbolico"]
        assert desconto["min"] >= 10, "Min should respect some lower bound"
        assert desconto["max"] <= 80, "Max should respect some upper bound"

    def test_conflicting_vies_status_quo(self):
        """
        Test vies_status_quo when:
        - High Conscienciosidade (70-100) → High vies_status_quo (70-90)
        - Low Abertura (0-30) → High vies_status_quo (60-85)

        Expected: Both push in same direction, should reinforce.
        """
        personality = {
            "abertura": 20,  # → High vies_status_quo
            "conscienciosidade": 85,  # → High vies_status_quo
            "extroversao": 50,
            "amabilidade": 50,
            "neuroticismo": 50,
        }
        result = get_coherence_expectations(personality)

        # Both traits push high, so result should be high (reinforced)
        vies_sq = result["vies_status_quo"]
        assert vies_sq["min"] >= 65, "Min should be high when rules reinforce"
        assert vies_sq["max"] >= 80, "Max should be high when rules reinforce"
