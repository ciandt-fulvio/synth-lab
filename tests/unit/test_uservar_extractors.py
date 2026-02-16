"""
T028 Unit test for userVar extractors.

Tests each of the 10 extractors with real synth data shapes,
verifies normalization to [0,1], and defaults for missing data.

References:
    - Engine: src/synth_lab/services/simulation_engine.py
    - Data Model: specs/042-quantitative-analysis/data-model.md
"""

import numpy as np
import pytest

from synth_lab.services.simulation_engine import (
    USERVAR_EXTRACTORS,
    _clamp,
    _normalize,
    extract_user_vars,
)


@pytest.mark.unit
class TestClampAndNormalize:
    """Unit tests for _clamp and _normalize helpers."""

    def test_clamp_within_range(self):
        assert _clamp(0.5) == 0.5

    def test_clamp_below(self):
        assert _clamp(-0.1) == 0.0

    def test_clamp_above(self):
        assert _clamp(1.5) == 1.0

    def test_normalize_midpoint(self):
        assert _normalize(50, 0, 100) == 0.5

    def test_normalize_min(self):
        assert _normalize(0, 0, 100) == 0.0

    def test_normalize_max(self):
        assert _normalize(100, 0, 100) == 1.0

    def test_normalize_beyond_max(self):
        assert _normalize(150, 0, 100) == 1.0


@pytest.mark.unit
class TestAgeNormExtractor:
    """Tests for ageNorm extractor."""

    def test_young_person(self):
        synth = {"data": {"demografia": {"idade": 18}}}
        result = USERVAR_EXTRACTORS["ageNorm"](synth)
        assert result == 0.0

    def test_old_person(self):
        synth = {"data": {"demografia": {"idade": 80}}}
        result = USERVAR_EXTRACTORS["ageNorm"](synth)
        assert result == 1.0

    def test_middle_age(self):
        synth = {"data": {"demografia": {"idade": 49}}}
        result = USERVAR_EXTRACTORS["ageNorm"](synth)
        assert 0.4 < result < 0.6

    def test_missing_age_defaults(self):
        synth = {"data": {"demografia": {}}}
        result = USERVAR_EXTRACTORS["ageNorm"](synth)
        assert result == 0.5


@pytest.mark.unit
class TestIncomeNormExtractor:
    """Tests for incomeNorm extractor."""

    def test_zero_income(self):
        synth = {"data": {"demografia": {"renda_mensal": 0}}}
        result = USERVAR_EXTRACTORS["incomeNorm"](synth)
        assert result == 0.0

    def test_high_income(self):
        synth = {"data": {"demografia": {"renda_mensal": 20000}}}
        result = USERVAR_EXTRACTORS["incomeNorm"](synth)
        assert result == 1.0

    def test_mid_income(self):
        synth = {"data": {"demografia": {"renda_mensal": 10000}}}
        result = USERVAR_EXTRACTORS["incomeNorm"](synth)
        assert result == 0.5

    def test_missing_income_defaults(self):
        synth = {"data": {"demografia": {}}}
        result = USERVAR_EXTRACTORS["incomeNorm"](synth)
        assert result == 0.5


@pytest.mark.unit
class TestEduNormExtractor:
    """Tests for eduNorm extractor."""

    def test_no_education(self):
        synth = {"data": {"demografia": {"escolaridade": "sem escolaridade"}}}
        result = USERVAR_EXTRACTORS["eduNorm"](synth)
        assert result == 0.0

    def test_doctorate(self):
        synth = {"data": {"demografia": {"escolaridade": "doutorado"}}}
        result = USERVAR_EXTRACTORS["eduNorm"](synth)
        assert result == 1.0

    def test_medio_completo(self):
        synth = {"data": {"demografia": {"escolaridade": "médio completo"}}}
        result = USERVAR_EXTRACTORS["eduNorm"](synth)
        assert 0.3 < result < 0.6

    def test_missing_education_defaults(self):
        synth = {"data": {"demografia": {"escolaridade": ""}}}
        result = USERVAR_EXTRACTORS["eduNorm"](synth)
        assert result == 0.5


@pytest.mark.unit
class TestFamilySizeNormExtractor:
    """Tests for familySizeNorm extractor."""

    def test_single_person(self):
        synth = {"data": {"demografia": {"composicao_familiar": {"numero_pessoas": 1}}}}
        result = USERVAR_EXTRACTORS["familySizeNorm"](synth)
        assert result == 0.0

    def test_large_family(self):
        synth = {"data": {"demografia": {"composicao_familiar": {"numero_pessoas": 8}}}}
        result = USERVAR_EXTRACTORS["familySizeNorm"](synth)
        assert result == 1.0

    def test_missing_defaults(self):
        synth = {"data": {"demografia": {}}}
        result = USERVAR_EXTRACTORS["familySizeNorm"](synth)
        assert result == 0.5


@pytest.mark.unit
class TestDisabilityExtractors:
    """Tests for hasVisualDisab and hasMotorDisab extractors."""

    def test_no_visual_disability(self):
        synth = {"data": {"deficiencias": {"visual": {"tipo": "nenhuma"}}}}
        assert USERVAR_EXTRACTORS["hasVisualDisab"](synth) == 0.0

    def test_has_visual_disability(self):
        synth = {"data": {"deficiencias": {"visual": {"tipo": "moderada"}}}}
        assert USERVAR_EXTRACTORS["hasVisualDisab"](synth) == 1.0

    def test_no_motor_disability(self):
        synth = {"data": {"deficiencias": {"motora": {"tipo": "nenhuma"}}}}
        assert USERVAR_EXTRACTORS["hasMotorDisab"](synth) == 0.0

    def test_has_motor_disability(self):
        synth = {"data": {"deficiencias": {"motora": {"tipo": "severa"}}}}
        assert USERVAR_EXTRACTORS["hasMotorDisab"](synth) == 1.0

    def test_missing_disability_data(self):
        synth = {"data": {"deficiencias": {}}}
        assert USERVAR_EXTRACTORS["hasVisualDisab"](synth) == 0.0
        assert USERVAR_EXTRACTORS["hasMotorDisab"](synth) == 0.0


@pytest.mark.unit
class TestSensitivityExtractors:
    """Tests for digitalCapability, riskAversion, institutionalTrust, frictionTolerance."""

    def test_digital_capability(self):
        synth = {"data": {"sensitivities": {"digital_capability": 0.8}}}
        assert USERVAR_EXTRACTORS["digitalCapability"](synth) == 0.8

    def test_risk_aversion(self):
        synth = {"data": {"sensitivities": {"risk_aversion": 0.3}}}
        assert USERVAR_EXTRACTORS["riskAversion"](synth) == 0.3

    def test_institutional_trust(self):
        synth = {"data": {"sensitivities": {"institutional_trust_level": 0.7}}}
        assert USERVAR_EXTRACTORS["institutionalTrust"](synth) == 0.7

    def test_friction_tolerance(self):
        synth = {"data": {"sensitivities": {"friction_tolerance": 0.6}}}
        assert USERVAR_EXTRACTORS["frictionTolerance"](synth) == 0.6

    def test_missing_sensitivities_defaults(self):
        synth = {"data": {}}
        assert USERVAR_EXTRACTORS["digitalCapability"](synth) == 0.5
        assert USERVAR_EXTRACTORS["riskAversion"](synth) == 0.5
        assert USERVAR_EXTRACTORS["institutionalTrust"](synth) == 0.5
        assert USERVAR_EXTRACTORS["frictionTolerance"](synth) == 0.5


@pytest.mark.unit
class TestExtractUserVars:
    """Tests for extract_user_vars matrix builder."""

    def test_correct_shape(self):
        """Output shape is (n_synths, n_vars)."""
        synths = [
            {"data": {"demografia": {"idade": 25}}},
            {"data": {"demografia": {"idade": 50}}},
        ]
        result = extract_user_vars(synths, ["ageNorm", "incomeNorm"])
        assert result.shape == (2, 2)

    def test_values_in_range(self):
        """All values are in [0, 1]."""
        synths = [
            {"data": {"demografia": {"idade": 30, "renda_mensal": 5000, "escolaridade": "superior completo"}}},
        ]
        result = extract_user_vars(synths, ["ageNorm", "incomeNorm", "eduNorm"])
        assert np.all(result >= 0)
        assert np.all(result <= 1)

    def test_unknown_var_defaults_to_half(self):
        """Unknown userVar names produce 0.5."""
        synths = [{"data": {"demografia": {"idade": 30}}}]
        result = extract_user_vars(synths, ["unknownVar"])
        assert result[0, 0] == 0.5

    def test_all_ten_extractors_registered(self):
        """All 10 userVar extractors are in the registry."""
        expected = {
            "ageNorm", "incomeNorm", "eduNorm", "familySizeNorm",
            "hasVisualDisab", "hasMotorDisab", "digitalCapability",
            "riskAversion", "institutionalTrust", "frictionTolerance",
        }
        assert set(USERVAR_EXTRACTORS.keys()) == expected
