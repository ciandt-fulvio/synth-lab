"""
T001 [TEST] Database schema validation tests.

Verifies that experiments and synth_groups tables exist with correct columns,
and that existing tables have been modified to include experiment_id/synth_group_id.

References:
    - Data model: specs/018-experiment-hub/data-model.md
"""

import tempfile
from pathlib import Path

import pytest

from synth_lab.infrastructure.database import DatabaseManager, init_database


@pytest.fixture
def test_db() -> DatabaseManager:
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_schema.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        yield db
        db.close()


class TestExperimentsTable:
    """Tests for the experiments table schema."""

    def test_experiments_table_exists(self, test_db: DatabaseManager) -> None:
        """Verify experiments table is created."""
        result = test_db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='experiments'"
        )
        assert result is not None, "experiments table should exist"

    def test_experiments_has_required_columns(self, test_db: DatabaseManager) -> None:
        """Verify experiments table has all required columns."""
        cursor = test_db.execute("PRAGMA table_info(experiments)")
        columns = {row["name"]: row for row in cursor.fetchall()}

        required_columns = ["id", "name", "hypothesis", "description", "created_at", "updated_at"]
        for col in required_columns:
            assert col in columns, f"experiments table missing column: {col}"

    def test_experiments_id_is_primary_key(self, test_db: DatabaseManager) -> None:
        """Verify id is the primary key."""
        cursor = test_db.execute("PRAGMA table_info(experiments)")
        columns = {row["name"]: row for row in cursor.fetchall()}
        assert columns["id"]["pk"] == 1, "id should be primary key"

    def test_experiments_name_not_null(self, test_db: DatabaseManager) -> None:
        """Verify name is NOT NULL."""
        cursor = test_db.execute("PRAGMA table_info(experiments)")
        columns = {row["name"]: row for row in cursor.fetchall()}
        assert columns["name"]["notnull"] == 1, "name should be NOT NULL"

    def test_experiments_hypothesis_not_null(self, test_db: DatabaseManager) -> None:
        """Verify hypothesis is NOT NULL."""
        cursor = test_db.execute("PRAGMA table_info(experiments)")
        columns = {row["name"]: row for row in cursor.fetchall()}
        assert columns["hypothesis"]["notnull"] == 1, "hypothesis should be NOT NULL"

    def test_experiments_created_index_exists(self, test_db: DatabaseManager) -> None:
        """Verify idx_experiments_created index exists."""
        result = test_db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_experiments_created'"
        )
        assert result is not None, "idx_experiments_created index should exist"


class TestSynthGroupsTable:
    """Tests for the synth_groups table schema."""

    def test_synth_groups_table_exists(self, test_db: DatabaseManager) -> None:
        """Verify synth_groups table is created."""
        result = test_db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='synth_groups'"
        )
        assert result is not None, "synth_groups table should exist"

    def test_synth_groups_has_required_columns(self, test_db: DatabaseManager) -> None:
        """Verify synth_groups table has all required columns."""
        cursor = test_db.execute("PRAGMA table_info(synth_groups)")
        columns = {row["name"]: row for row in cursor.fetchall()}

        required_columns = ["id", "name", "description", "created_at"]
        for col in required_columns:
            assert col in columns, f"synth_groups table missing column: {col}"

    def test_synth_groups_id_is_primary_key(self, test_db: DatabaseManager) -> None:
        """Verify id is the primary key."""
        cursor = test_db.execute("PRAGMA table_info(synth_groups)")
        columns = {row["name"]: row for row in cursor.fetchall()}
        assert columns["id"]["pk"] == 1, "id should be primary key"


class TestModifiedTables:
    """Tests for modified existing tables."""

    def test_synths_has_synth_group_id(self, test_db: DatabaseManager) -> None:
        """Verify synths table has synth_group_id column."""
        cursor = test_db.execute("PRAGMA table_info(synths)")
        columns = {row["name"]: row for row in cursor.fetchall()}
        assert "synth_group_id" in columns, "synths table should have synth_group_id"

    def test_feature_scorecards_has_experiment_id(self, test_db: DatabaseManager) -> None:
        """Verify feature_scorecards table has experiment_id column."""
        cursor = test_db.execute("PRAGMA table_info(feature_scorecards)")
        columns = {row["name"]: row for row in cursor.fetchall()}
        assert "experiment_id" in columns, "feature_scorecards should have experiment_id"

    def test_research_executions_has_experiment_id(self, test_db: DatabaseManager) -> None:
        """Verify research_executions table has experiment_id column."""
        cursor = test_db.execute("PRAGMA table_info(research_executions)")
        columns = {row["name"]: row for row in cursor.fetchall()}
        assert "experiment_id" in columns, "research_executions should have experiment_id"

    def test_synths_group_index_exists(self, test_db: DatabaseManager) -> None:
        """Verify idx_synths_group index exists."""
        result = test_db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_synths_group'"
        )
        assert result is not None, "idx_synths_group index should exist"

    def test_scorecards_experiment_index_exists(self, test_db: DatabaseManager) -> None:
        """Verify idx_scorecards_experiment index exists."""
        result = test_db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_scorecards_experiment'"
        )
        assert result is not None, "idx_scorecards_experiment index should exist"

    def test_executions_experiment_index_exists(self, test_db: DatabaseManager) -> None:
        """Verify idx_executions_experiment index exists."""
        result = test_db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_executions_experiment'"
        )
        assert result is not None, "idx_executions_experiment index should exist"
