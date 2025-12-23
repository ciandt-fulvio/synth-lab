"""
Unit tests for coherence validation (User Story 3).

Tests the validation system that enforces personality-bias coherence rules
to ensure all synths maintain psychological consistency.

Tests cover:
- validate_coherence function
- CoherenceError exception
- Meaningful error messages for violations
- Backward compatibility checks
"""

import pytest

from synth_lab.gen_synth.validation import (
    CoherenceError,
    validate_coherence,
    validate_synth_full,
)


class TestValidateCoherence:
    """Test validate_coherence function (T040)."""

    def test_function_accepts_valid_coherent_synth(self):
        """Test that validate_coherence accepts synths with coherent biases."""
        synth = {
            "psicografia": {
                "personalidade_big_five": {
                    "abertura": 85,  # High openness
                    "conscienciosidade": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                }
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 50,
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 25,  # Low confirmation bias (coherent with high openness)
                "vies_status_quo": 50,
                "sobrecarga_informacao": 30,  # Low info overload (coherent with high openness)
            },
        }

        # Should not raise exception
        result = validate_coherence(synth)
        assert result is True or result == (True, [])

    def test_function_rejects_incoherent_synth(self):
        """Test that validate_coherence rejects synths with incoherent biases."""
        synth = {
            "psicografia": {
                "personalidade_big_five": {
                    "abertura": 85,  # High openness
                    "conscienciosidade": 85,  # High conscientiousness
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                }
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 75,  # HIGH - incoherent with high conscientiousness
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 80,  # HIGH - incoherent with high openness
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        # Should raise CoherenceError or return (False, errors)
        with pytest.raises(CoherenceError):
            validate_coherence(synth, strict=True)

    def test_function_returns_false_and_errors_in_non_strict_mode(self):
        """Test that validate_coherence returns errors without raising in non-strict mode."""
        synth = {
            "psicografia": {
                "personalidade_big_five": {
                    "conscienciosidade": 85,
                    "abertura": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                }
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 75,  # Incoherent with high conscientiousness
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 50,
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        is_valid, errors = validate_coherence(synth, strict=False)

        assert is_valid is False
        assert len(errors) > 0
        assert isinstance(errors, list)


class TestCoherenceErrorMessages:
    """Test coherence error messages (T041)."""

    def test_error_message_includes_trait_name(self):
        """Test that error messages include the personality trait name."""
        synth = {
            "psicografia": {
                "personalidade_big_five": {
                    "conscienciosidade": 85,
                    "abertura": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                }
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 75,
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 50,
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        is_valid, errors = validate_coherence(synth, strict=False)

        # Error should mention "conscienciosidade" or "conscientiousness"
        assert any("conscienciosidade" in err.lower() or "conscientiousness" in err.lower()
                   for err in errors), f"Error should mention trait: {errors}"

    def test_error_message_includes_bias_name(self):
        """Test that error messages include the bias name."""
        synth = {
            "psicografia": {
                "personalidade_big_five": {
                    "neuroticismo": 85,
                    "abertura": 50,
                    "conscienciosidade": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                }
            },
            "vieses": {
                "aversao_perda": 20,  # LOW - incoherent with high neuroticism
                "desconto_hiperbolico": 50,
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 50,
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        is_valid, errors = validate_coherence(synth, strict=False)

        # Error should mention "aversao_perda" or "loss aversion"
        assert any("aversao_perda" in err.lower() or "loss" in err.lower()
                   for err in errors), f"Error should mention bias: {errors}"

    def test_error_message_includes_expected_range(self):
        """Test that error messages include the expected value range."""
        synth = {
            "psicografia": {
                "personalidade_big_five": {
                    "abertura": 85,
                    "conscienciosidade": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                }
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 50,
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 80,
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        is_valid, errors = validate_coherence(synth, strict=False)

        # Error should include numbers indicating expected range
        assert any(any(char.isdigit() for char in err) for err in errors), \
            f"Error should include expected range: {errors}"

    def test_error_message_includes_actual_value(self):
        """Test that error messages include the actual bias value."""
        synth = {
            "psicografia": {
                "personalidade_big_five": {
                    "conscienciosidade": 85,
                    "abertura": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                }
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 75,
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 50,
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        is_valid, errors = validate_coherence(synth, strict=False)

        # Error should mention the actual value (75)
        assert any("75" in err for err in errors), f"Error should include actual value: {errors}"

    def test_multiple_violations_produce_multiple_errors(self):
        """Test that multiple coherence violations produce multiple error messages."""
        synth = {
            "psicografia": {
                "personalidade_big_five": {
                    "conscienciosidade": 85,  # → desconto should be low
                    "abertura": 85,  # → vies_confirmacao should be low
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                }
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 75,  # Violation 1
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 80,  # Violation 2
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        is_valid, errors = validate_coherence(synth, strict=False)

        assert len(errors) >= 2, f"Should have at least 2 errors, got {len(errors)}: {errors}"


class TestCoherenceErrorException:
    """Test CoherenceError exception handling (T042)."""

    def test_coherence_error_is_raised_in_strict_mode(self):
        """Test that CoherenceError is raised when strict=True."""
        synth = {
            "psicografia": {
                "personalidade_big_five": {
                    "conscienciosidade": 85,
                    "abertura": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                }
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 75,
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 50,
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        with pytest.raises(CoherenceError) as exc_info:
            validate_coherence(synth, strict=True)

        # Exception should have a meaningful message
        assert len(str(exc_info.value)) > 0

    def test_coherence_error_message_contains_details(self):
        """Test that CoherenceError contains violation details."""
        synth = {
            "psicografia": {
                "personalidade_big_five": {
                    "neuroticismo": 85,
                    "abertura": 50,
                    "conscienciosidade": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                }
            },
            "vieses": {
                "aversao_perda": 20,
                "desconto_hiperbolico": 50,
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 50,
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        with pytest.raises(CoherenceError) as exc_info:
            validate_coherence(synth, strict=True)

        error_message = str(exc_info.value)
        # Message should contain useful details
        assert len(error_message) > 20, "Error message should be detailed"

    def test_coherence_error_is_not_raised_in_non_strict_mode(self):
        """Test that CoherenceError is NOT raised when strict=False."""
        synth = {
            "psicografia": {
                "personalidade_big_five": {
                    "conscienciosidade": 85,
                    "abertura": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                }
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 75,
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 50,
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        # Should NOT raise exception
        is_valid, errors = validate_coherence(synth, strict=False)
        assert is_valid is False
        assert len(errors) > 0


class TestValidateSynthFull:
    """Test validate_synth_full function (T046)."""

    def test_validates_both_schema_and_coherence(self):
        """Test that validate_synth_full validates both schema and coherence."""
        # Create a synth that passes schema but fails coherence
        synth = {
            "id": "test12",  # 6 chars
            "nome": "Test Person",
            "descricao": "A test description that is longer than 50 characters to meet the minimum requirement.",
            "link_photo": "https://ui-avatars.com/api/?name=Test",
            "created_at": "2024-01-01T00:00:00Z",
            "version": "2.0.0",
            "demografia": {
                "idade": 30,
                "genero_biologico": "feminino",
                "identidade_genero": "mulher cis",
                "raca_etnia": "branco",
                "localizacao": {
                    "pais": "Brasil",
                    "regiao": "Sudeste",
                    "estado": "SP",
                    "cidade": "São Paulo",
                },
                "escolaridade": "Superior completo",
                "renda_mensal": 5000.0,
                "ocupacao": "Analista",
                "estado_civil": "solteiro",
                "composicao_familiar": {"tipo": "unipessoal", "numero_pessoas": 1},
            },
            "psicografia": {
                "personalidade_big_five": {
                    "abertura": 85,
                    "conscienciosidade": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                },
                "interesses": ["tecnologia"],
            },
            "deficiencias": {
                "visual": {"tipo": "nenhuma"},
                "auditiva": {"tipo": "nenhuma"},
                "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
                "cognitiva": {"tipo": "nenhuma"},
            },
            "capacidades_tecnologicas": {
                "alfabetizacao_digital": 75,
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 50,
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 80,  # INCOHERENT with high openness
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        is_valid, errors = validate_synth_full(synth, strict=False)

        # Should detect coherence violation
        assert is_valid is False
        assert len(errors) > 0

    def test_accepts_fully_valid_synth(self):
        """Test that validate_synth_full accepts synths that pass all validations."""
        synth = {
            "id": "test12",  # 6 chars
            "nome": "Test Person",
            "descricao": "A test description that is longer than 50 characters to meet the minimum requirement.",
            "link_photo": "https://ui-avatars.com/api/?name=Test",
            "created_at": "2024-01-01T00:00:00Z",
            "version": "2.0.0",
            "demografia": {
                "idade": 30,
                "genero_biologico": "feminino",
                "identidade_genero": "mulher cis",
                "raca_etnia": "branco",
                "localizacao": {
                    "pais": "Brasil",
                    "regiao": "Sudeste",
                    "estado": "SP",
                    "cidade": "São Paulo",
                },
                "escolaridade": "Superior completo",
                "renda_mensal": 5000.0,
                "ocupacao": "Analista",
                "estado_civil": "solteiro",
                "composicao_familiar": {"tipo": "unipessoal", "numero_pessoas": 1},
            },
            "psicografia": {
                "personalidade_big_five": {
                    "abertura": 50,
                    "conscienciosidade": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                },
                "interesses": ["tecnologia"],
            },
            "deficiencias": {
                "visual": {"tipo": "nenhuma"},
                "auditiva": {"tipo": "nenhuma"},
                "motora": {"tipo": "nenhuma", "usa_cadeira_rodas": False},
                "cognitiva": {"tipo": "nenhuma"},
            },
            "capacidades_tecnologicas": {
                "alfabetizacao_digital": 75,
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 50,
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 50,
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        is_valid, errors = validate_synth_full(synth, strict=False)

        assert is_valid is True or len(errors) == 0


class TestBackwardCompatibility:
    """Test backward compatibility checks (T049)."""

    def test_warns_about_removed_fields_in_v1_synth(self):
        """Test that validation warns about v1.0.0 synths with removed fields."""
        v1_synth = {
            "id": "test123",
            "version": "1.0.0",  # Old version
            "psicografia": {
                "personalidade_big_five": {
                    "abertura": 50,
                    "conscienciosidade": 50,
                    "extroversao": 50,
                    "amabilidade": 50,
                    "neuroticismo": 50,
                },
                "valores": ["honestidade"],  # Removed field
                "hobbies": ["leitura"],  # Removed field
                "estilo_vida": "Equilibrado",  # Removed field
                "interesses": ["tecnologia"],
                "inclinacao_politica": 0,
                "inclinacao_religiosa": "católico",
            },
            "comportamento": {
                "uso_tecnologia": {"smartphone": True},  # Removed field
                "comportamento_compra": {"impulsivo": 50},  # Removed field
                "habitos_consumo": {
                    "frequencia_compras": "semanal",
                    "preferencia_canal": "híbrido",
                    "categorias_preferidas": ["eletrônicos"],
                },
                "padroes_midia": {"tv_aberta": 10, "streaming": 30, "redes_sociais": 40},
                "fonte_noticias": ["portais online"],
                "lealdade_marca": 50,
                "engajamento_redes_sociais": {
                    "plataformas": ["Instagram"],
                    "frequencia_posts": "ocasional",
                },
            },
            "vieses": {
                "aversao_perda": 50,
                "desconto_hiperbolico": 50,
                "suscetibilidade_chamariz": 50,
                "ancoragem": 50,
                "vies_confirmacao": 50,
                "vies_status_quo": 50,
                "sobrecarga_informacao": 50,
            },
        }

        # Should detect removed fields (this is just a warning, not an error)
        # Implementation may return warnings in errors list or separate warnings list
        # For now, just verify function can handle v1 synths
        result = validate_coherence(v1_synth, strict=False)
        assert result is not None  # Should handle gracefully
