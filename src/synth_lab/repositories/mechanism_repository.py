"""
MechanismRepository for synth-lab.

Data access layer for mechanism definitions, options, and feature types.

References:
    - Spec: specs/039-narrative-mechanism-config/spec.md
    - Data model: specs/039-narrative-mechanism-config/data-model.md
    - ORM models: synth_lab.infrastructure.database
"""

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from synth_lab.domain.entities.feature_type import FeatureType
from synth_lab.domain.entities.mechanism_definition import (
    MechanismDefinition,
    MechanismOption,
)
from synth_lab.infrastructure.database import (
    FeatureTypeORM,
    MechanismDefinitionORM,
    MechanismOptionORM,
)
from synth_lab.repositories.base import BaseRepository


class MechanismRepository(BaseRepository):
    """Repository for mechanism data access.

    Provides CRUD operations for mechanism definitions, options, and feature types.

    Usage:
        repo = MechanismRepository(session=db_session)
        mechanisms = repo.list_all_with_options()
    """

    def __init__(self, session: Session | None = None):
        """Initialize repository with optional session."""
        super().__init__(session=session)

    # ========================================================================
    # Read Operations
    # ========================================================================

    def list_all_with_options(self) -> list[MechanismDefinition]:
        """List all mechanism definitions with their options.

        Returns:
            List of MechanismDefinition entities with loaded options.
        """
        stmt = (
            select(MechanismDefinitionORM)
            .options(joinedload(MechanismDefinitionORM.options))
            .order_by(MechanismDefinitionORM.key)
        )

        result = self.session.execute(stmt)
        orm_mechanisms = result.unique().scalars().all()

        return [self._orm_to_entity(orm) for orm in orm_mechanisms]

    def get_by_key(self, key: str) -> MechanismDefinition | None:
        """Get a mechanism definition by its key.

        Args:
            key: Mechanism key (e.g., "irreversibility")

        Returns:
            MechanismDefinition entity or None if not found.
        """
        stmt = (
            select(MechanismDefinitionORM)
            .options(joinedload(MechanismDefinitionORM.options))
            .where(MechanismDefinitionORM.key == key)
        )

        result = self.session.execute(stmt)
        orm = result.unique().scalar_one_or_none()

        return self._orm_to_entity(orm) if orm else None

    def list_feature_types(self) -> list[FeatureType]:
        """List all feature types.

        Returns:
            List of FeatureType entities.
        """
        stmt = select(FeatureTypeORM).order_by(FeatureTypeORM.key)
        result = self.session.execute(stmt)
        orm_types = result.scalars().all()

        return [self._feature_type_orm_to_entity(orm) for orm in orm_types]

    def get_option_by_id(self, option_id: str) -> MechanismOption | None:
        """Get a mechanism option by its ID.

        Args:
            option_id: Option UUID

        Returns:
            MechanismOption or None if not found.
        """
        stmt = select(MechanismOptionORM).where(MechanismOptionORM.id == option_id)
        result = self.session.execute(stmt)
        orm = result.scalar_one_or_none()

        if orm:
            return MechanismOption(
                id=orm.id,
                label=orm.label,
                value=float(orm.value),
                display_order=orm.display_order,
            )
        return None

    # ========================================================================
    # Write Operations (for US4 - Admin)
    # ========================================================================

    def create_mechanism(
        self,
        key: str,
        label_pt: str,
        description: str,
    ) -> MechanismDefinition:
        """Create a new mechanism definition.

        Args:
            key: Programmatic key (lowercase with underscores)
            label_pt: Portuguese display label
            description: Explanation of the mechanism

        Returns:
            Created MechanismDefinition entity.
        """
        mech_id = str(uuid.uuid4())

        orm = MechanismDefinitionORM(
            id=mech_id,
            key=key,
            label_pt=label_pt,
            description=description,
        )

        self.session.add(orm)
        self.session.flush()

        return MechanismDefinition(
            id=mech_id,
            key=key,
            label_pt=label_pt,
            description=description,
            options=[],
        )

    def update_mechanism(
        self,
        key: str,
        label_pt: str | None = None,
        description: str | None = None,
    ) -> MechanismDefinition | None:
        """Update an existing mechanism definition.

        Args:
            key: Mechanism key to update
            label_pt: New Portuguese label (optional)
            description: New description (optional)

        Returns:
            Updated MechanismDefinition or None if not found.
        """
        stmt = (
            select(MechanismDefinitionORM)
            .options(joinedload(MechanismDefinitionORM.options))
            .where(MechanismDefinitionORM.key == key)
        )

        result = self.session.execute(stmt)
        orm = result.unique().scalar_one_or_none()

        if not orm:
            return None

        if label_pt is not None:
            orm.label_pt = label_pt
        if description is not None:
            orm.description = description

        orm.updated_at = datetime.now(timezone.utc)
        self.session.flush()

        return self._orm_to_entity(orm)

    def add_option(
        self,
        mechanism_key: str,
        label: str,
        value: float,
        display_order: int,
    ) -> MechanismOption | None:
        """Add an option to a mechanism.

        Args:
            mechanism_key: Key of the mechanism to add option to
            label: Display text for the option
            value: Numeric value [0.0, 1.0]
            display_order: Order in dropdown

        Returns:
            Created MechanismOption or None if mechanism not found.
        """
        # Get mechanism
        stmt = select(MechanismDefinitionORM).where(
            MechanismDefinitionORM.key == mechanism_key
        )
        result = self.session.execute(stmt)
        mech_orm = result.scalar_one_or_none()

        if not mech_orm:
            return None

        opt_id = str(uuid.uuid4())

        orm = MechanismOptionORM(
            id=opt_id,
            mechanism_id=mech_orm.id,
            label=label,
            value=value,
            display_order=display_order,
        )

        self.session.add(orm)
        self.session.flush()

        return MechanismOption(
            id=opt_id,
            label=label,
            value=value,
            display_order=display_order,
        )

    def update_option(
        self,
        option_id: str,
        label: str | None = None,
        value: float | None = None,
        display_order: int | None = None,
    ) -> MechanismOption | None:
        """Update an existing mechanism option.

        Args:
            option_id: Option UUID to update
            label: New display text (optional)
            value: New numeric value (optional)
            display_order: New order (optional)

        Returns:
            Updated MechanismOption or None if not found.
        """
        stmt = select(MechanismOptionORM).where(MechanismOptionORM.id == option_id)
        result = self.session.execute(stmt)
        orm = result.scalar_one_or_none()

        if not orm:
            return None

        if label is not None:
            orm.label = label
        if value is not None:
            orm.value = value
        if display_order is not None:
            orm.display_order = display_order

        self.session.flush()

        return MechanismOption(
            id=orm.id,
            label=orm.label,
            value=float(orm.value),
            display_order=orm.display_order,
        )

    # ========================================================================
    # Private Helpers
    # ========================================================================

    def _orm_to_entity(self, orm: MechanismDefinitionORM) -> MechanismDefinition:
        """Convert ORM model to domain entity."""
        options = [
            MechanismOption(
                id=opt.id,
                label=opt.label,
                value=float(opt.value),
                display_order=opt.display_order,
            )
            for opt in sorted(orm.options, key=lambda o: o.display_order)
        ]

        return MechanismDefinition(
            id=orm.id,
            key=orm.key,
            label_pt=orm.label_pt,
            description=orm.description,
            options=options,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _feature_type_orm_to_entity(self, orm: FeatureTypeORM) -> FeatureType:
        """Convert feature type ORM model to domain entity."""
        amplifies = orm.amplifies_mechanisms or []
        if isinstance(amplifies, str):
            amplifies = json.loads(amplifies)

        return FeatureType(
            id=orm.id,
            key=orm.key,
            label_pt=orm.label_pt,
            description=orm.description,
            amplifies_mechanisms=amplifies,
            created_at=orm.created_at,
        )
