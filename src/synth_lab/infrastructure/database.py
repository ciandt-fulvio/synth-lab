"""SQLAlchemy ORM models for authentication, sharing, and mechanism configuration.

Defines database models for users, experiment_shares, synth_group_shares,
and mechanism configuration tables (039-narrative-mechanism-config).
"""
from sqlalchemy import String, Column, ForeignKey, Enum as SQLEnum, Integer, Numeric, Text, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
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


# ============================================================================
# Mechanism Configuration Models (039-narrative-mechanism-config)
# ============================================================================


class MechanismDefinitionORM(Base):
    """SQLAlchemy model for mechanism definitions.

    Defines a mechanism (e.g., irreversibility, network_effect) that can be
    configured by users via narrative dropdowns.

    References:
        - Spec: specs/039-narrative-mechanism-config/data-model.md
    """

    __tablename__ = "mechanism_definitions"

    id = Column(UUID(as_uuid=False), primary_key=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    label_pt = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    # Relationships
    options = relationship(
        "MechanismOptionORM",
        back_populates="mechanism",
        cascade="all, delete-orphan",
        order_by="MechanismOptionORM.display_order",
    )


class MechanismOptionORM(Base):
    """SQLAlchemy model for mechanism options.

    A text option for a mechanism (e.g., "totalmente reversível" with value 0.0).

    References:
        - Spec: specs/039-narrative-mechanism-config/data-model.md
    """

    __tablename__ = "mechanism_options"
    __table_args__ = (
        CheckConstraint("value >= 0 AND value <= 1", name="check_mechanism_option_value_range"),
    )

    id = Column(UUID(as_uuid=False), primary_key=True)
    mechanism_id = Column(
        UUID(as_uuid=False),
        ForeignKey("mechanism_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label = Column(String(100), nullable=False)
    value = Column(Numeric(3, 2), nullable=False)
    display_order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    mechanism = relationship("MechanismDefinitionORM", back_populates="options")


class FeatureTypeORM(Base):
    """SQLAlchemy model for feature types.

    Categorizes features (e.g., financial, social) and specifies which mechanisms
    are amplified for that type.

    References:
        - Spec: specs/039-narrative-mechanism-config/data-model.md
    """

    __tablename__ = "feature_types"

    id = Column(UUID(as_uuid=False), primary_key=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    label_pt = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    amplifies_mechanisms = Column(JSONB, nullable=False, server_default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
