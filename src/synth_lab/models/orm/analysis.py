"""
SQLAlchemy ORM models for analysis runs and outcomes.

These models map to the 'analysis_runs', 'synth_outcomes', and 'analysis_cache' tables.

References:
    - data-model.md: AnalysisRun, SynthOutcome, AnalysisCache entity definitions
    - SQLAlchemy relationships: https://docs.sqlalchemy.org/en/20/orm/relationships.html
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base, MutableJSON

if TYPE_CHECKING:
    from synth_lab.models.orm.experiment import Experiment
    from synth_lab.models.orm.exploration import Exploration


class AnalysisRun(Base):
    """
    Analysis run for an experiment.

    Represents a single analysis execution with configuration,
    status tracking, and aggregated outcomes.

    Attributes:
        id: UUID-style identifier
        experiment_id: Link to parent experiment (1:1)
        scenario_id: Scenario identifier (default: 'baseline')
        config: Analysis configuration as JSON
        status: pending/running/completed/failed
        started_at: ISO timestamp of start
        completed_at: ISO timestamp of completion
        total_synths: Number of synths analyzed
        aggregated_outcomes: Aggregated results as JSON
        execution_time_seconds: Total execution time

    Relationships:
        experiment: N:1 - Parent experiment
        synth_outcomes: 1:N - Individual synth results
        analysis_cache: 1:N - Cached chart data
        explorations: 1:N - Explorations using this as baseline
    """

    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    scenario_id: Mapped[str] = mapped_column(String(50), nullable=False, default="baseline")
    config: Mapped[dict[str, Any]] = mapped_column(MutableJSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[str] = mapped_column(String(50), nullable=False)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_synths: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    aggregated_outcomes: Mapped[dict[str, Any] | None] = mapped_column(MutableJSON, nullable=True)
    execution_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="analysis_run",
    )
    synth_outcomes: Mapped[list["SynthOutcome"]] = relationship(
        "SynthOutcome",
        back_populates="analysis_run",
        cascade="all, delete-orphan",
    )
    analysis_cache: Mapped[list["AnalysisCache"]] = relationship(
        "AnalysisCache",
        back_populates="analysis_run",
        cascade="all, delete-orphan",
    )
    explorations: Mapped[list["Exploration"]] = relationship(
        "Exploration",
        back_populates="baseline_analysis",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_analysis_runs_experiment", "experiment_id"),
        Index("idx_analysis_runs_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<AnalysisRun(id={self.id!r}, experiment_id={self.experiment_id!r}, status={self.status!r})>"


class SynthOutcome(Base):
    """
    Individual synth outcome within an analysis run.

    Stores outcome rates for a single synth in an analysis.

    Attributes:
        id: UUID-style identifier
        analysis_id: Link to parent analysis run
        synth_id: Link to synth
        did_not_try_rate: Rate of "did not try"
        failed_rate: Failure rate
        success_rate: Success rate
        synth_attributes: Synth attribute snapshot as JSON

    Relationships:
        analysis_run: N:1 - Parent analysis run
    """

    __tablename__ = "synth_outcomes"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    analysis_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    synth_id: Mapped[str] = mapped_column(String(50), nullable=False)
    did_not_try_rate: Mapped[float] = mapped_column(Float, nullable=False)
    failed_rate: Mapped[float] = mapped_column(Float, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False)
    synth_attributes: Mapped[dict[str, Any] | None] = mapped_column(MutableJSON, nullable=True)

    # Relationships
    analysis_run: Mapped["AnalysisRun"] = relationship(
        "AnalysisRun",
        back_populates="synth_outcomes",
    )

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint("analysis_id", "synth_id", name="uq_synth_outcomes_analysis_synth"),
        Index("idx_outcomes_analysis", "analysis_id"),
    )

    def __repr__(self) -> str:
        return f"<SynthOutcome(id={self.id!r}, synth_id={self.synth_id!r}, success_rate={self.success_rate})>"


class AnalysisCache(Base):
    """
    Cached data for analysis charts and visualizations.

    Stores computed chart data to avoid re-computation.

    Attributes:
        analysis_id: Composite primary key with cache_key
        cache_key: Cache key identifier
        data: Cached data as JSON
        params: Cache parameters as JSON
        computed_at: ISO timestamp of computation

    Relationships:
        analysis_run: N:1 - Parent analysis run
    """

    __tablename__ = "analysis_cache"

    analysis_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    cache_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(MutableJSON, nullable=False)
    params: Mapped[dict[str, Any] | None] = mapped_column(MutableJSON, nullable=True)
    computed_at: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    analysis_run: Mapped["AnalysisRun"] = relationship(
        "AnalysisRun",
        back_populates="analysis_cache",
    )

    # Indexes
    __table_args__ = (
        Index("idx_analysis_cache_analysis", "analysis_id"),
    )

    def __repr__(self) -> str:
        return f"<AnalysisCache(analysis_id={self.analysis_id!r}, cache_key={self.cache_key!r})>"


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: AnalysisRun has correct table name
    total_tests += 1
    if AnalysisRun.__tablename__ != "analysis_runs":
        all_validation_failures.append(
            f"AnalysisRun table name is {AnalysisRun.__tablename__}, expected 'analysis_runs'"
        )

    # Test 2: SynthOutcome has correct table name
    total_tests += 1
    if SynthOutcome.__tablename__ != "synth_outcomes":
        all_validation_failures.append(
            f"SynthOutcome table name is {SynthOutcome.__tablename__}, expected 'synth_outcomes'"
        )

    # Test 3: AnalysisCache has correct table name
    total_tests += 1
    if AnalysisCache.__tablename__ != "analysis_cache":
        all_validation_failures.append(
            f"AnalysisCache table name is {AnalysisCache.__tablename__}, expected 'analysis_cache'"
        )

    # Test 4: AnalysisRun has required columns
    total_tests += 1
    required_columns = {"id", "experiment_id", "scenario_id", "config", "status", "started_at", "completed_at", "total_synths", "aggregated_outcomes", "execution_time_seconds"}
    actual_columns = set(AnalysisRun.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"AnalysisRun missing columns: {missing}")

    # Test 5: SynthOutcome has required columns
    total_tests += 1
    required_columns = {"id", "analysis_id", "synth_id", "did_not_try_rate", "failed_rate", "success_rate", "synth_attributes"}
    actual_columns = set(SynthOutcome.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"SynthOutcome missing columns: {missing}")

    # Test 6: AnalysisCache has required columns
    total_tests += 1
    required_columns = {"analysis_id", "cache_key", "data", "params", "computed_at"}
    actual_columns = set(AnalysisCache.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"AnalysisCache missing columns: {missing}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
