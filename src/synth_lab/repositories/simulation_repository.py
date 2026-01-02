"""
Simulation repository for synth-lab.

Provides data access layer for simulation runs and outcomes with SQLite persistence.
Uses SQLAlchemy ORM for database operations.

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
    - ORM models: synth_lab.models.orm.legacy

Sample usage:
    from synth_lab.repositories.simulation_repository import SimulationRepository

    # ORM mode
    repo = SimulationRepository(db=database_manager)

    # ORM mode (SQLAlchemy)
    repo = SimulationRepository(session=session)

    run_id = repo.create_simulation_run(simulation_run)
    outcomes = repo.get_synth_outcomes(run_id)
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from sqlalchemy import func as sqlfunc
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities import SimulationConfig, SimulationRun, SynthOutcome
from synth_lab.models.orm.analysis import SynthOutcome as SynthOutcomeORM
from synth_lab.models.orm.legacy import SimulationRun as SimulationRunORM
from synth_lab.repositories.base import BaseRepository


class SimulationRepository(BaseRepository):
    """Repository for simulation run and outcome persistence.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # ORM mode
        repo = SimulationRepository(db=database_manager)

        # ORM mode (SQLAlchemy)
        repo = SimulationRepository(session=session)
    """

    def __init__(
        self,
session: Session | None = None) -> None:
        """
        Initialize repository with database manager or SQLAlchemy session.

        Args:
            db: Legacy database manager instance
            session: SQLAlchemy session for ORM operations
        """
        super().__init__( session=session)
        self.logger = logger.bind(component="simulation_repository")

    def create_simulation_run(self, run: SimulationRun) -> str:
        """
        Create a new simulation run in the database.

        Args:
            run: SimulationRun instance to persist

        Returns:
            str: Created simulation run ID
        """
        return self._create_simulation_run_orm(run)

    def _create_simulation_run_orm(self, run: SimulationRun) -> str:
        """Create simulation run using ORM."""
        default_started = datetime.now(timezone.utc).isoformat()
        orm_run = SimulationRunORM(
            id=run.id,
            scorecard_id=run.scorecard_id,
            scenario_id=run.scenario_id,
            config=run.config.model_dump(mode="json"),
            status=run.status,
            started_at=run.started_at.isoformat() if run.started_at else default_started,
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
            total_synths=run.total_synths,
            aggregated_outcomes=run.aggregated_outcomes,
            execution_time_seconds=run.execution_time_seconds)
        self._add(orm_run)
        self._flush()
        self._commit()
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
        return self._update_simulation_run_orm(run)

    def _update_simulation_run_orm(self, run: SimulationRun) -> bool:
        """Update simulation run using ORM."""
        stmt = select(SimulationRunORM).where(SimulationRunORM.id == run.id)
        orm_run = self.session.execute(stmt).scalar_one_or_none()
        if orm_run is None:
            self.logger.warning(f"Simulation run {run.id} not found for update")
            return False

        orm_run.status = run.status
        orm_run.completed_at = run.completed_at.isoformat() if run.completed_at else None
        orm_run.total_synths = run.total_synths
        orm_run.aggregated_outcomes = run.aggregated_outcomes
        orm_run.execution_time_seconds = run.execution_time_seconds
        self._flush()
        self._commit()

        self.logger.info(f"Updated simulation run {run.id}")
        return True

    def get_simulation_run(self, run_id: str) -> SimulationRun | None:
        """
        Get a simulation run by ID.

        Args:
            run_id: Simulation run ID to retrieve

        Returns:
            SimulationRun if found, None otherwise
        """
        return self._get_simulation_run_orm(run_id)

    def _get_simulation_run_orm(self, run_id: str) -> SimulationRun | None:
        """Get simulation run by ID using ORM."""
        stmt = select(SimulationRunORM).where(SimulationRunORM.id == run_id)
        orm_run = self.session.execute(stmt).scalar_one_or_none()
        if orm_run is None:
            return None
        return self._orm_to_simulation_run(orm_run)

    def list_simulation_runs(
        self,
        scorecard_id: str | None = None,
        scenario_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0) -> tuple[list[SimulationRun], int]:
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
        return self._list_simulation_runs_orm(
                scorecard_id=scorecard_id,
                scenario_id=scenario_id,
                status=status,
                limit=limit,
                offset=offset)

    def _list_simulation_runs_orm(
        self,
        scorecard_id: str | None = None,
        scenario_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0) -> tuple[list[SimulationRun], int]:
        """List simulation runs using ORM."""
        # Build query with filters
        stmt = select(SimulationRunORM)

        if scorecard_id:
            stmt = stmt.where(SimulationRunORM.scorecard_id == scorecard_id)
        if scenario_id:
            stmt = stmt.where(SimulationRunORM.scenario_id == scenario_id)
        if status:
            stmt = stmt.where(SimulationRunORM.status == status)

        # Get total count
        count_stmt = select(sqlfunc.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar() or 0

        # Apply ordering and pagination
        stmt = stmt.order_by(SimulationRunORM.started_at.desc())
        stmt = stmt.limit(limit).offset(offset)
        orm_runs = list(self.session.execute(stmt).scalars().all())

        runs = [self._orm_to_simulation_run(orm_run) for orm_run in orm_runs]
        return runs, total

    def save_synth_outcomes(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome]) -> int:
        """
        Save synth outcomes for a simulation.

        Args:
            simulation_id: Simulation run ID
            outcomes: List of SynthOutcome to save

        Returns:
            int: Number of outcomes saved
        """
        return self._save_synth_outcomes_orm(simulation_id, outcomes)

    def _save_synth_outcomes_orm(
        self,
        simulation_id: str,
        outcomes: list[SynthOutcome]) -> int:
        """Save synth outcomes using ORM."""
        # Convert simulation_id to analysis_id format (sim_ -> ana_)
        analysis_id = simulation_id.replace("sim_", "ana_")

        # Ensure analysis_runs entry exists for foreign key constraint
        self._ensure_analysis_run_exists_orm(simulation_id, analysis_id)

        for outcome in outcomes:
            orm_outcome = SynthOutcomeORM(
                id=f"out_{uuid.uuid4().hex[:12]}",
                analysis_id=analysis_id,
                synth_id=outcome.synth_id,
                did_not_try_rate=outcome.did_not_try_rate,
                failed_rate=outcome.failed_rate,
                success_rate=outcome.success_rate,
                synth_attributes=(
                    outcome.synth_attributes.model_dump()
                    if outcome.synth_attributes
                    else None
                ))
            self._add(orm_outcome)

        self._flush()
        self._commit()
        self.logger.info(f"Saved {len(outcomes)} outcomes for simulation {simulation_id}")
        return len(outcomes)

    def _ensure_analysis_run_exists_orm(self, simulation_id: str, analysis_id: str) -> None:
        """
        Ensure an analysis_runs entry exists for the given simulation using ORM.

        This is needed because synth_outcomes has a foreign key to analysis_runs.
        Creates a shadow entry in analysis_runs if it doesn't exist.

        Args:
            simulation_id: Original simulation run ID
            analysis_id: Converted analysis ID (ana_* format)
        """
        from synth_lab.models.orm.analysis import AnalysisRun as AnalysisRunORM
        from synth_lab.models.orm.experiment import Experiment as ExperimentORM

        # Check if analysis_runs entry already exists
        stmt = select(AnalysisRunORM).where(AnalysisRunORM.id == analysis_id)
        existing = self.session.execute(stmt).scalar_one_or_none()
        if existing:
            return

        # Get simulation run details to create matching analysis_runs entry
        sim_run = self._get_simulation_run_orm(simulation_id)
        if not sim_run:
            self.logger.warning(f"Simulation run not found: {simulation_id}")
            return

        # Create a placeholder experiment if needed
        exp_id = f"exp_{simulation_id[4:]}"  # sim_xxxx -> exp_xxxx
        exp_stmt = select(ExperimentORM).where(ExperimentORM.id == exp_id)
        exp_check = self.session.execute(exp_stmt).scalar_one_or_none()
        if not exp_check:
            orm_exp = ExperimentORM(
                id=exp_id,
                name=f"Simulation {simulation_id}",
                hypothesis="Auto-generated from simulation",
                status="active",
                created_at=datetime.now(timezone.utc).isoformat())
            self._add(orm_exp)
            self._flush()
            self._commit()

        # Create analysis_runs entry
        default_started = datetime.now(timezone.utc).isoformat()
        orm_analysis = AnalysisRunORM(
            id=analysis_id,
            experiment_id=exp_id,
            scenario_id=sim_run.scenario_id,
            config=sim_run.config.model_dump() if sim_run.config else {},
            status=sim_run.status,
            started_at=(
                sim_run.started_at.isoformat() if sim_run.started_at else default_started
            ),
            completed_at=sim_run.completed_at.isoformat() if sim_run.completed_at else None,
            total_synths=sim_run.total_synths)
        self._add(orm_analysis)
        self._flush()
        self._commit()

    def get_synth_outcomes(
        self,
        simulation_id: str,
        limit: int = 100,
        offset: int = 0) -> tuple[list[SynthOutcome], int]:
        """
        Get synth outcomes for a simulation.

        Args:
            simulation_id: Simulation run ID
            limit: Maximum results
            offset: Results to skip

        Returns:
            Tuple of (list of outcomes, total count)
        """
        return self._get_synth_outcomes_orm(simulation_id, limit, offset)

    def _get_synth_outcomes_orm(
        self,
        simulation_id: str,
        limit: int = 100,
        offset: int = 0) -> tuple[list[SynthOutcome], int]:
        """Get synth outcomes using ORM."""
        # Convert simulation_id to analysis_id format (sim_ -> ana_)
        analysis_id = simulation_id.replace("sim_", "ana_")

        # Build query
        stmt = select(SynthOutcomeORM).where(SynthOutcomeORM.analysis_id == analysis_id)

        # Get total count
        count_stmt = select(sqlfunc.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar() or 0

        # Apply ordering and pagination
        stmt = stmt.order_by(SynthOutcomeORM.synth_id)
        stmt = stmt.limit(limit).offset(offset)
        orm_outcomes = list(self.session.execute(stmt).scalars().all())

        outcomes = [
            self._orm_to_synth_outcome(orm_outcome, analysis_id)
            for orm_outcome in orm_outcomes
        ]
        return outcomes, total

    def list_by_experiment_id(
        self,
        experiment_id: str,
        limit: int = 20,
        offset: int = 0) -> tuple[list[SimulationRun], int]:
        """
        List simulation runs for a specific experiment (via scorecards).

        Args:
            experiment_id: Experiment ID to filter by
            limit: Maximum results
            offset: Results to skip

        Returns:
            Tuple of (list of runs, total count)
        """
        return self._list_by_experiment_id_orm(experiment_id, limit, offset)

    def _list_by_experiment_id_orm(
        self,
        experiment_id: str,
        limit: int = 20,
        offset: int = 0) -> tuple[list[SimulationRun], int]:
        """List simulation runs by experiment ID using ORM."""
        from synth_lab.models.orm.legacy import FeatureScorecard as FeatureScorecardORM

        # Build query with join
        stmt = (
            select(SimulationRunORM)
            .join(FeatureScorecardORM, SimulationRunORM.scorecard_id == FeatureScorecardORM.id)
            .where(FeatureScorecardORM.experiment_id == experiment_id)
        )

        # Get total count
        count_stmt = select(sqlfunc.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar() or 0

        # Apply ordering and pagination
        stmt = stmt.order_by(SimulationRunORM.started_at.desc())
        stmt = stmt.limit(limit).offset(offset)
        orm_runs = list(self.session.execute(stmt).scalars().all())

        runs = [self._orm_to_simulation_run(orm_run) for orm_run in orm_runs]
        return runs, total

    def _row_to_simulation_run(self, row: Any) -> SimulationRun:
        """Convert a database row to SimulationRun."""
        config = SimulationConfig.model_validate(json.loads(row["config"]))
        aggregated = json.loads(row["aggregated_outcomes"]) if row["aggregated_outcomes"] else None

        return SimulationRun(
            id=row["id"],
            scorecard_id=row["scorecard_id"],
            scenario_id=row["scenario_id"],
            config=config,
            status=row["status"],
            started_at=(datetime.fromisoformat(row["started_at"]) if row["started_at"] else None),
            completed_at=(
                datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
            ),
            total_synths=row["total_synths"],
            aggregated_outcomes=aggregated,
            execution_time_seconds=row["execution_time_seconds"])

    # =========================================================================
    # ORM conversion methods
    # =========================================================================

    def _orm_to_simulation_run(self, orm_run: SimulationRunORM) -> SimulationRun:
        """Convert ORM model to SimulationRun entity."""
        config = SimulationConfig.model_validate(orm_run.config)

        started_at = orm_run.started_at
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = orm_run.completed_at
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return SimulationRun(
            id=orm_run.id,
            scorecard_id=orm_run.scorecard_id,
            scenario_id=orm_run.scenario_id,
            config=config,
            status=orm_run.status,
            started_at=started_at,
            completed_at=completed_at,
            total_synths=orm_run.total_synths,
            aggregated_outcomes=orm_run.aggregated_outcomes,
            execution_time_seconds=orm_run.execution_time_seconds)

    def _orm_to_synth_outcome(
        self, orm_outcome: SynthOutcomeORM, analysis_id: str
    ) -> SynthOutcome:
        """Convert ORM model to SynthOutcome entity."""
        from synth_lab.domain.entities.simulation_attributes import SimulationAttributes

        attrs = None
        if orm_outcome.synth_attributes:
            attrs = SimulationAttributes.model_validate(orm_outcome.synth_attributes)

        return SynthOutcome(
            analysis_id=analysis_id,
            synth_id=orm_outcome.synth_id,
            did_not_try_rate=orm_outcome.did_not_try_rate,
            failed_rate=orm_outcome.failed_rate,
            success_rate=orm_outcome.success_rate,
            synth_attributes=attrs)


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities import (
        FeatureScorecard,
        ScorecardDimension,
        ScorecardIdentification)
    from synth_lab.domain.entities.simulation_attributes import (
        SimulationAttributes,
        SimulationLatentTraits,
        SimulationObservables)
    from synth_lab.repositories.scorecard_repository import ScorecardRepository

    print("=== Simulation Repository Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Use temp database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_database(db_path)
        db = DatabaseManager(db_path)
        repo = SimulationRepository()

        # Create test scorecard first (to satisfy foreign key constraint)
        scorecard_repo = ScorecardRepository()
        test_scorecard = FeatureScorecard(
            id="testsc01",  # Must be 8 alphanumeric chars
            identification=ScorecardIdentification(
                feature_name="Test Feature",
                use_scenario="Testing simulation repository"),
            description_text="A test scorecard for validation",
            complexity=ScorecardDimension(score=0.5),
            initial_effort=ScorecardDimension(score=0.4),
            perceived_risk=ScorecardDimension(score=0.3),
            time_to_value=ScorecardDimension(score=0.6))
        scorecard_repo.create_scorecard(test_scorecard)

        # Create test simulation run
        test_config = SimulationConfig(
            n_executions=100,
            sigma=0.1,
            seed=42)
        test_run = SimulationRun(
            scorecard_id="testsc01",
            scenario_id="baseline",
            config=test_config,
            status="running",
            total_synths=10)

        # Test 1: Create simulation run
        total_tests += 1
        try:
            run_id = repo.create_simulation_run(test_run)
            if run_id != test_run.id:
                all_validation_failures.append(f"Create: ID mismatch {run_id} != {test_run.id}")
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
                    domain_expertise=0.5),
                latent_traits=SimulationLatentTraits(
                    capability_mean=0.5,
                    trust_mean=0.5,
                    friction_tolerance_mean=0.5,
                    exploration_prob=0.5))
            # Convert simulation_id to analysis_id format for SynthOutcome
            analysis_id = test_run.id.replace("sim_", "ana_")
            test_outcomes = [
                SynthOutcome(
                    analysis_id=analysis_id,
                    synth_id=f"synth_{i}",
                    did_not_try_rate=0.3,
                    failed_rate=0.2,
                    success_rate=0.5,
                    synth_attributes=sample_attrs)
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
                all_validation_failures.append(f"Get outcomes: Expected total=5, got {total}")
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
                all_validation_failures.append(f"List: Expected total=1, got {total}")
            elif len(runs) != 1:
                all_validation_failures.append(f"List: Expected 1 run, got {len(runs)}")
            else:
                print(f"Test 6 PASSED: Listed {len(runs)} simulation runs")
        except Exception as e:
            all_validation_failures.append(f"List failed: {e}")

        # Test 7: List with filter
        total_tests += 1
        try:
            runs, total = repo.list_simulation_runs(scenario_id="nonexistent")
            if total != 0:
                all_validation_failures.append(f"List filter: Expected total=0, got {total}")
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
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
