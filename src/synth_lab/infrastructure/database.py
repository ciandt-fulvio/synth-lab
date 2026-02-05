"""SQLAlchemy ORM models for mechanism configuration.

Defines database models for mechanism configuration tables (039-narrative-mechanism-config).
Share models (User, ExperimentShare, SynthGroupShare) are in models/orm/.
"""
from sqlalchemy import String, Column, ForeignKey, Integer, Numeric, Text, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from synth_lab.models.orm.base import Base
from synth_lab.models.orm.user import User  # noqa: F401 - Re-exported for backwards compatibility
from synth_lab.models.orm.share import (  # noqa: F401 - Re-exported for backwards compatibility
    ExperimentShare,
    SynthGroupShare,
    PermissionLevel,
)


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
