"""Data migration script to assign owner_id to existing experiments and synth_groups.

This script should be run ONCE after deploying the authentication feature to assign
ownership of existing resources to a default/admin user.

Usage:
    # Set the owner user ID (UUID of user who should own existing resources)
    export MIGRATION_OWNER_ID="550e8400-e29b-41d4-a716-446655440000"

    # Run migration
    uv run python scripts/migrate_ownership.py

    # Or with dry-run to preview changes
    uv run python scripts/migrate_ownership.py --dry-run

References:
    - Spec: specs/034-user-login/spec.md
    - Task: T150
"""
import os
import sys
from uuid import UUID
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from synth_lab.infrastructure.database_v2 import get_db_session
from loguru import logger


async def validate_owner_user(db: AsyncSession, owner_id: str) -> bool:
    """Validate that the owner user exists in the database.

    Args:
        db: Database session
        owner_id: UUID of the owner user

    Returns:
        True if user exists, False otherwise
    """
    query = text("SELECT id, email FROM users WHERE id = :owner_id")
    result = await db.execute(query, {"owner_id": owner_id})
    row = result.fetchone()

    if row:
        logger.info(f"Owner user found: {row[1]} ({row[0]})")
        return True
    else:
        logger.error(f"Owner user {owner_id} not found in database")
        return False


async def count_resources(db: AsyncSession) -> dict:
    """Count experiments and synth_groups that need migration.

    Args:
        db: Database session

    Returns:
        Dict with counts of resources needing migration
    """
    # Count experiments without owner
    exp_query = text("SELECT COUNT(*) FROM experiments WHERE owner_id IS NULL")
    exp_result = await db.execute(exp_query)
    exp_count = exp_result.scalar()

    # Count synth_groups without owner
    grp_query = text("SELECT COUNT(*) FROM synth_groups WHERE owner_id IS NULL")
    grp_result = await db.execute(grp_query)
    grp_count = grp_result.scalar()

    return {
        "experiments": exp_count,
        "synth_groups": grp_count,
        "total": exp_count + grp_count,
    }


async def migrate_experiments(
    db: AsyncSession,
    owner_id: str,
    dry_run: bool = False
) -> int:
    """Assign owner_id to experiments that don't have one.

    Args:
        db: Database session
        owner_id: UUID of the owner user
        dry_run: If True, don't commit changes

    Returns:
        Number of experiments updated
    """
    if dry_run:
        # Just count
        query = text("SELECT id FROM experiments WHERE owner_id IS NULL")
        result = await db.execute(query)
        rows = result.fetchall()
        logger.info(f"[DRY RUN] Would update {len(rows)} experiments")

        # Show first 5 as examples
        if rows:
            logger.info("Example experiment IDs:")
            for row in rows[:5]:
                logger.info(f"  - {row[0]}")
            if len(rows) > 5:
                logger.info(f"  ... and {len(rows) - 5} more")

        return len(rows)
    else:
        # Actual update
        query = text("""
            UPDATE experiments
            SET owner_id = :owner_id
            WHERE owner_id IS NULL
        """)
        result = await db.execute(query, {"owner_id": owner_id})
        await db.commit()

        count = result.rowcount
        logger.info(f"Updated {count} experiments with owner_id = {owner_id}")
        return count


async def migrate_synth_groups(
    db: AsyncSession,
    owner_id: str,
    dry_run: bool = False
) -> int:
    """Assign owner_id to synth_groups that don't have one.

    Args:
        db: Database session
        owner_id: UUID of the owner user
        dry_run: If True, don't commit changes

    Returns:
        Number of synth_groups updated
    """
    if dry_run:
        # Just count
        query = text("SELECT id FROM synth_groups WHERE owner_id IS NULL")
        result = await db.execute(query)
        rows = result.fetchall()
        logger.info(f"[DRY RUN] Would update {len(rows)} synth_groups")

        # Show first 5 as examples
        if rows:
            logger.info("Example synth_group IDs:")
            for row in rows[:5]:
                logger.info(f"  - {row[0]}")
            if len(rows) > 5:
                logger.info(f"  ... and {len(rows) - 5} more")

        return len(rows)
    else:
        # Actual update
        query = text("""
            UPDATE synth_groups
            SET owner_id = :owner_id
            WHERE owner_id IS NULL
        """)
        result = await db.execute(query, {"owner_id": owner_id})
        await db.commit()

        count = result.rowcount
        logger.info(f"Updated {count} synth_groups with owner_id = {owner_id}")
        return count


async def run_migration(owner_id: str, dry_run: bool = False):
    """Run the complete ownership migration.

    Args:
        owner_id: UUID of the owner user
        dry_run: If True, preview changes without committing
    """
    logger.info("=" * 60)
    logger.info("Ownership Migration Script")
    logger.info("=" * 60)
    logger.info(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (changes will be committed)'}")
    logger.info(f"Owner ID: {owner_id}")
    logger.info("")

    # Get database session
    async for db in get_db_session():
        try:
            # Validate owner user exists
            logger.info("Step 1: Validating owner user...")
            if not await validate_owner_user(db, owner_id):
                logger.error("Migration aborted: Owner user not found")
                logger.error("Please ensure the user exists before running migration")
                return False

            logger.info("")

            # Count resources needing migration
            logger.info("Step 2: Counting resources...")
            counts = await count_resources(db)
            logger.info(f"Experiments without owner: {counts['experiments']}")
            logger.info(f"Synth groups without owner: {counts['synth_groups']}")
            logger.info(f"Total resources to migrate: {counts['total']}")

            if counts['total'] == 0:
                logger.info("No resources need migration. All done!")
                return True

            logger.info("")

            # Confirm if not dry run
            if not dry_run:
                logger.warning("⚠️  This will permanently assign ownership to all unowned resources")
                response = input("Continue? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Migration cancelled by user")
                    return False
                logger.info("")

            # Migrate experiments
            logger.info("Step 3: Migrating experiments...")
            exp_count = await migrate_experiments(db, owner_id, dry_run)
            logger.info("")

            # Migrate synth_groups
            logger.info("Step 4: Migrating synth_groups...")
            grp_count = await migrate_synth_groups(db, owner_id, dry_run)
            logger.info("")

            # Summary
            logger.info("=" * 60)
            logger.info("Migration Summary")
            logger.info("=" * 60)
            logger.info(f"Experiments: {exp_count} {'would be' if dry_run else 'were'} updated")
            logger.info(f"Synth groups: {grp_count} {'would be' if dry_run else 'were'} updated")
            logger.info(f"Total: {exp_count + grp_count} resources")

            if dry_run:
                logger.info("")
                logger.info("This was a DRY RUN. No changes were made.")
                logger.info("Run without --dry-run to apply changes.")
            else:
                logger.info("")
                logger.info("✅ Migration completed successfully!")

            return True

        except Exception as e:
            logger.error(f"Migration failed with error: {e}")
            logger.exception("Full traceback:")
            return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate ownership of existing experiments and synth_groups"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without committing to database"
    )
    parser.add_argument(
        "--owner-id",
        type=str,
        help="UUID of user who should own existing resources (overrides MIGRATION_OWNER_ID env var)"
    )

    args = parser.parse_args()

    # Get owner ID from args or environment
    owner_id = args.owner_id or os.getenv("MIGRATION_OWNER_ID")

    if not owner_id:
        logger.error("Error: Owner ID not provided")
        logger.error("")
        logger.error("Please set MIGRATION_OWNER_ID environment variable or use --owner-id flag:")
        logger.error("")
        logger.error("  export MIGRATION_OWNER_ID='550e8400-e29b-41d4-a716-446655440000'")
        logger.error("  uv run python scripts/migrate_ownership.py")
        logger.error("")
        logger.error("Or:")
        logger.error("")
        logger.error("  uv run python scripts/migrate_ownership.py --owner-id '550e8400-e29b-41d4-a716-446655440000'")
        sys.exit(1)

    # Validate UUID format
    try:
        UUID(owner_id)
    except ValueError:
        logger.error(f"Error: Invalid UUID format: {owner_id}")
        logger.error("Owner ID must be a valid UUID")
        sys.exit(1)

    # Run migration
    success = asyncio.run(run_migration(owner_id, dry_run=args.dry_run))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
