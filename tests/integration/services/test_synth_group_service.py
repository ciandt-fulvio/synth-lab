"""
Integration tests for SynthGroupService.

These tests verify business logic and orchestration between repository and
synth generation components.

References:
    - Service: synth_lab.services.synth_group_service
    - Spec: specs/030-custom-synth-groups/spec.md
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from synth_lab.models.orm.base import Base
from synth_lab.models.orm.synth import Synth as SynthORM
from synth_lab.models.pagination import PaginationParams
from synth_lab.repositories.synth_group_repository import SynthGroupRepository
from synth_lab.services.synth_group_service import SynthGroupService


@pytest.fixture(scope="function")
def engine():
    """Create an in-memory SQLite engine for testing."""
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
def service(session: Session):
    """Create SynthGroupService with repository."""
    repo = SynthGroupRepository(session=session)
    return SynthGroupService(repository=repo)


class TestSynthGroupServiceCreate:
    """Tests for creating synth groups via service."""

    def test_create_group_success(self, service: SynthGroupService, session: Session):
        """Create synth group with valid data."""
        result = service.create_group(name="Service Test Group")

        assert result is not None
        assert result.name == "Service Test Group"
        assert result.id.startswith("grp_")
        assert result.synth_count == 0
        session.commit()

    def test_create_group_with_description(
        self, service: SynthGroupService, session: Session
    ):
        """Create synth group with description."""
        result = service.create_group(
            name="Described Group", description="Test description"
        )

        assert result.description == "Test description"
        session.commit()

    def test_create_group_with_custom_id(
        self, service: SynthGroupService, session: Session
    ):
        """Create synth group with custom ID."""
        result = service.create_group(
            name="Custom ID Group", group_id="grp_custom01"
        )

        assert result.id == "grp_custom01"
        session.commit()

    def test_create_group_validates_empty_name(self, service: SynthGroupService):
        """Create fails with empty name."""
        with pytest.raises(ValueError, match="name is required"):
            service.create_group(name="")

        with pytest.raises(ValueError, match="name is required"):
            service.create_group(name="   ")

    def test_create_group_trims_name(self, service: SynthGroupService, session: Session):
        """Create trims whitespace from name."""
        result = service.create_group(name="  Trimmed Name  ")

        assert result.name == "Trimmed Name"
        session.commit()

    def test_create_group_trims_description(
        self, service: SynthGroupService, session: Session
    ):
        """Create trims whitespace from description."""
        result = service.create_group(
            name="Test", description="  Trimmed Description  "
        )

        assert result.description == "Trimmed Description"
        session.commit()


class TestSynthGroupServiceCreateWithConfig:
    """Tests for creating synth groups with custom distributions."""

    def test_create_with_config_generates_synths(
        self, service: SynthGroupService, session: Session
    ):
        """Create with config generates specified number of synths."""
        config = {
            "n_synths": 10,
            "distributions": {
                "idade": {"15-29": 0.25, "30-44": 0.25, "45-59": 0.25, "60+": 0.25},
                "escolaridade": {
                    "sem_instrucao": 0.25,
                    "fundamental": 0.25,
                    "medio": 0.25,
                    "superior": 0.25,
                },
                "deficiencias": {
                    "taxa_com_deficiencia": 0.1,
                    "distribuicao_severidade": {
                        "nenhuma": 0.2,
                        "leve": 0.2,
                        "moderada": 0.2,
                        "severa": 0.2,
                        "total": 0.2,
                    },
                },
                "composicao_familiar": {
                    "unipessoal": 0.2,
                    "casal_sem_filhos": 0.2,
                    "casal_com_filhos": 0.3,
                    "monoparental": 0.15,
                    "multigeracional": 0.15,
                },
                "domain_expertise": {"alpha": 3, "beta": 3},
            },
        }

        result = service.create_with_config(
            name="Config Group", config=config, description="Test with config"
        )

        assert result.synth_count == 10
        assert result.name == "Config Group"

        # Verify synths exist in database
        synths = session.query(SynthORM).filter_by(synth_group_id=result.id).all()
        assert len(synths) == 10
        session.commit()

    def test_create_with_config_default_n_synths(
        self, service: SynthGroupService, session: Session
    ):
        """Create with config uses default n_synths if not specified."""
        config = {
            "distributions": {
                "idade": {"15-29": 0.25, "30-44": 0.25, "45-59": 0.25, "60+": 0.25},
                "escolaridade": {
                    "sem_instrucao": 0.25,
                    "fundamental": 0.25,
                    "medio": 0.25,
                    "superior": 0.25,
                },
            }
        }

        result = service.create_with_config(name="Default Size Group", config=config)

        # Default is 500
        assert result.synth_count == 500
        session.commit()

    def test_create_with_config_validates_n_synths_range(
        self, service: SynthGroupService
    ):
        """Create with config validates n_synths range."""
        config = {"n_synths": 0}

        with pytest.raises(ValueError, match="n_synths must be between 1 and 1000"):
            service.create_with_config(name="Invalid", config=config)

        config = {"n_synths": 1001}

        with pytest.raises(ValueError, match="n_synths must be between 1 and 1000"):
            service.create_with_config(name="Invalid", config=config)

    def test_create_with_config_validates_name(self, service: SynthGroupService):
        """Create with config validates name."""
        config = {"n_synths": 10}

        with pytest.raises(ValueError, match="name is required"):
            service.create_with_config(name="", config=config)

    def test_create_with_config_synths_have_group_id(
        self, service: SynthGroupService, session: Session
    ):
        """Synths created with config have correct group_id."""
        config = {"n_synths": 5}

        result = service.create_with_config(name="Group Link Test", config=config)

        synths = session.query(SynthORM).filter_by(synth_group_id=result.id).all()
        assert len(synths) == 5
        for synth in synths:
            assert synth.synth_group_id == result.id
        session.commit()


class TestSynthGroupServiceGetOrCreate:
    """Tests for get-or-create pattern."""

    def test_get_or_create_returns_existing(
        self, service: SynthGroupService, session: Session
    ):
        """Get or create returns existing group by name."""
        # Create first group
        first = service.create_group(name="Existing Group")
        session.commit()

        # Try to get or create again
        second = service.get_or_create_group(name="Existing Group")

        assert second.id == first.id
        assert second.name == first.name

    def test_get_or_create_creates_new(
        self, service: SynthGroupService, session: Session
    ):
        """Get or create creates new group if not found."""
        result = service.get_or_create_group(
            name="New Group", description="New description"
        )

        assert result is not None
        assert result.name == "New Group"
        assert result.description == "New description"
        session.commit()

    def test_get_or_create_exact_name_match(
        self, service: SynthGroupService, session: Session
    ):
        """Get or create matches exact name only."""
        service.create_group(name="Group One")
        session.commit()

        # Different name should create new
        result = service.get_or_create_group(name="Group Two")

        assert result.name == "Group Two"
        session.commit()


class TestSynthGroupServiceAutoCreate:
    """Tests for auto-generating group names."""

    def test_create_auto_group_generates_name(
        self, service: SynthGroupService, session: Session
    ):
        """Auto create generates name with month and year."""
        result = service.create_auto_group()

        assert result.name is not None
        assert "Geração" in result.name
        assert str(datetime.now().year) in result.name
        session.commit()

    def test_create_auto_group_custom_prefix(
        self, service: SynthGroupService, session: Session
    ):
        """Auto create accepts custom prefix."""
        result = service.create_auto_group(prefix="Batch")

        assert result.name.startswith("Batch")
        session.commit()

    def test_create_auto_group_handles_duplicates(
        self, service: SynthGroupService, session: Session
    ):
        """Auto create adds time suffix if name exists."""
        # Create first auto group
        first = service.create_auto_group()
        session.commit()

        # Create second should have different name (with time)
        second = service.create_auto_group()
        session.commit()

        assert first.name != second.name


class TestSynthGroupServiceRead:
    """Tests for reading synth groups."""

    def test_get_group_success(self, service: SynthGroupService, session: Session):
        """Get group by ID returns correct group."""
        created = service.create_group(name="Findable")
        session.commit()

        result = service.get_group(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Findable"

    def test_get_group_not_found(self, service: SynthGroupService):
        """Get group returns None for non-existent ID."""
        result = service.get_group("grp_nonexist")
        assert result is None

    def test_get_group_detail_success(
        self, service: SynthGroupService, session: Session
    ):
        """Get group detail returns group with synths list."""
        # Create group with synths
        config = {"n_synths": 3}
        created = service.create_with_config(name="Detailed", config=config)
        session.commit()

        result = service.get_group_detail(created.id)

        assert result is not None
        assert result.id == created.id
        assert len(result.synths) == 3

    def test_get_group_detail_not_found(self, service: SynthGroupService):
        """Get group detail returns None for non-existent ID."""
        result = service.get_group_detail("grp_nonexist")
        assert result is None

    def test_list_groups_empty(self, service: SynthGroupService):
        """List groups returns empty when no groups exist."""
        result = service.list_groups()

        assert len(result.data) == 0
        assert result.pagination.total == 0

    def test_list_groups_with_data(self, service: SynthGroupService, session: Session):
        """List groups returns all groups."""
        service.create_group(name="Group 1")
        service.create_group(name="Group 2")
        service.create_group(name="Group 3")
        session.commit()

        result = service.list_groups()

        assert len(result.data) == 3

    def test_list_groups_with_pagination(
        self, service: SynthGroupService, session: Session
    ):
        """List groups respects pagination parameters."""
        for i in range(5):
            service.create_group(name=f"Group {i}")
        session.commit()

        params = PaginationParams(limit=2, offset=0)
        result = service.list_groups(params)

        assert len(result.data) == 2
        assert result.pagination.total == 5


class TestSynthGroupServiceDelete:
    """Tests for deleting synth groups."""

    def test_delete_group_success(self, service: SynthGroupService, session: Session):
        """Delete removes group."""
        created = service.create_group(name="To Delete")
        session.commit()

        result = service.delete_group(created.id)

        assert result is True
        assert service.get_group(created.id) is None

    def test_delete_group_not_found(self, service: SynthGroupService):
        """Delete returns False for non-existent group."""
        result = service.delete_group("grp_nonexist")
        assert result is False

    def test_delete_group_preserves_synths(
        self, service: SynthGroupService, session: Session
    ):
        """Delete nullifies synth group_id but keeps synths."""
        # Create group with synths
        config = {"n_synths": 3}
        created = service.create_with_config(name="To Delete", config=config)
        session.commit()

        # Get synth IDs
        synths_before = (
            session.query(SynthORM).filter_by(synth_group_id=created.id).all()
        )
        synth_ids = [s.id for s in synths_before]
        assert len(synth_ids) == 3

        # Delete group
        service.delete_group(created.id)

        # Synths should still exist
        for synth_id in synth_ids:
            synth = session.get(SynthORM, synth_id)
            assert synth is not None
            assert synth.synth_group_id is None
