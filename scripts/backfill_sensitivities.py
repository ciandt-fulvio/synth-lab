"""Backfill sensitivities for synths with derivation_version < 1.1.

Re-derives sensitivities using the current YAML rules (v1.1) for synths
that were created with older derivation versions and are missing
motor_ability and/or subject_domain fields.

Usage:
    DATABASE_URL="postgresql://synthlab:synthlab@localhost:5432/synthlab" \
        uv run python scripts/backfill_sensitivities.py [--dry-run]
"""

import json
import sys
from hashlib import sha256

from sqlalchemy import create_engine, text

# Add src to path for imports
sys.path.insert(0, "src")

from synth_lab.services.sensitivity_deriver import derive_sensitivities


def get_database_url() -> str:
    import os
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL environment variable is required")
        sys.exit(1)
    return url


def deterministic_seed(synth_id: str) -> int:
    """Generate a deterministic seed from synth ID for reproducibility."""
    return int(sha256(synth_id.encode()).hexdigest()[:8], 16)


def main():
    dry_run = "--dry-run" in sys.argv

    engine = create_engine(get_database_url())

    with engine.connect() as conn:
        # Find synths missing motor_ability in sensitivities
        result = conn.execute(text("""
            SELECT s.id, s.data, sg.name as group_name
            FROM synths s
            JOIN synth_groups sg ON s.synth_group_id = sg.id
            WHERE s.data->'sensitivities'->>'motor_ability' IS NULL
            ORDER BY sg.name, s.id
        """))
        rows = result.fetchall()

        if not rows:
            print("No synths need backfill. All sensitivities are up to date.")
            return

        print(f"Found {len(rows)} synths to backfill")

        # Group by synth_group for reporting
        groups: dict[str, int] = {}
        for row in rows:
            groups[row.group_name] = groups.get(row.group_name, 0) + 1
        for name, count in groups.items():
            print(f"  {name}: {count} synths")

        if dry_run:
            print("\n[DRY RUN] Would update these synths. Run without --dry-run to apply.")
            # Show a sample
            sample = rows[0]
            synth_data = sample.data
            seed = deterministic_seed(sample.id)
            new_sensitivities = derive_sensitivities(synth_data, seed=seed)
            print(f"\nSample (synth {sample.id}):")
            print(f"  Old: {json.dumps(synth_data.get('sensitivities', {}), indent=2)}")
            print(f"  New: {json.dumps(new_sensitivities, indent=2)}")
            return

        # Backfill
        updated = 0
        errors = 0
        for row in rows:
            try:
                synth_data = row.data
                # Use deterministic seed based on synth ID for reproducibility
                seed = deterministic_seed(row.id)
                new_sensitivities = derive_sensitivities(synth_data, seed=seed)

                # Update sensitivities in the data JSONB
                updated_data = dict(synth_data)
                updated_data["sensitivities"] = new_sensitivities
                conn.execute(
                    text("UPDATE synths SET data = :data WHERE id = :synth_id"),
                    {
                        "synth_id": row.id,
                        "data": json.dumps(updated_data),
                    },
                )
                updated += 1
            except Exception as e:
                print(f"  ERROR updating synth {row.id}: {e}")
                errors += 1

        conn.commit()

        print(f"\nBackfill complete: {updated} updated, {errors} errors")

        # Verify
        result = conn.execute(text("""
            SELECT COUNT(*) FROM synths
            WHERE data->'sensitivities'->>'motor_ability' IS NULL
        """))
        remaining = result.scalar()
        if remaining == 0:
            print("Verification: All synths now have motor_ability")
        else:
            print(f"WARNING: {remaining} synths still missing motor_ability")


if __name__ == "__main__":
    main()
