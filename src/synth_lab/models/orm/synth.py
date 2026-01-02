"""
SQLAlchemy ORM models for synths and synth groups.

These models map to the 'synths' and 'synth_groups' tables.

References:
    - data-model.md: Synth and SynthGroup entity definitions
    - SQLAlchemy relationships: https://docs.sqlalchemy.org/en/20/orm/relationships.html
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base, MutableJSON

if TYPE_CHECKING:
    pass


class SynthGroup(Base):
    """
    Group of synths for organization.

    Attributes:
        id: Group identifier
        name: Group name
        description: Optional group description
        created_at: ISO timestamp of creation

    Relationships:
        synths: 1:N - Synths in this group
    """

    __tablename__ = "synth_groups"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    synths: Mapped[list["Synth"]] = relationship(
        "Synth",
        back_populates="synth_group",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_synth_groups_created", "created_at", postgresql_ops={"created_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<SynthGroup(id={self.id!r}, name={self.name!r})>"


class Synth(Base):
    """
    Synthetic persona for research interviews.

    Attributes:
        id: UUID-style identifier
        synth_group_id: Optional group reference
        nome: Synth name (Portuguese)
        descricao: Description (Portuguese)
        link_photo: External photo URL
        avatar_path: Local avatar file path
        created_at: ISO timestamp of creation
        version: Schema version (default: 2.0.0)
        data: All synth attributes as JSON

    Relationships:
        synth_group: N:1 - Parent group (optional)
    """

    __tablename__ = "synths"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    synth_group_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("synth_groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    link_photo: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="2.0.0")
    data: Mapped[dict[str, Any] | None] = mapped_column(MutableJSON, nullable=True)

    # Relationships
    synth_group: Mapped["SynthGroup | None"] = relationship(
        "SynthGroup",
        back_populates="synths",
    )

    # Indexes
    __table_args__ = (
        Index("idx_synths_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index("idx_synths_nome", "nome"),
        Index("idx_synths_group", "synth_group_id"),
    )

    def __repr__(self) -> str:
        return f"<Synth(id={self.id!r}, nome={self.nome!r})>"


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: SynthGroup has correct table name
    total_tests += 1
    if SynthGroup.__tablename__ != "synth_groups":
        all_validation_failures.append(
            f"SynthGroup table name is {SynthGroup.__tablename__}, expected 'synth_groups'"
        )

    # Test 2: Synth has correct table name
    total_tests += 1
    if Synth.__tablename__ != "synths":
        all_validation_failures.append(
            f"Synth table name is {Synth.__tablename__}, expected 'synths'"
        )

    # Test 3: SynthGroup has required columns
    total_tests += 1
    required_columns = {"id", "name", "description", "created_at"}
    actual_columns = set(SynthGroup.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"SynthGroup missing columns: {missing}")

    # Test 4: Synth has required columns
    total_tests += 1
    required_columns = {"id", "synth_group_id", "nome", "descricao", "link_photo", "avatar_path", "created_at", "version", "data"}
    actual_columns = set(Synth.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"Synth missing columns: {missing}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
