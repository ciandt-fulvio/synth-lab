"""
SynthOutcomeRepository for synth-lab.

Data access layer for synth outcomes. Uses SQLAlchemy ORM for database operations. Handles N:1 relationship with analysis runs.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - Data model: specs/019-experiment-refactor/data-model.md
    - ORM models: synth_lab.models.orm.analysis
"""

import json

from sqlalchemy import func as sqlfunc
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities.simulation_attributes import (
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables)
from synth_lab.domain.entities.synth_outcome import SynthOutcome
from synth_lab.models.orm.analysis import AnalysisRun as AnalysisRunORM
from synth_lab.models.orm.analysis import SynthOutcome as SynthOutcomeORM
from synth_lab.models.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from synth_lab.repositories.base import BaseRepository


class SynthOutcomeRepository(BaseRepository):
    """Repository for synth outcome data access.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # ORM mode
        repo = SynthOutcomeRepository(db=database_manager)

        # ORM mode (SQLAlchemy)
        repo = SynthOutcomeRepository(session=session)
    """

    def __init__(
        self,
session: Session | None = None):
        super().__init__( session=session)

    def create(self, outcome: SynthOutcome) -> SynthOutcome:
        """
        Create a new synth outcome.

        Args:
            outcome: SynthOutcome entity to create.

        Returns:
            Created synth outcome.
        """
        orm_outcome = SynthOutcomeORM(
            id=outcome.id,
            analysis_id=outcome.analysis_id,
            synth_id=outcome.synth_id,
            did_not_try_rate=outcome.did_not_try_rate,
            failed_rate=outcome.failed_rate,
            success_rate=outcome.success_rate,
            synth_attributes=outcome.synth_attributes.model_dump())
        self._add(orm_outcome)
        self._flush()
        self._commit()
        return outcome
    def create_batch(self, outcomes: list[SynthOutcome]) -> list[SynthOutcome]:
        """
        Create multiple synth outcomes in a batch.

        Args:
            outcomes: List of SynthOutcome entities to create.

        Returns:
            List of created synth outcomes.
        """
        if not outcomes:
            return []

        for outcome in outcomes:
            orm_outcome = SynthOutcomeORM(
                id=outcome.id,
                analysis_id=outcome.analysis_id,
                synth_id=outcome.synth_id,
                did_not_try_rate=outcome.did_not_try_rate,
                failed_rate=outcome.failed_rate,
                success_rate=outcome.success_rate,
                synth_attributes=outcome.synth_attributes.model_dump())
            self._add(orm_outcome)
        self._flush()
        self._commit()
        return outcomes
    def get_by_id(self, outcome_id: str) -> SynthOutcome | None:
        """
        Get a synth outcome by ID.

        Args:
            outcome_id: Outcome ID to retrieve.

        Returns:
            SynthOutcome if found, None otherwise.
        """
        orm_outcome = self._get_by_id(SynthOutcomeORM, outcome_id)
        if orm_outcome is None:
            return None
        return self._orm_to_outcome(orm_outcome)
    def list_by_analysis_id(
        self,
        analysis_id: str,
        params: PaginationParams | None = None) -> PaginatedResponse[SynthOutcome]:
        """
        List outcomes for an analysis with pagination.

        Args:
            analysis_id: Parent analysis run ID.
            params: Pagination parameters.

        Returns:
            Paginated list of synth outcomes.
        """
        params = params or PaginationParams()

        # Get total count
        count_stmt = select(sqlfunc.count()).where(
            SynthOutcomeORM.analysis_id == analysis_id
        ).select_from(SynthOutcomeORM)
        total = self.session.execute(count_stmt).scalar() or 0

        # Get paginated results ordered by synth_id
        stmt = (
            select(SynthOutcomeORM)
            .where(SynthOutcomeORM.analysis_id == analysis_id)
            .order_by(SynthOutcomeORM.synth_id)
            .limit(params.limit)
            .offset(params.offset)
        )
        orm_outcomes = list(self.session.execute(stmt).scalars().all())

        outcomes = [self._orm_to_outcome(o) for o in orm_outcomes]

        return PaginatedResponse(
            data=outcomes,
            pagination=PaginationMeta(
                total=total,
                limit=params.limit,
                offset=params.offset,
                has_next=(params.offset + len(outcomes)) < total))
    def delete_by_analysis_id(self, analysis_id: str) -> int:
        """
        Delete all outcomes for an analysis.

        Args:
            analysis_id: Parent analysis run ID.

        Returns:
            Number of outcomes deleted.
        """
        # Get count first
        count_stmt = select(sqlfunc.count()).where(
            SynthOutcomeORM.analysis_id == analysis_id
        ).select_from(SynthOutcomeORM)
        count = self.session.execute(count_stmt).scalar() or 0

        # Get and delete each outcome
        stmt = select(SynthOutcomeORM).where(SynthOutcomeORM.analysis_id == analysis_id)
        outcomes = list(self.session.execute(stmt).scalars().all())
        for outcome in outcomes:
            self._delete(outcome)
        self._flush()
        self._commit()
        return count
    def count_by_analysis_id(self, analysis_id: str) -> int:
        """
        Count outcomes for an analysis.

        Args:
            analysis_id: Parent analysis run ID.

        Returns:
            Number of outcomes.
        """
        count_stmt = select(sqlfunc.count()).where(
            SynthOutcomeORM.analysis_id == analysis_id
        ).select_from(SynthOutcomeORM)
        return self.session.execute(count_stmt).scalar() or 0
    def get_by_synth_and_analysis(self, synth_id: str, analysis_id: str) -> SynthOutcome | None:
        """
        Get simulation results for a specific synth in an analysis.

        Used to retrieve a synth's performance for interview context.

        Args:
            synth_id: The synth ID.
            analysis_id: The analysis run ID.

        Returns:
            SynthOutcome if found, None otherwise.
        """
        stmt = select(SynthOutcomeORM).where(
            SynthOutcomeORM.synth_id == synth_id,
            SynthOutcomeORM.analysis_id == analysis_id)
        orm_outcome = self.session.execute(stmt).scalar_one_or_none()
        if orm_outcome is None:
            return None
        return self._orm_to_outcome(orm_outcome)
    def get_analysis_statistics(self, analysis_id: str) -> dict | None:
        """
        Get aggregated statistics for an analysis.

        Used to compare individual synth performance against the group average.

        Args:
            analysis_id: The analysis run ID.

        Returns:
            Dict with avg_success_rate, avg_did_not_try_rate, synth_count.
            None if no outcomes found.
        """
        stmt = select(
            sqlfunc.avg(SynthOutcomeORM.success_rate).label("avg_success_rate"),
            sqlfunc.avg(SynthOutcomeORM.did_not_try_rate).label("avg_did_not_try_rate"),
            sqlfunc.avg(SynthOutcomeORM.failed_rate).label("avg_failed_rate"),
            sqlfunc.count().label("synth_count")).where(SynthOutcomeORM.analysis_id == analysis_id)
        result = self.session.execute(stmt).one_or_none()
        if result is None or result.synth_count == 0:
            return None

        return {
            "avg_success_rate": result.avg_success_rate,
            "avg_did_not_try_rate": result.avg_did_not_try_rate,
            "avg_failed_rate": result.avg_failed_rate,
            "synth_count": result.synth_count,
        }
    def get_latest_outcome_for_synth(self, synth_id: str) -> SynthOutcome | None:
        """
        Get the most recent simulation outcome for a synth.

        Finds the latest completed analysis that includes this synth
        and returns their outcome.

        Args:
            synth_id: The synth ID.

        Returns:
            SynthOutcome from most recent analysis, or None if not found.
        """
        stmt = (
            select(SynthOutcomeORM)
            .join(AnalysisRunORM, SynthOutcomeORM.analysis_id == AnalysisRunORM.id)
            .where(
                SynthOutcomeORM.synth_id == synth_id,
                AnalysisRunORM.status == "completed")
            .order_by(AnalysisRunORM.completed_at.desc())
            .limit(1)
        )
        orm_outcome = self.session.execute(stmt).scalar_one_or_none()
        if orm_outcome is None:
            return None
        return self._orm_to_outcome(orm_outcome)
    def _row_to_outcome(self, row) -> SynthOutcome:
        """Convert a database row to SynthOutcome entity."""
        attrs_dict = json.loads(row["synth_attributes"])

        # Build SimulationAttributes from dict
        observables = SimulationObservables(**attrs_dict["observables"])
        latent_traits = SimulationLatentTraits(**attrs_dict["latent_traits"])
        synth_attrs = SimulationAttributes(
            observables=observables,
            latent_traits=latent_traits)

        return SynthOutcome(
            id=row["id"],
            analysis_id=row["analysis_id"],
            synth_id=row["synth_id"],
            did_not_try_rate=row["did_not_try_rate"],
            failed_rate=row["failed_rate"],
            success_rate=row["success_rate"],
            synth_attributes=synth_attrs)

    # =========================================================================
    # ORM conversion methods
    # =========================================================================

    def _orm_to_outcome(self, orm_outcome: SynthOutcomeORM) -> SynthOutcome:
        """Convert ORM model to SynthOutcome entity."""
        attrs_dict = orm_outcome.synth_attributes

        # Build SimulationAttributes from dict
        observables = SimulationObservables(**attrs_dict["observables"])
        latent_traits = SimulationLatentTraits(**attrs_dict["latent_traits"])
        synth_attrs = SimulationAttributes(
            observables=observables,
            latent_traits=latent_traits)

        return SynthOutcome(
            id=orm_outcome.id,
            analysis_id=orm_outcome.analysis_id,
            synth_id=orm_outcome.synth_id,
            did_not_try_rate=orm_outcome.did_not_try_rate,
            failed_rate=orm_outcome.failed_rate,
            success_rate=orm_outcome.success_rate,
            synth_attributes=synth_attrs)


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.analysis_run import AnalysisRun
    from synth_lab.domain.entities.experiment import Experiment
    from synth_lab.repositories.analysis_repository import AnalysisRepository
    from synth_lab.repositories.experiment_repository import ExperimentRepository

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Create sample attributes
    sample_observables = SimulationObservables(
        digital_literacy=0.35,
        similar_tool_experience=0.42,
        motor_ability=0.85,
        time_availability=0.28,
        domain_expertise=0.55)
    sample_latent = SimulationLatentTraits(
        capability_mean=0.42,
        trust_mean=0.39,
        friction_tolerance_mean=0.35,
        exploration_prob=0.38)
    sample_attrs = SimulationAttributes(
        observables=sample_observables,
        latent_traits=sample_latent)

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        exp_repo = ExperimentRepository()
        ana_repo = AnalysisRepository()
        outcome_repo = SynthOutcomeRepository()

        # Create parent experiment and analysis
        exp = Experiment(name="Test", hypothesis="Test hypothesis")
        exp_repo.create(exp)
        analysis = AnalysisRun(experiment_id=exp.id)
        ana_repo.create(analysis)

        # Test 1: Create outcome
        total_tests += 1
        try:
            outcome = SynthOutcome(
                analysis_id=analysis.id,
                synth_id="synth_001",
                did_not_try_rate=0.22,
                failed_rate=0.38,
                success_rate=0.40,
                synth_attributes=sample_attrs)
            result = outcome_repo.create(outcome)
            if result.id != outcome.id:
                all_validation_failures.append(f"ID mismatch: {result.id}")
        except Exception as e:
            all_validation_failures.append(f"Create outcome failed: {e}")

        # Test 2: Get outcome by ID
        total_tests += 1
        try:
            retrieved = outcome_repo.get_by_id(outcome.id)
            if retrieved is None:
                all_validation_failures.append("Get by ID returned None")
            elif retrieved.synth_id != "synth_001":
                all_validation_failures.append(f"synth_id mismatch: {retrieved.synth_id}")
            elif retrieved.synth_attributes.observables.digital_literacy != 0.35:
                all_validation_failures.append("synth_attributes not restored correctly")
        except Exception as e:
            all_validation_failures.append(f"Get by ID failed: {e}")

        # Test 3: Create batch
        total_tests += 1
        try:
            batch = [
                SynthOutcome(
                    analysis_id=analysis.id,
                    synth_id=f"synth_{i:03d}",
                    did_not_try_rate=0.20,
                    failed_rate=0.30,
                    success_rate=0.50,
                    synth_attributes=sample_attrs)
                for i in range(2, 12)  # 10 more outcomes
            ]
            result = outcome_repo.create_batch(batch)
            if len(result) != 10:
                all_validation_failures.append(f"Batch create returned {len(result)} items")
        except Exception as e:
            all_validation_failures.append(f"Create batch failed: {e}")

        # Test 4: List by analysis ID
        total_tests += 1
        try:
            response = outcome_repo.list_by_analysis_id(
                analysis.id,
                params=PaginationParams(limit=5, offset=0))
            if len(response.data) != 5:
                all_validation_failures.append(
                    f"List returned {len(response.data)} items, expected 5"
                )
            if response.pagination.total != 11:
                all_validation_failures.append(f"Total mismatch: {response.pagination.total}")
            if not response.pagination.has_next:
                all_validation_failures.append("has_next should be True")
        except Exception as e:
            all_validation_failures.append(f"List by analysis_id failed: {e}")

        # Test 5: Count by analysis ID
        total_tests += 1
        try:
            count = outcome_repo.count_by_analysis_id(analysis.id)
            if count != 11:
                all_validation_failures.append(f"Count mismatch: {count}")
        except Exception as e:
            all_validation_failures.append(f"Count by analysis_id failed: {e}")

        # Test 6: Get by synth and analysis
        total_tests += 1
        try:
            # First recreate an outcome for testing
            test_outcome = SynthOutcome(
                analysis_id=analysis.id,
                synth_id="synth_test",
                did_not_try_rate=0.25,
                failed_rate=0.35,
                success_rate=0.40,
                synth_attributes=sample_attrs)
            outcome_repo.create(test_outcome)

            retrieved = outcome_repo.get_by_synth_and_analysis("synth_test", analysis.id)
            if retrieved is None:
                all_validation_failures.append("get_by_synth_and_analysis returned None")
            elif retrieved.synth_id != "synth_test":
                all_validation_failures.append(f"synth_id mismatch: {retrieved.synth_id}")
            elif retrieved.success_rate != 0.40:
                all_validation_failures.append(f"success_rate mismatch: {retrieved.success_rate}")
        except Exception as e:
            all_validation_failures.append(f"Get by synth and analysis failed: {e}")

        # Test 7: Get by synth and analysis - not found
        total_tests += 1
        try:
            result = outcome_repo.get_by_synth_and_analysis("nonexistent", analysis.id)
            if result is not None:
                all_validation_failures.append("Should return None for nonexistent synth")
        except Exception as e:
            all_validation_failures.append(f"Get nonexistent synth failed: {e}")

        # Test 8: Delete by analysis ID
        total_tests += 1
        try:
            # Count before delete (11 original + 1 test_outcome = 12)
            count_before = outcome_repo.count_by_analysis_id(analysis.id)
            deleted = outcome_repo.delete_by_analysis_id(analysis.id)
            if deleted != count_before:
                all_validation_failures.append(
                    f"Delete returned {deleted}, expected {count_before}"
                )
            count = outcome_repo.count_by_analysis_id(analysis.id)
            if count != 0:
                all_validation_failures.append(f"Outcomes still exist after delete: {count}")
        except Exception as e:
            all_validation_failures.append(f"Delete by analysis_id failed: {e}")

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
