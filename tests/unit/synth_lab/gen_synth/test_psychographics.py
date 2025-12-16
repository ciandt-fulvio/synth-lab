"""Tests for psychographics module."""

import pytest
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
    """Test that psychographics have correct structure (v2.0.0)."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    required_fields = [
        "personalidade_big_five",
        "interesses",
        "inclinacao_politica",
        "inclinacao_religiosa",
    ]

    for field in required_fields:
        assert field in psycho

    # Verify removed fields are NOT present in v2.0.0
    removed_fields = ["valores", "hobbies", "estilo_vida"]
    for field in removed_fields:
        assert field not in psycho, f"Field {field} should not be in v2.0.0 schema"


def test_generate_psychographics_interesses(config_data):
    """Test interesses generation."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    assert isinstance(psycho["interesses"], list)
    assert 1 <= len(psycho["interesses"]) <= 4  # 1-4 items based on openness
    # Should be unique
    assert len(psycho["interesses"]) == len(set(psycho["interesses"]))


def test_generate_psychographics_inclinacao_politica(config_data):
    """Test political inclination range."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    assert isinstance(psycho["inclinacao_politica"], int)
    assert -100 <= psycho["inclinacao_politica"] <= 100


def test_generate_psychographics_inclinacao_religiosa(config_data):
    """Test religious inclination is valid."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    assert isinstance(psycho["inclinacao_religiosa"], str)
    # Should be one of the valid options from IBGE data
    valid_options = list(config_data["ibge"]["religiao"].keys())
    assert psycho["inclinacao_religiosa"] in valid_options


def test_generate_psychographics_religion_politics_correlation(config_data):
    """Test that católicos/evangélicos tend to be more right-wing."""
    # Generate many samples and check correlation
    right_wing_count = {"católico": 0, "evangélico": 0, "outros": 0}
    total_count = {"católico": 0, "evangélico": 0, "outros": 0}

    for _ in range(100):
        big_five = psychographics.generate_big_five()
        psycho = psychographics.generate_psychographics(big_five, config_data)

        religion = psycho["inclinacao_religiosa"]
        politics = psycho["inclinacao_politica"]

        # Classify religion
        if religion in ["católico", "evangélico"]:
            key = religion
        else:
            key = "outros"

        total_count[key] += 1

        # Right-wing is > 20
        if politics > 20:
            right_wing_count[key] += 1

    # Verify that católicos and evangélicos have higher right-wing percentage
    # We expect at least 50% to be right-wing for católicos/evangélicos
    for religion in ["católico", "evangélico"]:
        if total_count[religion] > 0:
            percentage = right_wing_count[religion] / total_count[religion]
            # Should be significantly higher than random (which would be ~33%)
            assert percentage > 0.40, (
                f"{religion} should have >40% right-wing tendency, got {percentage:.2%}"
            )


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
