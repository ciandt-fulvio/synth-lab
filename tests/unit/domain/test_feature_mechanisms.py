"""Tests for FeatureMechanisms entity (040-mechanism-sensitivity-update)."""

import pytest
from pydantic import ValidationError
from synth_lab.domain.entities.feature_mechanisms import FeatureMechanisms, ALL_9_FIELDS

ALL_MECHANISM_KEYS = [
    "irreversibility", "network_effect", "institutional_trust",
    "habit_displacement", "learning_curve", "social_visibility",
    "valor_intrinseco", "friccao_operacional", "frequencia_de_uso",
]
ORIGINAL_6 = ALL_MECHANISM_KEYS[:6]
NEW_3 = ALL_MECHANISM_KEYS[6:]


class TestFeatureMechanismsFields:
    def test_has_exactly_9_fields(self):
        assert len(FeatureMechanisms.model_fields) == 9

    def test_all_9_field_names(self):
        assert set(FeatureMechanisms.model_fields.keys()) == set(ALL_MECHANISM_KEYS)

    @pytest.mark.parametrize("field", ALL_MECHANISM_KEYS)
    def test_default_is_zero(self, field):
        m = FeatureMechanisms()
        assert getattr(m, field) == 0.0

    @pytest.mark.parametrize("field", ALL_MECHANISM_KEYS)
    def test_accepts_boundary_zero(self, field):
        m = FeatureMechanisms(**{field: 0.0})
        assert getattr(m, field) == 0.0

    @pytest.mark.parametrize("field", ALL_MECHANISM_KEYS)
    def test_accepts_boundary_one(self, field):
        m = FeatureMechanisms(**{field: 1.0})
        assert getattr(m, field) == 1.0

    @pytest.mark.parametrize("field", ALL_MECHANISM_KEYS)
    def test_rejects_negative(self, field):
        with pytest.raises(ValidationError):
            FeatureMechanisms(**{field: -0.1})

    @pytest.mark.parametrize("field", ALL_MECHANISM_KEYS)
    def test_rejects_above_one(self, field):
        with pytest.raises(ValidationError):
            FeatureMechanisms(**{field: 1.01})


class TestBackwardCompatibility:
    def test_construct_with_only_original_6(self):
        m = FeatureMechanisms(
            irreversibility=0.9,
            network_effect=0.7,
            institutional_trust=0.8,
            habit_displacement=0.4,
            learning_curve=0.5,
            social_visibility=0.3,
        )
        assert m.irreversibility == 0.9
        for field in NEW_3:
            assert getattr(m, field) == 0.0, f"{field} should default to 0.0"

    def test_new_fields_zero_impact_on_has_any(self):
        m = FeatureMechanisms()
        assert not m.has_any_mechanism()


class TestHasAnyMechanism:
    @pytest.mark.parametrize("field", ALL_MECHANISM_KEYS)
    def test_detects_each_field(self, field):
        m = FeatureMechanisms(**{field: 0.5})
        assert m.has_any_mechanism()

    def test_false_when_all_zero(self):
        m = FeatureMechanisms()
        assert not m.has_any_mechanism()

    def test_true_with_all_set(self):
        vals = {k: 0.5 for k in ALL_MECHANISM_KEYS}
        m = FeatureMechanisms(**vals)
        assert m.has_any_mechanism()


class TestModelDump:
    def test_dump_has_all_9_keys(self):
        m = FeatureMechanisms(irreversibility=0.9, valor_intrinseco=0.6)
        dump = m.model_dump()
        assert set(dump.keys()) == set(ALL_MECHANISM_KEYS)

    def test_dump_preserves_values(self):
        m = FeatureMechanisms(irreversibility=0.9, valor_intrinseco=0.6)
        dump = m.model_dump()
        assert dump["irreversibility"] == 0.9
        assert dump["valor_intrinseco"] == 0.6
        assert dump["network_effect"] == 0.0
