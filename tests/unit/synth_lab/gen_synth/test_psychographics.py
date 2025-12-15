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
    """Test that psychographics have correct structure."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    required_fields = [
        "personalidade_big_five",
        "valores",
        "interesses",
        "hobbies",
        "estilo_vida",
        "inclinacao_politica",
        "inclinacao_religiosa",
    ]

    for field in required_fields:
        assert field in psycho


def test_generate_psychographics_valores(config_data):
    """Test valores generation."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    assert isinstance(psycho["valores"], list)
    assert 3 <= len(psycho["valores"]) <= 5
    # Should be unique values
    assert len(psycho["valores"]) == len(set(psycho["valores"]))


def test_generate_psychographics_interesses(config_data):
    """Test interesses generation."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    assert isinstance(psycho["interesses"], list)
    assert 3 <= len(psycho["interesses"]) <= 10  # Based on code: 3 + (abertura // 20)
    # Should be unique
    assert len(psycho["interesses"]) == len(set(psycho["interesses"]))


def test_generate_psychographics_hobbies(config_data):
    """Test hobbies generation."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    assert isinstance(psycho["hobbies"], list)
    assert 3 <= len(psycho["hobbies"]) <= 5
    # Should be unique
    assert len(psycho["hobbies"]) == len(set(psycho["hobbies"]))


def test_generate_psychographics_no_overlap(config_data):
    """Test that hobbies don't overlap with interesses."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    # Hobbies and interesses should be distinct
    overlap = set(psycho["hobbies"]) & set(psycho["interesses"])
    assert len(overlap) == 0


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


def test_generate_psychographics_estilo_vida(config_data):
    """Test lifestyle field exists (even if empty initially)."""
    big_five = psychographics.generate_big_five()
    psycho = psychographics.generate_psychographics(big_five, config_data)

    assert isinstance(psycho["estilo_vida"], str)
    # Note: estilo_vida may be empty string initially, derived later
    assert "estilo_vida" in psycho
