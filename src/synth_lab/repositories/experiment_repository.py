"""
ExperimentRepository for synth-lab.

Data access layer for experiment data in SQLite database.
Supports embedded scorecard data and related counts.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - Data model: specs/019-experiment-refactor/data-model.md
"""

import json
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from synth_lab.domain.entities.experiment import Experiment, ScorecardData
from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.models.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from synth_lab.repositories.base import BaseRepository


class ExperimentSummary(BaseModel):
    """Summary of an experiment for list display."""

    id: str = Field(description="Experiment ID.")
    name: str = Field(description="Short name of the feature.")
    hypothesis: str = Field(description="Hypothesis description.")
    description: str | None = Field(default=None, description="Additional context.")
    has_scorecard: bool = Field(default=False, description="Whether scorecard is filled.")
    has_analysis: bool = Field(default=False, description="Whether analysis exists.")
    has_interview_guide: bool = Field(
        default=False, description="Whether interview guide is configured."
    )
    interview_count: int = Field(default=0, description="Number of linked interviews.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class ExperimentRepository(BaseRepository):
    """Repository for experiment data access."""

    def __init__(self, db: DatabaseManager | None = None):
        super().__init__(db)

    def create(self, experiment: Experiment) -> Experiment:
        """
        Create a new experiment.

        Args:
            experiment: Experiment entity to create.

        Returns:
            Created experiment with persisted data.
        """
        scorecard_json = None
        if experiment.scorecard_data:
            scorecard_json = json.dumps(experiment.scorecard_data.model_dump())

        self.db.execute(
            """
            INSERT INTO experiments (id, name, hypothesis, description, scorecard_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                experiment.id,
                experiment.name,
                experiment.hypothesis,
                experiment.description,
                scorecard_json,
                experiment.created_at.isoformat(),
                experiment.updated_at.isoformat() if experiment.updated_at else None,
            ),
        )
        return experiment

    def get_by_id(self, experiment_id: str) -> Experiment | None:
        """
        Get an experiment by ID.

        Only returns active experiments (not soft-deleted).

        Args:
            experiment_id: Experiment ID to retrieve.

        Returns:
            Experiment if found and active, None otherwise.
        """
        row = self.db.fetchone(
            "SELECT * FROM experiments WHERE id = ? AND (status = 'active' OR status IS NULL)",
            (experiment_id,),
        )
        if row is None:
            return None
        return self._row_to_experiment(row)

    def list_experiments(
        self, params: PaginationParams
    ) -> PaginatedResponse[ExperimentSummary]:
        """
        List experiments with pagination.

        Only returns active experiments (not soft-deleted).

        Args:
            params: Pagination parameters.

        Returns:
            Paginated response with experiment summaries.
        """
        # Query with analysis, interview guide, and interview counts
        # Filter out deleted experiments
        base_query = """
            SELECT
                e.id,
                e.name,
                e.hypothesis,
                e.description,
                e.scorecard_data,
                e.created_at,
                e.updated_at,
                CASE WHEN ana.id IS NOT NULL THEN 1 ELSE 0 END as has_analysis,
                CASE WHEN ig.experiment_id IS NOT NULL THEN 1 ELSE 0 END as has_interview_guide,
                COALESCE(int.cnt, 0) as interview_count
            FROM experiments e
            LEFT JOIN analysis_runs ana ON e.id = ana.experiment_id
            LEFT JOIN interview_guide ig ON e.id = ig.experiment_id
            LEFT JOIN (
                SELECT experiment_id, COUNT(*) as cnt
                FROM research_executions
                WHERE experiment_id IS NOT NULL
                GROUP BY experiment_id
            ) int ON e.id = int.experiment_id
            WHERE (e.status = 'active' OR e.status IS NULL)
            ORDER BY e.created_at DESC
        """

        count_query = """
            SELECT COUNT(*) as count FROM experiments
            WHERE (status = 'active' OR status IS NULL)
        """

        # Get total count
        count_row = self.db.fetchone(count_query)
        total = count_row["count"] if count_row else 0

        # Apply pagination
        paginated_query = f"{base_query} LIMIT ? OFFSET ?"
        rows = self.db.fetchall(paginated_query, (params.limit, params.offset))

        summaries = [self._row_to_summary(row) for row in rows]
        meta = PaginationMeta.from_params(total, params)

        return PaginatedResponse(data=summaries, pagination=meta)

    def update_scorecard(
        self, experiment_id: str, scorecard_data: ScorecardData
    ) -> Experiment | None:
        """
        Update the scorecard data of an experiment.

        Args:
            experiment_id: ID of experiment to update.
            scorecard_data: New scorecard data.

        Returns:
            Updated experiment if found, None otherwise.
        """
        existing = self.get_by_id(experiment_id)
        if existing is None:
            return None

        updated_at = datetime.now(timezone.utc)
        scorecard_json = json.dumps(scorecard_data.model_dump())

        self.db.execute(
            """
            UPDATE experiments
            SET scorecard_data = ?, updated_at = ?
            WHERE id = ?
            """,
            (scorecard_json, updated_at.isoformat(), experiment_id),
        )

        return self.get_by_id(experiment_id)

    def update(
        self,
        experiment_id: str,
        name: str | None = None,
        hypothesis: str | None = None,
        description: str | None = None,
    ) -> Experiment | None:
        """
        Update an experiment.

        Args:
            experiment_id: ID of experiment to update.
            name: New name (optional).
            hypothesis: New hypothesis (optional).
            description: New description (optional).

        Returns:
            Updated experiment if found, None otherwise.
        """
        # First check if experiment exists
        existing = self.get_by_id(experiment_id)
        if existing is None:
            return None

        # Build update fields
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if hypothesis is not None:
            updates.append("hypothesis = ?")
            params.append(hypothesis)
        if description is not None:
            updates.append("description = ?")
            params.append(description)

        # Always set updated_at
        updated_at = datetime.now(timezone.utc)
        updates.append("updated_at = ?")
        params.append(updated_at.isoformat())

        params.append(experiment_id)

        if updates:
            query = f"UPDATE experiments SET {', '.join(updates)} WHERE id = ?"
            self.db.execute(query, tuple(params))

        return self.get_by_id(experiment_id)

    def delete(self, experiment_id: str) -> bool:
        """
        Soft delete an experiment by setting status to 'deleted'.

        The experiment data is preserved but will be hidden from listings.

        Args:
            experiment_id: ID of experiment to delete.

        Returns:
            True if deleted, False if not found.
        """
        # Check if exists and is active
        existing = self.get_by_id(experiment_id)
        if existing is None:
            return False

        updated_at = datetime.now(timezone.utc)
        self.db.execute(
            "UPDATE experiments SET status = 'deleted', updated_at = ? WHERE id = ?",
            (updated_at.isoformat(), experiment_id),
        )
        return True

    def _row_to_experiment(self, row) -> Experiment:
        """Convert a database row to Experiment entity."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = row["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        # Parse scorecard data if present
        scorecard_data = None
        scorecard_json = row["scorecard_data"] if "scorecard_data" in row.keys() else None
        if scorecard_json:
            scorecard_dict = json.loads(scorecard_json)
            scorecard_data = ScorecardData(**scorecard_dict)

        return Experiment(
            id=row["id"],
            name=row["name"],
            hypothesis=row["hypothesis"],
            description=row["description"],
            scorecard_data=scorecard_data,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _row_to_summary(self, row) -> ExperimentSummary:
        """Convert a database row to ExperimentSummary."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = row["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        # Check if scorecard is present
        has_scorecard = False
        if "scorecard_data" in row.keys() and row["scorecard_data"]:
            has_scorecard = True

        return ExperimentSummary(
            id=row["id"],
            name=row["name"],
            hypothesis=row["hypothesis"],
            description=row["description"],
            has_scorecard=has_scorecard,
            has_analysis=bool(row["has_analysis"]) if "has_analysis" in row.keys() else False,
            has_interview_guide=(
                bool(row["has_interview_guide"])
                if "has_interview_guide" in row.keys()
                else False
            ),
            interview_count=row["interview_count"] if "interview_count" in row.keys() else 0,
            created_at=created_at,
            updated_at=updated_at,
        )


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.experiment import (
        Experiment,
        ScorecardData,
        ScorecardDimension,
    )
    from synth_lab.infrastructure.database import init_database

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        repo = ExperimentRepository(db)

        # Test 1: Create experiment
        total_tests += 1
        try:
            exp = Experiment(name="Test", hypothesis="Test hypothesis")
            result = repo.create(exp)
            if result.id != exp.id:
                all_validation_failures.append(f"ID mismatch: {result.id} != {exp.id}")
        except Exception as e:
            all_validation_failures.append(f"Create experiment failed: {e}")

        # Test 2: Get experiment by ID
        total_tests += 1
        try:
            retrieved = repo.get_by_id(exp.id)
            if retrieved is None:
                all_validation_failures.append("Get by ID returned None")
            elif retrieved.name != "Test":
                all_validation_failures.append(f"Name mismatch: {retrieved.name}")
        except Exception as e:
            all_validation_failures.append(f"Get by ID failed: {e}")

        # Test 3: Get non-existent experiment
        total_tests += 1
        try:
            result = repo.get_by_id("exp_nonexist")
            if result is not None:
                all_validation_failures.append("Should return None for non-existent")
        except Exception as e:
            all_validation_failures.append(f"Get non-existent failed: {e}")

        # Test 4: List experiments
        total_tests += 1
        try:
            params = PaginationParams(limit=10, offset=0)
            result = repo.list_experiments(params)
            if len(result.data) != 1:
                all_validation_failures.append(f"Expected 1 experiment, got {len(result.data)}")
        except Exception as e:
            all_validation_failures.append(f"List experiments failed: {e}")

        # Test 5: Update experiment
        total_tests += 1
        try:
            updated = repo.update(exp.id, name="Updated Name")
            if updated is None:
                all_validation_failures.append("Update returned None")
            elif updated.name != "Updated Name":
                all_validation_failures.append(f"Name not updated: {updated.name}")
            elif updated.updated_at is None:
                all_validation_failures.append("updated_at not set")
        except Exception as e:
            all_validation_failures.append(f"Update failed: {e}")

        # Test 6: Create experiment with scorecard
        total_tests += 1
        try:
            scorecard = ScorecardData(
                feature_name="Test Feature",
                description_text="A test feature",
                complexity=ScorecardDimension(score=0.3),
                initial_effort=ScorecardDimension(score=0.4),
                perceived_risk=ScorecardDimension(score=0.2),
                time_to_value=ScorecardDimension(score=0.6),
            )
            exp2 = Experiment(
                name="With Scorecard",
                hypothesis="Has scorecard",
                scorecard_data=scorecard,
            )
            result = repo.create(exp2)
            retrieved = repo.get_by_id(exp2.id)
            if retrieved is None:
                all_validation_failures.append("Experiment with scorecard not found")
            elif not retrieved.has_scorecard():
                all_validation_failures.append("has_scorecard() should be True")
            elif retrieved.scorecard_data.feature_name != "Test Feature":
                all_validation_failures.append("Scorecard feature_name mismatch")
        except Exception as e:
            all_validation_failures.append(f"Create with scorecard failed: {e}")

        # Test 7: Update scorecard
        total_tests += 1
        try:
            new_scorecard = ScorecardData(
                feature_name="Updated Feature",
                description_text="Updated description",
                complexity=ScorecardDimension(score=0.5),
                initial_effort=ScorecardDimension(score=0.5),
                perceived_risk=ScorecardDimension(score=0.5),
                time_to_value=ScorecardDimension(score=0.5),
            )
            updated = repo.update_scorecard(exp.id, new_scorecard)
            if updated is None:
                all_validation_failures.append("Update scorecard returned None")
            elif not updated.has_scorecard():
                all_validation_failures.append("Updated experiment should have scorecard")
            elif updated.scorecard_data.feature_name != "Updated Feature":
                all_validation_failures.append("Scorecard not updated correctly")
        except Exception as e:
            all_validation_failures.append(f"Update scorecard failed: {e}")

        # Test 8: List shows has_scorecard
        total_tests += 1
        try:
            params = PaginationParams(limit=10, offset=0)
            result = repo.list_experiments(params)
            scorecards_found = sum(1 for e in result.data if e.has_scorecard)
            if scorecards_found != 2:
                all_validation_failures.append(
                    f"Expected 2 experiments with scorecard, got {scorecards_found}"
                )
        except Exception as e:
            all_validation_failures.append(f"List with scorecard check failed: {e}")

        # Test 9: Delete experiment
        total_tests += 1
        try:
            result = repo.delete(exp.id)
            if not result:
                all_validation_failures.append("Delete returned False")
            if repo.get_by_id(exp.id) is not None:
                all_validation_failures.append("Experiment still exists after delete")
        except Exception as e:
            all_validation_failures.append(f"Delete failed: {e}")

        db.close()

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
