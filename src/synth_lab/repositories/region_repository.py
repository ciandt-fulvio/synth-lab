"""
Region analysis repository for synth-lab.

Handles persistence of region analysis results to database.
Uses SQLAlchemy ORM for database operations.

Classes:
- RegionRepository: Repository for region analyses

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Data model: specs/016-feature-impact-simulation/data-model.md
    - ORM models: synth_lab.models.orm.insight

Sample usage:
    from synth_lab.repositories.region_repository import RegionRepository

    # ORM mode
    repo = RegionRepository(db=database_manager)

    # ORM mode (SQLAlchemy)
    repo = RegionRepository(session=session)

    repo.save_region_analyses(analyses)
    regions = repo.get_region_analyses(simulation_id)

Expected output:
    List of RegionAnalysis objects persisted and retrieved from database
"""

import json

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities import RegionAnalysis, RegionRule
from synth_lab.models.orm.insight import RegionAnalysis as RegionAnalysisORM
from synth_lab.repositories.base import BaseRepository


class RegionRepository(BaseRepository):
    """Repository for region analysis results.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # ORM mode
        repo = RegionRepository(db=database_manager)

        # ORM mode (SQLAlchemy)
        repo = RegionRepository(session=session)
    """

    def __init__(
        self,
session: Session | None = None) -> None:
        """
        Initialize repository with database manager or session.

        Args:
            session: SQLAlchemy session for ORM operations.
        """
        super().__init__( session=session)
        self.logger = logger.bind(component="region_repository")

    def save_region_analyses(self, analyses: list[RegionAnalysis]) -> None:
        """
        Save region analyses to database.

        Args:
            analyses: List of RegionAnalysis objects to persist
        """
        if not analyses:
            self.logger.warning("No analyses to save")
            return

        self.logger.info(f"Saving {len(analyses)} region analyses")

        for analysis in analyses:
            orm_analysis = RegionAnalysisORM(
                id=analysis.id,
                simulation_id=analysis.simulation_id,
                rules=[rule.model_dump() for rule in analysis.rules],
                rule_text=analysis.rule_text,
                synth_count=analysis.synth_count,
                synth_percentage=analysis.synth_percentage,
                did_not_try_rate=analysis.did_not_try_rate,
                failed_rate=analysis.failed_rate,
                success_rate=analysis.success_rate,
                failure_delta=analysis.failure_delta)
            self._add(orm_analysis)
        self._flush()
        self._commit()
        self.logger.info(f"Saved {len(analyses)} region analyses successfully (ORM)")
        return
    def get_region_analyses(self, simulation_id: str) -> list[RegionAnalysis]:
        """
        Retrieve region analyses for a simulation.

        Args:
            simulation_id: ID of the simulation

        Returns:
            List of RegionAnalysis objects
        """
        self.logger.info(f"Retrieving region analyses for simulation {simulation_id}")

        stmt = (
            select(RegionAnalysisORM)
            .where(RegionAnalysisORM.simulation_id == simulation_id)
            .order_by(RegionAnalysisORM.failed_rate.desc())
        )
        result = self.session.execute(stmt).scalars().all()
        analyses = [self._orm_to_region_analysis(orm) for orm in result]
        self.logger.info(f"Retrieved {len(analyses)} region analyses (ORM)")
        return analyses
    def delete_region_analyses(self, simulation_id: str) -> int:
        """
        Delete all region analyses for a simulation.

        Args:
            simulation_id: ID of the simulation

        Returns:
            Number of analyses deleted
        """
        self.logger.info(f"Deleting region analyses for simulation {simulation_id}")

        stmt = select(RegionAnalysisORM).where(
            RegionAnalysisORM.simulation_id == simulation_id
        )
        orm_analyses = list(self.session.execute(stmt).scalars().all())
        deleted_count = len(orm_analyses)
        for orm in orm_analyses:
            self._delete(orm)
        self._flush()
        self._commit()
        self.logger.info(f"Deleted {deleted_count} region analyses (ORM)")
        return deleted_count
    def _orm_to_region_analysis(self, orm: RegionAnalysisORM) -> RegionAnalysis:
        """Convert ORM model to RegionAnalysis domain entity."""
        # ORM stores rules as list of dicts
        rules_data = orm.rules or []
        rules = [RegionRule(**rule) for rule in rules_data]

        return RegionAnalysis(
            id=orm.id,
            simulation_id=orm.simulation_id,
            rules=rules,
            rule_text=orm.rule_text,
            synth_count=orm.synth_count,
            synth_percentage=orm.synth_percentage,
            did_not_try_rate=orm.did_not_try_rate,
            failed_rate=orm.failed_rate,
            success_rate=orm.success_rate,
            failure_delta=orm.failure_delta)


if __name__ == "__main__":
    import sys
    import tempfile
    from datetime import datetime, timezone
    from pathlib import Path


    print("=== Region Repository Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        repo = RegionRepository()

        # Create parent records to satisfy foreign key constraints
        # 1. Create a feature_scorecard
        scorecard_id = "sc_test_12345"
        db.execute(
            """
            INSERT INTO feature_scorecards (id, data, created_at)
            VALUES (?, ?, ?)
            """,
            (scorecard_id, "{}", datetime.now(timezone.utc).isoformat()))

        # 2. Create a simulation_run that references the scorecard
        test_simulation_id = "sim_test_12345"
        db.execute(
            """
            INSERT INTO simulation_runs (id, scorecard_id, scenario_id, config, status, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                test_simulation_id,
                scorecard_id,
                "baseline",
                "{}",
                "completed",
                datetime.now(timezone.utc).isoformat()))

        test_analyses = [
            RegionAnalysis(
                simulation_id=test_simulation_id,
                rules=[
                    RegionRule(attribute="capability_mean", operator="<=", threshold=0.48),
                    RegionRule(attribute="trust_mean", operator="<=", threshold=0.4),
                ],
                rule_text="capability_mean <= 0.48 AND trust_mean <= 0.4",
                synth_count=50,
                synth_percentage=10.0,
                success_rate=0.25,
                failed_rate=0.65,
                did_not_try_rate=0.10,
                failure_delta=0.15),
            RegionAnalysis(
                simulation_id=test_simulation_id,
                rules=[
                    RegionRule(attribute="capability_mean", operator="<=", threshold=0.35),
                ],
                rule_text="capability_mean <= 0.35",
                synth_count=30,
                synth_percentage=6.0,
                success_rate=0.20,
                failed_rate=0.70,
                did_not_try_rate=0.10,
                failure_delta=0.20),
        ]

        # Test 1: Save region analyses
        total_tests += 1
        try:
            repo.save_region_analyses(test_analyses)
            print("Test 1 PASSED: Region analyses saved successfully")
        except Exception as e:
            all_validation_failures.append(f"Save failed: {e}")

        # Test 2: Retrieve region analyses
        total_tests += 1
        retrieved = []
        try:
            retrieved = repo.get_region_analyses(test_simulation_id)
            if len(retrieved) != 2:
                all_validation_failures.append(
                    f"Should retrieve 2 analyses, got {len(retrieved)}"
                )
            elif retrieved[0].failed_rate != 0.70:
                # Should be ordered by failure rate DESC
                all_validation_failures.append(
                    f"First analysis should have failed_rate=0.70, got {retrieved[0].failed_rate}"
                )
            else:
                print("Test 2 PASSED: Region analyses retrieved and ordered correctly")
        except Exception as e:
            all_validation_failures.append(f"Retrieval failed: {e}")

        # Test 3: Verify rule reconstruction
        total_tests += 1
        try:
            if len(retrieved) > 0:
                first_analysis = retrieved[0]
                if len(first_analysis.rules) != 1:
                    all_validation_failures.append(
                        f"First analysis should have 1 rule, got {len(first_analysis.rules)}"
                    )
                elif first_analysis.rules[0].attribute != "capability_mean":
                    attr = first_analysis.rules[0].attribute
                    all_validation_failures.append(
                        f"Rule attr should be capability_mean, got {attr}"
                    )
                else:
                    print("Test 3 PASSED: Rules reconstructed correctly")
            else:
                all_validation_failures.append("No analyses retrieved to verify rules")
        except Exception as e:
            all_validation_failures.append(f"Rule reconstruction failed: {e}")

        # Test 4: Delete region analyses
        total_tests += 1
        try:
            deleted_count = repo.delete_region_analyses(test_simulation_id)
            if deleted_count != 2:
                all_validation_failures.append(
                    f"Should delete 2 analyses, deleted {deleted_count}"
                )
            else:
                print("Test 4 PASSED: Region analyses deleted successfully")
        except Exception as e:
            all_validation_failures.append(f"Delete failed: {e}")

        # Test 5: Verify deletion
        total_tests += 1
        try:
            remaining = repo.get_region_analyses(test_simulation_id)
            if len(remaining) != 0:
                all_validation_failures.append(
                    f"Should have 0 remaining analyses, got {len(remaining)}"
                )
            else:
                print("Test 5 PASSED: Deletion verified")
        except Exception as e:
            all_validation_failures.append(f"Deletion verification failed: {e}")

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
        print("RegionRepository is validated and ready for use")
        sys.exit(0)
