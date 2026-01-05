"""
Setup PostgreSQL test database for synth-lab.

This script:
1. Drops and recreates the test database (clean slate)
2. Applies all Alembic migrations
3. Optionally seeds test data

Usage:
    # Setup clean database with migrations only
    uv run python scripts/setup_test_db.py

    # Setup with seed data
    uv run python scripts/setup_test_db.py --seed

    # Reset existing database
    uv run python scripts/setup_test_db.py --reset

Environment Variables Required:
    DATABASE_TEST_URL: PostgreSQL connection string for test database
    Example: postgresql://synthlab:synthlab@localhost:5432/synthlab_test
"""

import os
import sys
from pathlib import Path

import typer
from loguru import logger
from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

app = typer.Typer()


def get_test_db_url() -> str:
    """Get test database URL from environment."""
    db_url = os.getenv("DATABASE_TEST_URL")
    if not db_url:
        logger.error("DATABASE_TEST_URL environment variable not set")
        logger.info("Example: DATABASE_TEST_URL=postgresql://user:pass@localhost:5432/synthlab_test")
        sys.exit(1)
    return db_url


def get_admin_url(db_url: str) -> str:
    """Get admin connection URL (connects to postgres database)."""
    # Replace database name with 'postgres' for admin operations
    parts = db_url.rsplit("/", 1)
    return f"{parts[0]}/postgres"


def drop_database(db_name: str, admin_url: str) -> None:
    """Drop test database if it exists."""
    logger.info(f"Dropping database '{db_name}' if exists...")
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:
        # Terminate existing connections
        conn.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
            AND pid <> pg_backend_pid()
        """))

        # Drop database
        conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))

    engine.dispose()
    logger.success(f"Database '{db_name}' dropped")


def create_database(db_name: str, admin_url: str) -> None:
    """Create test database."""
    logger.info(f"Creating database '{db_name}'...")
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))

    engine.dispose()
    logger.success(f"Database '{db_name}' created")


def apply_migrations(db_url: str) -> None:
    """Apply all Alembic migrations."""
    logger.info("Applying Alembic migrations...")

    # Configure Alembic
    alembic_ini = project_root / "src" / "synth_lab" / "alembic" / "alembic.ini"
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(project_root / "src" / "synth_lab" / "alembic"))

    # Set DATABASE_URL for env.py
    os.environ["DATABASE_URL"] = db_url

    # Run migrations
    command.upgrade(config, "head")

    logger.success("Migrations applied successfully")


def seed_test_data(db_url: str) -> None:
    """Seed test database with initial data."""
    logger.info("Seeding test data...")

    # Import and run seed
    from tests.fixtures.seed_test import seed_database

    engine = create_engine(db_url)
    seed_database(engine)
    engine.dispose()

    logger.success("Test data seeded successfully")


@app.command()
def setup(
    seed: bool = typer.Option(False, "--seed", help="Seed database with test data"),
    reset: bool = typer.Option(False, "--reset", help="Reset existing database"),
) -> None:
    """
    Setup PostgreSQL test database.

    Creates a clean test database and applies migrations.
    Optionally seeds with test data.
    """
    logger.info("=" * 60)
    logger.info("PostgreSQL Test Database Setup")
    logger.info("=" * 60)

    # Get database URLs
    db_url = get_test_db_url()
    db_name = db_url.rsplit("/", 1)[1].split("?")[0]
    admin_url = get_admin_url(db_url)

    logger.info(f"Database: {db_name}")
    logger.info(f"URL: {db_url}")

    try:
        # Drop and create database
        if reset:
            drop_database(db_name, admin_url)
        create_database(db_name, admin_url)

        # Apply migrations
        apply_migrations(db_url)

        # Seed data if requested
        if seed:
            seed_test_data(db_url)

        logger.info("=" * 60)
        logger.success("✅ Test database setup complete!")
        logger.info("=" * 60)
        logger.info("You can now run tests with:")
        logger.info("  pytest tests/")

    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
