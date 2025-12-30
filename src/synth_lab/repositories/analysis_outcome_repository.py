"""
Analysis Outcome Repository for synth-lab.

Data access layer for synth outcomes linked to analysis runs.
Uses the v7 schema with analysis_id column.

References:
    - Schema: synth_outcomes table with analysis_id FK
    - Data model: specs/019-experiment-refactor/data-model.md
"""

import json
from typing import Any

from loguru import logger

from synth_lab.domain.entities import SynthOutcome
from synth_lab.domain.entities.simulation_attributes import SimulationAttributes
from synth_lab.infrastructure.database import DatabaseManager, get_database
from synth_lab.repositories.base import BaseRepository


class AnalysisOutcomeRepository(BaseRepository):
    """Repository for analysis outcome data access."""

    def __init__(self, db: DatabaseManager | None = None):
        super().__init__(db)
        self.logger = logger.bind(component="analysis_outcome_repository")

    def save_outcomes(
        self,
        analysis_id: str,
        outcomes: list[dict[str, Any]],
    ) -> int:
        """
        Save synth outcomes for an analysis.

        Args:
            analysis_id: Analysis run ID
            outcomes: List of outcome dicts with synth_id, rates, and attributes

        Returns:
            Number of outcomes saved
        """
        for outcome in outcomes:
            synth_attrs_json = None
            if outcome.get("synth_attributes"):
                synth_attrs_json = json.dumps(outcome["synth_attributes"])

            self.db.execute(
                """
                INSERT OR REPLACE INTO synth_outcomes (
                    id, analysis_id, synth_id,
                    did_not_try_rate, failed_rate, success_rate,
                    synth_attributes
                )
                VALUES (
                    ?, ?, ?,
                    ?, ?, ?,
                    ?
                )
                """,
                (
                    f"{analysis_id}_{outcome['synth_id']}",
                    analysis_id,
                    outcome["synth_id"],
                    outcome["did_not_try_rate"],
                    outcome["failed_rate"],
                    outcome["success_rate"],
                    synth_attrs_json,
                ),
            )

        self.logger.info(f"Saved {len(outcomes)} outcomes for analysis {analysis_id}")
        return len(outcomes)

    def get_outcomes(
        self,
        analysis_id: str,
        limit: int = 10000,
        offset: int = 0,
    ) -> tuple[list[SynthOutcome], int]:
        """
        Get synth outcomes for an analysis.

        Args:
            analysis_id: Analysis run ID
            limit: Maximum results
            offset: Results to skip

        Returns:
            Tuple of (list of outcomes, total count)
        """
        # Count total
        count_sql = """
            SELECT COUNT(*) as count FROM synth_outcomes
            WHERE analysis_id = ?
        """
        count_row = self.db.fetchone(count_sql, (analysis_id,))
        total = count_row["count"] if count_row else 0

        # Get paginated results
        list_sql = """
            SELECT synth_id, did_not_try_rate, failed_rate, success_rate, synth_attributes
            FROM synth_outcomes
            WHERE analysis_id = ?
            ORDER BY synth_id
            LIMIT ? OFFSET ?
        """
        rows = self.db.fetchall(list_sql, (analysis_id, limit, offset))

        outcomes = []
        for row in rows:
            attrs_dict = json.loads(row["synth_attributes"]) if row["synth_attributes"] else None
            attrs = SimulationAttributes.model_validate(attrs_dict) if attrs_dict else None

            # Skip rows without synth_attributes (required field in SynthOutcome)
            if attrs is None:
                self.logger.warning(
                    f"Skipping outcome for synth {row['synth_id']} - missing attributes"
                )
                continue

            outcomes.append(
                SynthOutcome(
                    analysis_id=analysis_id,
                    synth_id=row["synth_id"],
                    did_not_try_rate=row["did_not_try_rate"],
                    failed_rate=row["failed_rate"],
                    success_rate=row["success_rate"],
                    synth_attributes=attrs,
                )
            )

        return outcomes, total

    def delete_outcomes(self, analysis_id: str) -> int:
        """
        Delete all outcomes for an analysis.

        Args:
            analysis_id: Analysis run ID

        Returns:
            Number of outcomes deleted
        """
        cursor = self.db.execute(
            "DELETE FROM synth_outcomes WHERE analysis_id = ?",
            (analysis_id,),
        )
        deleted = cursor.rowcount
        self.logger.info(f"Deleted {deleted} outcomes for analysis {analysis_id}")
        return deleted


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test with actual database
    db = get_database()
    repo = AnalysisOutcomeRepository(db)

    # Test 1: Get outcomes for non-existent analysis
    total_tests += 1
    try:
        outcomes, count = repo.get_outcomes("nonexistent_analysis")
        if count != 0:
            all_validation_failures.append(f"Expected 0 count, got {count}")
        if len(outcomes) != 0:
            all_validation_failures.append(f"Expected 0 outcomes, got {len(outcomes)}")
    except Exception as e:
        all_validation_failures.append(f"Get outcomes failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
