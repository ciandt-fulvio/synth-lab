"""
T017 Unit tests for SynthGroupService.

Tests for the synth group business logic layer following TDD methodology.
Write tests first, then implement service to make them pass.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - Data model: specs/018-experiment-hub/data-model.md
"""

from datetime import datetime, timezone

import pytest

from synth_lab.domain.entities.synth_group import SynthGroup
from synth_lab.infrastructure.database import DatabaseManager, init_database
from synth_lab.models.pagination import PaginationParams
from synth_lab.repositories.synth_group_repository import SynthGroupRepository


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
    return SynthGroupRepository(test_db)


@pytest.fixture
def synth_group_service(synth_group_repo):
    """Create SynthGroupService with test repository."""
    from synth_lab.services.synth_group_service import SynthGroupService

    return SynthGroupService(synth_group_repo)


class TestSynthGroupServiceGetOrCreate:
    """Tests for get_or_create_group functionality."""

    def test_get_or_create_group_creates_new_when_not_exists(
        self, synth_group_service
    ) -> None:
        """Verify new group is created when it doesn't exist."""
        result = synth_group_service.get_or_create_group(
            name="New Group",
            description="Test description",
        )

        assert result is not None
        assert result.id.startswith("grp_")
        assert result.name == "New Group"
        assert result.description == "Test description"

    def test_get_or_create_group_returns_existing(
        self, synth_group_service
    ) -> None:
        """Verify existing group is returned if name matches."""
        # Create first group
        first = synth_group_service.get_or_create_group(
            name="Existing Group",
            description="First description",
        )

        # Try to create with same name
        second = synth_group_service.get_or_create_group(
            name="Existing Group",
            description="Second description",
        )

        # Should return same group (same ID)
        assert second.id == first.id
        # Description should not be updated
        assert second.description == "First description"

    def test_get_or_create_group_creates_with_id(
        self, synth_group_service
    ) -> None:
        """Verify group can be created with specific ID."""
        result = synth_group_service.get_or_create_group(
            group_id="grp_12345678",
            name="Custom ID Group",
        )

        assert result.id == "grp_12345678"


class TestSynthGroupServiceAutoGenerate:
    """Tests for auto-generated group names."""

    def test_auto_generate_group_name_includes_timestamp(
        self, synth_group_service
    ) -> None:
        """Verify auto-generated name includes timestamp."""
        result = synth_group_service.create_auto_group()

        assert result is not None
        assert result.name is not None
        # Name should contain date components
        now = datetime.now()
        assert str(now.year) in result.name or str(now.month) in result.name

    def test_auto_generate_group_with_prefix(
        self, synth_group_service
    ) -> None:
        """Verify auto-generated name can have custom prefix."""
        result = synth_group_service.create_auto_group(prefix="Batch")

        assert result is not None
        assert result.name.startswith("Batch")


class TestSynthGroupServiceCreate:
    """Tests for synth group creation."""

    def test_create_group_validates_name_required(
        self, synth_group_service
    ) -> None:
        """Verify name is required for group creation."""
        with pytest.raises(ValueError, match="name"):
            synth_group_service.create_group(name="")

    def test_create_group_success(self, synth_group_service) -> None:
        """Verify group is created with valid data."""
        result = synth_group_service.create_group(
            name="Test Group",
            description="Test description",
        )

        assert result is not None
        assert result.id.startswith("grp_")
        assert result.name == "Test Group"


class TestSynthGroupServiceList:
    """Tests for synth group listing."""

    def test_list_groups_with_pagination(self, synth_group_service) -> None:
        """Verify groups are listed with pagination."""
        # Create 5 groups (total will be 6 including default group)
        for i in range(5):
            synth_group_service.create_group(name=f"Group {i}")

        params = PaginationParams(limit=3, offset=0)
        result = synth_group_service.list_groups(params)

        assert len(result.data) == 3
        assert result.pagination.total == 6  # 5 + default group

    def test_list_groups_returns_default_group(
        self, synth_group_service
    ) -> None:
        """Verify default group is returned when no custom groups exist."""
        params = PaginationParams(limit=10, offset=0)
        result = synth_group_service.list_groups(params)

        # Database now always creates a default group
        assert len(result.data) == 1
        assert result.data[0].name == "Default"
        assert result.pagination.total == 1


class TestSynthGroupServiceGet:
    """Tests for synth group retrieval."""

    def test_get_group_by_id(self, synth_group_service) -> None:
        """Verify group can be retrieved by ID."""
        created = synth_group_service.create_group(name="Test Group")

        result = synth_group_service.get_group(created.id)

        assert result is not None
        assert result.id == created.id

    def test_get_group_not_found_returns_none(
        self, synth_group_service
    ) -> None:
        """Verify get returns None for non-existent group."""
        result = synth_group_service.get_group("grp_nonexist")

        assert result is None

    def test_get_group_detail_includes_synths(
        self, synth_group_service, test_db
    ) -> None:
        """Verify group detail includes list of synths."""
        created = synth_group_service.create_group(name="Group with Synths")

        # Add synth to the group
        test_db.execute(
            """
            INSERT INTO synths (id, synth_group_id, nome, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                "syn001",
                created.id,
                "Test Synth",
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        result = synth_group_service.get_group_detail(created.id)

        assert result is not None
        assert len(result.synths) == 1
        assert result.synths[0].nome == "Test Synth"


class TestSynthGroupServiceDelete:
    """Tests for synth group deletion."""

    def test_delete_group_success(self, synth_group_service) -> None:
        """Verify group can be deleted."""
        created = synth_group_service.create_group(name="To Delete")

        result = synth_group_service.delete_group(created.id)

        assert result is True
        assert synth_group_service.get_group(created.id) is None

    def test_delete_nonexistent_group_returns_false(
        self, synth_group_service
    ) -> None:
        """Verify delete returns False for non-existent group."""
        result = synth_group_service.delete_group("grp_nonexist")

        assert result is False
