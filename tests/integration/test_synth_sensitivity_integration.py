"""
Integration tests for synth sensitivity derivation.

Tests that the synth builder (assemble_synth) produces synths with derived
sensitivities, and that derive_sensitivities works correctly with realistic
synth data structures.

These tests are part of US1 (User Story 1: Synths Are Created With Derived
Sensitivities) from spec 040-mechanism-sensitivity-update.

References:
    - Spec: specs/040-mechanism-sensitivity-update/tasks.md (T008)
    - Contract: specs/040-mechanism-sensitivity-update/contracts/simulation-api.md
    - YAML rules: src/synth_lab/config/sensitivity_rules.yaml

Expected behavior:
    - assemble_synth() returns a synth dict with a "sensitivities" key
    - sensitivities contains 7 fields: risk_aversion, social_dependency,
      institutional_trust_level, habit_plasticity, friction_tolerance,
      pragmatism, digital_capability
    - Each sensitivity value is between 0.0 and 1.0
    - sensitivities["_meta"] contains derivation_version, config_name, applied_rules
    - Different demographics produce meaningfully different sensitivities
"""

import numpy as np
import pytest

from synth_lab.gen_synth.config import load_config_data
from synth_lab.gen_synth.synth_builder import assemble_synth

# All 7 sensitivity fields expected in the output
SENSITIVITY_FIELDS = [
    "risk_aversion",
    "social_dependency",
    "institutional_trust_level",
    "habit_plasticity",
    "friction_tolerance",
    "pragmatism",
    "digital_capability",
]


@pytest.fixture(scope="module")
def config():
    """Load config data once for all tests in this module."""
    return load_config_data()


@pytest.fixture(scope="module")
def generated_synth(config):
    """Generate a single synth for reuse across tests that only need one."""
    rng = np.random.default_rng(seed=42)
    return assemble_synth(config, rng=rng)


@pytest.mark.integration
class TestAssembleSynthIncludesSensitivities:
    """Test that assemble_synth() produces a synth with derived sensitivities."""

    def test_synth_contains_sensitivities_key(self, generated_synth):
        """Verify the resulting synth dict contains a 'sensitivities' key."""
        assert "sensitivities" in generated_synth, (
            "assemble_synth() should produce a synth with a 'sensitivities' key. "
            "This requires T010 integration of derive_sensitivities into synth_builder."
        )

    def test_sensitivities_has_all_seven_fields(self, generated_synth):
        """Verify sensitivities has all 7 sensitivity fields."""
        sensitivities = generated_synth.get("sensitivities", {})

        missing_fields = [field for field in SENSITIVITY_FIELDS if field not in sensitivities]
        assert not missing_fields, (
            f"Sensitivities missing fields: {missing_fields}. "
            f"Expected all 7: {SENSITIVITY_FIELDS}. "
            f"Got keys: {list(sensitivities.keys())}"
        )

    @pytest.mark.parametrize("field", SENSITIVITY_FIELDS)
    def test_each_sensitivity_value_in_valid_range(self, generated_synth, field):
        """Verify each sensitivity value is between 0.0 and 1.0."""
        sensitivities = generated_synth.get("sensitivities", {})
        assert field in sensitivities, f"Missing sensitivity field: {field}"

        value = sensitivities[field]
        assert isinstance(value, (int, float)), (
            f"Sensitivity '{field}' should be numeric, got {type(value).__name__}"
        )
        assert 0.0 <= value <= 1.0, (
            f"Sensitivity '{field}' = {value} is outside valid range [0.0, 1.0]"
        )

    def test_sensitivities_do_not_break_existing_fields(self, generated_synth):
        """Verify that adding sensitivities does not remove existing synth fields."""
        required_existing_fields = [
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
        missing = [f for f in required_existing_fields if f not in generated_synth]
        assert not missing, f"Adding sensitivities broke existing synth fields. Missing: {missing}"


@pytest.mark.integration
class TestAssembleSynthSensitivitiesMetadata:
    """Test that sensitivities include proper metadata."""

    def test_meta_key_exists(self, generated_synth):
        """Verify synth['sensitivities']['_meta'] exists."""
        sensitivities = generated_synth.get("sensitivities", {})
        assert "_meta" in sensitivities, (
            "sensitivities should contain '_meta' key with derivation metadata"
        )

    def test_meta_has_derivation_version(self, generated_synth):
        """Verify _meta has 'derivation_version' key."""
        meta = generated_synth.get("sensitivities", {}).get("_meta", {})
        assert "derivation_version" in meta, (
            "_meta should contain 'derivation_version' key. "
            "This should match the 'version' field in sensitivity_rules.yaml"
        )
        actual_type = type(meta["derivation_version"]).__name__
        assert isinstance(meta["derivation_version"], str), (
            f"derivation_version should be a string, got {actual_type}"
        )

    def test_meta_has_config_name(self, generated_synth):
        """Verify _meta has 'config_name' key."""
        meta = generated_synth.get("sensitivities", {}).get("_meta", {})
        assert "config_name" in meta, (
            "_meta should contain 'config_name' key identifying the YAML config used"
        )
        assert isinstance(meta["config_name"], str), (
            f"config_name should be a string, got {type(meta['config_name']).__name__}"
        )

    def test_meta_has_applied_rules(self, generated_synth):
        """Verify _meta has 'applied_rules' key which is a list."""
        meta = generated_synth.get("sensitivities", {}).get("_meta", {})
        assert "applied_rules" in meta, (
            "_meta should contain 'applied_rules' key listing which rules were triggered"
        )
        assert isinstance(meta["applied_rules"], list), (
            f"applied_rules should be a list, got {type(meta['applied_rules']).__name__}"
        )

    def test_meta_derivation_version_matches_yaml(self, generated_synth):
        """Verify _meta.derivation_version matches the YAML config version."""
        meta = generated_synth.get("sensitivities", {}).get("_meta", {})
        # The YAML sensitivity_rules.yaml has version: "1.0"
        assert meta.get("derivation_version") == "1.0", (
            f"derivation_version should be '1.0' (matching sensitivity_rules.yaml), "
            f"got '{meta.get('derivation_version')}'"
        )


@pytest.mark.integration
class TestAssembleSynthSensitivitiesVaryWithDemographics:
    """Test that different demographics produce different sensitivities.

    This verifies that the sensitivity deriver actually uses demographic data
    to adjust sensitivity values (not just returning static defaults).
    """

    def test_multiple_synths_produce_varying_sensitivities(self, config):
        """Generate multiple synths and verify sensitivities are not all identical.

        Since demographics are randomized, different synths should produce
        at least some variation in sensitivity values.
        """
        synths = [assemble_synth(config) for _ in range(10)]

        # Collect all sensitivity values per field
        for field in SENSITIVITY_FIELDS:
            values = []
            for synth in synths:
                sensitivities = synth.get("sensitivities", {})
                if field in sensitivities:
                    values.append(sensitivities[field])

            if len(values) >= 2:
                unique_values = set(values)
                # With 10 random synths, we expect at least some variation
                # (unless the field has no rules, which would make all values = base)
                # We check for at least 2 unique values, which is a very lenient check
                assert len(unique_values) >= 2, (
                    f"Sensitivity '{field}' has the same value ({values[0]}) "
                    f"across all 10 synths. Rules may not be applying correctly."
                )


@pytest.mark.integration
class TestDeriveSensitivitiesDirectly:
    """Test derive_sensitivities() directly with realistic synth data.

    These tests import derive_sensitivities directly and test it with
    hand-crafted synth data structures to verify specific rule application.
    """

    @pytest.fixture
    def young_tech_synth(self):
        """A 22-year-old tech-savvy person with higher education."""
        return {
            "demografia": {
                "idade": 22,
                "genero_biologico": "masculino",
                "escolaridade": "Superior completo",
                "renda_mensal": 6000.0,
                "ocupacao": "Desenvolvedor",
                "estado_civil": "solteiro",
                "composicao_familiar": {"tipo": "unipessoal", "numero_pessoas": 1},
                "localizacao": {
                    "pais": "Brasil",
                    "regiao": "Sudeste",
                    "estado": "SP",
                    "cidade": "Sao Paulo",
                },
            },
            "psicografia": {
                "interesses": ["Tecnologia", "Games"],
                "contrato_cognitivo": {
                    "tipo": "factual",
                    "perfil_cognitivo": "test",
                    "regras": [],
                    "efeito_esperado": "test",
                },
            },
            "deficiencias": {
                "visual": {"tipo": "nenhuma"},
                "auditiva": {"tipo": "nenhuma"},
                "motora": {"tipo": "nenhuma"},
                "cognitiva": {"tipo": "nenhuma"},
            },
        }

    @pytest.fixture
    def elderly_synth(self):
        """A 68-year-old elderly person with basic education and motor disability."""
        return {
            "demografia": {
                "idade": 68,
                "genero_biologico": "feminino",
                "escolaridade": "ensino fundamental completo",
                "renda_mensal": 1500.0,
                "ocupacao": "Aposentada",
                "estado_civil": "viuvo",
                "composicao_familiar": {"tipo": "unipessoal", "numero_pessoas": 1},
                "localizacao": {
                    "pais": "Brasil",
                    "regiao": "Nordeste",
                    "estado": "BA",
                    "cidade": "Salvador",
                },
            },
            "psicografia": {
                "interesses": ["Novelas", "Receitas"],
                "contrato_cognitivo": {
                    "tipo": "factual",
                    "perfil_cognitivo": "test",
                    "regras": [],
                    "efeito_esperado": "test",
                },
            },
            "deficiencias": {
                "visual": {"tipo": "nenhuma"},
                "auditiva": {"tipo": "nenhuma"},
                "motora": {"tipo": "moderada"},
                "cognitiva": {"tipo": "nenhuma"},
            },
        }

    def test_derive_sensitivities_returns_all_fields(self, young_tech_synth):
        """Verify derive_sensitivities returns dict with all 7 fields."""
        from synth_lab.services.sensitivity_deriver import derive_sensitivities

        result = derive_sensitivities(young_tech_synth)

        missing = [f for f in SENSITIVITY_FIELDS if f not in result]
        assert not missing, (
            f"derive_sensitivities missing fields: {missing}. Got: {list(result.keys())}"
        )

    def test_derive_sensitivities_values_in_range(self, young_tech_synth):
        """Verify all derived sensitivity values are in [0.0, 1.0]."""
        from synth_lab.services.sensitivity_deriver import derive_sensitivities

        result = derive_sensitivities(young_tech_synth)

        for field in SENSITIVITY_FIELDS:
            value = result.get(field)
            assert value is not None, f"Missing field: {field}"
            assert 0.0 <= value <= 1.0, f"Sensitivity '{field}' = {value} out of range [0.0, 1.0]"

    def test_derive_sensitivities_includes_meta(self, young_tech_synth):
        """Verify derive_sensitivities includes _meta with required keys."""
        from synth_lab.services.sensitivity_deriver import derive_sensitivities

        result = derive_sensitivities(young_tech_synth)

        assert "_meta" in result, "Result should contain '_meta' key"
        meta = result["_meta"]
        assert "derivation_version" in meta, "_meta missing 'derivation_version'"
        assert "config_name" in meta, "_meta missing 'config_name'"
        assert "applied_rules" in meta, "_meta missing 'applied_rules'"
        assert isinstance(meta["applied_rules"], list), "applied_rules should be a list"

    def test_young_person_has_higher_digital_capability(self, young_tech_synth, elderly_synth):
        """Young tech-savvy person should have higher digital_capability than elderly.

        Per sensitivity_rules.yaml:
        - age <= 30: +0.15 for digital_capability
        - age >= 60: -0.20 for digital_capability
        - ensino superior completo: +0.10 for digital_capability
        So young_tech should get base(0.50) + 0.15 + 0.10 = 0.75
        And elderly should get base(0.50) - 0.20 = 0.30
        """
        from synth_lab.services.sensitivity_deriver import derive_sensitivities

        young_result = derive_sensitivities(young_tech_synth)
        elderly_result = derive_sensitivities(elderly_synth)

        young_dc = young_result["digital_capability"]
        elderly_dc = elderly_result["digital_capability"]

        assert young_dc > elderly_dc, (
            f"Young tech person's digital_capability ({young_dc}) should be "
            f"higher than elderly person's ({elderly_dc})"
        )

    def test_elderly_has_higher_risk_aversion(self, young_tech_synth, elderly_synth):
        """Elderly person should have higher risk_aversion than young person.

        Per sensitivity_rules.yaml:
        - age >= 60: +0.10 for risk_aversion
        - age <= 25: -0.05 for risk_aversion
        - ensino superior completo: -0.05 for risk_aversion (young only)
        """
        from synth_lab.services.sensitivity_deriver import derive_sensitivities

        young_result = derive_sensitivities(young_tech_synth)
        elderly_result = derive_sensitivities(elderly_synth)

        young_ra = young_result["risk_aversion"]
        elderly_ra = elderly_result["risk_aversion"]

        assert elderly_ra > young_ra, (
            f"Elderly person's risk_aversion ({elderly_ra}) should be "
            f"higher than young person's ({young_ra})"
        )

    def test_young_has_higher_habit_plasticity(self, young_tech_synth, elderly_synth):
        """Young person should have higher habit_plasticity than elderly.

        Per sensitivity_rules.yaml:
        - age <= 30: +0.10 for habit_plasticity
        - age >= 60: -0.15 for habit_plasticity
        """
        from synth_lab.services.sensitivity_deriver import derive_sensitivities

        young_result = derive_sensitivities(young_tech_synth)
        elderly_result = derive_sensitivities(elderly_synth)

        young_hp = young_result["habit_plasticity"]
        elderly_hp = elderly_result["habit_plasticity"]

        assert young_hp > elderly_hp, (
            f"Young person's habit_plasticity ({young_hp}) should be "
            f"higher than elderly person's ({elderly_hp})"
        )

    def test_elderly_motor_disability_reduces_friction_tolerance(self, elderly_synth):
        """Elderly person with motor disability should have lower friction_tolerance.

        Per sensitivity_rules.yaml:
        - age >= 60: -0.10 for friction_tolerance
        - motora moderada/severa: -0.10 for friction_tolerance
        So elderly_synth should get base(0.50) - 0.10 - 0.10 = 0.30
        """
        from synth_lab.services.sensitivity_deriver import derive_sensitivities

        result = derive_sensitivities(elderly_synth)

        friction = result["friction_tolerance"]
        # Base is 0.50, with -0.10 (age) and -0.10 (motor disability) = 0.30
        assert friction < 0.50, (
            f"Elderly person with motor disability should have friction_tolerance < 0.50, "
            f"got {friction}"
        )

    def test_sensitivity_profiles_differ_meaningfully(self, young_tech_synth, elderly_synth):
        """Young and elderly profiles should differ by >= 0.15 average across 7 dimensions.

        This is success criterion SC-002 from the spec.
        """
        from synth_lab.services.sensitivity_deriver import derive_sensitivities

        young_result = derive_sensitivities(young_tech_synth)
        elderly_result = derive_sensitivities(elderly_synth)

        diffs = []
        for field in SENSITIVITY_FIELDS:
            diff = abs(young_result[field] - elderly_result[field])
            diffs.append(diff)

        avg_diff = sum(diffs) / len(diffs)
        assert avg_diff >= 0.15, (
            f"Average sensitivity difference between young tech and elderly profiles "
            f"should be >= 0.15, got {avg_diff:.3f}. "
            f"Per-field diffs: {dict(zip(SENSITIVITY_FIELDS, [f'{d:.3f}' for d in diffs]))}"
        )

    def test_applied_rules_are_populated(self, young_tech_synth):
        """Verify that applied_rules in _meta is non-empty for a profile that triggers rules."""
        from synth_lab.services.sensitivity_deriver import derive_sensitivities

        result = derive_sensitivities(young_tech_synth)
        meta = result["_meta"]

        # A 22-year-old with higher education should trigger multiple rules
        assert len(meta["applied_rules"]) > 0, (
            "A 22-year-old with ensino superior completo should trigger at least one rule. "
            "applied_rules is empty."
        )
