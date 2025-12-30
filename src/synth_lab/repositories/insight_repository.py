"""
Repository for chart insights persistence.

Handles saving and retrieving LLM-generated insights for simulation charts.

References:
    - Spec: specs/017-analysis-ux-research/spec.md (US6)
    - Data model: specs/017-analysis-ux-research/data-model.md
    - Entities: synth_lab.domain.entities.chart_insight

Sample usage:
    from synth_lab.repositories.insight_repository import InsightRepository
    from synth_lab.infrastructure.database import get_database

    repo = InsightRepository(get_database())
    insight = repo.get("sim_123", "try_vs_success")
    if insight is None:
        # Generate via LLM and save
        repo.save("sim_123", "try_vs_success", chart_insight)

Expected output:
    ChartInsight or None (if not found)
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from loguru import logger

from synth_lab.domain.entities.chart_insight import ChartInsight, ChartType
from synth_lab.infrastructure.database import DatabaseManager, get_database


def generate_insight_id() -> str:
    """Generate unique ID for chart insight."""
    return f"ins_{uuid.uuid4().hex[:12]}"


class InsightRepository:
    """Repository for chart insight persistence."""

    # Table name
    TABLE = "chart_insights"

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """
        Initialize repository.

        Args:
            db: Database manager instance. Defaults to global instance.
        """
        self.db = db or get_database()
        self.logger = logger.bind(component="insight_repository")
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Create table if it doesn't exist."""
        sql = """
            CREATE TABLE IF NOT EXISTS chart_insights (
                id TEXT PRIMARY KEY,
                simulation_id TEXT NOT NULL,
                insight_type TEXT NOT NULL,
                response_json TEXT NOT NULL CHECK(json_valid(response_json)),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(simulation_id, insight_type)
            )
        """
        self.db.execute(sql)

        # Create indices
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_chart_insights_simulation "
            "ON chart_insights(simulation_id)"
        )
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_chart_insights_type ON chart_insights(insight_type)"
        )

    def get(
        self,
        simulation_id: str,
        insight_type: ChartType,
    ) -> ChartInsight | None:
        """
        Get insight for a simulation and chart type.

        Args:
            simulation_id: Simulation identifier
            insight_type: Type of chart insight

        Returns:
            ChartInsight if found, None otherwise
        """
        sql = """
            SELECT id, simulation_id, insight_type, response_json, created_at, updated_at
            FROM chart_insights
            WHERE simulation_id = ? AND insight_type = ?
        """

        row = self.db.fetchone(sql, (simulation_id, insight_type))

        if row is None:
            return None

        return self._row_to_insight(row)

    def get_all_for_simulation(
        self,
        simulation_id: str,
    ) -> dict[str, ChartInsight]:
        """
        Get all insights for a simulation (excluding executive_summary).

        Args:
            simulation_id: Simulation identifier

        Returns:
            Dict mapping insight_type to ChartInsight
        """
        sql = """
            SELECT id, simulation_id, insight_type, response_json, created_at, updated_at
            FROM chart_insights
            WHERE simulation_id = ? AND insight_type != 'executive_summary'
            ORDER BY created_at ASC
        """

        rows = self.db.fetchall(sql, (simulation_id,))

        result: dict[str, ChartInsight] = {}
        for row in rows:
            insight = self._row_to_insight(row)
            result[row["insight_type"]] = insight

        return result

    def save(
        self,
        simulation_id: str,
        insight_type: ChartType,
        insight: ChartInsight,
    ) -> str:
        """
        Save or update an insight.

        Args:
            simulation_id: Simulation identifier
            insight_type: Type of chart insight
            insight: ChartInsight to save

        Returns:
            ID of the saved insight
        """
        now = datetime.now(timezone.utc).isoformat()

        # Serialize insight to JSON
        response_json = json.dumps(insight.model_dump())

        # Check if exists
        existing = self.get(simulation_id, insight_type)

        if existing:
            # Update
            sql = """
                UPDATE chart_insights
                SET response_json = ?, updated_at = ?
                WHERE simulation_id = ? AND insight_type = ?
            """
            self.db.execute(sql, (response_json, now, simulation_id, insight_type))

            # Get the ID
            row = self.db.fetchone(
                "SELECT id FROM chart_insights WHERE simulation_id = ? AND insight_type = ?",
                (simulation_id, insight_type),
            )
            insight_id = row["id"] if row else generate_insight_id()

            self.logger.debug(f"Updated insight {insight_id} for {simulation_id}/{insight_type}")
        else:
            # Insert
            insight_id = generate_insight_id()
            sql = """
                INSERT INTO chart_insights (
                    id, simulation_id, insight_type, response_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db.execute(sql, (insight_id, simulation_id, insight_type, response_json, now, now))

            self.logger.debug(f"Saved insight {insight_id} for {simulation_id}/{insight_type}")

        return insight_id

    def save_executive_summary(
        self,
        simulation_id: str,
        summary: str,
    ) -> str:
        """
        Save executive summary for a simulation.

        Args:
            simulation_id: Simulation identifier
            summary: Executive summary text

        Returns:
            ID of the saved record
        """
        now = datetime.now(timezone.utc).isoformat()
        insight_type = "executive_summary"

        # Serialize as JSON
        response_json = json.dumps({"executive_summary": summary, "generated_at": now})

        # Check if exists
        existing_row = self.db.fetchone(
            "SELECT id FROM chart_insights WHERE simulation_id = ? AND insight_type = ?",
            (simulation_id, insight_type),
        )

        if existing_row:
            sql = """
                UPDATE chart_insights
                SET response_json = ?, updated_at = ?
                WHERE simulation_id = ? AND insight_type = ?
            """
            self.db.execute(sql, (response_json, now, simulation_id, insight_type))
            insight_id = existing_row["id"]
        else:
            insight_id = generate_insight_id()
            sql = """
                INSERT INTO chart_insights (
                    id, simulation_id, insight_type, response_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db.execute(sql, (insight_id, simulation_id, insight_type, response_json, now, now))

        self.logger.debug(f"Saved executive summary for {simulation_id}")
        return insight_id

    def get_executive_summary(self, simulation_id: str) -> str | None:
        """
        Get executive summary for a simulation.

        Args:
            simulation_id: Simulation identifier

        Returns:
            Executive summary text or None
        """
        sql = """
            SELECT response_json
            FROM chart_insights
            WHERE simulation_id = ? AND insight_type = 'executive_summary'
        """
        row = self.db.fetchone(sql, (simulation_id,))

        if row is None:
            return None

        data = json.loads(row["response_json"])
        return data.get("executive_summary")

    def delete_for_simulation(self, simulation_id: str) -> int:
        """
        Delete all insights for a simulation.

        Args:
            simulation_id: Simulation identifier

        Returns:
            Number of deleted records
        """
        sql = "DELETE FROM chart_insights WHERE simulation_id = ?"
        cursor = self.db.execute(sql, (simulation_id,))
        deleted = cursor.rowcount

        self.logger.info(f"Deleted {deleted} insights for simulation {simulation_id}")
        return deleted

    def delete_insight(
        self,
        simulation_id: str,
        insight_type: ChartType,
    ) -> bool:
        """
        Delete a specific insight.

        Args:
            simulation_id: Simulation identifier
            insight_type: Type of chart insight

        Returns:
            True if deleted, False if not found
        """
        sql = "DELETE FROM chart_insights WHERE simulation_id = ? AND insight_type = ?"
        cursor = self.db.execute(sql, (simulation_id, insight_type))
        return cursor.rowcount > 0

    def _row_to_insight(self, row: dict[str, Any]) -> ChartInsight:
        """
        Convert database row to ChartInsight entity.

        Args:
            row: Database row dict

        Returns:
            ChartInsight entity
        """
        data = json.loads(row["response_json"])
        return ChartInsight(**data)


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Initialize database and repository
    db = get_database()
    repo = InsightRepository(db)

    # Use a test simulation ID
    test_sim_id = "sim_test_insight_repo"

    # Clean up any existing test data
    repo.delete_for_simulation(test_sim_id)

    # Test 1: Save and retrieve insight
    total_tests += 1
    try:
        test_insight = ChartInsight(
            simulation_id=test_sim_id,
            chart_type="try_vs_success",
            caption="42% of synths in usability issue quadrant",
            explanation="Analysis shows significant usability challenges.",
            evidence=["Point 1", "Point 2"],
            recommendation="Focus on improving discoverability",
            confidence=0.95,
        )

        # Save
        insight_id = repo.save(test_sim_id, "try_vs_success", test_insight)

        # Retrieve
        retrieved = repo.get(test_sim_id, "try_vs_success")

        if retrieved is None:
            all_validation_failures.append("Failed to retrieve saved insight")
        elif retrieved.caption != test_insight.caption:
            all_validation_failures.append(
                f"Caption mismatch: {retrieved.caption} != {test_insight.caption}"
            )
        elif retrieved.confidence != 0.95:
            all_validation_failures.append(f"Confidence mismatch: {retrieved.confidence}")
        else:
            print(f"Test 1 PASSED: Save and retrieve insight (id={insight_id})")
    except Exception as e:
        all_validation_failures.append(f"Save/retrieve test failed: {e}")

    # Test 2: Update existing insight
    total_tests += 1
    try:
        updated_insight = ChartInsight(
            simulation_id=test_sim_id,
            chart_type="try_vs_success",
            caption="Updated caption",
            explanation="Updated explanation",
        )

        repo.save(test_sim_id, "try_vs_success", updated_insight)
        retrieved = repo.get(test_sim_id, "try_vs_success")

        if retrieved is None:
            all_validation_failures.append("Failed to retrieve updated insight")
        elif retrieved.caption != "Updated caption":
            all_validation_failures.append(f"Update failed: {retrieved.caption}")
        else:
            print("Test 2 PASSED: Update existing insight")
    except Exception as e:
        all_validation_failures.append(f"Update test failed: {e}")

    # Test 3: Get all insights for simulation
    total_tests += 1
    try:
        # Add another insight
        clustering_insight = ChartInsight(
            simulation_id=test_sim_id,
            chart_type="clustering",
            caption="3 personas identified",
            explanation="K-means clustering results.",
        )
        repo.save(test_sim_id, "clustering", clustering_insight)

        all_insights = repo.get_all_for_simulation(test_sim_id)

        if len(all_insights) != 2:
            all_validation_failures.append(f"Expected 2 insights, got {len(all_insights)}")
        elif "try_vs_success" not in all_insights:
            all_validation_failures.append("try_vs_success not in results")
        elif "clustering" not in all_insights:
            all_validation_failures.append("clustering not in results")
        else:
            print("Test 3 PASSED: Get all insights for simulation")
    except Exception as e:
        all_validation_failures.append(f"Get all test failed: {e}")

    # Test 4: Save and retrieve executive summary
    total_tests += 1
    try:
        summary = "This is an executive summary of the analysis."
        repo.save_executive_summary(test_sim_id, summary)

        retrieved_summary = repo.get_executive_summary(test_sim_id)

        if retrieved_summary != summary:
            all_validation_failures.append(f"Summary mismatch: {retrieved_summary} != {summary}")
        else:
            print("Test 4 PASSED: Save and retrieve executive summary")
    except Exception as e:
        all_validation_failures.append(f"Executive summary test failed: {e}")

    # Test 5: Get non-existent insight
    total_tests += 1
    try:
        result = repo.get("non_existent_sim", "tornado")
        if result is not None:
            all_validation_failures.append("Should return None for non-existent")
        else:
            print("Test 5 PASSED: Returns None for non-existent insight")
    except Exception as e:
        all_validation_failures.append(f"Non-existent test failed: {e}")

    # Test 6: Delete specific insight
    total_tests += 1
    try:
        deleted = repo.delete_insight(test_sim_id, "clustering")
        if not deleted:
            all_validation_failures.append("Delete should return True")
        else:
            remaining = repo.get_all_for_simulation(test_sim_id)
            # Should have try_vs_success and executive_summary
            if "clustering" in remaining:
                all_validation_failures.append("clustering should be deleted")
            else:
                print("Test 6 PASSED: Delete specific insight")
    except Exception as e:
        all_validation_failures.append(f"Delete specific test failed: {e}")

    # Cleanup
    repo.delete_for_simulation(test_sim_id)

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
        print("InsightRepository is validated and ready for use")
        sys.exit(0)
