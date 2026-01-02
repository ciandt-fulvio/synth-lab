#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL for synth-lab.

This script reads all data from the SQLite database and inserts it into PostgreSQL.
It handles schema differences and ensures data integrity during migration.

Usage:
    # Set environment variables
    export SQLITE_PATH=output/synthlab.db
    export POSTGRES_URL=postgresql://user:pass@localhost:5432/synthlab

    # Run migration
    uv run python scripts/migrate_data_to_postgres.py

    # Dry run (no changes)
    uv run python scripts/migrate_data_to_postgres.py --dry-run

    # Verbose mode
    uv run python scripts/migrate_data_to_postgres.py --verbose

References:
    - SQLAlchemy bulk insert: https://docs.sqlalchemy.org/en/20/orm/persistence_techniques.html
    - PostgreSQL COPY: https://www.postgresql.org/docs/current/sql-copy.html
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from synth_lab.models.orm.base import Base
from synth_lab.models.orm import (
    Experiment, InterviewGuide, AnalysisRun, SynthOutcome, AnalysisCache,
    Synth, SynthGroup, ResearchExecution, Transcript,
    Exploration, ScenarioNode, ChartInsight, SensitivityResult, RegionAnalysis,
    ExperimentDocument, FeatureScorecard, SimulationRun,
)


# Tables in dependency order (parent tables before child tables)
MIGRATION_ORDER = [
    ("synth_groups", SynthGroup),
    ("synths", Synth),
    ("experiments", Experiment),
    ("interview_guide", InterviewGuide),
    ("analysis_runs", AnalysisRun),
    ("synth_outcomes", SynthOutcome),
    ("analysis_cache", AnalysisCache),
    ("research_executions", ResearchExecution),
    ("transcripts", Transcript),
    ("explorations", Exploration),
    ("scenario_nodes", ScenarioNode),
    ("chart_insights", ChartInsight),
    ("sensitivity_results", SensitivityResult),
    ("region_analyses", RegionAnalysis),
    ("experiment_documents", ExperimentDocument),
    ("feature_scorecards", FeatureScorecard),
    ("simulation_runs", SimulationRun),
]


def get_sqlite_engine(sqlite_path: Path):
    """Create SQLite engine for reading source data."""
    url = f"sqlite:///{sqlite_path}"
    return create_engine(url, echo=False)


def get_postgres_engine(postgres_url: str):
    """Create PostgreSQL engine for writing data."""
    return create_engine(postgres_url, echo=False)


def count_rows(session: Session, table_name: str) -> int:
    """Count rows in a table."""
    result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    return result.scalar() or 0


def migrate_table(
    sqlite_session: Session,
    postgres_session: Session,
    table_name: str,
    model_class,
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[int, int]:
    """
    Migrate a single table from SQLite to PostgreSQL.

    Args:
        sqlite_session: Source SQLite session
        postgres_session: Target PostgreSQL session
        table_name: Name of the table
        model_class: SQLAlchemy model class
        dry_run: If True, don't commit changes
        verbose: If True, log detailed info

    Returns:
        Tuple of (rows_read, rows_written)
    """
    log = logger.bind(table=table_name)

    # Count source rows
    source_count = count_rows(sqlite_session, table_name)
    log.info(f"Found {source_count} rows in source")

    if source_count == 0:
        return 0, 0

    # Read all rows from SQLite
    result = sqlite_session.execute(text(f"SELECT * FROM {table_name}"))
    columns = result.keys()
    rows = result.fetchall()

    if verbose:
        log.debug(f"Columns: {list(columns)}")

    # Clear existing data in PostgreSQL (if not dry run)
    if not dry_run:
        try:
            postgres_session.execute(text(f"DELETE FROM {table_name}"))
            log.info("Cleared existing data in target table")
        except Exception as e:
            log.warning(f"Could not clear target table: {e}")

    # Insert rows into PostgreSQL
    inserted = 0
    for row in rows:
        row_dict = dict(zip(columns, row))

        # Create model instance
        try:
            instance = model_class(**row_dict)
            if not dry_run:
                postgres_session.add(instance)
            inserted += 1
        except Exception as e:
            log.error(f"Failed to insert row: {e}")
            if verbose:
                log.debug(f"Row data: {row_dict}")

    if not dry_run:
        postgres_session.flush()

    return source_count, inserted


def run_migration(
    sqlite_path: Path,
    postgres_url: str,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """
    Run full data migration from SQLite to PostgreSQL.

    Args:
        sqlite_path: Path to SQLite database
        postgres_url: PostgreSQL connection URL
        dry_run: If True, don't commit changes
        verbose: If True, log detailed info

    Returns:
        Dictionary with migration statistics
    """
    log = logger.bind(component="migration")

    if not sqlite_path.exists():
        log.error(f"SQLite database not found: {sqlite_path}")
        return {"error": "SQLite database not found"}

    log.info(f"Starting migration from {sqlite_path}")
    log.info(f"Target: {postgres_url.split('@')[-1] if '@' in postgres_url else postgres_url}")

    if dry_run:
        log.info("DRY RUN MODE - No changes will be committed")

    # Create engines and sessions
    sqlite_engine = get_sqlite_engine(sqlite_path)
    postgres_engine = get_postgres_engine(postgres_url)

    # Create tables in PostgreSQL if they don't exist
    log.info("Creating tables in PostgreSQL...")
    Base.metadata.create_all(postgres_engine)

    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)

    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()

    stats = {
        "started_at": datetime.now().isoformat(),
        "dry_run": dry_run,
        "tables": {},
        "total_read": 0,
        "total_written": 0,
    }

    try:
        for table_name, model_class in MIGRATION_ORDER:
            log.info(f"Migrating {table_name}...")
            try:
                read, written = migrate_table(
                    sqlite_session,
                    postgres_session,
                    table_name,
                    model_class,
                    dry_run=dry_run,
                    verbose=verbose,
                )
                stats["tables"][table_name] = {"read": read, "written": written}
                stats["total_read"] += read
                stats["total_written"] += written
            except Exception as e:
                log.error(f"Failed to migrate {table_name}: {e}")
                stats["tables"][table_name] = {"error": str(e)}

        if not dry_run:
            postgres_session.commit()
            log.info("Migration committed successfully")
        else:
            postgres_session.rollback()
            log.info("Dry run completed - changes rolled back")

    except Exception as e:
        log.error(f"Migration failed: {e}")
        postgres_session.rollback()
        stats["error"] = str(e)

    finally:
        sqlite_session.close()
        postgres_session.close()
        sqlite_engine.dispose()
        postgres_engine.dispose()

    stats["completed_at"] = datetime.now().isoformat()

    # Summary
    log.info("=" * 50)
    log.info("Migration Summary")
    log.info("=" * 50)
    for table_name, table_stats in stats["tables"].items():
        if "error" in table_stats:
            log.error(f"  {table_name}: ERROR - {table_stats['error']}")
        else:
            log.info(f"  {table_name}: {table_stats['read']} read, {table_stats['written']} written")
    log.info("-" * 50)
    log.info(f"  Total: {stats['total_read']} read, {stats['total_written']} written")

    return stats


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate data from SQLite to PostgreSQL"
    )
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=Path(os.getenv("SQLITE_PATH", "output/synthlab.db")),
        help="Path to SQLite database (default: output/synthlab.db or SQLITE_PATH env)",
    )
    parser.add_argument(
        "--postgres-url",
        type=str,
        default=os.getenv("POSTGRES_URL", "postgresql://synthlab:synthlab_dev@localhost:5432/synthlab"),
        help="PostgreSQL connection URL (default: POSTGRES_URL env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run migration without committing changes",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    logger.remove()
    log_level = "DEBUG" if args.verbose else "INFO"
    logger.add(sys.stderr, level=log_level, format="{time:HH:mm:ss} | {level: <7} | {message}")

    # Run migration
    stats = run_migration(
        sqlite_path=args.sqlite_path,
        postgres_url=args.postgres_url,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    # Exit with appropriate code
    if "error" in stats:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
