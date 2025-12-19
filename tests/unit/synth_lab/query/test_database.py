"""Unit tests for database module."""

import pytest
from pathlib import Path


# T014: Unit test for DatabaseConfig creation and validation
@pytest.mark.unit
def test_database_config_creation():
    """Test DatabaseConfig dataclass creation."""
    from synth_lab.query.database import DatabaseConfig
    
    config = DatabaseConfig(
        db_path=Path("output/synths/synths.duckdb"),
        json_path=Path("output/synths/synths.json"),
        table_name="synths"
    )
    
    assert config.db_path == Path("output/synths/synths.duckdb")
    assert config.json_path == Path("output/synths/synths.json")
    assert config.table_name == "synths"


@pytest.mark.unit
def test_database_config_default():
    """Test DatabaseConfig.default() factory method."""
    from synth_lab.query.database import DatabaseConfig
    
    config = DatabaseConfig.default()
    
    assert config.db_path == Path("output/synths/synths.duckdb")
    assert config.json_path == Path("output/synths/synths.json")
    assert config.table_name == "synths"


@pytest.mark.unit
def test_database_config_immutable():
    """Test that DatabaseConfig is frozen/immutable."""
    from synth_lab.query.database import DatabaseConfig
    
    config = DatabaseConfig.default()
    
    with pytest.raises((AttributeError, ValueError, TypeError)):
        config.table_name = "modified"
