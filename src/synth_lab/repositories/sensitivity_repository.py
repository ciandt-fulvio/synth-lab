"""
Repository for sensitivity analysis results.

Handles persistence of sensitivity analysis results in the database.

References:
    - Spec: specs/017-analysis-ux-research/spec.md
    - Data model: specs/017-analysis-ux-research/data-model.md
"""

import json
import uuid
from typing import Any

from loguru import logger

from synth_lab.domain.entities import DimensionSensitivity, SensitivityResult
from synth_lab.infrastructure.database import DatabaseManager


def generate_sensitivity_id() -> str:
    """Generate unique ID for sensitivity analysis."""
    return f"sens_{uuid.uuid4().hex[:12]}"


class SensitivityRepository:
    """Repository for sensitivity analysis results."""

    def __init__(self, db: DatabaseManager) -> None:
        """
        Initialize repository.

        Args:
            db: Database manager instance
        """
        self.db = db
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

        # Serialize dimensions to JSON
        dimensions_json = json.dumps([dim.model_dump() for dim in result.dimensions])

        # Serialize deltas_used to JSON
        deltas_json = json.dumps(result.deltas_used)

        sql = """
            INSERT INTO sensitivity_results (
                id, simulation_id, analyzed_at, deltas_used,
                baseline_success, most_sensitive_dimension, dimensions
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        self.db.execute(
            sql,
            (
                result_id,
                result.simulation_id,
                result.analyzed_at.isoformat(),
                deltas_json,
                result.baseline_success,
                result.most_sensitive_dimension,
                dimensions_json,
            ),
        )

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
        sql = """
            SELECT
                id, simulation_id, analyzed_at, deltas_used,
                baseline_success, most_sensitive_dimension, dimensions
            FROM sensitivity_results
            WHERE simulation_id = ?
            ORDER BY analyzed_at DESC
            LIMIT 1
        """

        rows = self.db.fetchall(sql, (simulation_id,))

        if not rows:
            return None

        row = rows[0]
        return self._row_to_entity(row)

    def get_by_id(self, result_id: str) -> SensitivityResult | None:
        """
        Get sensitivity result by ID.

        Args:
            result_id: ID of the result

        Returns:
            SensitivityResult if found, None otherwise
        """
        sql = """
            SELECT
                id, simulation_id, analyzed_at, deltas_used,
                baseline_success, most_sensitive_dimension, dimensions
            FROM sensitivity_results
            WHERE id = ?
        """

        rows = self.db.fetchall(sql, (result_id,))

        if not rows:
            return None

        row = rows[0]
        return self._row_to_entity(row)

    def delete_by_simulation(self, simulation_id: str) -> int:
        """
        Delete all sensitivity results for a simulation.

        Args:
            simulation_id: ID of the simulation

        Returns:
            Number of deleted results
        """
        sql = "DELETE FROM sensitivity_results WHERE simulation_id = ?"
        cursor = self.db.execute(sql, (simulation_id,))
        deleted = cursor.rowcount

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
        from datetime import datetime, timezone

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
            baseline_success=row["baseline_success"],
        )


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Initialize database and repository
    db = DatabaseManager("output/synthlab.db")
    repo = SensitivityRepository(db)

    # Get an existing simulation for testing
    sql = "SELECT id FROM simulation_runs ORDER BY started_at DESC LIMIT 1"
    rows = db.fetchall(sql)

    if not rows:
        print("⚠️  WARNING: No simulations in database")
        print("   Skipping validation - run a simulation first")
        sys.exit(0)

    test_simulation_id = rows[0]["id"]
    print(f"Using simulation: {test_simulation_id}\n")

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
                    rank=1,
                ),
            ],
            most_sensitive_dimension="complexity",
            baseline_success=0.5,
        )

        # Save
        result_id = repo.save_result(test_result)

        # Retrieve
        retrieved = repo.get_by_simulation(test_simulation_id)

        if retrieved is None:
            all_validation_failures.append("Failed to retrieve saved result")
        elif retrieved.simulation_id != test_simulation_id:
            all_validation_failures.append(f"Simulation ID mismatch: {retrieved.simulation_id}")
        elif len(retrieved.dimensions) != 1:
            all_validation_failures.append(
                f"Dimensions count mismatch: {len(retrieved.dimensions)}"
            )
        elif retrieved.baseline_success != 0.5:
            all_validation_failures.append(
                f"Baseline success mismatch: {retrieved.baseline_success}"
            )
        else:
            print("Test 1 PASSED: Save and retrieve sensitivity result")

        # Cleanup
        repo.delete_by_simulation(test_simulation_id)

    except Exception as e:
        all_validation_failures.append(f"Save/retrieve test failed: {e}")

    # Test 2: Get non-existent result
    total_tests += 1
    try:
        result = repo.get_by_simulation("non_existent_sim")
        if result is not None:
            all_validation_failures.append("Should return None for non-existent simulation")
        else:
            print("Test 2 PASSED: Returns None for non-existent simulation")
    except Exception as e:
        all_validation_failures.append(f"Non-existent result test failed: {e}")

    # Final validation result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("SensitivityRepository is validated and ready for use")
        sys.exit(0)
