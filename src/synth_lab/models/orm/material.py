"""
SQLAlchemy ORM model for experiment materials.

Represents files (images, videos, documents) attached to experiments
for synth interview context.

References:
    - data-model.md: ExperimentMaterial entity definition
    - SQLAlchemy relationships: https://docs.sqlalchemy.org/en/20/orm/relationships.html
"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base

if TYPE_CHECKING:
    from synth_lab.models.orm.experiment import Experiment


class ExperimentMaterial(Base):
    """
    Material file attached to an experiment.

    Stores metadata for images, videos, and documents uploaded by researchers
    for synth interview context. Actual files are stored in S3.

    Attributes:
        id: UUID-style identifier (e.g., "mat_abc123def456")
        experiment_id: Foreign key to parent experiment
        file_type: Category - 'image', 'video', or 'document'
        file_url: Full S3 URL of the uploaded file
        thumbnail_url: Optional S3 URL of generated thumbnail
        file_name: Original filename
        file_size: File size in bytes
        mime_type: MIME type (e.g., "image/png")
        material_type: Purpose - 'design', 'prototype', 'competitor', 'spec', 'other'
        description: AI-generated description (up to 30 words)
        description_status: 'pending', 'generating', 'completed', 'failed'
        display_order: Order for display (0-indexed)
        created_at: ISO timestamp of creation

    Relationships:
        experiment: N:1 - Parent experiment
    """

    __tablename__ = "experiment_materials"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    material_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="materials",
    )

    # Indexes
    __table_args__ = (
        Index("idx_experiment_materials_experiment", "experiment_id"),
        Index("idx_experiment_materials_type", "material_type"),
        Index("idx_experiment_materials_order", "experiment_id", "display_order"),
        Index("idx_experiment_materials_status", "description_status"),
    )

    def __repr__(self) -> str:
        return (
            f"<ExperimentMaterial(id={self.id!r}, "
            f"experiment_id={self.experiment_id!r}, "
            f"file_name={self.file_name!r})>"
        )


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: Table name is correct
    total_tests += 1
    if ExperimentMaterial.__tablename__ != "experiment_materials":
        all_validation_failures.append(
            f"Table name is {ExperimentMaterial.__tablename__}, expected 'experiment_materials'"
        )

    # Test 2: Has all required columns
    total_tests += 1
    required_columns = {
        "id",
        "experiment_id",
        "file_type",
        "file_url",
        "thumbnail_url",
        "file_name",
        "file_size",
        "mime_type",
        "material_type",
        "description",
        "description_status",
        "display_order",
        "created_at",
    }
    actual_columns = set(ExperimentMaterial.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"Missing columns: {missing}")

    # Test 3: Has foreign key to experiments
    total_tests += 1
    fks = [fk.target_fullname for fk in ExperimentMaterial.__table__.foreign_keys]
    if "experiments.id" not in fks:
        all_validation_failures.append(
            f"Missing foreign key to experiments.id, found: {fks}"
        )

    # Test 4: Has indexes
    total_tests += 1
    indexes = [idx.name for idx in ExperimentMaterial.__table__.indexes]
    expected_indexes = [
        "idx_experiment_materials_experiment",
        "idx_experiment_materials_type",
        "idx_experiment_materials_order",
        "idx_experiment_materials_status",
    ]
    missing_indexes = [idx for idx in expected_indexes if idx not in indexes]
    if missing_indexes:
        all_validation_failures.append(f"Missing indexes: {missing_indexes}")

    # Final validation result
    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
