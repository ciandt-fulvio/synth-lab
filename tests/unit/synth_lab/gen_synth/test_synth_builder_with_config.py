"""
Unit tests for synth_builder.assemble_synth_with_config function.

Tests custom distribution-based synth generation for custom synth groups.
"""

import numpy as np
import pytest

from synth_lab.gen_synth import validation
from synth_lab.gen_synth.synth_builder import assemble_synth_with_config


class TestAssembleSynthWithConfig:
    """Tests for assemble_synth_with_config function."""

    def test_returns_complete_synth_structure(self, config_data):
        """Test that assemble_synth_with_config returns complete synth structure."""
        group_config = {
            "distributions": {
                "idade": {"15-29": 0.25, "30-44": 0.25, "45-59": 0.25, "60+": 0.25},
                "escolaridade": {
                    "sem_instrucao": 0.1,
                    "fundamental": 0.3,
                    "medio": 0.3,
                    "superior": 0.3,
                },
                "deficiencias": {
                    "taxa_com_deficiencia": 0.1,
                    "distribuicao_severidade": {
                        "nenhuma": 0.2,
                        "leve": 0.2,
                        "moderada": 0.2,
                        "severa": 0.2,
                        "total": 0.2,
                    },
                },
                "composicao_familiar": {
                    "unipessoal": 0.2,
                    "casal_sem_filhos": 0.2,
                    "casal_com_filhos": 0.3,
                    "monoparental": 0.15,
                    "multigeracional": 0.15,
                },
                "domain_expertise": {"alpha": 3, "beta": 3},
            }
        }

        synth = assemble_synth_with_config(config_data, group_config)

        # Check required fields
        required_fields = [
            "id",
            "nome",
            "descricao",
            "link_photo",
            "created_at",
            "version",
            "demografia",
            "psicografia",
            "deficiencias",
            "observables",
        ]
        for field in required_fields:
            assert field in synth, f"Missing field: {field}"

    def test_passes_validation(self, config_data):
        """Test that synths with custom config pass schema validation."""
        group_config = {
            "distributions": {
                "idade": {"15-29": 0.25, "30-44": 0.25, "45-59": 0.25, "60+": 0.25},
                "escolaridade": {
                    "sem_instrucao": 0.1,
                    "fundamental": 0.3,
                    "medio": 0.3,
                    "superior": 0.3,
                },
                "deficiencias": {
                    "taxa_com_deficiencia": 0.1,
                    "distribuicao_severidade": {
                        "nenhuma": 0.2,
                        "leve": 0.2,
                        "moderada": 0.2,
                        "severa": 0.2,
                        "total": 0.2,
                    },
                },
                "composicao_familiar": {
                    "unipessoal": 0.2,
                    "casal_sem_filhos": 0.2,
                    "casal_com_filhos": 0.3,
                    "monoparental": 0.15,
                    "multigeracional": 0.15,
                },
                "domain_expertise": {"alpha": 3, "beta": 3},
            }
        }

        synth = assemble_synth_with_config(config_data, group_config)
        is_valid, errors = validation.validate_synth(synth)

        assert is_valid, f"Validation failed: {errors}"

    def test_uses_custom_age_distribution(self, config_data):
        """Test that custom age distribution affects generated ages."""
        # Skew heavily toward 60+
        group_config = {
            "distributions": {
                "idade": {"15-29": 0.0, "30-44": 0.0, "45-59": 0.1, "60+": 0.9},
                "escolaridade": {
                    "sem_instrucao": 0.25,
                    "fundamental": 0.25,
                    "medio": 0.25,
                    "superior": 0.25,
                },
                "deficiencias": {"taxa_com_deficiencia": 0.1},
                "composicao_familiar": {
                    "unipessoal": 0.2,
                    "casal_sem_filhos": 0.2,
                    "casal_com_filhos": 0.3,
                    "monoparental": 0.15,
                    "multigeracional": 0.15,
                },
                "domain_expertise": {"alpha": 3, "beta": 3},
            }
        }

        # Generate multiple synths and check age distribution
        ages_60_plus = 0
        total = 50
        rng = np.random.default_rng(42)

        for _ in range(total):
            synth = assemble_synth_with_config(config_data, group_config, rng=rng)
            if synth["demografia"]["idade"] >= 60:
                ages_60_plus += 1

        # With 90% skew toward 60+, expect most to be 60+
        ratio = ages_60_plus / total
        assert ratio > 0.7, f"Expected >70% ages 60+, got {ratio * 100:.1f}%"

    def test_uses_custom_expertise_params(self, config_data):
        """Test that custom expertise alpha/beta affects domain_expertise."""
        # Low expertise (alpha=2, beta=5) should skew toward lower values
        group_config_low = {
            "distributions": {
                "idade": {"15-29": 0.25, "30-44": 0.25, "45-59": 0.25, "60+": 0.25},
                "escolaridade": {
                    "sem_instrucao": 0.25,
                    "fundamental": 0.25,
                    "medio": 0.25,
                    "superior": 0.25,
                },
                "deficiencias": {"taxa_com_deficiencia": 0.1},
                "composicao_familiar": {"unipessoal": 1.0},
                "domain_expertise": {"alpha": 2, "beta": 5},  # Low expertise
            }
        }

        # High expertise (alpha=5, beta=2) should skew toward higher values
        group_config_high = {
            "distributions": {
                "idade": {"15-29": 0.25, "30-44": 0.25, "45-59": 0.25, "60+": 0.25},
                "escolaridade": {
                    "sem_instrucao": 0.25,
                    "fundamental": 0.25,
                    "medio": 0.25,
                    "superior": 0.25,
                },
                "deficiencias": {"taxa_com_deficiencia": 0.1},
                "composicao_familiar": {"unipessoal": 1.0},
                "domain_expertise": {"alpha": 5, "beta": 2},  # High expertise
            }
        }

        total = 30
        rng = np.random.default_rng(42)

        low_expertise_values = []
        for _ in range(total):
            synth = assemble_synth_with_config(config_data, group_config_low, rng=rng)
            low_expertise_values.append(synth["observables"]["domain_expertise"])

        high_expertise_values = []
        for _ in range(total):
            synth = assemble_synth_with_config(config_data, group_config_high, rng=rng)
            high_expertise_values.append(synth["observables"]["domain_expertise"])

        low_mean = sum(low_expertise_values) / len(low_expertise_values)
        high_mean = sum(high_expertise_values) / len(high_expertise_values)

        # High expertise config should produce higher mean
        assert high_mean > low_mean, (
            f"Expected high expertise mean ({high_mean:.3f}) > "
            f"low expertise mean ({low_mean:.3f})"
        )

    def test_uses_custom_disability_rate(self, config_data):
        """Test that custom disability rate affects generated disabilities."""
        # High disability rate
        group_config = {
            "distributions": {
                "idade": {"15-29": 0.25, "30-44": 0.25, "45-59": 0.25, "60+": 0.25},
                "escolaridade": {
                    "sem_instrucao": 0.25,
                    "fundamental": 0.25,
                    "medio": 0.25,
                    "superior": 0.25,
                },
                "deficiencias": {
                    "taxa_com_deficiencia": 0.5,  # 50% with disabilities
                    "distribuicao_severidade": {
                        "nenhuma": 0.0,
                        "leve": 0.25,
                        "moderada": 0.25,
                        "severa": 0.25,
                        "total": 0.25,
                    },
                },
                "composicao_familiar": {"unipessoal": 1.0},
                "domain_expertise": {"alpha": 3, "beta": 3},
            }
        }

        total = 50
        rng = np.random.default_rng(42)
        with_disability = 0

        for _ in range(total):
            synth = assemble_synth_with_config(config_data, group_config, rng=rng)
            defic = synth["deficiencias"]
            # Check if any disability is not "nenhuma"
            has_disability = any(
                d.get("tipo") != "nenhuma"
                for d in [defic["visual"], defic["auditiva"], defic["motora"], defic["cognitiva"]]
            )
            if has_disability:
                with_disability += 1

        # With 50% rate, expect around 50% with disabilities (with some variance)
        ratio = with_disability / total
        assert 0.3 <= ratio <= 0.7, f"Expected ~50% with disabilities, got {ratio * 100:.1f}%"

    def test_generates_unique_ids(self, config_data):
        """Test that each generated synth has a unique ID."""
        group_config = {
            "distributions": {
                "idade": {"15-29": 0.25, "30-44": 0.25, "45-59": 0.25, "60+": 0.25},
                "escolaridade": {
                    "sem_instrucao": 0.25,
                    "fundamental": 0.25,
                    "medio": 0.25,
                    "superior": 0.25,
                },
                "deficiencias": {"taxa_com_deficiencia": 0.1},
                "composicao_familiar": {"unipessoal": 1.0},
                "domain_expertise": {"alpha": 3, "beta": 3},
            }
        }

        ids = set()
        for _ in range(10):
            synth = assemble_synth_with_config(config_data, group_config)
            ids.add(synth["id"])

        assert len(ids) == 10, "All synth IDs should be unique"

    def test_handles_empty_distributions(self, config_data):
        """Test that function works with minimal/empty distribution config."""
        group_config = {"distributions": {}}

        # Should still generate a valid synth using defaults
        synth = assemble_synth_with_config(config_data, group_config)

        assert synth is not None
        assert "id" in synth
        assert "nome" in synth

    def test_multiple_synths_are_diverse(self, config_data):
        """Test that generated synths have diverse attributes."""
        group_config = {
            "distributions": {
                "idade": {"15-29": 0.25, "30-44": 0.25, "45-59": 0.25, "60+": 0.25},
                "escolaridade": {
                    "sem_instrucao": 0.1,
                    "fundamental": 0.3,
                    "medio": 0.3,
                    "superior": 0.3,
                },
                "deficiencias": {"taxa_com_deficiencia": 0.1},
                "composicao_familiar": {
                    "unipessoal": 0.2,
                    "casal_sem_filhos": 0.2,
                    "casal_com_filhos": 0.3,
                    "monoparental": 0.15,
                    "multigeracional": 0.15,
                },
                "domain_expertise": {"alpha": 3, "beta": 3},
            }
        }

        names = set()
        ages = set()
        for _ in range(10):
            synth = assemble_synth_with_config(config_data, group_config)
            names.add(synth["nome"])
            ages.add(synth["demografia"]["idade"])

        # Expect at least some diversity
        assert len(names) >= 5, "Expected more name diversity"
        assert len(ages) >= 3, "Expected more age diversity"
