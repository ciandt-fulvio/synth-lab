"""SQLAlchemy ORM models for sharing resources.

Maps to experiment_shares and synth_group_shares tables.

References:
    - SQLAlchemy 2.0 ORM: https://docs.sqlalchemy.org/en/20/orm/
"""
import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base

if TYPE_CHECKING:
    from synth_lab.models.orm.user import User


class PermissionLevel(str, enum.Enum):
    """Permission level for shared resources."""

    VIEWER = "viewer"
    EDITOR = "editor"


class ExperimentShare(Base):
    """Experiment sharing model.

    Attributes:
        id: UUID of the share
        experiment_id: ID of the shared experiment
        user_id: UUID of the user receiving access
        permission_level: viewer or editor
        granted_at: ISO timestamp when share was created
        granted_by_id: UUID of the user who granted access

    Relationships:
        user: User who has access
        granted_by: User who granted access
    """

    __tablename__ = "experiment_shares"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    permission_level: Mapped[PermissionLevel] = mapped_column(
        SQLEnum(PermissionLevel, name="permission_level"),
        nullable=False
    )
    granted_at: Mapped[str] = mapped_column(String(50), nullable=False)
    granted_by_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
    )
    granted_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[granted_by_id],
    )

    def __repr__(self) -> str:
        return f"<ExperimentShare(id={self.id!r}, experiment_id={self.experiment_id!r}, user_id={self.user_id!r})>"


class SynthGroupShare(Base):
    """Synth group sharing model.

    Attributes:
        id: UUID of the share
        synth_group_id: ID of the shared synth group
        user_id: UUID of the user receiving access
        permission_level: viewer or editor
        granted_at: ISO timestamp when share was created
        granted_by_id: UUID of the user who granted access

    Relationships:
        user: User who has access
        granted_by: User who granted access
    """

    __tablename__ = "synth_group_shares"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    synth_group_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("synth_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    permission_level: Mapped[PermissionLevel] = mapped_column(
        SQLEnum(PermissionLevel, name="permission_level"),
        nullable=False
    )
    granted_at: Mapped[str] = mapped_column(String(50), nullable=False)
    granted_by_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
    )
    granted_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[granted_by_id],
    )

    def __repr__(self) -> str:
        return f"<SynthGroupShare(id={self.id!r}, synth_group_id={self.synth_group_id!r}, user_id={self.user_id!r})>"
