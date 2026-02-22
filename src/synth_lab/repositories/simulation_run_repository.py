"""
Repository for simulation run data access.

Handles CRUD operations for simulation runs and analysis interpretations.
Uses SQLAlchemy ORM for database operations.

References:
    - Data model: specs/042-quantitative-analysis/data-model.md
    - ORM models: synth_lab.models.orm.simulation_run

Sample input:
    repo = SimulationRunRepository(session=db_session)
    run = repo.get_latest_by_experiment("exp_12345678")

Expected output:
    SimulationRunORM instance with interpretations loaded, or None.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from synth_lab.models.orm.simulation_run import (
    AnalysisInterpretation as AnalysisInterpretationORM,
)
from synth_lab.models.orm.simulation_run import SimulationBatch as SimulationBatchORM
from synth_lab.models.orm.simulation_run import SimulationRun as SimulationRunORM
from synth_lab.repositories.base import BaseRepository


class SimulationRunRepository(BaseRepository):
    """Repository for simulation run data access.

    Usage:
        repo = SimulationRunRepository(session=session)
        run = repo.get_latest_by_experiment("exp_12345678")
    """

    def __init__(self, session: Session | None = None):
        super().__init__(session=session)

    def create_run(
        self,
        run_id: str,
        experiment_id: str,
        causal_model_id: str,
        n_iterations: int,
        n_synths: int,
        selections: dict,
        stats: dict,
        distribution: list,
        segments: dict,
        sensitivity: list,
        batch_id: str | None = None,
        product_values: dict | None = None,
        per_synth_outcomes: dict | None = None,
        auto_commit: bool = True,
    ) -> SimulationRunORM:
        """
        Create a simulation run record.

        Args:
            run_id: Unique run ID (sr_xxx).
            experiment_id: Parent experiment ID.
            causal_model_id: Causal model used.
            n_iterations: Number of Monte Carlo iterations.
            n_synths: Number of synths used.
            selections: Node selections at simulation time.
            stats: Aggregated statistics dict.
            distribution: Adoption rate per iteration.
            segments: Results by demographic segment.
            sensitivity: Per-edge sensitivity results.
            batch_id: Parent batch ID (batch runs only).
            product_values: Product calibration levels used (batch runs only).
            per_synth_outcomes: Dict {synth_id: outcome} with 2 decimal places (batch runs only).
            auto_commit: If True (default), flush+commit immediately. Set False for batching.

        Returns:
            Created SimulationRunORM instance.
        """
        orm_run = SimulationRunORM(
            id=run_id,
            experiment_id=experiment_id,
            causal_model_id=causal_model_id,
            n_iterations=n_iterations,
            n_synths=n_synths,
            selections=selections,
            stats=stats,
            distribution=distribution,
            segments=segments,
            sensitivity=sensitivity,
            batch_id=batch_id,
            product_values=product_values,
            per_synth_outcomes=per_synth_outcomes,
        )
        self._add(orm_run)
        if auto_commit:
            self._flush()
            self._commit()
        return orm_run

    def flush_and_commit(self) -> None:
        """Flush pending changes and commit. Use after batched create_run calls."""
        self._flush()
        self._commit()

    def create_interpretations(
        self,
        interpretations: list[dict],
    ) -> list[AnalysisInterpretationORM]:
        """
        Create analysis interpretation records for a simulation run.

        Args:
            interpretations: List of dicts with keys:
                id, simulation_run_id, section, raw_text, ai_text, model.

        Returns:
            List of created AnalysisInterpretationORM instances.
        """
        created = []
        for interp_data in interpretations:
            orm_interp = AnalysisInterpretationORM(
                id=interp_data["id"],
                simulation_run_id=interp_data["simulation_run_id"],
                section=interp_data["section"],
                raw_text=interp_data["raw_text"],
                ai_text=interp_data["ai_text"],
                model=interp_data.get("model", "gpt-4o-mini"),
            )
            self._add(orm_interp)
            created.append(orm_interp)

        self._flush()
        self._commit()
        return created

    def get_latest_by_experiment(
        self, experiment_id: str
    ) -> SimulationRunORM | None:
        """
        Get the most recent standalone simulation run for an experiment.

        Excludes batch scenario runs (batch_id IS NOT NULL) which have
        incomplete data (empty segments/sensitivity) by design.

        Eagerly loads interpretations.

        Args:
            experiment_id: Experiment ID.

        Returns:
            SimulationRunORM with interpretations, or None.
        """
        stmt = (
            select(SimulationRunORM)
            .where(
                SimulationRunORM.experiment_id == experiment_id,
                SimulationRunORM.batch_id.is_(None),
            )
            .options(joinedload(SimulationRunORM.interpretations))
            .order_by(SimulationRunORM.created_at.desc())
            .limit(1)
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def list_by_experiment(
        self, experiment_id: str
    ) -> list[SimulationRunORM]:
        """
        List all simulation runs for an experiment, newest first.

        Does not eagerly load interpretations (use get_latest for that).

        Args:
            experiment_id: Experiment ID.

        Returns:
            List of SimulationRunORM instances.
        """
        stmt = (
            select(SimulationRunORM)
            .where(SimulationRunORM.experiment_id == experiment_id)
            .order_by(SimulationRunORM.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    # =========================================================================
    # Batch methods
    # =========================================================================

    def create_batch(
        self,
        batch_id: str,
        experiment_id: str,
        causal_model_id: str,
        n_scenarios: int,
        n_synths: int,
        n_repetitions: int = 10,
    ) -> SimulationBatchORM:
        """Create a simulation batch record."""
        orm_batch = SimulationBatchORM(
            id=batch_id,
            experiment_id=experiment_id,
            causal_model_id=causal_model_id,
            n_scenarios=n_scenarios,
            n_synths=n_synths,
            n_repetitions=n_repetitions,
            status="running",
        )
        self._add(orm_batch)
        self._flush()
        self._commit()
        return orm_batch

    def update_batch_status(self, batch_id: str, status: str) -> None:
        """Update batch status (completed / failed)."""
        batch = self._get_by_id(SimulationBatchORM, batch_id)
        if batch:
            batch.status = status
            self._flush()
            self._commit()

    def get_latest_batch_by_experiment(
        self, experiment_id: str
    ) -> SimulationBatchORM | None:
        """Get the most recent simulation batch for an experiment."""
        stmt = (
            select(SimulationBatchORM)
            .where(SimulationBatchORM.experiment_id == experiment_id)
            .options(joinedload(SimulationBatchORM.runs))
            .order_by(SimulationBatchORM.created_at.desc())
            .limit(1)
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def get_batch_by_id(self, batch_id: str) -> SimulationBatchORM | None:
        """Get a batch by ID with runs eagerly loaded."""
        stmt = (
            select(SimulationBatchORM)
            .where(SimulationBatchORM.id == batch_id)
            .options(joinedload(SimulationBatchORM.runs))
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Repository instantiation
    total_tests += 1
    try:
        repo = SimulationRunRepository()
        if repo._session is not None:
            all_validation_failures.append("Session should be None initially")
        if repo._owns_session is not True:
            all_validation_failures.append("Should own session when none provided")
    except Exception as e:
        all_validation_failures.append(f"Init failed: {e}")

    # Test 2: Required methods exist
    total_tests += 1
    try:
        repo = SimulationRunRepository()
        methods = [
            "create_run",
            "create_interpretations",
            "get_latest_by_experiment",
            "list_by_experiment",
            "create_batch",
            "update_batch_status",
            "get_batch_by_id",
        ]
        for method in methods:
            if not hasattr(repo, method):
                all_validation_failures.append(f"Missing method: {method}")
    except Exception as e:
        all_validation_failures.append(f"Method check failed: {e}")

    # Test 3: Removed methods are gone
    total_tests += 1
    try:
        repo = SimulationRunRepository()
        removed = ["create_synth_results_bulk", "get_synth_results_by_run"]
        for method in removed:
            if hasattr(repo, method):
                all_validation_failures.append(f"Method should be removed: {method}")
    except Exception as e:
        all_validation_failures.append(f"Removed method check failed: {e}")

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
