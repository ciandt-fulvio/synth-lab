"""
SQLAlchemy ORM models for tags.

These models map to the 'tags' and 'experiment_tags' tables.

References:
    - Alembic migration: 20260106_1103_09d318020a17_add_tags_and_experiment_tags_tables.py
    - SQLAlchemy relationships: https://docs.sqlalchemy.org/en/20/orm/relationships.html
"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base

if TYPE_CHECKING:
    from synth_lab.models.orm.experiment import Experiment


class Tag(Base):
    """
    Tag entity for categorizing experiments.

    Attributes:
        id: UUID-style identifier (e.g., "tag_12345678")
        name: Tag name (max 50 chars, unique)
        created_at: ISO timestamp of creation
        updated_at: ISO timestamp of last update (inherited from TimestampMixin)

    Relationships:
        experiment_tags: M:N - Links to experiments via ExperimentTag junction
    """

    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)
    updated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    experiment_tags: Mapped[list["ExperimentTag"]] = relationship(
        "ExperimentTag",
        back_populates="tag",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (Index("idx_tags_name", "name"),)

    def __repr__(self) -> str:
        return f"<Tag(id={self.id!r}, name={self.name!r})>"


class ExperimentTag(Base):
    """
    Junction table for many-to-many relationship between experiments and tags.

    Attributes:
        experiment_id: Foreign key to experiments table
        tag_id: Foreign key to tags table
        created_at: ISO timestamp when tag was added to experiment

    Relationships:
        experiment: N:1 - Parent experiment
        tag: N:1 - Associated tag
    """

    __tablename__ = "experiment_tags"

    experiment_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="experiment_tags",
    )
    tag: Mapped["Tag"] = relationship(
        "Tag",
        back_populates="experiment_tags",
    )

    # Indexes
    __table_args__ = (
        Index("idx_experiment_tags_experiment", "experiment_id"),
        Index("idx_experiment_tags_tag", "tag_id"),
    )

    def __repr__(self) -> str:
        return f"<ExperimentTag(experiment_id={self.experiment_id!r}, tag_id={self.tag_id!r})>"


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: Tag has correct table name
    total_tests += 1
    if Tag.__tablename__ != "tags":
        all_validation_failures.append(
            f"Tag table name is {Tag.__tablename__}, expected 'tags'"
        )

    # Test 2: ExperimentTag has correct table name
    total_tests += 1
    if ExperimentTag.__tablename__ != "experiment_tags":
        all_validation_failures.append(
            f"ExperimentTag table name is {ExperimentTag.__tablename__}, expected 'experiment_tags'"
        )

    # Test 3: Tag has required columns
    total_tests += 1
    required_columns = {"id", "name", "created_at", "updated_at"}
    actual_columns = set(Tag.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"Tag missing columns: {missing}")

    # Test 4: ExperimentTag has required columns
    total_tests += 1
    required_columns = {"experiment_id", "tag_id", "created_at", "updated_at"}
    actual_columns = set(ExperimentTag.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"ExperimentTag missing columns: {missing}")

    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
