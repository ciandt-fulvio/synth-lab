"""
Simulation repository for synth-lab.

Provides data access layer for simulation runs and outcomes with SQLite persistence.

Functions:
- create_simulation_run(): Create a new simulation run
- update_simulation_run(): Update simulation run status/results
- get_simulation_run(): Get simulation run by ID
- list_simulation_runs(): List simulation runs with filters
- save_synth_outcomes(): Save simulation outcomes for synths
- get_synth_outcomes(): Get outcomes for a simulation

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Database: src/synth_lab/infrastructure/database.py

Sample usage:
    from synth_lab.repositories.simulation_repository import SimulationRepository

    repo = SimulationRepository(db)
    run_id = repo.create_simulation_run(simulation_run)
    outcomes = repo.get_synth_outcomes(run_id)
"""

import json
from datetime import datetime, timezone
from typing import Any

from loguru import logger

from synth_lab.domain.entities import SimulationConfig, SimulationRun, SynthOutcome
from synth_lab.infrastructure.database import DatabaseManager


class SimulationRepository:
    """Repository for simulation run and outcome persistence."""

    def __init__(self, db: DatabaseManager) -> None:
        """
        Initialize repository with database manager.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.logger = logger.bind(component="simulation_repository")

    def create_simulation_run(self, run: SimulationRun) -> str:
        """
        Create a new simulation run in the database.

        Args:
            run: SimulationRun instance to persist

        Returns:
            str: Created simulation run ID
        """
        config_json = run.config.model_dump(mode="json")
        aggregated_json = (
            json.dumps(run.aggregated_outcomes) if run.aggregated_outcomes else None
        )

        sql = """
            INSERT INTO simulation_runs (
                id, scorecard_id, scenario_id, config, status,
                started_at, completed_at, total_synths,
                aggregated_outcomes, execution_time_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            run.id,
            run.scorecard_id,
            run.scenario_id,
            json.dumps(config_json),
            run.status,
            run.started_at.isoformat() if run.started_at else None,
            run.completed_at.isoformat() if run.completed_at else None,
            run.total_synths,
            aggregated_json,
            run.execution_time_seconds,
        )

        with self.db.transaction() as conn:
            conn.execute(sql, params)

        self.logger.info(f"Created simulation run {run.id}")
        return run.id

    def update_simulation_run(self, run: SimulationRun) -> bool:
        """
        Update an existing simulation run.

        Args:
            run: SimulationRun with updated data

        Returns:
            bool: True if updated, False if not found
        """
        aggregated_json = (
            json.dumps(run.aggregated_outcomes) if run.aggregated_outcomes else None
        )

        sql = """
            UPDATE simulation_runs
            SET status = ?,
                completed_at = ?,
                total_synths = ?,
                aggregated_outcomes = ?,
                execution_time_seconds = ?
            WHERE id = ?
        """

        params = (
            run.status,
            run.completed_at.isoformat() if run.completed_at else None,
            run.total_synths,
            aggregated_json,
            run.execution_time_seconds,
            run.id,
        )

        with self.db.transaction() as conn:
            cursor = conn.execute(sql, params)
            updated = cursor.rowcount > 0

        if updated:
            self.logger.info(f"Updated simulation run {run.id}")
        else:
            self.logger.warning(f"Simulation run {run.id} not found for update")

        return updated

    def get_simulation_run(self, run_id: str) -> SimulationRun | None:
        """
        Get a simulation run by ID.

        Args:
            run_id: Simulation run ID to retrieve

        Returns:
            SimulationRun if found, None otherwise
        """
        sql = """
            SELECT id, scorecard_id, scenario_id, config, status,
                   started_at, completed_at, total_synths,
                   aggregated_outcomes, execution_time_seconds
            FROM simulation_runs
            WHERE id = ?
        """
        row = self.db.fetchone(sql, (run_id,))

        if row is None:
            return None

        return self._row_to_simulation_run(row)

    def list_simulation_runs(
        self,
        scorecard_id: str | None = None,
        scenario_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[SimulationRun], int]:
        """
        List simulation runs with optional filters.

        Args:
            scorecard_id: Filter by scorecard
            scenario_id: Filter by scenario
            status: Filter by status
            limit: Maximum results
            offset: Results to skip

        Returns:
            Tuple of (list of runs, total count)
        """
        # Build WHERE clause
        conditions = []
        params: list[Any] = []

        if scorecard_id:
            conditions.append("scorecard_id = ?")
            params.append(scorecard_id)
        if scenario_id:
            conditions.append("scenario_id = ?")
            params.append(scenario_id)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Count total
        count_sql = f"SELECT COUNT(*) as count FROM simulation_runs WHERE {where_clause}"
        count_row = self.db.fetchone(count_sql, tuple(params))
        total = count_row["count"] if count_row else 0

        # Get paginated results
        list_sql = f"""
            SELECT id, scorecard_id, scenario_id, config, status,
                   started_at, completed_at, total_synths,
                   aggregated_outcomes, execution_time_seconds
            FROM simulation_runs
            WHERE {where_clause}
            ORDER BY started_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        rows = self.db.fetchall(list_sql, tuple(params))

        runs = [self._row_to_simulation_run(row) for row in rows]
        return runs, total

    def save_synth_outcomes(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome],
    ) -> int:
        """
        Save synth outcomes for a simulation.

        Args:
            simulation_id: Simulation run ID
            outcomes: List of SynthOutcome to save

        Returns:
            int: Number of outcomes saved
        """
        sql = """
            INSERT INTO synth_outcomes (
                simulation_id, synth_id,
                did_not_try_rate, failed_rate, success_rate,
                synth_attributes
            ) VALUES (?, ?, ?, ?, ?, ?)
        """

        params_list = [
            (
                simulation_id,
                outcome.synth_id,
                outcome.did_not_try_rate,
                outcome.failed_rate,
                outcome.success_rate,
                json.dumps(outcome.synth_attributes.model_dump()) if outcome.synth_attributes else None,
            )
            for outcome in outcomes
        ]

        with self.db.transaction() as conn:
            conn.executemany(sql, params_list)

        self.logger.info(f"Saved {len(outcomes)} outcomes for simulation {simulation_id}")
        return len(outcomes)

    def get_synth_outcomes(
        self,
        simulation_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SynthOutcome], int]:
        """
        Get synth outcomes for a simulation.

        Args:
            simulation_id: Simulation run ID
            limit: Maximum results
            offset: Results to skip

        Returns:
            Tuple of (list of outcomes, total count)
        """
        # Count total
        count_sql = """
            SELECT COUNT(*) as count FROM synth_outcomes
            WHERE simulation_id = ?
        """
        count_row = self.db.fetchone(count_sql, (simulation_id,))
        total = count_row["count"] if count_row else 0

        # Get paginated results
        list_sql = """
            SELECT synth_id, did_not_try_rate, failed_rate, success_rate, synth_attributes
            FROM synth_outcomes
            WHERE simulation_id = ?
            ORDER BY synth_id
            LIMIT ? OFFSET ?
        """
        rows = self.db.fetchall(list_sql, (simulation_id, limit, offset))

        outcomes = []
        for row in rows:
            attrs_dict = json.loads(row["synth_attributes"]) if row["synth_attributes"] else None
            # Convert dict to SimulationAttributes if present
            from synth_lab.domain.entities.simulation_attributes import SimulationAttributes
            attrs = SimulationAttributes.model_validate(attrs_dict) if attrs_dict else None
            outcomes.append(
                SynthOutcome(
                    simulation_id=simulation_id,
                    synth_id=row["synth_id"],
                    did_not_try_rate=row["did_not_try_rate"],
                    failed_rate=row["failed_rate"],
                    success_rate=row["success_rate"],
                    synth_attributes=attrs,
                )
            )

        return outcomes, total

    def list_by_experiment_id(
        self,
        experiment_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[SimulationRun], int]:
        """
        List simulation runs for a specific experiment (via scorecards).

        Args:
            experiment_id: Experiment ID to filter by
            limit: Maximum results
            offset: Results to skip

        Returns:
            Tuple of (list of runs, total count)
        """
        # Count total - join with feature_scorecards to filter by experiment
        count_sql = """
            SELECT COUNT(*) as count
            FROM simulation_runs sr
            JOIN feature_scorecards fs ON sr.scorecard_id = fs.id
            WHERE fs.experiment_id = ?
        """
        count_row = self.db.fetchone(count_sql, (experiment_id,))
        total = count_row["count"] if count_row else 0

        # Get paginated results
        list_sql = """
            SELECT sr.id, sr.scorecard_id, sr.scenario_id, sr.config, sr.status,
                   sr.started_at, sr.completed_at, sr.total_synths,
                   sr.aggregated_outcomes, sr.execution_time_seconds
            FROM simulation_runs sr
            JOIN feature_scorecards fs ON sr.scorecard_id = fs.id
            WHERE fs.experiment_id = ?
            ORDER BY sr.started_at DESC
            LIMIT ? OFFSET ?
        """
        rows = self.db.fetchall(list_sql, (experiment_id, limit, offset))

        runs = [self._row_to_simulation_run(row) for row in rows]
        return runs, total

    def _row_to_simulation_run(self, row: Any) -> SimulationRun:
        """Convert a database row to SimulationRun."""
        config = SimulationConfig.model_validate(json.loads(row["config"]))
        aggregated = (
            json.loads(row["aggregated_outcomes"])
            if row["aggregated_outcomes"]
            else None
        )

        return SimulationRun(
            id=row["id"],
            scorecard_id=row["scorecard_id"],
            scenario_id=row["scenario_id"],
            config=config,
            status=row["status"],
            started_at=(
                datetime.fromisoformat(row["started_at"])
                if row["started_at"]
                else None
            ),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
            total_synths=row["total_synths"],
            aggregated_outcomes=aggregated,
            execution_time_seconds=row["execution_time_seconds"],
        )


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities import (
        FeatureScorecard,
        ScorecardDimension,
        ScorecardIdentification,
    )
    from synth_lab.domain.entities.simulation_attributes import (
        SimulationAttributes,
        SimulationLatentTraits,
        SimulationObservables,
    )
    from synth_lab.infrastructure.database import init_database
    from synth_lab.repositories.scorecard_repository import ScorecardRepository

    print("=== Simulation Repository Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Use temp database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_database(db_path)
        db = DatabaseManager(db_path)
        repo = SimulationRepository(db)

        # Create test scorecard first (to satisfy foreign key constraint)
        scorecard_repo = ScorecardRepository(db)
        test_scorecard = FeatureScorecard(
            id="testsc01",  # Must be 8 alphanumeric chars
            identification=ScorecardIdentification(
                feature_name="Test Feature",
                use_scenario="Testing simulation repository",
            ),
            description_text="A test scorecard for validation",
            complexity=ScorecardDimension(score=0.5),
            initial_effort=ScorecardDimension(score=0.4),
            perceived_risk=ScorecardDimension(score=0.3),
            time_to_value=ScorecardDimension(score=0.6),
        )
        scorecard_repo.create_scorecard(test_scorecard)

        # Create test simulation run
        test_config = SimulationConfig(
            n_executions=100,
            sigma=0.1,
            seed=42,
        )
        test_run = SimulationRun(
            scorecard_id="testsc01",
            scenario_id="baseline",
            config=test_config,
            status="running",
            total_synths=10,
        )

        # Test 1: Create simulation run
        total_tests += 1
        try:
            run_id = repo.create_simulation_run(test_run)
            if run_id != test_run.id:
                all_validation_failures.append(
                    f"Create: ID mismatch {run_id} != {test_run.id}"
                )
            else:
                print(f"Test 1 PASSED: Created simulation run {run_id}")
        except Exception as e:
            all_validation_failures.append(f"Create failed: {e}")

        # Test 2: Get simulation run
        total_tests += 1
        try:
            retrieved = repo.get_simulation_run(test_run.id)
            if retrieved is None:
                all_validation_failures.append("Get: Simulation run not found")
            elif retrieved.scorecard_id != "testsc01":
                all_validation_failures.append(
                    f"Get: Scorecard ID mismatch: {retrieved.scorecard_id}"
                )
            else:
                print(f"Test 2 PASSED: Retrieved simulation run {retrieved.id}")
        except Exception as e:
            all_validation_failures.append(f"Get failed: {e}")

        # Test 3: Update simulation run
        total_tests += 1
        try:
            test_run.status = "completed"
            test_run.completed_at = datetime.now(timezone.utc)
            test_run.aggregated_outcomes = {
                "did_not_try": 0.3,
                "failed": 0.2,
                "success": 0.5,
            }
            test_run.execution_time_seconds = 0.15

            updated = repo.update_simulation_run(test_run)
            if not updated:
                all_validation_failures.append("Update: Should return True")
            else:
                # Verify update
                retrieved = repo.get_simulation_run(test_run.id)
                if retrieved.status != "completed":
                    all_validation_failures.append(
                        f"Update: Status not updated: {retrieved.status}"
                    )
                else:
                    print("Test 3 PASSED: Updated simulation run")
        except Exception as e:
            all_validation_failures.append(f"Update failed: {e}")

        # Test 4: Save synth outcomes
        total_tests += 1
        try:
            # Create proper SimulationAttributes for each outcome
            sample_attrs = SimulationAttributes(
                observables=SimulationObservables(
                    digital_literacy=0.5,
                    similar_tool_experience=0.5,
                    motor_ability=1.0,
                    time_availability=0.5,
                    domain_expertise=0.5,
                ),
                latent_traits=SimulationLatentTraits(
                    capability_mean=0.5,
                    trust_mean=0.5,
                    friction_tolerance_mean=0.5,
                    exploration_prob=0.5,
                ),
            )
            test_outcomes = [
                SynthOutcome(
                    simulation_id=test_run.id,
                    synth_id=f"synth_{i}",
                    did_not_try_rate=0.3,
                    failed_rate=0.2,
                    success_rate=0.5,
                    synth_attributes=sample_attrs,
                )
                for i in range(5)
            ]

            count = repo.save_synth_outcomes(test_run.id, test_outcomes)
            if count != 5:
                all_validation_failures.append(f"Save outcomes: Expected 5, got {count}")
            else:
                print("Test 4 PASSED: Saved 5 synth outcomes")
        except Exception as e:
            all_validation_failures.append(f"Save outcomes failed: {e}")

        # Test 5: Get synth outcomes
        total_tests += 1
        try:
            outcomes, total = repo.get_synth_outcomes(test_run.id)
            if total != 5:
                all_validation_failures.append(
                    f"Get outcomes: Expected total=5, got {total}"
                )
            elif len(outcomes) != 5:
                all_validation_failures.append(
                    f"Get outcomes: Expected 5 outcomes, got {len(outcomes)}"
                )
            else:
                print(f"Test 5 PASSED: Retrieved {len(outcomes)} synth outcomes")
        except Exception as e:
            all_validation_failures.append(f"Get outcomes failed: {e}")

        # Test 6: List simulation runs
        total_tests += 1
        try:
            runs, total = repo.list_simulation_runs()
            if total != 1:
                all_validation_failures.append(
                    f"List: Expected total=1, got {total}"
                )
            elif len(runs) != 1:
                all_validation_failures.append(
                    f"List: Expected 1 run, got {len(runs)}"
                )
            else:
                print(f"Test 6 PASSED: Listed {len(runs)} simulation runs")
        except Exception as e:
            all_validation_failures.append(f"List failed: {e}")

        # Test 7: List with filter
        total_tests += 1
        try:
            runs, total = repo.list_simulation_runs(scenario_id="nonexistent")
            if total != 0:
                all_validation_failures.append(
                    f"List filter: Expected total=0, got {total}"
                )
            else:
                print("Test 7 PASSED: List filter returns 0 for non-matching")
        except Exception as e:
            all_validation_failures.append(f"List filter failed: {e}")

        # Test 8: Get non-existent run
        total_tests += 1
        try:
            result = repo.get_simulation_run("nonexistent")
            if result is not None:
                all_validation_failures.append("Get non-existent: Should return None")
            else:
                print("Test 8 PASSED: Non-existent run returns None")
        except Exception as e:
            all_validation_failures.append(f"Get non-existent failed: {e}")

        db.close()

    # Final result
    print()
    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
