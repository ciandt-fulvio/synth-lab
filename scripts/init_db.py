"""
Initialize SQLite database with schema.

Creates the database with all required tables and indexes.
Does NOT migrate any data - just creates the empty schema.

Usage:
    uv run python scripts/init_db.py

References:
    - Schema definition: specs/010-rest-api/data-model.md
"""

from loguru import logger

from synth_lab.infrastructure.config import DB_PATH, OUTPUT_DIR
from synth_lab.infrastructure.database import init_database


def main() -> None:
    """Run database initialization."""
    logger.info(f"Creating database at {DB_PATH}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    init_database()

    logger.info("=" * 50)
    logger.info("Database initialization complete:")
    logger.info(f"  - Database: {DB_PATH}")


if __name__ == "__main__":
    main()
