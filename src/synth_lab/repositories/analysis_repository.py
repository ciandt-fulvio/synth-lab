"""
AnalysisRepository for synth-lab.

Data access layer for analysis runs in SQLite database.
Handles 1:1 relationship with experiments.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - Data model: specs/019-experiment-refactor/data-model.md
"""

import json
from datetime import datetime, timezone

from synth_lab.domain.entities.analysis_run import (
    AggregatedOutcomes,
    AnalysisConfig,
    AnalysisRun,
)
from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.repositories.base import BaseRepository


class AnalysisRepository(BaseRepository):
    """Repository for analysis run data access."""

    def __init__(self, db: DatabaseManager | None = None):
        super().__init__(db)

    def create(self, analysis: AnalysisRun) -> AnalysisRun:
        """
        Create a new analysis run.

        Args:
            analysis: AnalysisRun entity to create.

        Returns:
            Created analysis run.

        Raises:
            sqlite3.IntegrityError: If experiment already has an analysis.
        """
        config_json = json.dumps(analysis.config.model_dump())
        outcomes_json = None
        if analysis.aggregated_outcomes:
            outcomes_json = json.dumps(analysis.aggregated_outcomes.model_dump())

        self.db.execute(
            """
            INSERT INTO analysis_runs (
                id, experiment_id, config, status, started_at, completed_at,
                total_synths, aggregated_outcomes, execution_time_seconds
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis.id,
                analysis.experiment_id,
                config_json,
                analysis.status,
                analysis.started_at.isoformat(),
                analysis.completed_at.isoformat() if analysis.completed_at else None,
                analysis.total_synths,
                outcomes_json,
                analysis.execution_time_seconds,
            ),
        )
        return analysis

    def get_by_id(self, analysis_id: str) -> AnalysisRun | None:
        """
        Get an analysis by ID.

        Args:
            analysis_id: Analysis ID to retrieve.

        Returns:
            AnalysisRun if found, None otherwise.
        """
        row = self.db.fetchone(
            "SELECT * FROM analysis_runs WHERE id = ?",
            (analysis_id,),
        )
        if row is None:
            return None
        return self._row_to_analysis(row)

    def get_by_experiment_id(self, experiment_id: str) -> AnalysisRun | None:
        """
        Get analysis by experiment ID.

        Since it's a 1:1 relationship, returns single analysis or None.

        Args:
            experiment_id: Parent experiment ID.

        Returns:
            AnalysisRun if found, None otherwise.
        """
        row = self.db.fetchone(
            "SELECT * FROM analysis_runs WHERE experiment_id = ?",
            (experiment_id,),
        )
        if row is None:
            return None
        return self._row_to_analysis(row)

    def update_status(
        self,
        analysis_id: str,
        status: str,
        completed_at: datetime | None = None,
        total_synths: int | None = None,
        aggregated_outcomes: AggregatedOutcomes | None = None,
        execution_time_seconds: float | None = None,
    ) -> AnalysisRun | None:
        """
        Update analysis status and results.

        Args:
            analysis_id: ID of analysis to update.
            status: New status.
            completed_at: Completion timestamp.
            total_synths: Total synths processed.
            aggregated_outcomes: Aggregated results.
            execution_time_seconds: Execution time.

        Returns:
            Updated analysis if found, None otherwise.
        """
        existing = self.get_by_id(analysis_id)
        if existing is None:
            return None

        updates = ["status = ?"]
        params = [status]

        if completed_at is not None:
            updates.append("completed_at = ?")
            params.append(completed_at.isoformat())

        if total_synths is not None:
            updates.append("total_synths = ?")
            params.append(total_synths)

        if aggregated_outcomes is not None:
            updates.append("aggregated_outcomes = ?")
            params.append(json.dumps(aggregated_outcomes.model_dump()))

        if execution_time_seconds is not None:
            updates.append("execution_time_seconds = ?")
            params.append(execution_time_seconds)

        params.append(analysis_id)
        query = f"UPDATE analysis_runs SET {', '.join(updates)} WHERE id = ?"
        self.db.execute(query, tuple(params))

        return self.get_by_id(analysis_id)

    def delete(self, analysis_id: str) -> bool:
        """
        Delete an analysis run.

        Args:
            analysis_id: ID of analysis to delete.

        Returns:
            True if deleted, False if not found.
        """
        existing = self.get_by_id(analysis_id)
        if existing is None:
            return False

        self.db.execute("DELETE FROM analysis_runs WHERE id = ?", (analysis_id,))
        return True

    def delete_by_experiment_id(self, experiment_id: str) -> bool:
        """
        Delete analysis by experiment ID.

        Args:
            experiment_id: Parent experiment ID.

        Returns:
            True if deleted, False if not found.
        """
        existing = self.get_by_experiment_id(experiment_id)
        if existing is None:
            return False

        self.db.execute(
            "DELETE FROM analysis_runs WHERE experiment_id = ?",
            (experiment_id,),
        )
        return True

    def _row_to_analysis(self, row) -> AnalysisRun:
        """Convert a database row to AnalysisRun entity."""
        started_at = row["started_at"]
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = row["completed_at"]
        if completed_at and isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        config_dict = json.loads(row["config"])
        config = AnalysisConfig(**config_dict)

        aggregated_outcomes = None
        if row["aggregated_outcomes"]:
            outcomes_dict = json.loads(row["aggregated_outcomes"])
            aggregated_outcomes = AggregatedOutcomes(**outcomes_dict)

        return AnalysisRun(
            id=row["id"],
            experiment_id=row["experiment_id"],
            config=config,
            status=row["status"],
            started_at=started_at,
            completed_at=completed_at,
            total_synths=row["total_synths"],
            aggregated_outcomes=aggregated_outcomes,
            execution_time_seconds=row["execution_time_seconds"],
        )


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.analysis_run import AnalysisRun
    from synth_lab.domain.entities.experiment import Experiment
    from synth_lab.infrastructure.database import init_database
    from synth_lab.repositories.experiment_repository import ExperimentRepository

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        exp_repo = ExperimentRepository(db)
        ana_repo = AnalysisRepository(db)

        # Create parent experiment
        exp = Experiment(name="Test", hypothesis="Test hypothesis")
        exp_repo.create(exp)

        # Test 1: Create analysis
        total_tests += 1
        try:
            analysis = AnalysisRun(
                experiment_id=exp.id,
                config=AnalysisConfig(n_synths=100, n_executions=50),
            )
            result = ana_repo.create(analysis)
            if result.id != analysis.id:
                all_validation_failures.append(f"ID mismatch: {result.id}")
        except Exception as e:
            all_validation_failures.append(f"Create analysis failed: {e}")

        # Test 2: Get analysis by ID
        total_tests += 1
        try:
            retrieved = ana_repo.get_by_id(analysis.id)
            if retrieved is None:
                all_validation_failures.append("Get by ID returned None")
            elif retrieved.config.n_synths != 100:
                all_validation_failures.append(f"n_synths mismatch: {retrieved.config.n_synths}")
        except Exception as e:
            all_validation_failures.append(f"Get by ID failed: {e}")

        # Test 3: Get analysis by experiment ID
        total_tests += 1
        try:
            retrieved = ana_repo.get_by_experiment_id(exp.id)
            if retrieved is None:
                all_validation_failures.append("Get by experiment_id returned None")
            elif retrieved.id != analysis.id:
                all_validation_failures.append("Wrong analysis returned")
        except Exception as e:
            all_validation_failures.append(f"Get by experiment_id failed: {e}")

        # Test 4: Update status with outcomes
        total_tests += 1
        try:
            outcomes = AggregatedOutcomes(
                did_not_try_rate=0.2,
                failed_rate=0.3,
                success_rate=0.5,
            )
            updated = ana_repo.update_status(
                analysis.id,
                status="completed",
                completed_at=datetime.now(timezone.utc),
                total_synths=100,
                aggregated_outcomes=outcomes,
                execution_time_seconds=5.5,
            )
            if updated is None:
                all_validation_failures.append("Update returned None")
            elif updated.status != "completed":
                all_validation_failures.append(f"Status not updated: {updated.status}")
            elif not updated.has_results():
                all_validation_failures.append("Should have results")
            elif updated.aggregated_outcomes.success_rate != 0.5:
                all_validation_failures.append("success_rate mismatch")
        except Exception as e:
            all_validation_failures.append(f"Update status failed: {e}")

        # Test 5: 1:1 constraint - try to create second analysis for same experiment
        total_tests += 1
        try:
            second_analysis = AnalysisRun(experiment_id=exp.id)
            ana_repo.create(second_analysis)
            all_validation_failures.append("Should reject second analysis for same experiment")
        except Exception:
            pass  # Expected - UNIQUE constraint violation

        # Test 6: Delete analysis
        total_tests += 1
        try:
            result = ana_repo.delete(analysis.id)
            if not result:
                all_validation_failures.append("Delete returned False")
            if ana_repo.get_by_id(analysis.id) is not None:
                all_validation_failures.append("Analysis still exists after delete")
        except Exception as e:
            all_validation_failures.append(f"Delete failed: {e}")

        # Test 7: Delete by experiment ID
        total_tests += 1
        try:
            # Create a new analysis first
            new_analysis = AnalysisRun(experiment_id=exp.id)
            ana_repo.create(new_analysis)

            result = ana_repo.delete_by_experiment_id(exp.id)
            if not result:
                all_validation_failures.append("Delete by experiment_id returned False")
            if ana_repo.get_by_experiment_id(exp.id) is not None:
                all_validation_failures.append("Analysis still exists after delete by exp")
        except Exception as e:
            all_validation_failures.append(f"Delete by experiment_id failed: {e}")

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
