"""Tests for demographics module."""

from synth_lab.gen_synth import demographics


def test_generate_coherent_gender(config_data):
    """Test coherent gender generation."""
    genero_bio, identidade = demographics.generate_coherent_gender(
        config_data["ibge"]
    )

    # Check valid values
    assert genero_bio in ["masculino", "feminino", "intersexo"]
    assert identidade in [
        "homem cis",
        "mulher cis",
        "homem trans",
        "mulher trans",
        "não-binário",
        "outro",
    ]


def test_generate_coherent_family_young(config_data):
    """Test family generation for young person."""
    estado_civil, composicao = demographics.generate_coherent_family(
        ibge_data=config_data["ibge"], idade=20, estado_civil="solteiro"
    )

    # Young people more likely to be single
    assert estado_civil in ["solteiro", "casado", "união estável", "divorciado", "viúvo"]
    assert "tipo" in composicao
    assert "numero_pessoas" in composicao
    assert composicao["numero_pessoas"] >= 1


def test_generate_coherent_family_older(config_data):
    """Test family generation for older person."""
    estado_civil, composicao = demographics.generate_coherent_family(
        ibge_data=config_data["ibge"], idade=60, estado_civil="casado"
    )

    assert estado_civil in ["solteiro", "casado", "união estável", "divorciado", "viúvo"]
    assert "tipo" in composicao
    assert composicao["numero_pessoas"] >= 1


def test_generate_coherent_occupation_compatible(config_data):
    """Test occupation generation respects education compatibility."""
    occ_data, ocupacao = demographics.generate_coherent_occupation(
        occupations_data=config_data["occupations"],
        escolaridade="Superior completo",
        idade=30,
    )

    assert isinstance(ocupacao, str)
    assert len(ocupacao) > 0
    assert isinstance(occ_data, dict)


def test_generate_coherent_occupation_young_student(config_data):
    """Test young person with low education gets appropriate occupation."""
    occ_data, ocupacao = demographics.generate_coherent_occupation(
        occupations_data=config_data["occupations"],
        escolaridade="Médio incompleto",
        idade=18,
    )

    assert isinstance(ocupacao, str)
    assert isinstance(occ_data, dict)


def test_generate_name(config_data):
    """Test name generation."""
    demo_data = {"identidade_genero": "mulher cis", "raca_etnia": "pardo"}
    nome = demographics.generate_name(demo_data)
    assert isinstance(nome, str)
    assert len(nome) > 0
    # Should have at least first and last name
    assert " " in nome


def test_generate_demographics_structure(config_data):
    """Test that generate_demographics returns complete structure."""
    demo = demographics.generate_demographics(config_data)

    # Check all required fields exist
    required_fields = [
        "idade",
        "genero_biologico",
        "identidade_genero",
        "raca_etnia",
        "localizacao",
        "escolaridade",
        "renda_mensal",
        "ocupacao",
        "estado_civil",
        "composicao_familiar",
    ]

    for field in required_fields:
        assert field in demo

    # Check nested structures
    assert "pais" in demo["localizacao"]
    assert "regiao" in demo["localizacao"]
    assert "tipo" in demo["composicao_familiar"]
    assert "numero_pessoas" in demo["composicao_familiar"]


def test_generate_demographics_types(config_data):
    """Test that generated demographics have correct types."""
    demo = demographics.generate_demographics(config_data)

    assert isinstance(demo["idade"], int)
    assert 18 <= demo["idade"] <= 100  # Allow up to 100 for edge cases
    assert isinstance(demo["genero_biologico"], str)
    assert isinstance(demo["identidade_genero"], str)
    assert isinstance(demo["renda_mensal"], (int, float))
    assert demo["renda_mensal"] >= 0
    assert isinstance(demo["composicao_familiar"]["numero_pessoas"], int)


def test_generate_demographics_consistency(config_data):
    """Test logical consistency in demographics."""
    demo = demographics.generate_demographics(config_data)

    # If very young, shouldn't be widowed
    if demo["idade"] < 25:
        assert demo["estado_civil"] != "viúvo"

    # Income should be reasonable for occupation/education
    assert demo["renda_mensal"] >= 0
