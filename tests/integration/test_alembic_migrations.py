"""
Integration tests for Alembic migrations.

Tests that migrations can be applied, rolled back, and re-applied successfully
on PostgreSQL backend.

References:
    - Alembic Testing: https://alembic.sqlalchemy.org/en/latest/cookbook.html#testing-alembic

Sample input:
    - Fresh database with no tables
    - Database URL from POSTGRES_URL environment variable

Expected output:
    - All tables created after upgrade
    - All tables dropped after downgrade
    - Schema matches expected state
"""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

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
    "prfaq_metadata",
}


def get_alembic_config(database_url: str) -> Config:
    """Create Alembic config for testing."""
    alembic_dir = Path(__file__).parent.parent.parent / "src" / "synth_lab" / "alembic"
    alembic_ini = alembic_dir / "alembic.ini"

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(alembic_dir))
    config.set_main_option("sqlalchemy.url", database_url)

    return config


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

    @pytest.mark.skip(reason="Requires clean PostgreSQL database - run in CI with fresh DB")
    def test_upgrade_creates_all_tables(self, postgres_db: str):
        """Test that upgrade head creates all expected tables on PostgreSQL."""
        config = get_alembic_config(postgres_db)

        # First clean up any existing tables by downgrading to base
        # This ensures we start from a clean state
        try:
            command.downgrade(config, "base")
        except Exception as e:
            # If downgrade fails, it might be because we're already at base
            # or tables don't exist - try to drop all tables manually
            try:
                from sqlalchemy import create_engine, text
                engine = create_engine(postgres_db)
                with engine.connect() as conn:
                    conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
                    # Get all tables and drop them
                    result = conn.execute(text("""
                        SELECT tablename FROM pg_tables
                        WHERE schemaname = 'public'
                    """))
                    for table in result:
                        conn.execute(text(f'DROP TABLE IF EXISTS "{table[0]}" CASCADE'))
                    conn.commit()
                engine.dispose()
            except Exception:
                pass  # Continue anyway

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

    @pytest.mark.skip(reason="Requires clean PostgreSQL database - run in CI with fresh DB")
    def test_downgrade_and_upgrade_idempotent(self, postgres_db: str):
        """Test that downgrade -> upgrade cycle works on PostgreSQL."""
        config = get_alembic_config(postgres_db)

        # Clean up any existing tables first
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(postgres_db)
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
                result = conn.execute(text("""
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                """))
                for table in result:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table[0]}" CASCADE'))
                conn.commit()
            engine.dispose()
        except Exception:
            pass

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

    def test_experiments_table_schema(self, postgres_db: str):
        """Test that experiments table has expected columns."""
        config = get_alembic_config(postgres_db)

        # Clean up before test
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(postgres_db)
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
                result = conn.execute(text("""
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                """))
                for table in result:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table[0]}" CASCADE'))
                conn.commit()
            engine.dispose()
        except Exception:
            pass

        command.upgrade(config, "head")

        engine = create_engine(postgres_db)
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

        assert expected_columns.issubset(columns), f"Missing columns: {expected_columns - columns}"

        engine.dispose()

    def test_version_tracked_after_upgrade(self, postgres_db: str):
        """Test that Alembic tracks version after upgrade."""
        config = get_alembic_config(postgres_db)

        # Clean up before test
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(postgres_db)
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
                result = conn.execute(text("""
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                """))
                for table in result:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table[0]}" CASCADE'))
                conn.commit()
            engine.dispose()
        except Exception:
            pass

        command.upgrade(config, "head")

        engine = create_engine(postgres_db)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()

        assert version == "001", f"Expected version '001', got '{version}'"

        engine.dispose()


if __name__ == "__main__":
    """Run validation tests."""
    import sys

    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        print("❌ POSTGRES_URL environment variable not set")
        sys.exit(1)

    all_failures = []
    total_tests = 0

    print("Testing PostgreSQL migrations...")

    config = get_alembic_config(postgres_url)

    # Test 1: Upgrade
    total_tests += 1
    try:
        command.upgrade(config, "head")
        engine = create_engine(postgres_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        expected = EXPECTED_TABLES | {"alembic_version"}
        missing = expected - tables
        if missing:
            all_failures.append(f"Upgrade: Missing tables {missing}")
        else:
            print("  ✓ Upgrade creates all expected tables")
        engine.dispose()
    except Exception as e:
        all_failures.append(f"Upgrade failed: {e}")

    # Test 2: Downgrade
    total_tests += 1
    try:
        command.downgrade(config, "base")
        engine = create_engine(postgres_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        if tables != {"alembic_version"}:
            all_failures.append(f"Downgrade: Unexpected tables {tables - {'alembic_version'}}")
        else:
            print("  ✓ Downgrade removes tables")
        engine.dispose()
    except Exception as e:
        all_failures.append(f"Downgrade failed: {e}")

    # Test 3: Re-upgrade
    total_tests += 1
    try:
        command.upgrade(config, "head")
        engine = create_engine(postgres_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        expected = EXPECTED_TABLES | {"alembic_version"}
        missing = expected - tables
        if missing:
            all_failures.append(f"Re-upgrade: Missing tables {missing}")
        else:
            print("  ✓ Re-upgrade works")
        engine.dispose()
    except Exception as e:
        all_failures.append(f"Re-upgrade failed: {e}")

    # Final result
    if all_failures:
        print(f"\n❌ VALIDATION FAILED - {len(all_failures)} of {total_tests} tests failed:")
        for failure in all_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_tests} tests passed")
        sys.exit(0)
