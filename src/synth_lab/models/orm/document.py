"""
SQLAlchemy ORM model for experiment documents.

This model maps to the 'experiment_documents' table.

References:
    - data-model.md: ExperimentDocument entity definition
    - SQLAlchemy relationships: https://docs.sqlalchemy.org/en/20/orm/relationships.html
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base, MutableJSON

if TYPE_CHECKING:
    from synth_lab.models.orm.experiment import Experiment


class ExperimentDocument(Base):
    """
    Document generated for an experiment.

    Stores generated documents like summaries, PRFAQs, and executive summaries.

    Attributes:
        id: Document identifier
        experiment_id: Link to parent experiment
        document_type: Type enum (exploration_summary, research_prfaq, etc.)
        source_id: ID of the source (exploration_id or exec_id), NULL for executive_summary
        markdown_content: Document content in markdown
        doc_metadata: Generation metadata as JSON (column name: metadata)
        generated_at: ISO timestamp of generation
        model: LLM model used (default: gpt-4o-mini)
        status: pending/generating/completed/failed/partial
        error_message: Error details if failed

    Relationships:
        experiment: N:1 - Parent experiment

    Note:
        source_id contains:
        - exploration_id for exploration_summary, exploration_prfaq
        - exec_id (research_execution_id) for research_summary, research_prfaq
        - NULL for executive_summary (unique per experiment)
    """

    __tablename__ = "experiment_documents"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    doc_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", MutableJSON, nullable=True)
    generated_at: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False, default="gpt-4o-mini")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="documents",
    )

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint(
            "experiment_id", "document_type", "source_id",
            name="uq_experiment_documents_exp_type_source"
        ),
        Index("idx_experiment_documents_experiment", "experiment_id"),
        Index("idx_experiment_documents_type", "document_type"),
        Index("idx_experiment_documents_source", "source_id"),
        Index("idx_experiment_documents_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<ExperimentDocument(id={self.id!r}, type={self.document_type!r}, status={self.status!r})>"


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: ExperimentDocument has correct table name
    total_tests += 1
    if ExperimentDocument.__tablename__ != "experiment_documents":
        all_validation_failures.append(
            f"ExperimentDocument table name is {ExperimentDocument.__tablename__}, expected 'experiment_documents'"
        )

    # Test 2: ExperimentDocument has required columns
    total_tests += 1
    required_columns = {"id", "experiment_id", "document_type", "markdown_content", "metadata", "generated_at", "model", "status", "error_message"}  # Note: doc_metadata maps to 'metadata' column
    actual_columns = set(ExperimentDocument.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"ExperimentDocument missing columns: {missing}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
