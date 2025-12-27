"""
T012 ExperimentRepository for synth-lab.

Data access layer for experiment data in SQLite database.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - Data model: specs/018-experiment-hub/data-model.md
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from synth_lab.domain.entities.experiment import Experiment
from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.models.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from synth_lab.repositories.base import BaseRepository


class ExperimentSummary(BaseModel):
    """Summary of an experiment for list display."""

    id: str = Field(description="Experiment ID.")
    name: str = Field(description="Short name of the feature.")
    hypothesis: str = Field(description="Hypothesis description.")
    description: str | None = Field(default=None, description="Additional context.")
    simulation_count: int = Field(default=0, description="Number of linked simulations.")
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
        self.db.execute(
            """
            INSERT INTO experiments (id, name, hypothesis, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                experiment.id,
                experiment.name,
                experiment.hypothesis,
                experiment.description,
                experiment.created_at.isoformat(),
                experiment.updated_at.isoformat() if experiment.updated_at else None,
            ),
        )
        return experiment

    def get_by_id(self, experiment_id: str) -> Experiment | None:
        """
        Get an experiment by ID.

        Args:
            experiment_id: Experiment ID to retrieve.

        Returns:
            Experiment if found, None otherwise.
        """
        row = self.db.fetchone(
            "SELECT * FROM experiments WHERE id = ?",
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

        Args:
            params: Pagination parameters.

        Returns:
            Paginated response with experiment summaries.
        """
        # Query with simulation and interview counts
        base_query = """
            SELECT
                e.id,
                e.name,
                e.hypothesis,
                e.description,
                e.created_at,
                e.updated_at,
                COALESCE(sim.cnt, 0) as simulation_count,
                COALESCE(int.cnt, 0) as interview_count
            FROM experiments e
            LEFT JOIN (
                SELECT experiment_id, COUNT(*) as cnt
                FROM feature_scorecards
                WHERE experiment_id IS NOT NULL
                GROUP BY experiment_id
            ) sim ON e.id = sim.experiment_id
            LEFT JOIN (
                SELECT experiment_id, COUNT(*) as cnt
                FROM research_executions
                WHERE experiment_id IS NOT NULL
                GROUP BY experiment_id
            ) int ON e.id = int.experiment_id
            ORDER BY e.created_at DESC
        """

        count_query = "SELECT COUNT(*) as count FROM experiments"

        # Get total count
        count_row = self.db.fetchone(count_query)
        total = count_row["count"] if count_row else 0

        # Apply pagination
        paginated_query = f"{base_query} LIMIT ? OFFSET ?"
        rows = self.db.fetchall(paginated_query, (params.limit, params.offset))

        summaries = [self._row_to_summary(row) for row in rows]
        meta = PaginationMeta.from_params(total, params)

        return PaginatedResponse(data=summaries, pagination=meta)

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
        Delete an experiment.

        Args:
            experiment_id: ID of experiment to delete.

        Returns:
            True if deleted, False if not found.
        """
        # Check if exists
        existing = self.get_by_id(experiment_id)
        if existing is None:
            return False

        self.db.execute("DELETE FROM experiments WHERE id = ?", (experiment_id,))
        return True

    def _row_to_experiment(self, row) -> Experiment:
        """Convert a database row to Experiment entity."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = row["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return Experiment(
            id=row["id"],
            name=row["name"],
            hypothesis=row["hypothesis"],
            description=row["description"],
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

        return ExperimentSummary(
            id=row["id"],
            name=row["name"],
            hypothesis=row["hypothesis"],
            description=row["description"],
            simulation_count=row["simulation_count"] if "simulation_count" in row.keys() else 0,
            interview_count=row["interview_count"] if "interview_count" in row.keys() else 0,
            created_at=created_at,
            updated_at=updated_at,
        )


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.experiment import Experiment

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
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

        # Test 6: Delete experiment
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
