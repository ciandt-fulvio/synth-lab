"""
Integration tests for Alembic migrations.

Tests that migrations can be applied, rolled back, and re-applied successfully
on both SQLite and PostgreSQL backends.

References:
    - Alembic Testing: https://alembic.sqlalchemy.org/en/latest/cookbook.html#testing-alembic

Sample input:
    - Fresh database with no tables
    - Database URL from environment or default SQLite

Expected output:
    - All tables created after upgrade
    - All tables dropped after downgrade
    - Schema matches expected state
"""

import os
import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Expected tables from 001_initial_schema.py
EXPECTED_TABLES = {
    "synth_groups",
    "synths",
    "experiments",
    "interview_guide",
    "analysis_runs",
    "synth_outcomes",
    "analysis_cache",
    "research_executions",
    "transcripts",
    "explorations",
    "scenario_nodes",
    "chart_insights",
    "sensitivity_results",
    "region_analyses",
    "experiment_documents",
    "feature_scorecards",
    "simulation_runs",
}


def get_alembic_config(database_url: str) -> Config:
    """Create Alembic config for testing."""
    # Get the path to alembic directory
    alembic_dir = Path(__file__).parent.parent.parent / "src" / "synth_lab" / "alembic"
    alembic_ini = alembic_dir / "alembic.ini"

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(alembic_dir))
    config.set_main_option("sqlalchemy.url", database_url)

    return config


class TestAlembicMigrationsSQLite:
    """Test Alembic migrations with SQLite backend."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create a temporary SQLite database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        yield f"sqlite:///{db_path}"

        # Cleanup
        try:
            os.unlink(db_path)
        except OSError:
            pass

    def test_upgrade_creates_all_tables(self, temp_db: str):
        """Test that upgrade head creates all expected tables."""
        config = get_alembic_config(temp_db)

        # Run upgrade to head
        command.upgrade(config, "head")

        # Check tables exist
        engine = create_engine(temp_db)
        inspector = inspect(engine)
        actual_tables = set(inspector.get_table_names())

        # Alembic creates its own version table
        expected_with_alembic = EXPECTED_TABLES | {"alembic_version"}

        assert actual_tables == expected_with_alembic, (
            f"Missing tables: {expected_with_alembic - actual_tables}, "
            f"Extra tables: {actual_tables - expected_with_alembic}"
        )

        engine.dispose()

    def test_downgrade_removes_all_tables(self, temp_db: str):
        """Test that downgrade base removes all tables (except alembic_version)."""
        config = get_alembic_config(temp_db)

        # First upgrade
        command.upgrade(config, "head")

        # Then downgrade
        command.downgrade(config, "base")

        # Check only alembic_version remains
        engine = create_engine(temp_db)
        inspector = inspect(engine)
        actual_tables = set(inspector.get_table_names())

        # Only alembic_version should remain after full downgrade
        assert actual_tables == {"alembic_version"}, f"Unexpected tables after downgrade: {actual_tables}"

        engine.dispose()

    def test_upgrade_downgrade_upgrade_idempotent(self, temp_db: str):
        """Test that upgrade -> downgrade -> upgrade works correctly."""
        config = get_alembic_config(temp_db)

        # Upgrade
        command.upgrade(config, "head")

        # Downgrade
        command.downgrade(config, "base")

        # Re-upgrade
        command.upgrade(config, "head")

        # Verify tables
        engine = create_engine(temp_db)
        inspector = inspect(engine)
        actual_tables = set(inspector.get_table_names())

        expected_with_alembic = EXPECTED_TABLES | {"alembic_version"}
        assert actual_tables == expected_with_alembic

        engine.dispose()

    def test_experiments_table_schema(self, temp_db: str):
        """Test that experiments table has expected columns."""
        config = get_alembic_config(temp_db)
        command.upgrade(config, "head")

        engine = create_engine(temp_db)
        inspector = inspect(engine)

        columns = {col["name"] for col in inspector.get_columns("experiments")}
        expected_columns = {
            "id",
            "name",
            "hypothesis",
            "description",
            "scorecard_data",
            "status",
            "created_at",
            "updated_at",
        }

        assert columns == expected_columns, f"Missing columns: {expected_columns - columns}"

        engine.dispose()

    def test_synths_table_foreign_key(self, temp_db: str):
        """Test that synths table has foreign key to synth_groups."""
        config = get_alembic_config(temp_db)
        command.upgrade(config, "head")

        engine = create_engine(temp_db)
        inspector = inspect(engine)

        fks = inspector.get_foreign_keys("synths")
        synth_group_fk = next(
            (fk for fk in fks if fk["referred_table"] == "synth_groups"), None
        )

        assert synth_group_fk is not None, "Missing FK to synth_groups"
        assert "synth_group_id" in synth_group_fk["constrained_columns"]

        engine.dispose()

    def test_cascade_delete_constraint(self, temp_db: str):
        """Test that foreign key constraints with cascade delete work."""
        config = get_alembic_config(temp_db)
        command.upgrade(config, "head")

        # SQLite requires explicit foreign key enforcement
        from sqlalchemy import event

        engine = create_engine(temp_db, connect_args={"check_same_thread": False})

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Session = sessionmaker(bind=engine)

        with Session() as session:
            # Insert experiment
            session.execute(
                text(
                    """
                INSERT INTO experiments (id, name, hypothesis, status, created_at)
                VALUES ('exp_test', 'Test', 'Test hypothesis', 'active', '2026-01-01T00:00:00')
            """
                )
            )

            # Insert analysis_run referencing experiment
            session.execute(
                text(
                    """
                INSERT INTO analysis_runs (id, experiment_id, scenario_id, config, status, started_at, total_synths)
                VALUES ('run_test', 'exp_test', 'baseline', '{}', 'completed', '2026-01-01T00:00:00', 10)
            """
                )
            )

            session.commit()

            # Verify both exist
            exp_count = session.execute(
                text("SELECT COUNT(*) FROM experiments WHERE id = 'exp_test'")
            ).scalar()
            assert exp_count == 1

            run_count = session.execute(
                text("SELECT COUNT(*) FROM analysis_runs WHERE experiment_id = 'exp_test'")
            ).scalar()
            assert run_count == 1

            # Delete experiment (should cascade to analysis_run)
            session.execute(text("DELETE FROM experiments WHERE id = 'exp_test'"))
            session.commit()

            # Verify cascade worked
            run_count = session.execute(
                text("SELECT COUNT(*) FROM analysis_runs WHERE experiment_id = 'exp_test'")
            ).scalar()
            assert run_count == 0, "Cascade delete did not work"

        engine.dispose()

    def test_indexes_created(self, temp_db: str):
        """Test that expected indexes are created."""
        config = get_alembic_config(temp_db)
        command.upgrade(config, "head")

        engine = create_engine(temp_db)
        inspector = inspect(engine)

        # Check experiments indexes
        exp_indexes = {idx["name"] for idx in inspector.get_indexes("experiments")}
        assert "idx_experiments_created" in exp_indexes
        assert "idx_experiments_name" in exp_indexes
        assert "idx_experiments_status" in exp_indexes

        # Check synths indexes
        synth_indexes = {idx["name"] for idx in inspector.get_indexes("synths")}
        assert "idx_synths_created_at" in synth_indexes
        assert "idx_synths_nome" in synth_indexes
        assert "idx_synths_group" in synth_indexes

        engine.dispose()


@pytest.mark.skipif(
    not os.getenv("POSTGRES_URL"),
    reason="POSTGRES_URL not set - skipping PostgreSQL tests",
)
class TestAlembicMigrationsPostgres:
    """Test Alembic migrations with PostgreSQL backend."""

    @pytest.fixture
    def postgres_db(self) -> str:
        """Get PostgreSQL database URL from environment."""
        return os.environ["POSTGRES_URL"]

    def test_upgrade_creates_all_tables(self, postgres_db: str):
        """Test that upgrade head creates all expected tables on PostgreSQL."""
        config = get_alembic_config(postgres_db)

        # First clean up any existing tables
        try:
            command.downgrade(config, "base")
        except Exception:
            pass  # May fail if tables don't exist

        # Run upgrade to head
        command.upgrade(config, "head")

        # Check tables exist
        engine = create_engine(postgres_db)
        inspector = inspect(engine)
        actual_tables = set(inspector.get_table_names())

        # Alembic creates its own version table
        expected_with_alembic = EXPECTED_TABLES | {"alembic_version"}

        assert expected_with_alembic.issubset(actual_tables), (
            f"Missing tables: {expected_with_alembic - actual_tables}"
        )

        engine.dispose()

    def test_downgrade_and_upgrade_idempotent(self, postgres_db: str):
        """Test that downgrade -> upgrade cycle works on PostgreSQL."""
        config = get_alembic_config(postgres_db)

        # Ensure we're at head
        command.upgrade(config, "head")

        # Downgrade
        command.downgrade(config, "base")

        # Re-upgrade
        command.upgrade(config, "head")

        # Verify tables exist
        engine = create_engine(postgres_db)
        inspector = inspect(engine)
        actual_tables = set(inspector.get_table_names())

        expected_with_alembic = EXPECTED_TABLES | {"alembic_version"}
        assert expected_with_alembic.issubset(actual_tables)

        engine.dispose()


class TestMigrationVersioning:
    """Test Alembic version tracking."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create a temporary SQLite database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        yield f"sqlite:///{db_path}"

        try:
            os.unlink(db_path)
        except OSError:
            pass

    def test_version_tracked_after_upgrade(self, temp_db: str):
        """Test that Alembic tracks version after upgrade."""
        config = get_alembic_config(temp_db)
        command.upgrade(config, "head")

        engine = create_engine(temp_db)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()

        assert version == "001", f"Expected version '001', got '{version}'"

        engine.dispose()

    def test_version_empty_after_downgrade(self, temp_db: str):
        """Test that version table is empty after full downgrade."""
        config = get_alembic_config(temp_db)

        # Upgrade then downgrade
        command.upgrade(config, "head")
        command.downgrade(config, "base")

        engine = create_engine(temp_db)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM alembic_version"))
            count = result.scalar()

        assert count == 0, "Version table should be empty after downgrade"

        engine.dispose()


if __name__ == "__main__":
    """Run validation tests."""
    import sys

    all_failures = []
    total_tests = 0

    # Test SQLite migrations
    print("Testing SQLite migrations...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    test_db_url = f"sqlite:///{db_path}"

    try:
        config = get_alembic_config(test_db_url)

        # Test 1: Upgrade
        total_tests += 1
        try:
            command.upgrade(config, "head")
            engine = create_engine(test_db_url)
            inspector = inspect(engine)
            tables = set(inspector.get_table_names())
            expected = EXPECTED_TABLES | {"alembic_version"}
            if tables != expected:
                all_failures.append(f"Upgrade: Missing tables {expected - tables}")
            else:
                print("  ✓ Upgrade creates all tables")
            engine.dispose()
        except Exception as e:
            all_failures.append(f"Upgrade failed: {e}")

        # Test 2: Downgrade
        total_tests += 1
        try:
            command.downgrade(config, "base")
            engine = create_engine(test_db_url)
            inspector = inspect(engine)
            tables = set(inspector.get_table_names())
            if tables != {"alembic_version"}:
                all_failures.append(f"Downgrade: Unexpected tables {tables}")
            else:
                print("  ✓ Downgrade removes tables")
            engine.dispose()
        except Exception as e:
            all_failures.append(f"Downgrade failed: {e}")

        # Test 3: Re-upgrade
        total_tests += 1
        try:
            command.upgrade(config, "head")
            engine = create_engine(test_db_url)
            inspector = inspect(engine)
            tables = set(inspector.get_table_names())
            expected = EXPECTED_TABLES | {"alembic_version"}
            if tables != expected:
                all_failures.append(f"Re-upgrade: Missing tables {expected - tables}")
            else:
                print("  ✓ Re-upgrade works")
            engine.dispose()
        except Exception as e:
            all_failures.append(f"Re-upgrade failed: {e}")

    finally:
        try:
            os.unlink(db_path)
        except OSError:
            pass

    # Final result
    if all_failures:
        print(f"\n❌ VALIDATION FAILED - {len(all_failures)} of {total_tests} tests failed:")
        for failure in all_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_tests} tests passed")
        sys.exit(0)
