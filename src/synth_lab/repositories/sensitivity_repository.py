"""
Repository for sensitivity analysis results.

Handles persistence of sensitivity analysis results in the database.
Uses SQLAlchemy ORM for database operations.

References:
    - Spec: specs/017-analysis-ux-research/spec.md
    - Data model: specs/017-analysis-ux-research/data-model.md
    - ORM models: synth_lab.models.orm.insight
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities import DimensionSensitivity, SensitivityResult
from synth_lab.models.orm.insight import SensitivityResult as SensitivityResultORM
from synth_lab.repositories.base import BaseRepository


def generate_sensitivity_id() -> str:
    """Generate unique ID for sensitivity analysis."""
    return f"sens_{uuid.uuid4().hex[:12]}"


class SensitivityRepository(BaseRepository):
    """Repository for sensitivity analysis results.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # ORM mode
        repo = SensitivityRepository(db=database_manager)

        # ORM mode (SQLAlchemy)
        repo = SensitivityRepository(session=session)
    """

    def __init__(
        self,
session: Session | None = None) -> None:
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session (ORM mode)
        """
        super().__init__( session=session)
        self.logger = logger.bind(component="sensitivity_repository")

    def save_result(self, result: SensitivityResult) -> str:
        """
        Save sensitivity analysis result to database.

        Args:
            result: SensitivityResult to save

        Returns:
            ID of saved result
        """
        result_id = generate_sensitivity_id()

        return self._save_result_orm(result, result_id)

    def _save_result_orm(self, result: SensitivityResult, result_id: str) -> str:
        """Save sensitivity result using ORM."""
        orm_result = SensitivityResultORM(
            id=result_id,
            simulation_id=result.simulation_id,
            analyzed_at=result.analyzed_at.isoformat(),
            deltas_used=result.deltas_used,
            baseline_success=result.baseline_success,
            most_sensitive_dimension=result.most_sensitive_dimension,
            dimensions=[dim.model_dump() for dim in result.dimensions],
            created_at=datetime.now(timezone.utc).isoformat())
        self._add(orm_result)
        self._flush()
        self._commit()

        self.logger.info(
            f"Saved sensitivity result {result_id} for simulation {result.simulation_id}"
        )

        return result_id

    def get_by_simulation(self, simulation_id: str) -> SensitivityResult | None:
        """
        Get most recent sensitivity result for a simulation.

        Args:
            simulation_id: ID of the simulation

        Returns:
            SensitivityResult if found, None otherwise
        """
        return self._get_by_simulation_orm(simulation_id)

    def _get_by_simulation_orm(self, simulation_id: str) -> SensitivityResult | None:
        """Get most recent sensitivity result for a simulation using ORM."""
        stmt = (
            select(SensitivityResultORM)
            .where(SensitivityResultORM.simulation_id == simulation_id)
            .order_by(SensitivityResultORM.analyzed_at.desc())
            .limit(1)
        )
        orm_result = self.session.execute(stmt).scalar_one_or_none()
        if orm_result is None:
            return None
        return self._orm_to_entity(orm_result)

    def get_by_id(self, result_id: str) -> SensitivityResult | None:
        """
        Get sensitivity result by ID.

        Args:
            result_id: ID of the result

        Returns:
            SensitivityResult if found, None otherwise
        """
        orm_result = self.session.get(SensitivityResultORM, result_id)
        if orm_result is None:
            return None
        return self._orm_to_entity(orm_result)
    def delete_by_simulation(self, simulation_id: str) -> int:
        """
        Delete all sensitivity results for a simulation.

        Args:
            simulation_id: ID of the simulation

        Returns:
            Number of deleted results
        """
        return self._delete_by_simulation_orm(simulation_id)

    def _delete_by_simulation_orm(self, simulation_id: str) -> int:
        """Delete all sensitivity results for a simulation using ORM."""
        stmt = select(SensitivityResultORM).where(
            SensitivityResultORM.simulation_id == simulation_id
        )
        results = list(self.session.execute(stmt).scalars().all())
        deleted = len(results)

        for orm_result in results:
            self.session.delete(orm_result)

        self._flush()
        self._commit()
        self.logger.info(f"Deleted {deleted} sensitivity results for simulation {simulation_id}")

        return deleted

    def _row_to_entity(self, row: dict[str, Any]) -> SensitivityResult:
        """
        Convert database row to SensitivityResult entity.

        Args:
            row: Database row dict

        Returns:
            SensitivityResult entity
        """
        # Parse JSON fields
        deltas_used = json.loads(row["deltas_used"])
        dimensions_data = json.loads(row["dimensions"])

        # Reconstruct DimensionSensitivity objects
        dimensions = [DimensionSensitivity(**dim_data) for dim_data in dimensions_data]

        # Parse datetime
        analyzed_at = datetime.fromisoformat(row["analyzed_at"])
        if analyzed_at.tzinfo is None:
            analyzed_at = analyzed_at.replace(tzinfo=timezone.utc)

        return SensitivityResult(
            simulation_id=row["simulation_id"],
            analyzed_at=analyzed_at,
            deltas_used=deltas_used,
            dimensions=dimensions,
            most_sensitive_dimension=row["most_sensitive_dimension"],
            baseline_success=row["baseline_success"])

    # =========================================================================
    # ORM conversion methods
    # =========================================================================

    def _orm_to_entity(self, orm_result: SensitivityResultORM) -> SensitivityResult:
        """
        Convert ORM model to SensitivityResult entity.

        Args:
            orm_result: ORM model instance

        Returns:
            SensitivityResult entity
        """
        # Parse datetime
        analyzed_at = orm_result.analyzed_at
        if isinstance(analyzed_at, str):
            analyzed_at = datetime.fromisoformat(analyzed_at)
        if analyzed_at.tzinfo is None:
            analyzed_at = analyzed_at.replace(tzinfo=timezone.utc)

        # ORM stores dimensions as list of dicts
        dimensions_data = orm_result.dimensions or []
        dimensions = [DimensionSensitivity(**dim_data) for dim_data in dimensions_data]

        # ORM stores deltas_used as list
        deltas_used = orm_result.deltas_used or []

        return SensitivityResult(
            simulation_id=orm_result.simulation_id,
            analyzed_at=analyzed_at,
            deltas_used=deltas_used,
            dimensions=dimensions,
            most_sensitive_dimension=orm_result.most_sensitive_dimension,
            baseline_success=orm_result.baseline_success)


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path


    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        repo = SensitivityRepository()

        # Create parent records to satisfy foreign key constraint
        # First create a scorecard, then create a simulation run
        db.execute(
            """
            INSERT INTO feature_scorecards (id, data, created_at)
            VALUES (?, ?, datetime('now'))
            """,
            ("sc_test123", '{"name": "test"}'))
        test_simulation_id = "sim_test123456"
        db.execute(
            """
            INSERT INTO simulation_runs (id, scorecard_id, scenario_id, config, status, started_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (test_simulation_id, "sc_test123", "baseline", '{}', "completed"))

        # Test 1: Save and retrieve a sensitivity result
        total_tests += 1
        try:
            # Create test result
            test_result = SensitivityResult(
                simulation_id=test_simulation_id,
                deltas_used=[0.05, 0.10],
                dimensions=[
                    DimensionSensitivity(
                        dimension="complexity",
                        baseline_value=0.5,
                        deltas_tested=[-0.1, -0.05, 0.05, 0.1],
                        outcomes_by_delta={
                            "-0.1": {"success": 0.3, "failed": 0.4, "did_not_try": 0.3},
                            "-0.05": {"success": 0.4, "failed": 0.35, "did_not_try": 0.25},
                            "0.05": {"success": 0.6, "failed": 0.25, "did_not_try": 0.15},
                            "0.1": {"success": 0.7, "failed": 0.2, "did_not_try": 0.1},
                        },
                        sensitivity_index=2.5,
                        rank=1),
                ],
                most_sensitive_dimension="complexity",
                baseline_success=0.5)

            # Save
            result_id = repo.save_result(test_result)

            # Retrieve by simulation
            retrieved = repo.get_by_simulation(test_simulation_id)

            if retrieved is None:
                all_validation_failures.append("Failed to retrieve saved result by simulation")
            elif retrieved.simulation_id != test_simulation_id:
                all_validation_failures.append(
                    f"Simulation ID mismatch: {retrieved.simulation_id}"
                )
            elif len(retrieved.dimensions) != 1:
                all_validation_failures.append(
                    f"Dimensions count mismatch: {len(retrieved.dimensions)}"
                )
            elif retrieved.baseline_success != 0.5:
                all_validation_failures.append(
                    f"Baseline success mismatch: {retrieved.baseline_success}"
                )
            else:
                print("Test 1 PASSED: Save and retrieve sensitivity result by simulation")
        except Exception as e:
            all_validation_failures.append(f"Save/retrieve by simulation failed: {e}")

        # Test 2: Get by ID
        total_tests += 1
        try:
            retrieved_by_id = repo.get_by_id(result_id)
            if retrieved_by_id is None:
                all_validation_failures.append("Failed to retrieve saved result by ID")
            elif retrieved_by_id.simulation_id != test_simulation_id:
                all_validation_failures.append("Get by ID: simulation ID mismatch")
            else:
                print("Test 2 PASSED: Get sensitivity result by ID")
        except Exception as e:
            all_validation_failures.append(f"Get by ID failed: {e}")

        # Test 3: Get non-existent simulation
        total_tests += 1
        try:
            result = repo.get_by_simulation("non_existent_sim")
            if result is not None:
                all_validation_failures.append(
                    "Should return None for non-existent simulation"
                )
            else:
                print("Test 3 PASSED: Returns None for non-existent simulation")
        except Exception as e:
            all_validation_failures.append(f"Non-existent simulation test failed: {e}")

        # Test 4: Get non-existent ID
        total_tests += 1
        try:
            result = repo.get_by_id("sens_nonexistent")
            if result is not None:
                all_validation_failures.append("Should return None for non-existent ID")
            else:
                print("Test 4 PASSED: Returns None for non-existent ID")
        except Exception as e:
            all_validation_failures.append(f"Non-existent ID test failed: {e}")

        # Test 5: Delete by simulation
        total_tests += 1
        try:
            deleted = repo.delete_by_simulation(test_simulation_id)
            if deleted != 1:
                all_validation_failures.append(f"Expected 1 deleted, got {deleted}")
            elif repo.get_by_simulation(test_simulation_id) is not None:
                all_validation_failures.append("Result still exists after delete")
            else:
                print("Test 5 PASSED: Delete by simulation")
        except Exception as e:
            all_validation_failures.append(f"Delete by simulation failed: {e}")

        # Test 6: Delete non-existent returns 0
        total_tests += 1
        try:
            deleted = repo.delete_by_simulation("non_existent_sim")
            if deleted != 0:
                all_validation_failures.append(
                    f"Delete non-existent should return 0, got {deleted}"
                )
            else:
                print("Test 6 PASSED: Delete non-existent returns 0")
        except Exception as e:
            all_validation_failures.append(f"Delete non-existent test failed: {e}")

        db.close()

    # Final validation result
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
