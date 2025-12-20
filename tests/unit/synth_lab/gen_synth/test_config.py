"""Tests for config module."""

from synth_lab.gen_synth import config


def test_load_config_data_returns_dict(config_data):
    """Test that load_config_data returns a dictionary."""
    result = config.load_config_data()
    assert isinstance(result, dict)


def test_config_has_required_keys():
    """Test that config has all required keys."""
    result = config.load_config_data()
    assert "ibge" in result
    assert "occupations" in result
    assert "interests_hobbies" in result


def test_paths_exist():
    """Test that all config paths are defined and point to existing locations."""
    assert config.DATA_DIR.exists()
    assert config.CONFIG_DIR.exists()
    assert config.SCHEMAS_DIR.exists()
    assert config.SYNTHS_DIR.exists() or config.SYNTHS_DIR.parent.exists()
    assert config.SCHEMA_PATH.exists()
