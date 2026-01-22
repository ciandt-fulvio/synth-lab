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

from synth_lab.infrastructure.database_v2 import create_db_engine
from tests.fixtures.seed_test import seed_database


def main() -> None:
    """Seed database with test data."""
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

    print(f"🌱 Seeding database: {db_url.split('@')[-1]}")  # Print only host/db, not credentials
    print("")

    # Create engine and seed
    try:
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
