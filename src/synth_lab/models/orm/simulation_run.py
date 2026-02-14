"""
SQLAlchemy ORM models for simulation runs and interpretations.

These models map to the 'simulation_runs' and 'analysis_interpretations' tables.

References:
    - Data model: specs/042-quantitative-analysis/data-model.md
    - SQLAlchemy 2.0: https://docs.sqlalchemy.org/en/20/orm/relationships.html
"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base, JSONVariant, TimestampMixin

if TYPE_CHECKING:
    from synth_lab.models.orm.causal_model import CausalModel
    from synth_lab.models.orm.experiment import Experiment


class SimulationRun(Base, TimestampMixin):
    """
    Monte Carlo simulation run result.

    Immutable after creation. Multiple runs per experiment (history).

    Attributes:
        id: Unique identifier (sr_[a-f0-9]{8})
        experiment_id: FK to experiments.id
        causal_model_id: FK to causal_models.id
        n_iterations: Number of Monte Carlo iterations (default 3000)
        n_synths: Number of synths used
        selections: JSON map of edge_id -> selected_option at simulation time
        stats: JSON with mean, median, std, p10, p90
        distribution: JSON array of adoption rates per iteration
        segments: JSON with age, income, education breakdowns
        sensitivity: JSON array of per-edge sensitivity results
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
    selections: Mapped[dict] = mapped_column(JSONVariant, nullable=False)
    stats: Mapped[dict] = mapped_column(JSONVariant, nullable=False)
    distribution: Mapped[list] = mapped_column(JSONVariant, nullable=False)
    segments: Mapped[dict] = mapped_column(JSONVariant, nullable=False)
    sensitivity: Mapped[list] = mapped_column(JSONVariant, nullable=False)

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", foreign_keys=[experiment_id])
    causal_model: Mapped["CausalModel"] = relationship(
        "CausalModel", foreign_keys=[causal_model_id]
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


class AnalysisInterpretation(Base, TimestampMixin):
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
    required = {"id", "experiment_id", "causal_model_id", "n_iterations", "n_synths",
                "selections", "stats", "distribution", "segments", "sensitivity"}
    missing = required - sr_cols
    if missing:
        all_validation_failures.append(f"SimulationRun missing columns: {missing}")

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
