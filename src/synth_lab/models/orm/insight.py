"""
SQLAlchemy ORM models for chart insights.

References:
    - data-model.md: ChartInsight entity definition
    - SQLAlchemy relationships: https://docs.sqlalchemy.org/en/20/orm/relationships.html
"""

from typing import Any

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from synth_lab.models.orm.base import Base, MutableJSON, TimestampMixin


class ChartInsight(Base, TimestampMixin):
    """
    LLM-generated insight for a chart visualization.

    Stores AI analysis responses for simulation/analysis charts.

    Attributes:
        id: Insight identifier
        simulation_id: Link to simulation/analysis
        insight_type: Type of insight (e.g., 'distribution', 'trend')
        response_json: LLM response as JSON
        created_at: ISO timestamp of creation
        updated_at: ISO timestamp of last update
    """

    __tablename__ = "chart_insights"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(String(50), nullable=False)
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)
    response_json: Mapped[dict[str, Any]] = mapped_column(MutableJSON, nullable=False)

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint("simulation_id", "insight_type", name="uq_chart_insights_sim_type"),
        Index("idx_chart_insights_simulation", "simulation_id"),
        Index("idx_chart_insights_type", "insight_type"),
    )

    def __repr__(self) -> str:
        return f"<ChartInsight(id={self.id!r}, type={self.insight_type!r})>"


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: ChartInsight has correct table name
    total_tests += 1
    if ChartInsight.__tablename__ != "chart_insights":
        all_validation_failures.append(
            f"ChartInsight table name is {ChartInsight.__tablename__}, expected 'chart_insights'"
        )

    # Test 2: ChartInsight has required columns
    total_tests += 1
    required_columns = {"id", "simulation_id", "insight_type", "response_json", "created_at", "updated_at"}
    actual_columns = set(ChartInsight.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"ChartInsight missing columns: {missing}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
