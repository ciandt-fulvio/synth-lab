"""Tests for seed_mechanisms data definitions (040-mechanism-sensitivity-update)."""

import sys
from pathlib import Path

import pytest

# Add project root to path so we can import from scripts/
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.seed_mechanisms import MECHANISM_DEFINITIONS, FEATURE_TYPES


class TestMechanismDefinitions:
    def test_has_9_mechanisms(self):
        assert len(MECHANISM_DEFINITIONS) == 9

    def test_all_keys_present(self):
        keys = {m["key"] for m in MECHANISM_DEFINITIONS}
        expected = {
            "irreversibility", "network_effect", "institutional_trust",
            "habit_displacement", "learning_curve", "social_visibility",
            "intrinsic_value", "operational_friction", "frequency_of_use",
        }
        assert keys == expected

    @pytest.mark.parametrize("mech", MECHANISM_DEFINITIONS, ids=lambda m: m["key"])
    def test_each_has_5_options(self, mech):
        assert len(mech["options"]) == 5, f"{mech['key']} should have 5 options"

    @pytest.mark.parametrize("mech", MECHANISM_DEFINITIONS, ids=lambda m: m["key"])
    def test_options_range_0_to_1(self, mech):
        values = [o["value"] for o in mech["options"]]
        assert min(values) == 0.0, f"{mech['key']} min should be 0.0"
        assert max(values) == 1.0, f"{mech['key']} max should be 1.0"

    @pytest.mark.parametrize("mech", MECHANISM_DEFINITIONS, ids=lambda m: m["key"])
    def test_options_have_required_fields(self, mech):
        for opt in mech["options"]:
            assert "label" in opt
            assert "value" in opt
            assert "display_order" in opt

    def test_total_options_count(self):
        total = sum(len(m["options"]) for m in MECHANISM_DEFINITIONS)
        assert total == 45  # 9 mechanisms × 5 options


class TestNewMechanisms:
    def _get_mech(self, key):
        return next(m for m in MECHANISM_DEFINITIONS if m["key"] == key)

    def test_intrinsic_value_labels(self):
        m = self._get_mech("intrinsic_value")
        labels = [o["label"] for o in m["options"]]
        assert labels[0] == "cosmético"
        assert labels[-1] == "transformador"

    def test_operational_friction_labels(self):
        m = self._get_mech("operational_friction")
        labels = [o["label"] for o in m["options"]]
        assert labels[0] == "sem fricção"
        assert labels[-1] == "fricção extrema"

    def test_frequency_of_use_labels(self):
        m = self._get_mech("frequency_of_use")
        labels = [o["label"] for o in m["options"]]
        assert labels[0] == "raríssimo"
        assert labels[-1] == "diário ou mais"

    @pytest.mark.parametrize("key", ["intrinsic_value", "operational_friction", "frequency_of_use"])
    def test_new_mechanism_has_label_pt(self, key):
        m = self._get_mech(key)
        assert "label_pt" in m and len(m["label_pt"]) > 0

    @pytest.mark.parametrize("key", ["intrinsic_value", "operational_friction", "frequency_of_use"])
    def test_new_mechanism_has_description(self, key):
        m = self._get_mech(key)
        assert "description" in m and len(m["description"]) > 0
