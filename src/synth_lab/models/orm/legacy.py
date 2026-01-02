"""
SQLAlchemy ORM models for legacy/deprecated tables.

These models map to the 'feature_scorecards', 'simulation_runs', and 'prfaq_metadata' tables.
These tables are deprecated and maintained only for backward compatibility.

References:
    - data-model.md: FeatureScorecard, SimulationRun, PRFAQMetadata entity definitions
    - Note: Scorecard data is now embedded in experiments.scorecard_data
    - Note: SimulationRun replaced by analysis_runs table
    - Note: PRFAQMetadata is legacy; documents are now in experiment_documents table
"""

from typing import Any

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from synth_lab.models.orm.base import Base, MutableJSON, TimestampMixin


class FeatureScorecard(Base, TimestampMixin):
    """
    Legacy scorecard model (deprecated).

    Scorecard data is now embedded in experiments.scorecard_data.
    This model is maintained for backward compatibility only.

    Attributes:
        id: Scorecard identifier
        experiment_id: Link to experiment
        data: Scorecard data as JSON
        created_at: ISO timestamp of creation
        updated_at: ISO timestamp of last update
    """

    __tablename__ = "feature_scorecards"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    experiment_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
    )
    data: Mapped[dict[str, Any]] = mapped_column(MutableJSON, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_scorecards_experiment", "experiment_id"),
    )

    def __repr__(self) -> str:
        return f"<FeatureScorecard(id={self.id!r}, experiment_id={self.experiment_id!r})>"


class SimulationRun(Base):
    """
    Legacy simulation run model (deprecated).

    Replaced by analysis_runs table.
    This model is maintained for backward compatibility only.

    Attributes:
        id: Simulation identifier
        scorecard_id: Link to feature scorecard
        scenario_id: Scenario identifier
        config: Simulation configuration as JSON
        status: pending/running/completed/failed
        started_at: ISO timestamp of start
        completed_at: ISO timestamp of completion
        total_synths: Number of synths
        aggregated_outcomes: Aggregated results as JSON
        execution_time_seconds: Execution time
    """

    __tablename__ = "simulation_runs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    scorecard_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("feature_scorecards.id", ondelete="CASCADE"),
        nullable=False,
    )
    scenario_id: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(MutableJSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[str] = mapped_column(String(50), nullable=False)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_synths: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    aggregated_outcomes: Mapped[dict[str, Any] | None] = mapped_column(MutableJSON, nullable=True)
    execution_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_simulations_scorecard", "scorecard_id"),
        Index("idx_simulations_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<SimulationRun(id={self.id!r}, status={self.status!r})>"


class PRFAQMetadata(Base):
    """
    Legacy PR-FAQ metadata model (deprecated).

    PR-FAQ documents are now managed via experiment_documents table.
    This model is maintained for backward compatibility with existing data.

    Attributes:
        exec_id: Research execution ID (primary key, FK to research_executions)
        generated_at: ISO timestamp of generation
        model: LLM model used (default: gpt-4o-mini)
        validation_status: valid/invalid/pending
        confidence_score: Confidence score 0-1
        headline: Press release headline
        one_liner: One-line summary
        faq_count: Number of FAQ items
        markdown_content: PR-FAQ markdown content
        json_content: PR-FAQ JSON content
        status: generating/completed/failed
        error_message: Error details if failed
        started_at: ISO timestamp when generation started
    """

    __tablename__ = "prfaq_metadata"

    exec_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("research_executions.exec_id", ondelete="CASCADE"),
        primary_key=True,
    )
    generated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str] = mapped_column(String(50), nullable=False, default="gpt-4o-mini")
    validation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="valid")
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    headline: Mapped[str | None] = mapped_column(String(500), nullable=True)
    one_liner: Mapped[str | None] = mapped_column(String(500), nullable=True)
    faq_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    markdown_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    json_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_prfaq_generated", "generated_at", postgresql_ops={"generated_at": "DESC"}),
        Index("idx_prfaq_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<PRFAQMetadata(exec_id={self.exec_id!r}, status={self.status!r})>"


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: FeatureScorecard has correct table name
    total_tests += 1
    if FeatureScorecard.__tablename__ != "feature_scorecards":
        tbl = FeatureScorecard.__tablename__
        all_validation_failures.append(
            f"FeatureScorecard table name is {tbl}, expected 'feature_scorecards'"
        )

    # Test 2: SimulationRun has correct table name
    total_tests += 1
    if SimulationRun.__tablename__ != "simulation_runs":
        all_validation_failures.append(
            f"SimulationRun table name is {SimulationRun.__tablename__}, expected 'simulation_runs'"
        )

    # Test 3: FeatureScorecard has required columns
    total_tests += 1
    required_columns = {"id", "experiment_id", "data", "created_at", "updated_at"}
    actual_columns = set(FeatureScorecard.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"FeatureScorecard missing columns: {missing}")

    # Test 4: SimulationRun has required columns
    total_tests += 1
    required_columns = {
        "id", "scorecard_id", "scenario_id", "config", "status", "started_at",
        "completed_at", "total_synths", "aggregated_outcomes", "execution_time_seconds"
    }
    actual_columns = set(SimulationRun.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"SimulationRun missing columns: {missing}")

    # Test 5: PRFAQMetadata has correct table name
    total_tests += 1
    if PRFAQMetadata.__tablename__ != "prfaq_metadata":
        all_validation_failures.append(
            f"PRFAQMetadata table name is {PRFAQMetadata.__tablename__}, expected 'prfaq_metadata'"
        )

    # Test 6: PRFAQMetadata has required columns
    total_tests += 1
    required_columns = {
        "exec_id", "generated_at", "model", "validation_status", "confidence_score",
        "headline", "one_liner", "faq_count", "markdown_content", "json_content",
        "status", "error_message", "started_at"
    }
    actual_columns = set(PRFAQMetadata.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"PRFAQMetadata missing columns: {missing}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
