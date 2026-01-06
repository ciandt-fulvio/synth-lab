"""
SQLAlchemy ORM models for experiments and interview guides.

These models map to the 'experiments' and 'interview_guide' tables.

References:
    - data-model.md: Experiment and InterviewGuide entity definitions
    - SQLAlchemy relationships: https://docs.sqlalchemy.org/en/20/orm/relationships.html
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base, MutableJSON, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from synth_lab.models.orm.analysis import AnalysisRun
    from synth_lab.models.orm.document import ExperimentDocument
    from synth_lab.models.orm.exploration import Exploration
    from synth_lab.models.orm.material import ExperimentMaterial
    from synth_lab.models.orm.research import ResearchExecution


class Experiment(Base, TimestampMixin, SoftDeleteMixin):
    """
    Experiment entity for feature testing.

    Represents a research experiment with hypothesis, scorecard configuration,
    and relationships to analysis runs, research executions, and documents.

    Attributes:
        id: UUID-style identifier (e.g., "exp_12345678")
        name: Experiment name (max 100 chars)
        hypothesis: Research hypothesis (max 500 chars)
        description: Optional detailed description (max 2000 chars)
        scorecard_data: Embedded scorecard configuration as JSON
        status: 'active' or 'deleted' (soft delete)
        created_at: ISO timestamp of creation
        updated_at: ISO timestamp of last update

    Relationships:
        analysis_run: 1:1 - Associated analysis run
        interview_guide: 1:1 - Optional interview guide
        research_executions: 1:N - Multiple research executions
        explorations: 1:N - Multiple scenario explorations
        documents: 1:N - Multiple documents (summary, prfaq, etc.)
        materials: 1:N - Multiple uploaded materials (images, videos, documents)
    """

    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hypothesis: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scorecard_data: Mapped[dict[str, Any] | None] = mapped_column(MutableJSON, nullable=True)

    # Relationships
    analysis_run: Mapped["AnalysisRun | None"] = relationship(
        "AnalysisRun",
        back_populates="experiment",
        uselist=False,
        cascade="all, delete-orphan",
    )
    interview_guide: Mapped["InterviewGuide | None"] = relationship(
        "InterviewGuide",
        back_populates="experiment",
        uselist=False,
        cascade="all, delete-orphan",
    )
    research_executions: Mapped[list["ResearchExecution"]] = relationship(
        "ResearchExecution",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )
    explorations: Mapped[list["Exploration"]] = relationship(
        "Exploration",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["ExperimentDocument"]] = relationship(
        "ExperimentDocument",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )
    materials: Mapped[list["ExperimentMaterial"]] = relationship(
        "ExperimentMaterial",
        back_populates="experiment",
        order_by="ExperimentMaterial.display_order",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_experiments_created", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index("idx_experiments_name", "name"),
        Index("idx_experiments_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Experiment(id={self.id!r}, name={self.name!r}, status={self.status!r})>"


class InterviewGuide(Base, TimestampMixin):
    """
    Interview guide for an experiment (1:1 relationship).

    Contains context definition and questions for conducting
    qualitative research interviews with synths.

    Attributes:
        experiment_id: Primary key and foreign key to experiment
        context_definition: Interview context description
        questions: Interview questions text
        context_examples: Example contexts for reference
        created_at: ISO timestamp of creation
        updated_at: ISO timestamp of last update

    Relationships:
        experiment: N:1 - Parent experiment
    """

    __tablename__ = "interview_guide"

    experiment_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    context_definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    questions: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_examples: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="interview_guide",
    )

    def __repr__(self) -> str:
        return f"<InterviewGuide(experiment_id={self.experiment_id!r})>"


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: Experiment has correct table name
    total_tests += 1
    if Experiment.__tablename__ != "experiments":
        all_validation_failures.append(
            f"Experiment table name is {Experiment.__tablename__}, expected 'experiments'"
        )

    # Test 2: InterviewGuide has correct table name
    total_tests += 1
    if InterviewGuide.__tablename__ != "interview_guide":
        all_validation_failures.append(
            f"InterviewGuide table name is {InterviewGuide.__tablename__}, expected 'interview_guide'"
        )

    # Test 3: Experiment has required columns
    total_tests += 1
    required_columns = {"id", "name", "hypothesis", "description", "scorecard_data", "status", "created_at", "updated_at"}
    actual_columns = set(Experiment.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"Experiment missing columns: {missing}")

    # Test 4: InterviewGuide has required columns
    total_tests += 1
    required_columns = {"experiment_id", "context_definition", "questions", "context_examples", "created_at", "updated_at"}
    actual_columns = set(InterviewGuide.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"InterviewGuide missing columns: {missing}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
