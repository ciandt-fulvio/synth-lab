"""
T013 Unit tests for SynthGroupRepository.

Tests for the synth group data access layer following TDD methodology.
Write tests first, then implement repository to make them pass.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - Data model: specs/018-experiment-hub/data-model.md
"""

from datetime import datetime, timezone

import pytest

from synth_lab.domain.entities.synth_group import SynthGroup
from synth_lab.infrastructure.database import DatabaseManager, init_database
from synth_lab.models.pagination import PaginationParams


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with schema."""
    db_path = tmp_path / "test.db"
    init_database(db_path)
    db = DatabaseManager(db_path)
    yield db
    db.close()


@pytest.fixture
def synth_group_repo(test_db):
    """Create SynthGroupRepository with test database."""
    from synth_lab.repositories.synth_group_repository import SynthGroupRepository

    return SynthGroupRepository(test_db)


class TestSynthGroupRepositoryCreate:
    """Tests for synth group creation."""

    def test_create_synth_group_success(self, synth_group_repo) -> None:
        """Verify synth group is created and persisted."""
        group = SynthGroup(
            name="December 2025 Generation",
            description="Synths for checkout testing",
        )

        result = synth_group_repo.create(group)

        assert result is not None
        assert result.id == group.id
        assert result.name == "December 2025 Generation"
        assert result.description == "Synths for checkout testing"
        assert result.created_at is not None

    def test_create_synth_group_generates_id_if_not_provided(self, synth_group_repo) -> None:
        """Verify synth group ID is generated when not provided."""
        group = SynthGroup(name="Test Group")

        result = synth_group_repo.create(group)

        assert result.id.startswith("grp_")
        assert len(result.id) == 12  # grp_ + 8 hex chars

    def test_create_synth_group_with_custom_id(self, synth_group_repo) -> None:
        """Verify synth group is created with custom ID."""
        group = SynthGroup(
            id="grp_12345678",
            name="Custom ID Group",
        )

        result = synth_group_repo.create(group)

        assert result.id == "grp_12345678"

    def test_create_synth_group_without_description(self, synth_group_repo) -> None:
        """Verify synth group can be created without description."""
        group = SynthGroup(name="Minimal Group")

        result = synth_group_repo.create(group)

        assert result.name == "Minimal Group"
        assert result.description is None


class TestSynthGroupRepositoryGet:
    """Tests for synth group retrieval."""

    def test_get_synth_group_by_id(self, synth_group_repo) -> None:
        """Verify synth group can be retrieved by ID."""
        group = SynthGroup(
            name="Test Group",
            description="Test description",
        )
        synth_group_repo.create(group)

        result = synth_group_repo.get_by_id(group.id)

        assert result is not None
        assert result.id == group.id
        assert result.name == "Test Group"

    def test_get_synth_group_not_found_returns_none(self, synth_group_repo) -> None:
        """Verify get returns None for non-existent group."""
        result = synth_group_repo.get_by_id("grp_nonexist")

        assert result is None

    def test_get_synth_group_includes_synth_count(self, synth_group_repo, test_db) -> None:
        """Verify retrieved group includes synth count."""
        group = SynthGroup(name="Group with Synths")
        synth_group_repo.create(group)

        # Add synths to the group
        for i in range(3):
            test_db.execute(
                """
                INSERT INTO synths (id, synth_group_id, nome, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    f"syn{i:03d}",
                    group.id,
                    f"Synth {i}",
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        result = synth_group_repo.get_by_id(group.id)

        assert result is not None
        assert result.synth_count == 3


class TestSynthGroupRepositoryList:
    """Tests for synth group listing."""

    def test_list_synth_groups_with_pagination(self, synth_group_repo) -> None:
        """Verify synth groups are listed with pagination."""
        # Create 5 groups (total will be 6 including default group)
        for i in range(5):
            group = SynthGroup(name=f"Group {i}")
            synth_group_repo.create(group)

        params = PaginationParams(limit=3, offset=0)
        result = synth_group_repo.list_groups(params)

        assert len(result.data) == 3
        assert result.pagination.total == 6  # 5 + default group
        assert result.pagination.has_next is True

    def test_list_synth_groups_returns_default_group(self, synth_group_repo) -> None:
        """Verify default group is returned when no custom groups exist."""
        params = PaginationParams(limit=10, offset=0)
        result = synth_group_repo.list_groups(params)

        # Database now always creates a default group
        assert len(result.data) == 1
        assert result.data[0].name == "Default"
        assert result.pagination.total == 1

    def test_list_synth_groups_with_synth_count(self, synth_group_repo, test_db) -> None:
        """Verify listed groups include synth counts."""
        # Create groups with different synth counts
        group1 = SynthGroup(name="Group 1")
        group2 = SynthGroup(name="Group 2")
        synth_group_repo.create(group1)
        synth_group_repo.create(group2)

        # Add synths to group1
        for i in range(2):
            test_db.execute(
                """
                INSERT INTO synths (id, synth_group_id, nome, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    f"s1_{i:03d}",
                    group1.id,
                    f"Synth 1-{i}",
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        # Add synths to group2
        for i in range(5):
            test_db.execute(
                """
                INSERT INTO synths (id, synth_group_id, nome, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    f"s2_{i:03d}",
                    group2.id,
                    f"Synth 2-{i}",
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        params = PaginationParams(limit=10, offset=0)
        result = synth_group_repo.list_groups(params)

        # Sort by name to check counts
        groups_by_name = {g.name: g for g in result.data}
        assert groups_by_name["Group 1"].synth_count == 2
        assert groups_by_name["Group 2"].synth_count == 5

    def test_list_synth_groups_sorted_by_created_at_desc(self, synth_group_repo) -> None:
        """Verify groups are sorted by created_at descending."""
        grp1 = SynthGroup(name="First")
        grp2 = SynthGroup(name="Second")
        grp3 = SynthGroup(name="Third")

        synth_group_repo.create(grp1)
        synth_group_repo.create(grp2)
        synth_group_repo.create(grp3)

        params = PaginationParams(limit=10, offset=0)
        result = synth_group_repo.list_groups(params)

        # Most recent first (default sort)
        assert result.data[0].name == "Third"
        assert result.data[2].name == "First"


class TestSynthGroupRepositoryGetDetail:
    """Tests for synth group detail retrieval."""

    def test_get_detail_includes_synths(self, synth_group_repo, test_db) -> None:
        """Verify group detail includes list of synths."""
        group = SynthGroup(name="Group with Synths")
        synth_group_repo.create(group)

        # Add synths
        for i in range(3):
            test_db.execute(
                """
                INSERT INTO synths (id, synth_group_id, nome, descricao, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    f"syn{i:03d}",
                    group.id,
                    f"Synth {i}",
                    f"Description {i}",
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        result = synth_group_repo.get_detail(group.id)

        assert result is not None
        assert len(result.synths) == 3
        # Check that all synth names are present (order is DESC by created_at)
        synth_names = {s.nome for s in result.synths}
        assert synth_names == {"Synth 0", "Synth 1", "Synth 2"}

    def test_get_detail_not_found_returns_none(self, synth_group_repo) -> None:
        """Verify get_detail returns None for non-existent group."""
        result = synth_group_repo.get_detail("grp_nonexist")

        assert result is None


class TestSynthGroupRepositoryDelete:
    """Tests for synth group deletion."""

    def test_delete_synth_group_success(self, synth_group_repo) -> None:
        """Verify synth group can be deleted."""
        group = SynthGroup(name="To Delete")
        synth_group_repo.create(group)

        result = synth_group_repo.delete(group.id)

        assert result is True
        assert synth_group_repo.get_by_id(group.id) is None

    def test_delete_nonexistent_group_returns_false(self, synth_group_repo) -> None:
        """Verify delete returns False for non-existent group."""
        result = synth_group_repo.delete("grp_nonexist")

        assert result is False

    def test_delete_group_nullifies_synth_references(self, synth_group_repo, test_db) -> None:
        """Verify deleting group sets synth.synth_group_id to NULL."""
        group = SynthGroup(name="Group with Synths")
        synth_group_repo.create(group)

        # Add synth to the group
        test_db.execute(
            """
            INSERT INTO synths (id, synth_group_id, nome, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                "syn001",
                group.id,
                "Test Synth",
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        synth_group_repo.delete(group.id)

        # Check synth's group_id is now NULL
        row = test_db.fetchone("SELECT synth_group_id FROM synths WHERE id = ?", ("syn001",))
        assert row["synth_group_id"] is None
