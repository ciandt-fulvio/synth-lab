"""
SQLAlchemy ORM models for simulation runs and interpretations.

These models map to the 'simulation_runs', 'simulation_batches',
and 'analysis_interpretations' tables.

References:
    - Data model: specs/042-quantitative-analysis/data-model.md
    - SQLAlchemy 2.0: https://docs.sqlalchemy.org/en/20/orm/relationships.html
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base

# Fresh JSON type (not shared with MutableDict in base.py)
_JSONVariant = JSON().with_variant(JSONB(), "postgresql")

if TYPE_CHECKING:
    from synth_lab.models.orm.causal_model import CausalModel
    from synth_lab.models.orm.experiment import Experiment


class SimulationBatch(Base):
    """
    Groups multiple scenario runs for one experiment.

    Each batch explores combinations of product calibration values.

    Attributes:
        id: Unique identifier (sb_[a-f0-9]{8})
        experiment_id: FK to experiments.id
        causal_model_id: FK to causal_models.id
        n_scenarios: Number of scenarios in this batch
        n_synths: Number of synths used per scenario
        n_repetitions: MC repetitions per synth (default 10)
        status: running / completed / failed
    """

    __tablename__ = "simulation_batches"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    causal_model_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("causal_models.id", ondelete="CASCADE"),
        nullable=False,
    )
    n_scenarios: Mapped[int] = mapped_column(Integer, nullable=False)
    n_synths: Mapped[int] = mapped_column(Integer, nullable=False)
    n_repetitions: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="running")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", foreign_keys=[experiment_id])
    causal_model: Mapped["CausalModel"] = relationship("CausalModel", foreign_keys=[causal_model_id])
    runs: Mapped[list["SimulationRun"]] = relationship(
        "SimulationRun",
        back_populates="batch",
        cascade="all, delete-orphan",
        foreign_keys="SimulationRun.batch_id",
    )

    __table_args__ = (
        Index("idx_simulation_batches_experiment", "experiment_id"),
    )

    def __repr__(self) -> str:
        return f"<SimulationBatch(id={self.id!r}, status={self.status!r})>"


class SimulationRun(Base):
    """
    Monte Carlo simulation run result.

    Immutable after creation. Multiple runs per experiment (history).
    Batch runs include per_synth_outcomes for cross-scenario analysis.

    Attributes:
        id: Unique identifier (sr_[a-f0-9]{8})
        experiment_id: FK to experiments.id
        causal_model_id: FK to causal_models.id
        n_iterations: Number of Monte Carlo iterations (default 3000)
        n_synths: Number of synths used
        selections: JSON map of node_name -> selected_option at simulation time
        stats: JSON with mean, median, std, p10, p90
        distribution: JSON array of adoption rates per iteration
        segments: JSON with age, income, education breakdowns
        sensitivity: JSON array of per-edge sensitivity results
        batch_id: FK to simulation_batches.id (null for standalone runs)
        product_values: JSON map of product node name -> calibration level (batch runs)
        per_synth_outcomes: JSON dict {synth_id: outcome} with 2 decimal places (batch runs)
    """

    __tablename__ = "simulation_runs"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    causal_model_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("causal_models.id", ondelete="CASCADE"),
        nullable=False,
    )
    n_iterations: Mapped[int] = mapped_column(Integer, nullable=False, default=3000)
    n_synths: Mapped[int] = mapped_column(Integer, nullable=False)
    selections: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    stats: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    distribution: Mapped[list] = mapped_column(_JSONVariant, nullable=False)
    segments: Mapped[dict] = mapped_column(_JSONVariant, nullable=False)
    sensitivity: Mapped[list] = mapped_column(_JSONVariant, nullable=False)
    batch_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("simulation_batches.id", ondelete="SET NULL"),
        nullable=True,
    )
    product_values: Mapped[dict | None] = mapped_column(_JSONVariant, nullable=True)
    per_synth_outcomes: Mapped[dict | None] = mapped_column(_JSONVariant, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", foreign_keys=[experiment_id])
    causal_model: Mapped["CausalModel"] = relationship(
        "CausalModel", foreign_keys=[causal_model_id]
    )
    batch: Mapped["SimulationBatch | None"] = relationship(
        "SimulationBatch",
        back_populates="runs",
        foreign_keys=[batch_id],
    )
    interpretations: Mapped[list["AnalysisInterpretation"]] = relationship(
        "AnalysisInterpretation",
        back_populates="simulation_run",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_simulation_runs_experiment", "experiment_id"),
        Index("idx_simulation_runs_created", "created_at",
              postgresql_ops={"created_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<SimulationRun(id={self.id!r}, experiment_id={self.experiment_id!r})>"


class AnalysisInterpretation(Base):
    """
    AI-generated interpretation for a simulation result section.

    One per section (distribution, segments, sensitivity) per run.
    Unique constraint on (simulation_run_id, section).

    Attributes:
        id: Unique identifier (ai_[a-f0-9]{8})
        simulation_run_id: FK to simulation_runs.id
        section: distribution, segments, or sensitivity
        raw_text: Raw statistical text (no LLM)
        ai_text: AI-generated contextual interpretation
        model: LLM model used (default gpt-4o-mini)
    """

    __tablename__ = "analysis_interpretations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    simulation_run_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("simulation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    section: Mapped[str] = mapped_column(String(20), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    ai_text: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False, default="gpt-4o-mini")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    simulation_run: Mapped["SimulationRun"] = relationship(
        "SimulationRun",
        back_populates="interpretations",
    )

    __table_args__ = (
        UniqueConstraint(
            "simulation_run_id", "section",
            name="uq_interpretations_run_section",
        ),
        Index("idx_interpretations_run", "simulation_run_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<AnalysisInterpretation(id={self.id!r}, "
            f"run={self.simulation_run_id!r}, section={self.section!r})>"
        )


class SimulationReport(Base):
    """
    LLM-generated analysis report for a simulation batch.

    One per batch. Auto-generated after batch completes.
    Content is markdown formatted for PM consumption.

    Attributes:
        id: Unique identifier (srp_[a-f0-9]{8})
        experiment_id: FK to experiments.id (SET NULL on delete)
        batch_id: FK to simulation_batches.id (SET NULL on delete)
        content: Markdown content generated by LLM
        model: LLM model used (e.g. "gpt-4o")
        created_at: Creation timestamp
    """

    __tablename__ = "simulation_reports"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    experiment_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
    )
    batch_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("simulation_batches.id", ondelete="SET NULL"),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False, default="gpt-4o")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_simulation_reports_experiment", "experiment_id"),
    )

    def __repr__(self) -> str:
        return f"<SimulationReport(id={self.id!r}, experiment_id={self.experiment_id!r})>"


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    total_tests += 1
    if SimulationRun.__tablename__ != "simulation_runs":
        all_validation_failures.append(
            f"SimulationRun table: {SimulationRun.__tablename__}, expected 'simulation_runs'"
        )

    total_tests += 1
    if AnalysisInterpretation.__tablename__ != "analysis_interpretations":
        all_validation_failures.append(
            f"AnalysisInterpretation table: {AnalysisInterpretation.__tablename__}"
        )

    total_tests += 1
    sr_cols = set(SimulationRun.__table__.columns.keys())
    required = {
        "id", "experiment_id", "causal_model_id", "n_iterations", "n_synths",
        "selections", "stats", "distribution", "segments", "sensitivity",
        "batch_id", "product_values", "per_synth_outcomes",
    }
    missing = required - sr_cols
    if missing:
        all_validation_failures.append(f"SimulationRun missing columns: {missing}")

    total_tests += 1
    if "synth_results" in {r.key for r in SimulationRun.__mapper__.relationships}:
        all_validation_failures.append("SimulationRun still has synth_results relationship")

    total_tests += 1
    ai_cols = set(AnalysisInterpretation.__table__.columns.keys())
    required = {"id", "simulation_run_id", "section", "raw_text", "ai_text", "model"}
    missing = required - ai_cols
    if missing:
        all_validation_failures.append(f"AnalysisInterpretation missing columns: {missing}")

    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
