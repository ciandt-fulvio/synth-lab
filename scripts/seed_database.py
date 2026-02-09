#!/usr/bin/env python3
"""
Seed database with test data.

Wrapper script that reuses tests/fixtures/seed_test.py for seeding
staging and other environments. This ensures consistency between
test data and staging data.

Usage:
    DATABASE_URL=<url> python scripts/seed_database.py

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (required)
    OPENAI_API_KEY: OpenAI API key (optional, for LLM features)

Examples:
    # Seed staging database
    DATABASE_URL=postgresql://user:pass@localhost:5432/staging python scripts/seed_database.py

    # Seed local dev database
    DATABASE_URL=postgresql://synthlab:synthlab@localhost:5432/synthlab python scripts/seed_database.py
"""

import os
import sys
from pathlib import Path

# Add project root to Python path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from synth_lab.infrastructure.database_v2 import create_db_engine
from tests.fixtures.seed_test import seed_database

# Import seed_mechanisms from the other script
from scripts.seed_mechanisms import seed_mechanisms, _check_mechanisms_exist


def _check_synth_groups_exist(db_url: str) -> bool:
    """Check if synth_groups table has any records.

    Args:
        db_url: Database connection URL

    Returns:
        True if synth_groups table has records, False otherwise
    """
    engine = create_db_engine(db_url)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM synth_groups"))
            count = result.scalar()
            return count > 0
    finally:
        engine.dispose()


def main() -> None:
    """Seed database with test data.

    Only executes if synth_group table is empty. If data already exists,
    skips seeding to preserve existing data.
    """
    # Validate DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set", file=sys.stderr)
        print("", file=sys.stderr)
        print("Usage:", file=sys.stderr)
        print("  DATABASE_URL=<url> python scripts/seed_database.py", file=sys.stderr)
        print("", file=sys.stderr)
        print("Example:", file=sys.stderr)
        print("  DATABASE_URL=postgresql://user:pass@localhost:5432/db python scripts/seed_database.py", file=sys.stderr)
        sys.exit(1)

    # Validate OPENAI_API_KEY (warning only, not blocking)
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not set - some LLM features may not work", file=sys.stderr)

    print(f"🌱 Checking database: {db_url.split('@')[-1]}")  # Print only host/db, not credentials
    print("")

    # Check if data already exists
    try:
        if _check_synth_groups_exist(db_url):
            print("ℹ️  Database already contains data (synth_groups table not empty)")
            print("   Skipping seed to preserve existing data")
            print("")
            print("✅ Seed skipped - data already exists")
            sys.exit(0)
    except Exception as e:
        print(f"⚠️  Warning: Could not check synth_groups table: {e}", file=sys.stderr)
        print("   Proceeding with seed anyway...", file=sys.stderr)
        print("", file=sys.stderr)

    # Create engine and seed
    try:
        print("📝 Database is empty - seeding with test data...")
        print("")

        engine = create_db_engine(db_url)
        seed_database(engine)
        engine.dispose()

        print("")
        print("✅ Database seeded successfully!")
        sys.exit(0)

    except Exception as e:
        print("", file=sys.stderr)
        print(f"❌ ERROR: Failed to seed database: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
