"""
SQLAlchemy ORM models for chart insights and analysis results.

These models map to the 'chart_insights', 'sensitivity_results', and 'region_analyses' tables.

References:
    - data-model.md: ChartInsight, SensitivityResult, RegionAnalysis entity definitions
    - SQLAlchemy relationships: https://docs.sqlalchemy.org/en/20/orm/relationships.html
"""

from typing import Any

from sqlalchemy import Float, Index, Integer, String, Text, UniqueConstraint
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


class SensitivityResult(Base):
    """
    Sensitivity analysis result for a simulation.

    Stores the results of analyzing which dimensions most impact outcomes.

    Attributes:
        id: Result identifier
        simulation_id: Link to simulation
        analyzed_at: Analysis timestamp
        deltas_used: Delta values used in analysis as JSON
        baseline_success: Baseline success rate
        most_sensitive_dimension: Most impactful dimension
        dimensions: All dimension results as JSON
        created_at: ISO timestamp of creation
    """

    __tablename__ = "sensitivity_results"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(String(50), nullable=False)
    analyzed_at: Mapped[str] = mapped_column(String(50), nullable=False)
    deltas_used: Mapped[dict[str, Any]] = mapped_column(MutableJSON, nullable=False)
    baseline_success: Mapped[float] = mapped_column(Float, nullable=False)
    most_sensitive_dimension: Mapped[str] = mapped_column(String(100), nullable=False)
    dimensions: Mapped[dict[str, Any]] = mapped_column(MutableJSON, nullable=False)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_sensitivity_simulation", "simulation_id"),
        Index("idx_sensitivity_analyzed_at", "analyzed_at"),
    )

    def __repr__(self) -> str:
        return f"<SensitivityResult(id={self.id!r}, most_sensitive={self.most_sensitive_dimension!r})>"


class RegionAnalysis(Base):
    """
    Region analysis result for a simulation.

    Stores analysis of synth subgroups with specific characteristics.

    Attributes:
        id: Analysis identifier
        simulation_id: Link to simulation
        rules: Region rules as JSON
        rule_text: Human-readable rules description
        synth_count: Number of synths in region
        synth_percentage: Percentage of total synths
        did_not_try_rate: Region "did not try" rate
        failed_rate: Region failure rate
        success_rate: Region success rate
        failure_delta: Delta from baseline failure rate
    """

    __tablename__ = "region_analyses"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(String(50), nullable=False)
    rules: Mapped[dict[str, Any]] = mapped_column(MutableJSON, nullable=False)
    rule_text: Mapped[str] = mapped_column(Text, nullable=False)
    synth_count: Mapped[int] = mapped_column(Integer, nullable=False)
    synth_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    did_not_try_rate: Mapped[float] = mapped_column(Float, nullable=False)
    failed_rate: Mapped[float] = mapped_column(Float, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False)
    failure_delta: Mapped[float] = mapped_column(Float, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_regions_simulation", "simulation_id"),
    )

    def __repr__(self) -> str:
        return f"<RegionAnalysis(id={self.id!r}, synth_count={self.synth_count})>"


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

    # Test 2: SensitivityResult has correct table name
    total_tests += 1
    if SensitivityResult.__tablename__ != "sensitivity_results":
        all_validation_failures.append(
            f"SensitivityResult table name is {SensitivityResult.__tablename__}, expected 'sensitivity_results'"
        )

    # Test 3: RegionAnalysis has correct table name
    total_tests += 1
    if RegionAnalysis.__tablename__ != "region_analyses":
        all_validation_failures.append(
            f"RegionAnalysis table name is {RegionAnalysis.__tablename__}, expected 'region_analyses'"
        )

    # Test 4: ChartInsight has required columns
    total_tests += 1
    required_columns = {"id", "simulation_id", "insight_type", "response_json", "created_at", "updated_at"}
    actual_columns = set(ChartInsight.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"ChartInsight missing columns: {missing}")

    # Test 5: SensitivityResult has required columns
    total_tests += 1
    required_columns = {"id", "simulation_id", "analyzed_at", "deltas_used", "baseline_success", "most_sensitive_dimension", "dimensions", "created_at"}
    actual_columns = set(SensitivityResult.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"SensitivityResult missing columns: {missing}")

    # Test 6: RegionAnalysis has required columns
    total_tests += 1
    required_columns = {"id", "simulation_id", "rules", "rule_text", "synth_count", "synth_percentage", "did_not_try_rate", "failed_rate", "success_rate", "failure_delta"}
    actual_columns = set(RegionAnalysis.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"RegionAnalysis missing columns: {missing}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
