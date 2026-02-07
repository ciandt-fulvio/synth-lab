"""
Unit tests for SensitivityDeriver service.

Tests config loading, nested value extraction, condition evaluation,
and sensitivity derivation from synth demographic data.

References:
    - Service: src/synth_lab/services/sensitivity_deriver.py
    - Config: src/synth_lab/config/sensitivity_rules.yaml
"""

import pytest

from synth_lab.services.sensitivity_deriver import (
    derive_sensitivities,
    evaluate_condition,
    get_nested_value,
    load_sensitivity_rules,
)

ALL_7_SENSITIVITIES = [
    "risk_aversion",
    "social_dependency",
    "institutional_trust_level",
    "habit_plasticity",
    "friction_tolerance",
    "pragmatism",
    "digital_capability",
]


# ==================== Config Loading ====================


class TestLoadConfig:
    """Tests for load_sensitivity_rules()."""

    def test_load_config_returns_dict_with_version(self):
        """GIVEN default config WHEN loading THEN returns dict with version='1.0'."""
        config = load_sensitivity_rules()
        assert isinstance(config, dict)
        assert config["version"] == "1.0"

    def test_load_config_has_all_7_sensitivities(self):
        """GIVEN default config WHEN loading THEN all 7 sensitivities are present."""
        config = load_sensitivity_rules()
        sensitivities = config["sensitivities"]
        for name in ALL_7_SENSITIVITIES:
            assert name in sensitivities, f"Missing sensitivity: {name}"

    def test_load_config_name_is_metadata_only(self):
        """GIVEN a custom config_name WHEN loading THEN it loads default YAML."""
        # config_name parameter is metadata-only; it doesn't map to a different file
        config = load_sensitivity_rules("custom_name")
        assert "version" in config
        assert "sensitivities" in config

    def test_metadata_reflects_specific_config_version(self):
        """GIVEN default config WHEN deriving THEN _meta.derivation_version matches YAML version."""
        result = derive_sensitivities({})
        assert result["_meta"]["derivation_version"] == "1.0"


# ==================== get_nested_value ====================


class TestGetNestedValue:
    """Tests for get_nested_value() with dot-notation field paths."""

    @pytest.mark.parametrize(
        "field_path, data, expected",
        [
            ("a.b", {"a": {"b": 1}}, 1),
            ("a.b.c", {"a": {"b": {"c": "deep"}}}, "deep"),
            ("missing", {}, None),
            ("a.missing", {"a": {}}, None),
            ("a", {"a": 42}, 42),
            ("a.b.c", {"a": {"b": 5}}, None),  # b is not a dict, can't go deeper
            ("x.y.z", {"x": {"y": {"z": 0}}}, 0),  # falsy but valid
            ("a.b", {"a": {"b": ""}}, ""),  # empty string is valid
        ],
        ids=[
            "two_level_int",
            "three_level_string",
            "missing_top_level",
            "missing_nested",
            "single_level",
            "path_beyond_non_dict",
            "falsy_zero_value",
            "empty_string_value",
        ],
    )
    def test_get_nested_value(self, field_path, data, expected):
        """GIVEN data dict and field path WHEN getting nested value THEN returns expected."""
        result = get_nested_value(data, field_path, default=None)
        assert result == expected

    def test_get_nested_value_with_custom_default(self):
        """GIVEN missing path WHEN getting with custom default THEN returns default."""
        result = get_nested_value({}, "missing.path", default="FALLBACK")
        assert result == "FALLBACK"


# ==================== evaluate_condition ====================


class TestEvaluateCondition:
    """Tests for evaluate_condition() with all supported operators."""

    @pytest.mark.parametrize(
        "condition, synth_data, expected",
        [
            # >= operator
            (
                {"field": "demografia.idade", "operator": ">=", "value": 25},
                {"demografia": {"idade": 30}},
                True,
            ),
            (
                {"field": "demografia.idade", "operator": ">=", "value": 25},
                {"demografia": {"idade": 20}},
                False,
            ),
            (
                {"field": "demografia.idade", "operator": ">=", "value": 25},
                {"demografia": {"idade": 25}},
                True,
            ),
            # <= operator
            (
                {"field": "demografia.idade", "operator": "<=", "value": 25},
                {"demografia": {"idade": 20}},
                True,
            ),
            (
                {"field": "demografia.idade", "operator": "<=", "value": 25},
                {"demografia": {"idade": 30}},
                False,
            ),
            # > operator
            (
                {"field": "demografia.idade", "operator": ">", "value": 25},
                {"demografia": {"idade": 30}},
                True,
            ),
            (
                {"field": "demografia.idade", "operator": ">", "value": 25},
                {"demografia": {"idade": 25}},
                False,
            ),
            # < operator
            (
                {"field": "demografia.idade", "operator": "<", "value": 25},
                {"demografia": {"idade": 20}},
                True,
            ),
            (
                {"field": "demografia.idade", "operator": "<", "value": 25},
                {"demografia": {"idade": 25}},
                False,
            ),
            # == operator
            (
                {"field": "demografia.idade", "operator": "==", "value": 25},
                {"demografia": {"idade": 25}},
                True,
            ),
            (
                {"field": "demografia.idade", "operator": "==", "value": 25},
                {"demografia": {"idade": 30}},
                False,
            ),
            # contains operator
            (
                {
                    "field": "composicao_familiar.tipo",
                    "operator": "contains",
                    "value": "mono",
                },
                {"composicao_familiar": {"tipo": "monoparental"}},
                True,
            ),
            (
                {
                    "field": "composicao_familiar.tipo",
                    "operator": "contains",
                    "value": "mono",
                },
                {"composicao_familiar": {"tipo": "nuclear"}},
                False,
            ),
            # contains_any operator
            (
                {
                    "field": "composicao_familiar.tipo",
                    "operator": "contains_any",
                    "value": ["qualquer", "outro"],
                },
                {"composicao_familiar": {"tipo": "qualquer valor"}},
                True,
            ),
            (
                {
                    "field": "composicao_familiar.tipo",
                    "operator": "contains_any",
                    "value": ["xyz", "abc"],
                },
                {"composicao_familiar": {"tipo": "nenhum match"}},
                False,
            ),
            # in operator
            (
                {
                    "field": "demografia.escolaridade",
                    "operator": "in",
                    "value": ["ensino superior completo", "pos-graduacao"],
                },
                {"demografia": {"escolaridade": "pos-graduacao"}},
                True,
            ),
            (
                {
                    "field": "demografia.escolaridade",
                    "operator": "in",
                    "value": ["superior", "pos-graduacao"],
                },
                {"demografia": {"escolaridade": "fundamental"}},
                False,
            ),
            # Missing field → False
            (
                {"field": "campo.inexistente", "operator": ">=", "value": 10},
                {},
                False,
            ),
            (
                {
                    "field": "campo.inexistente",
                    "operator": "in",
                    "value": ["a", "b"],
                },
                {"campo": {}},
                False,
            ),
        ],
        ids=[
            "gte_true",
            "gte_false",
            "gte_equal_boundary",
            "lte_true",
            "lte_false",
            "gt_true",
            "gt_equal_boundary_false",
            "lt_true",
            "lt_equal_boundary_false",
            "eq_true",
            "eq_false",
            "contains_true",
            "contains_false",
            "contains_any_true",
            "contains_any_false",
            "in_true",
            "in_false",
            "missing_field_numeric",
            "missing_field_in",
        ],
    )
    def test_evaluate_condition(self, condition, synth_data, expected):
        """GIVEN condition and synth data WHEN evaluating THEN returns expected bool."""
        result = evaluate_condition(condition, synth_data)
        assert result is expected


# ==================== derive_sensitivities ====================


class TestDeriveSensitivities:
    """Tests for derive_sensitivities() end-to-end derivation."""

    def test_derive_all_7_present(self):
        """GIVEN any valid synth data WHEN deriving THEN result has all 7 sensitivity keys."""
        result = derive_sensitivities({"demografia": {"idade": 35}})
        for name in ALL_7_SENSITIVITIES:
            assert name in result, f"Missing sensitivity key: {name}"

    def test_derive_missing_demographics_defaults(self):
        """GIVEN empty dict WHEN deriving THEN all 7 values present at base values."""
        result = derive_sensitivities({})
        # With no demographics, no rules fire; values should be base
        assert result["risk_aversion"] == pytest.approx(0.60)
        assert result["social_dependency"] == pytest.approx(0.50)
        assert result["institutional_trust_level"] == pytest.approx(0.50)
        assert result["habit_plasticity"] == pytest.approx(0.55)
        assert result["friction_tolerance"] == pytest.approx(0.50)
        assert result["pragmatism"] == pytest.approx(0.55)
        assert result["digital_capability"] == pytest.approx(0.50)

    def test_derive_young_tech_professional(self):
        """GIVEN young (25) with higher education WHEN deriving.

        Checks lower risk_aversion and higher digital_capability.
        """
        synth_data = {
            "demografia": {
                "idade": 25,
                "escolaridade": "Superior completo",
            },
        }
        result = derive_sensitivities(synth_data)

        # risk_aversion: base=0.60, age<=25 → -0.05, escolaridade in [superior, pos] → -0.05 = 0.50
        assert result["risk_aversion"] == pytest.approx(0.50)
        assert result["risk_aversion"] < 0.60  # Below base

        # digital_capability: base=0.50, age<=30 -> +0.15,
        # escolaridade in [superior, pos] -> +0.10 = 0.75
        assert result["digital_capability"] == pytest.approx(0.75)
        assert result["digital_capability"] > 0.50  # Above base

    def test_derive_elderly_with_disabilities(self):
        """GIVEN elderly (65) with fundamental education and motor disability.

        Checks high risk_aversion and low digital_capability.
        """
        synth_data = {
            "demografia": {
                "idade": 65,
                "escolaridade": "fundamental",
            },
            "deficiencias": {
                "motora": {"tipo": "moderada"},
            },
        }
        result = derive_sensitivities(synth_data)

        # risk_aversion: base=0.60, age>=60 → +0.10 = 0.70
        assert result["risk_aversion"] == pytest.approx(0.70)
        assert result["risk_aversion"] > 0.60

        # digital_capability: base=0.50, age>=60 → -0.20 = 0.30
        assert result["digital_capability"] == pytest.approx(0.30)
        assert result["digital_capability"] < 0.50

        # habit_plasticity: base=0.55, age>=60 → -0.15 = 0.40
        assert result["habit_plasticity"] == pytest.approx(0.40)
        assert result["habit_plasticity"] < 0.55

        # friction_tolerance: base=0.50, age>=60 → -0.10, deficiencia motora → -0.10 = 0.30
        assert result["friction_tolerance"] == pytest.approx(0.30)

    def test_derive_single_parent(self):
        """GIVEN single parent (monoparental) WHEN deriving THEN friction_tolerance < base."""
        synth_data = {
            "composicao_familiar": {"tipo": "monoparental"},
        }
        result = derive_sensitivities(synth_data)

        # friction_tolerance: base=0.50, monoparental contains "monoparental" → -0.05 = 0.45
        assert result["friction_tolerance"] == pytest.approx(0.45)
        assert result["friction_tolerance"] < 0.50

    def test_derive_values_clamped(self):
        """GIVEN extreme adjustments WHEN deriving THEN all values clamped between 0.0 and 1.0."""
        # Use very old person with many penalty conditions to push values low
        synth_data = {
            "demografia": {"idade": 95, "escolaridade": "fundamental"},
            "deficiencias": {
                "motora": {"tipo": "severa"},
                "visual": {"tipo": "severa"},
            },
            "composicao_familiar": {"tipo": "monoparental"},
        }
        result = derive_sensitivities(synth_data)

        for name in ALL_7_SENSITIVITIES:
            assert 0.0 <= result[name] <= 1.0, f"{name}={result[name]} is out of [0.0, 1.0] range"

    def test_derive_metadata_present(self):
        """GIVEN any synth data WHEN deriving THEN result has _meta with expected fields."""
        result = derive_sensitivities({"demografia": {"idade": 30}})
        assert "_meta" in result
        meta = result["_meta"]
        assert "derivation_version" in meta
        assert "config_name" in meta
        assert "applied_rules" in meta

    def test_derive_metadata_applied_rules_for_young(self):
        """GIVEN 25yo WHEN deriving THEN applied_rules includes reasons from age-based rules."""
        synth_data = {"demografia": {"idade": 25}}
        result = derive_sensitivities(synth_data)
        applied_rules = result["_meta"]["applied_rules"]

        # At age 25:
        # - risk_aversion: age<=25 fires ("Jovens sao mais aventureiros")
        # - social_dependency: age<=30 fires ("Jovens mais dependentes socialmente")
        # - habit_plasticity: age<=30 fires ("Jovens mudam habitos com facilidade")
        # - friction_tolerance: age<=30 fires ("Jovens toleram mais friccao")
        # - digital_capability: age<=30 fires ("Nativos digitais")
        assert len(applied_rules) >= 5
        # applied_rules is a list of reason strings
        assert any("Jovens" in reason or "jovens" in reason for reason in applied_rules), (
            f"Expected at least one youth-related reason, got: {applied_rules}"
        )

    def test_derive_metadata_applied_rules_empty_for_default(self):
        """GIVEN empty demographics WHEN deriving THEN applied_rules is empty list."""
        result = derive_sensitivities({})
        applied_rules = result["_meta"]["applied_rules"]
        assert applied_rules == []


# ==================== Age-based parametrized tests ====================


class TestAgeSensitivities:
    """Parametrized tests verifying sensitivity trends across age ranges."""

    @pytest.mark.parametrize(
        "age_younger, age_older",
        [
            (20, 30),
            (30, 50),
            (50, 65),
            (20, 65),
        ],
        ids=[
            "20_vs_30",
            "30_vs_50",
            "50_vs_65",
            "20_vs_65",
        ],
    )
    def test_risk_aversion_increases_with_age(self, age_younger, age_older):
        """GIVEN two ages WHEN deriving THEN risk_aversion is >= for older person."""
        younger_data = {"demografia": {"idade": age_younger}}
        older_data = {"demografia": {"idade": age_older}}

        younger_result = derive_sensitivities(younger_data)
        older_result = derive_sensitivities(older_data)

        assert older_result["risk_aversion"] >= younger_result["risk_aversion"], (
            f"risk_aversion should be >= for age {age_older} ({older_result['risk_aversion']}) "
            f"vs age {age_younger} ({younger_result['risk_aversion']})"
        )

    @pytest.mark.parametrize(
        "age_younger, age_older",
        [
            (20, 30),
            (30, 50),
            (50, 65),
            (20, 65),
        ],
        ids=[
            "20_vs_30",
            "30_vs_50",
            "50_vs_65",
            "20_vs_65",
        ],
    )
    def test_digital_capability_decreases_with_age(self, age_younger, age_older):
        """GIVEN two ages WHEN deriving THEN digital_capability is <= for older person."""
        younger_data = {"demografia": {"idade": age_younger}}
        older_data = {"demografia": {"idade": age_older}}

        younger_result = derive_sensitivities(younger_data)
        older_result = derive_sensitivities(older_data)

        assert older_result["digital_capability"] <= younger_result["digital_capability"], (
            f"digital_capability should be <= for age {age_older} "
            f"({older_result['digital_capability']}) "
            f"vs age {age_younger} "
            f"({younger_result['digital_capability']})"
        )

    @pytest.mark.parametrize(
        "age",
        [20, 25, 30, 35, 40, 50, 60, 65, 70, 80],
        ids=[f"age_{a}" for a in [20, 25, 30, 35, 40, 50, 60, 65, 70, 80]],
    )
    def test_all_sensitivities_in_valid_range(self, age):
        """GIVEN any age WHEN deriving THEN all sensitivities are in [0.0, 1.0]."""
        result = derive_sensitivities({"demografia": {"idade": age}})
        for name in ALL_7_SENSITIVITIES:
            assert 0.0 <= result[name] <= 1.0, f"age={age}: {name}={result[name]} out of range"


# ==================== Education-based tests ====================


class TestEducationSensitivities:
    """Tests verifying education-level impacts on sensitivities."""

    @pytest.mark.parametrize(
        "escolaridade, expected_adjustment",
        [
            ("Superior completo", True),
            ("Pós-graduação", True),
            ("Fundamental completo", False),
            ("Médio completo", False),
        ],
        ids=[
            "superior_triggers",
            "pos_grad_triggers",
            "fundamental_no_trigger",
            "medio_no_trigger",
        ],
    )
    def test_education_affects_risk_aversion(self, escolaridade, expected_adjustment):
        """GIVEN education level WHEN deriving THEN risk_aversion adjusted."""
        synth_data = {
            "demografia": {"idade": 40, "escolaridade": escolaridade},
        }
        result = derive_sensitivities(synth_data)
        base_result = derive_sensitivities({"demografia": {"idade": 40}})

        if expected_adjustment:
            # Higher education should lower risk_aversion (adjustment = -0.05)
            assert result["risk_aversion"] < base_result["risk_aversion"]
        else:
            # No education-based adjustment
            assert result["risk_aversion"] == pytest.approx(base_result["risk_aversion"])

    def test_high_education_boosts_digital_capability(self):
        """GIVEN high education at age 40 WHEN deriving THEN digital_capability > base."""
        synth_data = {
            "demografia": {
                "idade": 40,
                "escolaridade": "Superior completo",
            },
        }
        result = derive_sensitivities(synth_data)
        # base=0.50, education → +0.10 = 0.60
        assert result["digital_capability"] == pytest.approx(0.60)

    def test_high_education_boosts_institutional_trust(self):
        """GIVEN high education at age 40 WHEN deriving THEN institutional_trust_level > base."""
        synth_data = {
            "demografia": {
                "idade": 40,
                "escolaridade": "Superior completo",
            },
        }
        result = derive_sensitivities(synth_data)
        # base=0.50, education → +0.05 = 0.55
        assert result["institutional_trust_level"] == pytest.approx(0.55)

    def test_high_education_boosts_pragmatism(self):
        """GIVEN high education at age 40 WHEN deriving THEN pragmatism > base."""
        synth_data = {
            "demografia": {
                "idade": 40,
                "escolaridade": "Superior completo",
            },
        }
        result = derive_sensitivities(synth_data)
        # base=0.55, age>=35 → +0.05, education → +0.05 = 0.65
        assert result["pragmatism"] == pytest.approx(0.65)


# ==================== Disability-based tests ====================


class TestDisabilitySensitivities:
    """Tests verifying disability impacts on sensitivities."""

    def test_motor_disability_reduces_friction_tolerance(self):
        """GIVEN moderate motor disability WHEN deriving THEN friction_tolerance < base."""
        synth_data = {
            "demografia": {"idade": 40},
            "deficiencias": {"motora": {"tipo": "moderada"}},
        }
        result = derive_sensitivities(synth_data)
        base_result = derive_sensitivities({"demografia": {"idade": 40}})

        # friction_tolerance: motor disability → -0.10
        assert result["friction_tolerance"] < base_result["friction_tolerance"]

    def test_visual_disability_reduces_digital_capability(self):
        """GIVEN moderate visual disability WHEN deriving THEN digital_capability < base."""
        synth_data = {
            "demografia": {"idade": 40},
            "deficiencias": {"visual": {"tipo": "moderada"}},
        }
        result = derive_sensitivities(synth_data)
        base_result = derive_sensitivities({"demografia": {"idade": 40}})

        # digital_capability: visual disability → -0.10
        assert result["digital_capability"] < base_result["digital_capability"]

    @pytest.mark.parametrize(
        "severity",
        ["moderada", "severa"],
        ids=["moderate", "severe"],
    )
    def test_motor_disability_severity_triggers(self, severity):
        """GIVEN motor disability of severity WHEN deriving THEN reduced."""
        synth_data = {
            "demografia": {"idade": 40},
            "deficiencias": {"motora": {"tipo": severity}},
        }
        result = derive_sensitivities(synth_data)
        # base=0.50 at age 40, motor disability → -0.10 = 0.40
        assert result["friction_tolerance"] == pytest.approx(0.40)

    def test_mild_motor_disability_does_not_trigger(self):
        """GIVEN mild motor disability WHEN deriving THEN friction_tolerance stays at base."""
        synth_data = {
            "demografia": {"idade": 40},
            "deficiencias": {"motora": {"tipo": "leve"}},
        }
        result = derive_sensitivities(synth_data)
        base_result = derive_sensitivities({"demografia": {"idade": 40}})
        assert result["friction_tolerance"] == pytest.approx(base_result["friction_tolerance"])
