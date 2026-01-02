"""
SQLAlchemy ORM models for research executions and transcripts.

These models map to the 'research_executions' and 'transcripts' tables.

References:
    - data-model.md: ResearchExecution and Transcript entity definitions
    - SQLAlchemy relationships: https://docs.sqlalchemy.org/en/20/orm/relationships.html
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base

if TYPE_CHECKING:
    from synth_lab.models.orm.experiment import Experiment


class ResearchExecution(Base):
    """
    Research execution for conducting synth interviews.

    Represents a batch of interviews with synths on a specific topic.

    Attributes:
        exec_id: Execution identifier (primary key)
        experiment_id: Optional link to parent experiment
        topic_name: Research topic name
        status: pending/running/generating_summary/completed/failed
        synth_count: Total number of synths
        successful_count: Number of successful interviews
        failed_count: Number of failed interviews
        model: LLM model used (default: gpt-4o-mini)
        max_turns: Maximum conversation turns (default: 6)
        started_at: ISO timestamp of start
        completed_at: ISO timestamp of completion
        additional_context: Extra context for interviews

    Relationships:
        experiment: N:1 - Parent experiment (optional)
        transcripts: 1:N - Interview transcripts
    """

    __tablename__ = "research_executions"

    exec_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    experiment_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
    )
    topic_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    synth_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model: Mapped[str] = mapped_column(String(50), nullable=False, default="gpt-4o-mini")
    max_turns: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    started_at: Mapped[str] = mapped_column(String(50), nullable=False)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    additional_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    experiment: Mapped["Experiment | None"] = relationship(
        "Experiment",
        back_populates="research_executions",
    )
    transcripts: Mapped[list["Transcript"]] = relationship(
        "Transcript",
        back_populates="research_execution",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_executions_topic", "topic_name"),
        Index("idx_executions_status", "status"),
        Index("idx_executions_started", "started_at", postgresql_ops={"started_at": "DESC"}),
        Index("idx_executions_experiment", "experiment_id"),
    )

    def __repr__(self) -> str:
        return f"<ResearchExecution(exec_id={self.exec_id!r}, topic={self.topic_name!r}, status={self.status!r})>"


class Transcript(Base):
    """
    Interview transcript for a research execution.

    Contains the conversation messages between interviewer and synth.

    Attributes:
        id: Transcript identifier
        exec_id: Link to research execution
        synth_id: Synth identifier
        synth_name: Synth name snapshot
        status: pending/completed/failed
        turn_count: Number of conversation turns
        timestamp: ISO timestamp
        messages: Conversation messages as JSON

    Relationships:
        research_execution: N:1 - Parent research execution
    """

    __tablename__ = "transcripts"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    exec_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("research_executions.exec_id", ondelete="CASCADE"),
        nullable=False,
    )
    synth_id: Mapped[str] = mapped_column(String(50), nullable=False)
    synth_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    timestamp: Mapped[str] = mapped_column(String(50), nullable=False)
    messages: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    research_execution: Mapped["ResearchExecution"] = relationship(
        "ResearchExecution",
        back_populates="transcripts",
    )

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint("exec_id", "synth_id", name="uq_transcripts_exec_synth"),
        Index("idx_transcripts_exec", "exec_id"),
        Index("idx_transcripts_synth", "synth_id"),
    )

    def __repr__(self) -> str:
        return f"<Transcript(id={self.id!r}, synth_name={self.synth_name!r}, status={self.status!r})>"


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: ResearchExecution has correct table name
    total_tests += 1
    if ResearchExecution.__tablename__ != "research_executions":
        all_validation_failures.append(
            f"ResearchExecution table name is {ResearchExecution.__tablename__}, expected 'research_executions'"
        )

    # Test 2: Transcript has correct table name
    total_tests += 1
    if Transcript.__tablename__ != "transcripts":
        all_validation_failures.append(
            f"Transcript table name is {Transcript.__tablename__}, expected 'transcripts'"
        )

    # Test 3: ResearchExecution has required columns
    total_tests += 1
    required_columns = {"exec_id", "experiment_id", "topic_name", "status", "synth_count", "successful_count", "failed_count", "model", "max_turns", "started_at", "completed_at", "additional_context"}
    actual_columns = set(ResearchExecution.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"ResearchExecution missing columns: {missing}")

    # Test 4: Transcript has required columns
    total_tests += 1
    required_columns = {"id", "exec_id", "synth_id", "synth_name", "status", "turn_count", "timestamp", "messages"}
    actual_columns = set(Transcript.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"Transcript missing columns: {missing}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
