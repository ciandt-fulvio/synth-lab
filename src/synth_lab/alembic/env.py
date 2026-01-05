"""
Alembic migrations environment configuration for synth-lab.

PostgreSQL-only configuration for production use.

References:
    - Alembic cookbook: https://alembic.sqlalchemy.org/en/latest/cookbook.html
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy import create_engine

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import models to register with Base.metadata
from synth_lab.models.orm.base import Base
from synth_lab.models.orm import (  # noqa: F401
    Experiment, InterviewGuide,
    AnalysisRun, SynthOutcome, AnalysisCache,
    Synth, SynthGroup,
    ResearchExecution, Transcript,
    Exploration, ScenarioNode,
    ChartInsight, SensitivityResult, RegionAnalysis,
    ExperimentDocument,
)

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from environment or config.

    Priority:
    1. URL set via config.set_main_option("sqlalchemy.url", ...)
    2. DATABASE_URL environment variable

    Raises:
        ValueError: If DATABASE_URL is not set
    """
    # First check if URL was set via alembic config (e.g., in tests)
    config_url = config.get_main_option("sqlalchemy.url")
    if config_url:
        return config_url

    # Then try environment variable
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "Set it to your PostgreSQL connection string: "
        "postgresql://user:pass@host:5432/dbname"
    )


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL script without connecting to database.
    Used for reviewing migration SQL or applying to remote databases.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def _should_include_object(object, name, type_, reflected, compare_to):
    """
    Filter autogenerate differences to ignore false positives.

    Specifically handles DESC indexes which Alembic incorrectly flags as different
    even when they're identical between model and database.
    """
    # For indexes, check if this is a DESC index comparison issue
    if type_ == "index" and reflected and compare_to:
        # If both have the same name and are on created_at, they're the same
        # (This handles the DESC operator representation mismatch)
        if name and ("created" in name or "created_at" in name):
            return False  # Skip this comparison - it's a false positive
    return True


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates engine and runs migrations with an active connection.
    """
    url = get_url()

    # PostgreSQL configuration
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Compare types for autogenerate
            compare_type=True,
            # Compare server defaults
            compare_server_default=True,
            # Filter false positives (DESC indexes)
            include_object=_should_include_object,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
