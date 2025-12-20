"""Tests for psychographics module."""

from synth_lab.gen_synth import psychographics


def test_generate_big_five_structure():
    """Test that Big Five traits have correct structure."""
    big_five = psychographics.generate_big_five()

    required_traits = [
        "abertura",
        "conscienciosidade",
        "extroversao",
        "amabilidade",
        "neuroticismo",
    ]

    assert len(big_five) == 5
    for trait in required_traits:
        assert trait in big_five


def test_generate_big_five_values():
    """Test that Big Five values are within valid range."""
    big_five = psychographics.generate_big_five()

    for trait, value in big_five.items():
        assert isinstance(value, int)
        assert 0 <= value <= 100


def test_generate_big_five_distribution():
    """Test that Big Five values follow normal distribution (roughly)."""
    # Generate many samples
    samples = [psychographics.generate_big_five() for _ in range(100)]

    # Check that values aren't all the same (should vary)
    abertura_values = [s["abertura"] for s in samples]
    assert len(set(abertura_values)) > 20  # Should have variety


def test_generate_psychographics_structure(config_data):
    """Test that psychographics have correct structure."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    required_fields = [
        "personalidade_big_five",
        "interesses",
        "contrato_cognitivo",
    ]

    for field in required_fields:
        assert field in psycho

    # Verify removed fields are NOT present
    removed_fields = ["valores", "hobbies", "estilo_vida", "inclinacao_politica", "inclinacao_religiosa"]
    for field in removed_fields:
        assert field not in psycho, f"Field {field} should not be in schema"


def test_generate_psychographics_interesses(config_data):
    """Test interesses generation."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    assert isinstance(psycho["interesses"], list)
    assert 1 <= len(psycho["interesses"]) <= 4  # 1-4 items based on openness
    # Should be unique
    assert len(psycho["interesses"]) == len(set(psycho["interesses"]))


def test_generate_psychographics_contrato_cognitivo(config_data):
    """Test contrato cognitivo generation."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    assert isinstance(psycho["contrato_cognitivo"], dict)
    assert "tipo" in psycho["contrato_cognitivo"]
    assert "perfil_cognitivo" in psycho["contrato_cognitivo"]
    assert "regras" in psycho["contrato_cognitivo"]
    assert "efeito_esperado" in psycho["contrato_cognitivo"]


def test_generate_psychographics_interesses_correlates_with_openness(config_data):
    """Test that interesses count correlates with openness."""
    # Test low openness
    low_openness = {
        "abertura": 20,
        "conscienciosidade": 50,
        "extroversao": 50,
        "amabilidade": 50,
        "neuroticismo": 50,
    }

    psycho_low = psychographics.generate_psychographics(low_openness, config_data)
    assert 1 <= len(psycho_low["interesses"]) <= 2

    # Test high openness
    high_openness = {
        "abertura": 85,
        "conscienciosidade": 50,
        "extroversao": 50,
        "amabilidade": 50,
        "neuroticismo": 50,
    }

    psycho_high = psychographics.generate_psychographics(high_openness, config_data)
    assert 3 <= len(psycho_high["interesses"]) <= 4
