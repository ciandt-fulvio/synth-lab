"""
T014 SynthGroupRepository for synth-lab.

Data access layer for synth group data in SQLite database.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - Data model: specs/018-experiment-hub/data-model.md
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from synth_lab.domain.entities.synth_group import (
    DEFAULT_SYNTH_GROUP_DESCRIPTION,
    DEFAULT_SYNTH_GROUP_ID,
    DEFAULT_SYNTH_GROUP_NAME,
    SynthGroup,
)
from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.models.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from synth_lab.repositories.base import BaseRepository


class SynthGroupSummary(BaseModel):
    """Summary of a synth group for list display."""

    id: str = Field(description="Group ID.")
    name: str = Field(description="Group name.")
    description: str | None = Field(default=None, description="Group description.")
    synth_count: int = Field(default=0, description="Number of synths in group.")
    created_at: datetime = Field(description="Creation timestamp.")


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
    synths: list[SynthSummary] = Field(default_factory=list, description="Synths in this group.")


class SynthGroupRepository(BaseRepository):
    """Repository for synth group data access."""

    def __init__(self, db: DatabaseManager | None = None):
        super().__init__(db)

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

        # Create default group if it doesn't exist
        now = datetime.now(timezone.utc)
        self.db.execute(
            """
            INSERT OR IGNORE INTO synth_groups (id, name, description, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                DEFAULT_SYNTH_GROUP_ID,
                DEFAULT_SYNTH_GROUP_NAME,
                DEFAULT_SYNTH_GROUP_DESCRIPTION,
                now.isoformat(),
            ),
        )

        return self.get_by_id(DEFAULT_SYNTH_GROUP_ID)

    def create(self, group: SynthGroup) -> SynthGroup:
        """
        Create a new synth group.

        Args:
            group: SynthGroup entity to create.

        Returns:
            Created synth group with persisted data.
        """
        self.db.execute(
            """
            INSERT INTO synth_groups (id, name, description, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                group.id,
                group.name,
                group.description,
                group.created_at.isoformat(),
            ),
        )
        return group

    def get_by_id(self, group_id: str) -> SynthGroupSummary | None:
        """
        Get a synth group by ID with synth count.

        Args:
            group_id: Group ID to retrieve.

        Returns:
            SynthGroupSummary if found, None otherwise.
        """
        row = self.db.fetchone(
            """
            SELECT
                g.id,
                g.name,
                g.description,
                g.created_at,
                COALESCE(s.cnt, 0) as synth_count
            FROM synth_groups g
            LEFT JOIN (
                SELECT synth_group_id, COUNT(*) as cnt
                FROM synths
                WHERE synth_group_id IS NOT NULL
                GROUP BY synth_group_id
            ) s ON g.id = s.synth_group_id
            WHERE g.id = ?
            """,
            (group_id,),
        )
        if row is None:
            return None
        return self._row_to_summary(row)

    def get_detail(self, group_id: str) -> SynthGroupDetail | None:
        """
        Get a synth group with full details including synths.

        Args:
            group_id: Group ID to retrieve.

        Returns:
            SynthGroupDetail if found, None otherwise.
        """
        # First get the group summary
        summary = self.get_by_id(group_id)
        if summary is None:
            return None

        # Get synths in this group
        rows = self.db.fetchall(
            """
            SELECT id, nome, descricao, avatar_path, synth_group_id, created_at
            FROM synths
            WHERE synth_group_id = ?
            ORDER BY created_at DESC
            """,
            (group_id,),
        )

        synths = [self._row_to_synth_summary(row) for row in rows]

        return SynthGroupDetail(
            id=summary.id,
            name=summary.name,
            description=summary.description,
            synth_count=summary.synth_count,
            created_at=summary.created_at,
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
        base_query = """
            SELECT
                g.id,
                g.name,
                g.description,
                g.created_at,
                COALESCE(s.cnt, 0) as synth_count
            FROM synth_groups g
            LEFT JOIN (
                SELECT synth_group_id, COUNT(*) as cnt
                FROM synths
                WHERE synth_group_id IS NOT NULL
                GROUP BY synth_group_id
            ) s ON g.id = s.synth_group_id
            ORDER BY g.created_at DESC
        """

        count_query = "SELECT COUNT(*) as count FROM synth_groups"

        # Get total count
        count_row = self.db.fetchone(count_query)
        total = count_row["count"] if count_row else 0

        # Apply pagination
        paginated_query = f"{base_query} LIMIT ? OFFSET ?"
        rows = self.db.fetchall(paginated_query, (params.limit, params.offset))

        summaries = [self._row_to_summary(row) for row in rows]
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
        # Check if exists
        existing = self.get_by_id(group_id)
        if existing is None:
            return False

        # Nullify synth references
        self.db.execute(
            "UPDATE synths SET synth_group_id = NULL WHERE synth_group_id = ?",
            (group_id,),
        )

        # Delete the group
        self.db.execute("DELETE FROM synth_groups WHERE id = ?", (group_id,))
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


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.synth_group import SynthGroup
    from synth_lab.infrastructure.database import init_database

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)  # Initialize schema first
        db = DatabaseManager(test_db_path)
        repo = SynthGroupRepository(db)

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
