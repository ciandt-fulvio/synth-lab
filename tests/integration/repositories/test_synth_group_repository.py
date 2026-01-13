"""
Integration tests for SynthGroupRepository with SQLAlchemy ORM backend.

These tests verify that SynthGroupRepository works correctly with SQLAlchemy
sessions, ensuring full CRUD operations, relationships, and data integrity.

References:
    - Repository: synth_lab.repositories.synth_group_repository
    - ORM Models: synth_lab.models.orm.synth
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from synth_lab.models.orm.base import Base
from synth_lab.models.orm.synth import SynthGroup as SynthGroupORM, Synth as SynthORM
from synth_lab.domain.entities.synth_group import (
    SynthGroup,
    DEFAULT_SYNTH_GROUP_ID,
    DEFAULT_SYNTH_GROUP_NAME,
)
from synth_lab.models.pagination import PaginationParams
from synth_lab.repositories.synth_group_repository import SynthGroupRepository


@pytest.fixture(scope="function")
def engine():
    """Create an in-memory SQLite engine for testing.

    Note: Uses SQLite for fast in-memory testing.
    Production uses PostgreSQL.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def session(engine):
    """Create a session for testing."""
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def repo(session: Session):
    """Create SynthGroupRepository with ORM session."""
    return SynthGroupRepository(session=session)


class TestSynthGroupRepositoryDefaultGroup:
    """Tests for default group management."""

    def test_ensure_default_group_creates_when_missing(
        self, repo: SynthGroupRepository, session: Session
    ):
        """Default group is created if it doesn't exist."""
        # Verify default group doesn't exist yet
        assert session.get(SynthGroupORM, DEFAULT_SYNTH_GROUP_ID) is None

        # Ensure default group
        result = repo.ensure_default_group()

        # Verify it was created
        assert result.id == DEFAULT_SYNTH_GROUP_ID
        assert result.name == DEFAULT_SYNTH_GROUP_NAME
        assert result.synth_count == 0

        # Verify in database
        orm_group = session.get(SynthGroupORM, DEFAULT_SYNTH_GROUP_ID)
        assert orm_group is not None
        assert orm_group.name == DEFAULT_SYNTH_GROUP_NAME

    def test_ensure_default_group_idempotent(
        self, repo: SynthGroupRepository, session: Session
    ):
        """Calling ensure_default_group multiple times is safe."""
        # First call creates it
        result1 = repo.ensure_default_group()
        assert result1.id == DEFAULT_SYNTH_GROUP_ID

        # Second call returns existing
        result2 = repo.ensure_default_group()
        assert result2.id == DEFAULT_SYNTH_GROUP_ID
        assert result1.id == result2.id

        # Only one group exists in database
        groups = session.query(SynthGroupORM).filter_by(id=DEFAULT_SYNTH_GROUP_ID).all()
        assert len(groups) == 1


class TestSynthGroupRepositoryCreate:
    """Tests for creating synth groups via SQLAlchemy."""

    def test_create_group_success(self, repo: SynthGroupRepository, session: Session):
        """Create synth group using ORM backend."""
        group = SynthGroup(
            name="Test Group",
            description="Test description",
        )
        result = repo.create(group)
        session.commit()

        assert result.id == group.id
        assert result.name == "Test Group"

        # Verify in database
        orm_group = session.get(SynthGroupORM, group.id)
        assert orm_group is not None
        assert orm_group.name == "Test Group"
        assert orm_group.description == "Test description"
        assert orm_group.config is None

    def test_create_group_with_config(
        self, repo: SynthGroupRepository, session: Session
    ):
        """Create synth group with distribution config."""
        group = SynthGroup(name="Custom Group")
        config = {
            "n_synths": 100,
            "distributions": {
                "idade": {"15-29": 0.25, "30-44": 0.25, "45-59": 0.25, "60+": 0.25}
            },
        }

        result = repo.create(group, config=config)
        session.commit()

        # Verify in database
        orm_group = session.get(SynthGroupORM, group.id)
        assert orm_group is not None
        assert orm_group.config == config
        assert orm_group.config["n_synths"] == 100

    def test_create_group_without_description(
        self, repo: SynthGroupRepository, session: Session
    ):
        """Create synth group without optional description."""
        group = SynthGroup(name="Minimal Group")
        result = repo.create(group)
        session.commit()

        orm_group = session.get(SynthGroupORM, group.id)
        assert orm_group.description is None

    def test_create_with_config_and_synths(
        self, repo: SynthGroupRepository, session: Session
    ):
        """Create synth group with config and synths atomically."""
        group = SynthGroup(name="Group with Synths")
        config = {"n_synths": 3}

        # Create synth ORM objects
        now = datetime.now(timezone.utc).isoformat()
        synths = [
            SynthORM(
                id=f"synth_{i:03d}",
                nome=f"Synth {i}",
                created_at=now,
                data={"idade": 25 + i, "sexo": "masculino"},
            )
            for i in range(1, 4)
        ]

        result = repo.create_with_config(group, config, synths)

        # Verify group was created
        assert result.id == group.id
        assert result.synth_count == 3

        # Verify synths have correct group_id
        for synth_id in [s.id for s in synths]:
            orm_synth = session.get(SynthORM, synth_id)
            assert orm_synth is not None
            assert orm_synth.synth_group_id == group.id


class TestSynthGroupRepositoryRead:
    """Tests for reading synth groups."""

    def test_get_by_id_success(self, repo: SynthGroupRepository, session: Session):
        """Get synth group by ID."""
        group = SynthGroup(name="Findable Group")
        repo.create(group)
        session.commit()

        result = repo.get_by_id(group.id)

        assert result is not None
        assert result.id == group.id
        assert result.name == "Findable Group"
        assert result.synth_count == 0

    def test_get_by_id_not_found(self, repo: SynthGroupRepository):
        """Get non-existent group returns None."""
        result = repo.get_by_id("grp_nonexist")
        assert result is None

    def test_get_by_id_includes_synth_count(
        self, repo: SynthGroupRepository, session: Session
    ):
        """Get by ID includes correct synth count."""
        group = SynthGroup(name="Group with Count")
        now = datetime.now(timezone.utc).isoformat()

        # Create group with 2 synths
        synths = [
            SynthORM(
                id=f"synth_{i}",
                nome=f"Synth {i}",
                created_at=now,
                data={"idade": 30, "sexo": "feminino"},
            )
            for i in range(2)
        ]
        config = {"n_synths": 2}
        repo.create_with_config(group, config, synths)
        session.commit()

        result = repo.get_by_id(group.id)
        assert result.synth_count == 2

    def test_get_detail_success(self, repo: SynthGroupRepository, session: Session):
        """Get synth group detail with synths list."""
        group = SynthGroup(name="Detailed Group")
        now = datetime.now(timezone.utc).isoformat()

        # Create with 3 synths
        synths = [
            SynthORM(
                id=f"synth_{i}",
                nome=f"Synth {i}",
                created_at=now,
                data={"idade": 25, "sexo": "masculino"},
            )
            for i in range(3)
        ]
        config = {"n_synths": 3}
        repo.create_with_config(group, config, synths)
        session.commit()

        result = repo.get_detail(group.id)

        assert result is not None
        assert result.id == group.id
        assert result.synth_count == 3
        assert len(result.synths) == 3
        assert result.synths[0].nome == "Synth 0"

    def test_get_detail_not_found(self, repo: SynthGroupRepository):
        """Get detail for non-existent group returns None."""
        result = repo.get_detail("grp_nonexist")
        assert result is None

    def test_get_detail_synths_sorted_by_created_at(
        self, repo: SynthGroupRepository, session: Session
    ):
        """Synths in detail are sorted by created_at descending."""
        group = SynthGroup(name="Sorted Group")

        # Create synths with different timestamps
        base_time = datetime.now(timezone.utc)
        synths = [
            SynthORM(
                id=f"synth_{i}",
                nome=f"Synth {i}",
                created_at=base_time.replace(hour=i).isoformat(),
                data={"idade": 30, "sexo": "feminino"},
            )
            for i in range(3)
        ]
        config = {}
        repo.create_with_config(group, config, synths)
        session.commit()

        result = repo.get_detail(group.id)

        # Should be sorted descending (newest first)
        assert result.synths[0].id == "synth_2"
        assert result.synths[1].id == "synth_1"
        assert result.synths[2].id == "synth_0"


class TestSynthGroupRepositoryList:
    """Tests for listing synth groups."""

    def test_list_groups_empty(self, repo: SynthGroupRepository):
        """List returns empty result when no groups exist."""
        params = PaginationParams(limit=10, offset=0)
        result = repo.list_groups(params)

        assert len(result.data) == 0
        assert result.pagination.total == 0

    def test_list_groups_with_data(self, repo: SynthGroupRepository, session: Session):
        """List returns all groups with pagination."""
        # Create 3 groups
        for i in range(3):
            group = SynthGroup(name=f"Group {i}")
            repo.create(group)
        session.commit()

        params = PaginationParams(limit=10, offset=0)
        result = repo.list_groups(params)

        assert len(result.data) == 3
        assert result.pagination.total == 3
        assert result.pagination.limit == 10
        assert result.pagination.offset == 0

    def test_list_groups_pagination(self, repo: SynthGroupRepository, session: Session):
        """List respects pagination parameters."""
        # Create 5 groups
        for i in range(5):
            group = SynthGroup(name=f"Group {i}")
            repo.create(group)
        session.commit()

        # Get first 2
        params = PaginationParams(limit=2, offset=0)
        result = repo.list_groups(params)

        assert len(result.data) == 2
        assert result.pagination.total == 5

        # Get next 2
        params = PaginationParams(limit=2, offset=2)
        result = repo.list_groups(params)

        assert len(result.data) == 2
        assert result.pagination.total == 5

    def test_list_groups_sorted_by_created_at_desc(
        self, repo: SynthGroupRepository, session: Session
    ):
        """List returns groups sorted by created_at descending."""
        # Create groups with different timestamps
        base_time = datetime.now(timezone.utc)
        for i in range(3):
            group = SynthGroup(name=f"Group {i}")
            group.created_at = base_time.replace(hour=i)
            repo.create(group)
        session.commit()

        params = PaginationParams(limit=10, offset=0)
        result = repo.list_groups(params)

        # Should be newest first
        assert result.data[0].name == "Group 2"
        assert result.data[1].name == "Group 1"
        assert result.data[2].name == "Group 0"


class TestSynthGroupRepositoryDelete:
    """Tests for deleting synth groups."""

    def test_delete_success(self, repo: SynthGroupRepository, session: Session):
        """Delete removes group from database."""
        group = SynthGroup(name="To Delete")
        repo.create(group)
        session.commit()

        # Verify it exists
        assert repo.get_by_id(group.id) is not None

        # Delete it
        result = repo.delete(group.id)

        assert result is True
        assert repo.get_by_id(group.id) is None

    def test_delete_not_found(self, repo: SynthGroupRepository):
        """Delete returns False for non-existent group."""
        result = repo.delete("grp_nonexist")
        assert result is False

    def test_delete_cascade_deletes_synths(
        self, repo: SynthGroupRepository, session: Session
    ):
        """Delete cascade deletes associated synths due to delete-orphan."""
        group = SynthGroup(name="Group to Delete")
        now = datetime.now(timezone.utc).isoformat()

        # Create with 2 synths
        synths = [
            SynthORM(
                id=f"synth_{i}",
                nome=f"Synth {i}",
                created_at=now,
                data={"idade": 30, "sexo": "feminino"},
            )
            for i in range(2)
        ]
        repo.create_with_config(group, {}, synths)
        session.commit()

        # Verify synths exist
        synth_orm = session.get(SynthORM, "synth_0")
        assert synth_orm is not None
        assert synth_orm.synth_group_id == group.id

        # Delete group
        result = repo.delete(group.id)
        assert result is True

        # Due to delete-orphan cascade, synths are also deleted
        synth_orm = session.get(SynthORM, "synth_0")
        assert synth_orm is None
