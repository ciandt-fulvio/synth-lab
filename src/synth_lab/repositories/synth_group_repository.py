"""
T014 SynthGroupRepository for synth-lab.

Data access layer for synth group data. Uses SQLAlchemy ORM for database operations.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - Data model: specs/018-experiment-hub/data-model.md
    - ORM models: synth_lab.models.orm.synth
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy import func as sqlfunc
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities.synth_group import (
    DEFAULT_SYNTH_GROUP_DESCRIPTION,
    DEFAULT_SYNTH_GROUP_ID,
    DEFAULT_SYNTH_GROUP_NAME,
    SynthGroup,
)
from synth_lab.models.orm.synth import Synth as SynthORM
from synth_lab.models.orm.synth import SynthGroup as SynthGroupORM
from synth_lab.models.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from synth_lab.repositories.base import BaseRepository


class SynthGroupSummary(BaseModel):
    """Summary of a synth group for list display."""

    id: str = Field(description="Group ID.")
    name: str = Field(description="Group name.")
    description: str | None = Field(default=None, description="Group description.")
    synth_count: int = Field(default=0, description="Number of synths in group.")
    created_at: datetime = Field(description="Creation timestamp.")
    config: dict | None = Field(default=None, description="Distribution configuration.")


class SynthSummary(BaseModel):
    """Summary of a synth for group detail display."""

    id: str = Field(description="Synth ID.")
    nome: str = Field(description="Synth name.")
    descricao: str | None = Field(default=None, description="Synth description.")
    avatar_path: str | None = Field(default=None, description="Path to avatar image.")
    synth_group_id: str | None = Field(default=None, description="Group ID.")
    created_at: datetime = Field(description="Creation timestamp.")


class SynthGroupDetail(BaseModel):
    """Full synth group details including synths."""

    id: str = Field(description="Group ID.")
    name: str = Field(description="Group name.")
    description: str | None = Field(default=None, description="Group description.")
    synth_count: int = Field(default=0, description="Number of synths in group.")
    created_at: datetime = Field(description="Creation timestamp.")
    config: dict | None = Field(default=None, description="Distribution configuration.")
    synths: list[SynthSummary] = Field(default_factory=list, description="Synths in this group.")


class SynthGroupRepository(BaseRepository):
    """Repository for synth group data access.

    Uses SQLAlchemy ORM for database operations.
    """

    def __init__(self, session: Session | None = None):
        super().__init__(session=session)

    def ensure_default_group(self) -> SynthGroupSummary:
        """
        Ensure the default synth group exists.

        Creates the default group if it doesn't exist, returns it if it does.
        This is the group used when no specific group is provided during synth generation.

        Returns:
            SynthGroupSummary: The default synth group.
        """
        # Check if default group exists
        existing = self.get_by_id(DEFAULT_SYNTH_GROUP_ID)
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        orm_group = SynthGroupORM(
            id=DEFAULT_SYNTH_GROUP_ID,
            name=DEFAULT_SYNTH_GROUP_NAME,
            description=DEFAULT_SYNTH_GROUP_DESCRIPTION,
            created_at=now.isoformat(),
        )
        self._add(orm_group)
        self._flush()
        self._commit()
        return self.get_by_id(DEFAULT_SYNTH_GROUP_ID)

    def create(self, group: SynthGroup, config: dict | None = None) -> SynthGroup:
        """
        Create a new synth group.

        Args:
            group: SynthGroup entity to create.
            config: Optional distribution configuration (JSONB).

        Returns:
            Created synth group with persisted data.
        """
        orm_group = SynthGroupORM(
            id=group.id,
            name=group.name,
            description=group.description,
            created_at=group.created_at.isoformat(),
            config=config,
        )
        self._add(orm_group)
        self._flush()
        self._commit()
        return group

    def create_with_config(
        self,
        group: SynthGroup,
        config: dict,
        synths: list[SynthORM] | None = None,
    ) -> SynthGroupSummary:
        """
        Create a new synth group with config and optionally synths atomically.

        Args:
            group: SynthGroup entity to create.
            config: Distribution configuration (JSONB).
            synths: Optional list of synth ORM objects to persist with the group.

        Returns:
            Created synth group summary with config.
        """
        orm_group = SynthGroupORM(
            id=group.id,
            name=group.name,
            description=group.description,
            created_at=group.created_at.isoformat(),
            config=config,
        )
        self._add(orm_group)

        # Add synths if provided
        if synths:
            for synth in synths:
                synth.synth_group_id = group.id
                self._add(synth)

        # Calculate synth count before commit to avoid DetachedInstanceError
        synth_count = len(synths) if synths else 0

        self._flush()
        self._commit()

        # Build summary manually to avoid accessing detached orm_group.synths relationship
        created_at = group.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return SynthGroupSummary(
            id=orm_group.id,
            name=orm_group.name,
            description=orm_group.description,
            synth_count=synth_count,
            created_at=created_at,
            config=config,
        )

    def get_by_id(self, group_id: str) -> SynthGroupSummary | None:
        """
        Get a synth group by ID with synth count.

        Args:
            group_id: Group ID to retrieve.

        Returns:
            SynthGroupSummary if found, None otherwise.
        """
        orm_group = self.session.get(SynthGroupORM, group_id)
        if orm_group is None:
            return None
        return self._orm_to_summary(orm_group)

    def get_detail(self, group_id: str) -> SynthGroupDetail | None:
        """
        Get a synth group with full details including synths.

        Args:
            group_id: Group ID to retrieve.

        Returns:
            SynthGroupDetail if found, None otherwise.
        """
        orm_group = self.session.get(SynthGroupORM, group_id)
        if orm_group is None:
            return None

        created_at = orm_group.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        # Sort synths by created_at descending
        def get_sort_key(s: SynthORM) -> str:
            if isinstance(s.created_at, str):
                return s.created_at
            return s.created_at.isoformat()

        orm_synths = sorted(orm_group.synths, key=get_sort_key, reverse=True)

        synths = [self._orm_synth_to_summary(s) for s in orm_synths]

        return SynthGroupDetail(
            id=orm_group.id,
            name=orm_group.name,
            description=orm_group.description,
            synth_count=len(synths),
            created_at=created_at,
            config=orm_group.config,
            synths=synths,
        )

    def list_groups(self, params: PaginationParams) -> PaginatedResponse[SynthGroupSummary]:
        """
        List synth groups with pagination.

        Args:
            params: Pagination parameters.

        Returns:
            Paginated response with synth group summaries.
        """
        stmt = select(SynthGroupORM).order_by(SynthGroupORM.created_at.desc())
        count_stmt = select(sqlfunc.count()).select_from(SynthGroupORM)
        total = self.session.execute(count_stmt).scalar() or 0

        stmt = stmt.limit(params.limit).offset(params.offset)
        groups = list(self.session.execute(stmt).scalars().all())

        summaries = [self._orm_to_summary(g) for g in groups]
        meta = PaginationMeta.from_params(total, params)
        return PaginatedResponse(data=summaries, pagination=meta)

    def delete(self, group_id: str) -> bool:
        """
        Delete a synth group.

        Nullifies synth_group_id references in synths table.

        Args:
            group_id: ID of group to delete.

        Returns:
            True if deleted, False if not found.
        """
        orm_group = self.session.get(SynthGroupORM, group_id)
        if orm_group is None:
            return False

        # Nullify synth references
        for synth in orm_group.synths:
            synth.synth_group_id = None

        self.session.delete(orm_group)
        self._flush()
        self._commit()
        return True

    def _row_to_summary(self, row) -> SynthGroupSummary:
        """Convert a database row to SynthGroupSummary."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return SynthGroupSummary(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            synth_count=row["synth_count"],
            created_at=created_at,
        )

    def _row_to_synth_summary(self, row) -> SynthSummary:
        """Convert a database row to SynthSummary."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return SynthSummary(
            id=row["id"],
            nome=row["nome"],
            descricao=row["descricao"],
            avatar_path=row["avatar_path"],
            synth_group_id=row["synth_group_id"],
            created_at=created_at,
        )

    # =========================================================================
    # ORM conversion methods
    # =========================================================================

    def _orm_to_summary(self, orm_group: SynthGroupORM) -> SynthGroupSummary:
        """Convert ORM model to SynthGroupSummary."""
        created_at = orm_group.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        synth_count = len(orm_group.synths) if orm_group.synths else 0

        return SynthGroupSummary(
            id=orm_group.id,
            name=orm_group.name,
            description=orm_group.description,
            synth_count=synth_count,
            created_at=created_at,
            config=orm_group.config,
        )

    def _orm_synth_to_summary(self, orm_synth: SynthORM) -> SynthSummary:
        """Convert ORM Synth model to SynthSummary."""
        created_at = orm_synth.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return SynthSummary(
            id=orm_synth.id,
            nome=orm_synth.nome,
            descricao=orm_synth.descricao,
            avatar_path=orm_synth.avatar_path,
            synth_group_id=orm_synth.synth_group_id,
            created_at=created_at,
        )


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.synth_group import SynthGroup

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)  # Initialize schema first
        db = DatabaseManager(test_db_path)
        repo = SynthGroupRepository()

        # Test 0: Default group should already exist after init_database
        total_tests += 1
        try:
            default_group = repo.get_by_id(DEFAULT_SYNTH_GROUP_ID)
            if default_group is None:
                all_validation_failures.append("Default group not found after init_database")
            elif default_group.name != DEFAULT_SYNTH_GROUP_NAME:
                all_validation_failures.append(f"Default group name mismatch: {default_group.name}")
        except Exception as e:
            all_validation_failures.append(f"Default group check failed: {e}")

        # Test 1: Create synth group
        total_tests += 1
        try:
            group = SynthGroup(name="Test Group", description="Test description")
            result = repo.create(group)
            if result.id != group.id:
                all_validation_failures.append(f"ID mismatch: {result.id} != {group.id}")
        except Exception as e:
            all_validation_failures.append(f"Create synth group failed: {e}")

        # Test 2: Get synth group by ID
        total_tests += 1
        try:
            retrieved = repo.get_by_id(group.id)
            if retrieved is None:
                all_validation_failures.append("Get by ID returned None")
            elif retrieved.name != "Test Group":
                all_validation_failures.append(f"Name mismatch: {retrieved.name}")
        except Exception as e:
            all_validation_failures.append(f"Get by ID failed: {e}")

        # Test 3: Get non-existent group
        total_tests += 1
        try:
            result = repo.get_by_id("grp_nonexist")
            if result is not None:
                all_validation_failures.append("Should return None for non-existent")
        except Exception as e:
            all_validation_failures.append(f"Get non-existent failed: {e}")

        # Test 4: List groups (should have default + created group = 2)
        total_tests += 1
        try:
            params = PaginationParams(limit=10, offset=0)
            result = repo.list_groups(params)
            # Default group + created group = 2
            if len(result.data) != 2:
                all_validation_failures.append(
                    f"Expected 2 groups (default + created), got {len(result.data)}"
                )
        except Exception as e:
            all_validation_failures.append(f"List groups failed: {e}")

        # Test 5: Delete group
        total_tests += 1
        try:
            result = repo.delete(group.id)
            if not result:
                all_validation_failures.append("Delete returned False")
            if repo.get_by_id(group.id) is not None:
                all_validation_failures.append("Group still exists after delete")
        except Exception as e:
            all_validation_failures.append(f"Delete failed: {e}")

        db.close()

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
