"""
Repository for chart insights persistence.

Handles saving and retrieving LLM-generated insights for simulation charts.
Uses SQLAlchemy ORM for database operations.

References:
    - Spec: specs/017-analysis-ux-research/spec.md (US6)
    - Data model: specs/017-analysis-ux-research/data-model.md
    - Entities: synth_lab.domain.entities.chart_insight
    - ORM models: synth_lab.models.orm.insight

Sample usage:
    from synth_lab.repositories.insight_repository import InsightRepository

    # ORM mode
    repo = InsightRepository(db=get_database())
    insight = repo.get("sim_123", "try_vs_success")

    # ORM mode (SQLAlchemy)
    repo = InsightRepository(session=session)
    insight = repo.get("sim_123", "try_vs_success")

Expected output:
    ChartInsight or None (if not found)
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities.chart_insight import ChartInsight, ChartType
from synth_lab.models.orm.insight import ChartInsight as ChartInsightORM
from synth_lab.repositories.base import BaseRepository


def generate_insight_id() -> str:
    """Generate unique ID for chart insight."""
    return f"ins_{uuid.uuid4().hex[:12]}"


class InsightRepository(BaseRepository):
    """Repository for chart insight persistence.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # ORM mode
        repo = InsightRepository(db=database_manager)

        # ORM mode (SQLAlchemy)
        repo = InsightRepository(session=session)
    """

    # Table name
    TABLE = "chart_insights"

    def __init__(
        self,
session: Session | None = None) -> None:
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session for ORM operations.
        """
        super().__init__(session=session)
        self.logger = logger.bind(component="insight_repository")

    def get(
        self,
        simulation_id: str,
        insight_type: ChartType) -> ChartInsight | None:
        """
        Get insight for a simulation and chart type.

        Args:
            simulation_id: Simulation identifier
            insight_type: Type of chart insight

        Returns:
            ChartInsight if found, None otherwise
        """
        stmt = select(ChartInsightORM).where(
            ChartInsightORM.simulation_id == simulation_id,
            ChartInsightORM.insight_type == insight_type)
        orm_insight = self.session.execute(stmt).scalar_one_or_none()
        if orm_insight is None:
            return None
        return self._orm_to_insight(orm_insight)
    def get_all_for_simulation(
        self,
        simulation_id: str) -> dict[str, ChartInsight]:
        """
        Get all insights for a simulation (excluding executive_summary).

        Args:
            simulation_id: Simulation identifier

        Returns:
            Dict mapping insight_type to ChartInsight
        """
        stmt = (
            select(ChartInsightORM)
            .where(
                ChartInsightORM.simulation_id == simulation_id,
                ChartInsightORM.insight_type != "executive_summary")
            .order_by(ChartInsightORM.created_at.asc())
        )
        orm_insights = list(self.session.execute(stmt).scalars().all())
        result: dict[str, ChartInsight] = {}
        for orm_insight in orm_insights:
            insight = self._orm_to_insight(orm_insight)
            result[orm_insight.insight_type] = insight
        return result
    def save(
        self,
        simulation_id: str,
        insight_type: ChartType,
        insight: ChartInsight) -> str:
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

        # Serialize insight to JSON (dict for ORM, string for SQLite)
        # Use mode="json" to ensure datetime objects are serialized
        insight_dict = insight.model_dump(mode="json")
        response_json = json.dumps(insight_dict)

        # Check if exists
        stmt = select(ChartInsightORM).where(
            ChartInsightORM.simulation_id == simulation_id,
            ChartInsightORM.insight_type == insight_type)
        orm_insight = self.session.execute(stmt).scalar_one_or_none()

        if orm_insight:
            # Update
            orm_insight.response_json = insight_dict
            orm_insight.updated_at = now
            self._flush()
            self._commit()
            insight_id = orm_insight.id
            self.logger.debug(
                f"Updated insight {insight_id} for {simulation_id}/{insight_type}"
            )
        else:
            # Insert
            insight_id = generate_insight_id()
            new_insight = ChartInsightORM(
                id=insight_id,
                simulation_id=simulation_id,
                insight_type=insight_type,
                response_json=insight_dict,
                created_at=now,
                updated_at=now)
            self._add(new_insight)
            self._flush()
            self._commit()
            self.logger.debug(
                f"Saved insight {insight_id} for {simulation_id}/{insight_type}"
            )

        return insight_id
    def save_executive_summary(
        self,
        simulation_id: str,
        summary: str) -> str:
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

        # Serialize as JSON (dict for ORM, string for SQLite)
        summary_dict = {"executive_summary": summary, "generated_at": now}
        response_json = json.dumps(summary_dict)

        stmt = select(ChartInsightORM).where(
            ChartInsightORM.simulation_id == simulation_id,
            ChartInsightORM.insight_type == insight_type)
        orm_insight = self.session.execute(stmt).scalar_one_or_none()

        if orm_insight:
            orm_insight.response_json = summary_dict
            orm_insight.updated_at = now
            self._flush()
            self._commit()
            insight_id = orm_insight.id
        else:
            insight_id = generate_insight_id()
            new_insight = ChartInsightORM(
                id=insight_id,
                simulation_id=simulation_id,
                insight_type=insight_type,
                response_json=summary_dict,
                created_at=now,
                updated_at=now)
            self._add(new_insight)
            self._flush()
            self._commit()

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
        stmt = select(ChartInsightORM).where(
            ChartInsightORM.simulation_id == simulation_id,
            ChartInsightORM.insight_type == "executive_summary")
        orm_insight = self.session.execute(stmt).scalar_one_or_none()
        if orm_insight is None:
            return None
        # response_json is a dict in ORM mode
        return orm_insight.response_json.get("executive_summary")
    def delete_for_simulation(self, simulation_id: str) -> int:
        """
        Delete all insights for a simulation.

        Args:
            simulation_id: Simulation identifier

        Returns:
            Number of deleted records
        """
        stmt = select(ChartInsightORM).where(
            ChartInsightORM.simulation_id == simulation_id
        )
        orm_insights = list(self.session.execute(stmt).scalars().all())
        deleted = len(orm_insights)
        for orm_insight in orm_insights:
            self._delete(orm_insight)
        self._flush()
        self._commit()
        self.logger.info(f"Deleted {deleted} insights for simulation {simulation_id}")
        return deleted
    def delete_insight(
        self,
        simulation_id: str,
        insight_type: ChartType) -> bool:
        """
        Delete a specific insight.

        Args:
            simulation_id: Simulation identifier
            insight_type: Type of chart insight

        Returns:
            True if deleted, False if not found
        """
        stmt = select(ChartInsightORM).where(
            ChartInsightORM.simulation_id == simulation_id,
            ChartInsightORM.insight_type == insight_type)
        orm_insight = self.session.execute(stmt).scalar_one_or_none()
        if orm_insight is None:
            return False
        self._delete(orm_insight)
        self._flush()
        self._commit()
        return True
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

    def _orm_to_insight(self, orm_insight: ChartInsightORM) -> ChartInsight:
        """
        Convert ORM model to ChartInsight entity.

        Args:
            orm_insight: ORM ChartInsight model

        Returns:
            ChartInsight domain entity
        """
        # response_json is already a dict in ORM mode
        return ChartInsight(**orm_insight.response_json)


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Initialize database and repository
    db = get_database()
    repo = InsightRepository()

    # Use a test simulation ID (must match analysis_id pattern)
    test_analysis_id = "ana_12345678"
    test_sim_id = f"sim_{test_analysis_id}"

    # Clean up any existing test data
    repo.delete_for_simulation(test_sim_id)

    # Test 1: Save and retrieve insight
    total_tests += 1
    try:
        test_insight = ChartInsight(
            analysis_id=test_analysis_id,
            chart_type="try_vs_success",
            summary="42% of synths in usability issue quadrant. Analysis shows challenges.",
            status="completed",
            model="gpt-4.1-mini")

        # Save
        insight_id = repo.save(test_sim_id, "try_vs_success", test_insight)

        # Retrieve
        retrieved = repo.get(test_sim_id, "try_vs_success")

        if retrieved is None:
            all_validation_failures.append("Failed to retrieve saved insight")
        elif retrieved.summary != test_insight.summary:
            all_validation_failures.append(
                f"Summary mismatch: {retrieved.summary} != {test_insight.summary}"
            )
        elif retrieved.status != "completed":
            all_validation_failures.append(f"Status mismatch: {retrieved.status}")
        else:
            print(f"Test 1 PASSED: Save and retrieve insight (id={insight_id})")
    except Exception as e:
        all_validation_failures.append(f"Save/retrieve test failed: {e}")

    # Test 2: Update existing insight
    total_tests += 1
    try:
        updated_insight = ChartInsight(
            analysis_id=test_analysis_id,
            chart_type="try_vs_success",
            summary="Updated summary with new analysis.",
            status="completed")

        repo.save(test_sim_id, "try_vs_success", updated_insight)
        retrieved = repo.get(test_sim_id, "try_vs_success")

        if retrieved is None:
            all_validation_failures.append("Failed to retrieve updated insight")
        elif retrieved.summary != "Updated summary with new analysis.":
            all_validation_failures.append(f"Update failed: {retrieved.summary}")
        else:
            print("Test 2 PASSED: Update existing insight")
    except Exception as e:
        all_validation_failures.append(f"Update test failed: {e}")

    # Test 3: Get all insights for simulation
    total_tests += 1
    try:
        # Add another insight
        clustering_insight = ChartInsight(
            analysis_id=test_analysis_id,
            chart_type="clustering",
            summary="3 personas identified via K-means clustering.",
            status="completed")
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
        result = repo.get("non_existent_sim", "dendrogram")
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
            # Should only have try_vs_success (executive_summary is excluded)
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
