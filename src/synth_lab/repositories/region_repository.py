"""
Region analysis repository for synth-lab.

Handles persistence of region analysis results to database.

Classes:
- RegionRepository: Repository for region analyses

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Data model: specs/016-feature-impact-simulation/data-model.md

Sample usage:
    from synth_lab.repositories.region_repository import RegionRepository

    repo = RegionRepository(db)
    repo.save_region_analyses(analyses)
    regions = repo.get_region_analyses(simulation_id)

Expected output:
    List of RegionAnalysis objects persisted and retrieved from database
"""

import json

from loguru import logger

from synth_lab.domain.entities import RegionAnalysis, RegionRule
from synth_lab.infrastructure.database import DatabaseManager


class RegionRepository:
    """Repository for region analysis results."""

    def __init__(self, db: DatabaseManager) -> None:
        """
        Initialize repository with database manager.

        Args:
            db: Database manager instance
        """
        self.db = db
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

        # Prepare records for insertion
        records = []
        for analysis in analyses:
            # Serialize rules to JSON string
            rules_json = json.dumps([rule.model_dump() for rule in analysis.rules])

            records.append(
                (
                    analysis.id,
                    analysis.simulation_id,
                    rules_json,
                    analysis.rule_text,
                    analysis.synth_count,
                    analysis.synth_percentage,
                    analysis.did_not_try_rate,
                    analysis.failed_rate,
                    analysis.success_rate,
                    analysis.failure_delta,
                )
            )

        # Batch insert
        sql = """
            INSERT INTO region_analyses (
                id, simulation_id, rules, rule_text,
                synth_count, synth_percentage,
                did_not_try_rate, failed_rate, success_rate, failure_delta
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.executemany(sql, records)

        self.logger.info(f"Saved {len(analyses)} region analyses successfully")

    def get_region_analyses(self, simulation_id: str) -> list[RegionAnalysis]:
        """
        Retrieve region analyses for a simulation.

        Args:
            simulation_id: ID of the simulation

        Returns:
            List of RegionAnalysis objects
        """
        self.logger.info(f"Retrieving region analyses for simulation {simulation_id}")

        sql = """
            SELECT *
            FROM region_analyses
            WHERE simulation_id = ?
            ORDER BY failed_rate DESC
        """

        rows = self.db.fetchall(sql, (simulation_id,))

        analyses = []
        for row in rows:
            # Parse rules JSON
            rules_data = json.loads(row["rules"])
            rules = [RegionRule(**rule) for rule in rules_data]

            # Reconstruct RegionAnalysis
            analysis = RegionAnalysis(
                id=row["id"],
                simulation_id=row["simulation_id"],
                rules=rules,
                rule_text=row["rule_text"],
                synth_count=row["synth_count"],
                synth_percentage=row["synth_percentage"],
                did_not_try_rate=row["did_not_try_rate"],
                failed_rate=row["failed_rate"],
                success_rate=row["success_rate"],
                failure_delta=row["failure_delta"],
            )
            analyses.append(analysis)

        self.logger.info(f"Retrieved {len(analyses)} region analyses")
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

        sql = "DELETE FROM region_analyses WHERE simulation_id = ?"
        cursor = self.db.execute(sql, (simulation_id,))
        deleted_count = cursor.rowcount

        self.logger.info(f"Deleted {deleted_count} region analyses")
        return deleted_count


if __name__ == "__main__":
    import sys

    print("=== Region Repository Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Initialize database
    db = DatabaseManager("output/synthlab.db")
    repo = RegionRepository(db)

    # Get a real simulation from database
    sql = "SELECT id FROM simulation_runs LIMIT 1"
    rows = db.fetchall(sql)

    if not rows:
        print("⚠️  WARNING: No simulation_runs found in database")
        print("   Skipping validation - run a simulation first via:")
        print("   uv run python docs/guides/test_simulation.py")
        sys.exit(0)

    test_simulation_id = rows[0]["id"]
    print(f"Using existing simulation: {test_simulation_id}\n")

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
            failure_delta=0.15,
        ),
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
            failure_delta=0.20,
        ),
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
    try:
        retrieved = repo.get_region_analyses(test_simulation_id)
        if len(retrieved) != 2:
            all_validation_failures.append(f"Should retrieve 2 analyses, got {len(retrieved)}")
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
                all_validation_failures.append(
                    f"Rule attribute should be capability_mean, got {first_analysis.rules[0].attribute}"
                )
            else:
                print("Test 3 PASSED: Rules reconstructed correctly")
    except Exception as e:
        all_validation_failures.append(f"Rule reconstruction failed: {e}")

    # Test 4: Delete region analyses
    total_tests += 1
    try:
        deleted_count = repo.delete_region_analyses(test_simulation_id)
        if deleted_count != 2:
            all_validation_failures.append(f"Should delete 2 analyses, deleted {deleted_count}")
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

    # Final result
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
        print("RegionRepository is validated and ready for use")
        sys.exit(0)
