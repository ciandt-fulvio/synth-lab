"""
Analysis Outcome Repository for synth-lab.

Data access layer for synth outcomes linked to analysis runs.
Uses the v7 schema with analysis_id column.

Uses SQLAlchemy ORM for database operations.

References:
    - Schema: synth_outcomes table with analysis_id FK
    - Data model: specs/019-experiment-refactor/data-model.md
    - ORM models: synth_lab.models.orm.analysis
"""

import json
from typing import Any

from loguru import logger
from sqlalchemy import func as sqlfunc
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities import SynthOutcome
from synth_lab.domain.entities.simulation_attributes import SimulationAttributes
from synth_lab.models.orm.analysis import SynthOutcome as SynthOutcomeORM
from synth_lab.repositories.base import BaseRepository


class AnalysisOutcomeRepository(BaseRepository):
    """Repository for analysis outcome data access.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # ORM mode
        repo = AnalysisOutcomeRepository(db=database_manager)

        # ORM mode (SQLAlchemy)
        repo = AnalysisOutcomeRepository(session=session)
    """

    def __init__(
        self,
session: Session | None = None):
        super().__init__( session=session)
        self.logger = logger.bind(component="analysis_outcome_repository")

    def save_outcomes(
        self,
        analysis_id: str,
        outcomes: list[dict[str, Any]]) -> int:
        """
        Save synth outcomes for an analysis.

        Args:
            analysis_id: Analysis run ID
            outcomes: List of outcome dicts with synth_id, rates, and attributes

        Returns:
            Number of outcomes saved
        """
        return self._save_outcomes_orm(analysis_id, outcomes)

    def _save_outcomes_orm(
        self,
        analysis_id: str,
        outcomes: list[dict[str, Any]]) -> int:
        """Save synth outcomes using ORM."""
        for outcome in outcomes:
            synth_attrs_dict = outcome.get("synth_attributes")
            outcome_id = f"{analysis_id}_{outcome['synth_id']}"

            # Check if outcome already exists (for INSERT OR REPLACE behavior)
            existing = self.session.get(SynthOutcomeORM, outcome_id)
            if existing:
                existing.did_not_try_rate = outcome["did_not_try_rate"]
                existing.failed_rate = outcome["failed_rate"]
                existing.success_rate = outcome["success_rate"]
                existing.synth_attributes = synth_attrs_dict
            else:
                orm_outcome = SynthOutcomeORM(
                    id=outcome_id,
                    analysis_id=analysis_id,
                    synth_id=outcome["synth_id"],
                    did_not_try_rate=outcome["did_not_try_rate"],
                    failed_rate=outcome["failed_rate"],
                    success_rate=outcome["success_rate"],
                    synth_attributes=synth_attrs_dict)
                self._add(orm_outcome)

        self._flush()
        self._commit()
        self.logger.info(f"Saved {len(outcomes)} outcomes for analysis {analysis_id}")
        return len(outcomes)

    def get_outcomes(
        self,
        analysis_id: str,
        limit: int = 10000,
        offset: int = 0) -> tuple[list[SynthOutcome], int]:
        """
        Get synth outcomes for an analysis.

        Args:
            analysis_id: Analysis run ID
            limit: Maximum results
            offset: Results to skip

        Returns:
            Tuple of (list of outcomes, total count)
        """
        return self._get_outcomes_orm(analysis_id, limit, offset)

    def _get_outcomes_orm(
        self,
        analysis_id: str,
        limit: int = 10000,
        offset: int = 0) -> tuple[list[SynthOutcome], int]:
        """Get synth outcomes using ORM."""
        # Count total
        count_stmt = (
            select(sqlfunc.count())
            .select_from(SynthOutcomeORM)
            .where(SynthOutcomeORM.analysis_id == analysis_id)
        )
        total = self.session.execute(count_stmt).scalar() or 0

        # Get paginated results
        stmt = (
            select(SynthOutcomeORM)
            .where(SynthOutcomeORM.analysis_id == analysis_id)
            .order_by(SynthOutcomeORM.synth_id)
            .limit(limit)
            .offset(offset)
        )
        orm_outcomes = list(self.session.execute(stmt).scalars().all())

        outcomes = []
        for orm_outcome in orm_outcomes:
            outcome = self._orm_to_synth_outcome(orm_outcome, analysis_id)
            if outcome is not None:
                outcomes.append(outcome)

        return outcomes, total

    def delete_outcomes(self, analysis_id: str) -> int:
        """
        Delete all outcomes for an analysis.

        Args:
            analysis_id: Analysis run ID

        Returns:
            Number of outcomes deleted
        """
        return self._delete_outcomes_orm(analysis_id)

    def _delete_outcomes_orm(self, analysis_id: str) -> int:
        """Delete all outcomes for an analysis using ORM."""
        stmt = select(SynthOutcomeORM).where(SynthOutcomeORM.analysis_id == analysis_id)
        orm_outcomes = list(self.session.execute(stmt).scalars().all())

        deleted = len(orm_outcomes)
        for orm_outcome in orm_outcomes:
            self.session.delete(orm_outcome)

        self._flush()
        self._commit()
        self.logger.info(f"Deleted {deleted} outcomes for analysis {analysis_id}")
        return deleted

    # =========================================================================
    # ORM conversion methods
    # =========================================================================

    def _orm_to_synth_outcome(
        self, orm_outcome: SynthOutcomeORM, analysis_id: str
    ) -> SynthOutcome | None:
        """Convert ORM model to SynthOutcome entity.

        Args:
            orm_outcome: ORM model instance
            analysis_id: Analysis ID

        Returns:
            SynthOutcome entity or None if synth_attributes is missing
        """
        attrs_dict = orm_outcome.synth_attributes
        attrs = SimulationAttributes.model_validate(attrs_dict) if attrs_dict else None

        # Skip outcomes without synth_attributes (required field in SynthOutcome)
        if attrs is None:
            self.logger.warning(
                f"Skipping outcome for synth {orm_outcome.synth_id} - missing attributes"
            )
            return None

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

    from synth_lab.domain.entities.analysis_run import AnalysisConfig, AnalysisRun
    from synth_lab.domain.entities.experiment import Experiment
    from synth_lab.repositories.analysis_repository import AnalysisRepository
    from synth_lab.repositories.experiment_repository import ExperimentRepository

    all_validation_failures: list[str] = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)

        # Create required parent entities
        exp_repo = ExperimentRepository()
        ana_repo = AnalysisRepository()
        repo = AnalysisOutcomeRepository()

        exp = Experiment(name="Test", hypothesis="Test hypothesis")
        exp_repo.create(exp)

        analysis = AnalysisRun(
            experiment_id=exp.id,
            config=AnalysisConfig(n_synths=100, n_executions=50))
        ana_repo.create(analysis)

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

        # Test 2: Save and retrieve outcomes
        total_tests += 1
        try:
            test_outcomes = [
                {
                    "synth_id": "synth_001",
                    "did_not_try_rate": 0.1,
                    "failed_rate": 0.2,
                    "success_rate": 0.7,
                    "synth_attributes": {
                        "observables": {
                            "digital_literacy": 0.35,
                            "similar_tool_experience": 0.42,
                            "motor_ability": 0.85,
                            "time_availability": 0.28,
                            "domain_expertise": 0.55,
                        },
                        "latent_traits": {
                            "capability_mean": 0.42,
                            "trust_mean": 0.39,
                            "friction_tolerance_mean": 0.35,
                            "exploration_prob": 0.38,
                        },
                    },
                },
                {
                    "synth_id": "synth_002",
                    "did_not_try_rate": 0.3,
                    "failed_rate": 0.3,
                    "success_rate": 0.4,
                    "synth_attributes": {
                        "observables": {
                            "digital_literacy": 0.60,
                            "similar_tool_experience": 0.50,
                            "motor_ability": 1.0,
                            "time_availability": 0.45,
                            "domain_expertise": 0.70,
                        },
                        "latent_traits": {
                            "capability_mean": 0.58,
                            "trust_mean": 0.54,
                            "friction_tolerance_mean": 0.50,
                            "exploration_prob": 0.45,
                        },
                    },
                },
            ]
            saved = repo.save_outcomes(analysis.id, test_outcomes)
            if saved != 2:
                all_validation_failures.append(f"Expected 2 saved, got {saved}")
        except Exception as e:
            all_validation_failures.append(f"Save outcomes failed: {e}")

        # Test 3: Get saved outcomes
        total_tests += 1
        try:
            outcomes, count = repo.get_outcomes(analysis.id)
            if count != 2:
                all_validation_failures.append(f"Expected count 2, got {count}")
            if len(outcomes) != 2:
                all_validation_failures.append(f"Expected 2 outcomes, got {len(outcomes)}")
            if outcomes[0].synth_id != "synth_001":
                all_validation_failures.append(f"Expected synth_001, got {outcomes[0].synth_id}")
            if outcomes[0].success_rate != 0.7:
                all_validation_failures.append(
                    f"Expected success_rate 0.7, got {outcomes[0].success_rate}"
                )
        except Exception as e:
            all_validation_failures.append(f"Get saved outcomes failed: {e}")

        # Test 4: Pagination
        total_tests += 1
        try:
            outcomes, count = repo.get_outcomes(analysis.id, limit=1, offset=0)
            if count != 2:
                all_validation_failures.append(f"Expected total 2, got {count}")
            if len(outcomes) != 1:
                all_validation_failures.append(f"Expected 1 outcome, got {len(outcomes)}")
        except Exception as e:
            all_validation_failures.append(f"Pagination test failed: {e}")

        # Test 5: Update outcomes (INSERT OR REPLACE)
        total_tests += 1
        try:
            updated_outcomes = [
                {
                    "synth_id": "synth_001",
                    "did_not_try_rate": 0.05,
                    "failed_rate": 0.15,
                    "success_rate": 0.8,
                    "synth_attributes": {
                        "observables": {
                            "digital_literacy": 0.35,
                            "similar_tool_experience": 0.42,
                            "motor_ability": 0.85,
                            "time_availability": 0.28,
                            "domain_expertise": 0.55,
                        },
                        "latent_traits": {
                            "capability_mean": 0.42,
                            "trust_mean": 0.39,
                            "friction_tolerance_mean": 0.35,
                            "exploration_prob": 0.38,
                        },
                    },
                },
            ]
            saved = repo.save_outcomes(analysis.id, updated_outcomes)
            outcomes, count = repo.get_outcomes(analysis.id)
            synth_001_outcome = next(o for o in outcomes if o.synth_id == "synth_001")
            if synth_001_outcome.success_rate != 0.8:
                all_validation_failures.append(
                    f"Expected updated success_rate 0.8, got {synth_001_outcome.success_rate}"
                )
        except Exception as e:
            all_validation_failures.append(f"Update outcomes failed: {e}")

        # Test 6: Delete outcomes
        total_tests += 1
        try:
            deleted = repo.delete_outcomes(analysis.id)
            if deleted != 2:
                all_validation_failures.append(f"Expected 2 deleted, got {deleted}")
            outcomes, count = repo.get_outcomes(analysis.id)
            if count != 0:
                all_validation_failures.append(f"Expected 0 after delete, got {count}")
        except Exception as e:
            all_validation_failures.append(f"Delete outcomes failed: {e}")

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
