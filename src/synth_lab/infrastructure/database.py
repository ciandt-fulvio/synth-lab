"""SQLAlchemy ORM models for authentication and sharing.

Defines database models for users, experiment_shares, and synth_group_shares.
"""
from sqlalchemy import String, Column, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import enum


Base = declarative_base()


class PermissionLevel(str, enum.Enum):
    """Permission level for shared resources."""

    VIEWER = "viewer"
    EDITOR = "editor"


class User(Base):
    """User model for authenticated users."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True)
    google_user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)

    # Relationships
    # Note: owned_experiments and owned_synth_groups relationships are defined
    # in models/orm/experiment.py and models/orm/synth.py respectively,
    # using the same Base from models/orm/base.py
    experiment_shares = relationship("ExperimentShare", back_populates="user", foreign_keys="[ExperimentShare.user_id]")
    synth_group_shares = relationship("SynthGroupShare", back_populates="user", foreign_keys="[SynthGroupShare.user_id]")


class ExperimentShare(Base):
    """Experiment sharing model."""

    __tablename__ = "experiment_shares"

    id = Column(UUID(as_uuid=False), primary_key=True)
    experiment_id = Column(String(50), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_level = Column(SQLEnum(PermissionLevel, name="permission_level"), nullable=False)
    granted_at = Column(String(50), nullable=False)
    granted_by_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="experiment_shares", foreign_keys=[user_id])
    granted_by = relationship("User", foreign_keys=[granted_by_id])


class SynthGroupShare(Base):
    """Synth group sharing model."""

    __tablename__ = "synth_group_shares"

    id = Column(UUID(as_uuid=False), primary_key=True)
    synth_group_id = Column(String(50), ForeignKey("synth_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_level = Column(SQLEnum(PermissionLevel, name="permission_level"), nullable=False)
    granted_at = Column(String(50), nullable=False)
    granted_by_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="synth_group_shares", foreign_keys=[user_id])
    granted_by = relationship("User", foreign_keys=[granted_by_id])
