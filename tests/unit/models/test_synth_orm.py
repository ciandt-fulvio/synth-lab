"""
Unit tests for Synth and SynthGroup ORM models.

Tests validate SQLAlchemy model structure, table names, column definitions,
relationships, and basic CRUD operations.

References:
    - ORM Models: synth_lab.models.orm.synth
    - Data Model: specs/027-postgresql-migration/data-model.md
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from synth_lab.models.orm.base import Base
from synth_lab.models.orm.synth import Synth, SynthGroup


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


class TestSynthGroupModel:
    """Tests for SynthGroup ORM model structure."""

    def test_table_name(self):
        """SynthGroup should map to 'synth_groups' table."""
        assert SynthGroup.__tablename__ == "synth_groups"

    def test_required_columns_exist(self):
        """SynthGroup should have all required columns."""
        columns = set(SynthGroup.__table__.columns.keys())
        required = {"id", "name", "description", "created_at"}
        assert required.issubset(columns)

    def test_primary_key(self):
        """SynthGroup id should be primary key."""
        pk_columns = [c.name for c in SynthGroup.__table__.primary_key.columns]
        assert pk_columns == ["id"]

    def test_nullable_columns(self):
        """Verify nullable column settings."""
        cols = {c.name: c.nullable for c in SynthGroup.__table__.columns}
        assert cols["name"] is False
        assert cols["description"] is True
        assert cols["created_at"] is False


class TestSynthModel:
    """Tests for Synth ORM model structure."""

    def test_table_name(self):
        """Synth should map to 'synths' table."""
        assert Synth.__tablename__ == "synths"

    def test_required_columns_exist(self):
        """Synth should have all required columns."""
        columns = set(Synth.__table__.columns.keys())
        required = {"id", "synth_group_id", "nome", "descricao", "link_photo",
                   "avatar_path", "created_at", "version", "data"}
        assert required.issubset(columns)

    def test_primary_key(self):
        """Synth id should be primary key."""
        pk_columns = [c.name for c in Synth.__table__.primary_key.columns]
        assert pk_columns == ["id"]

    def test_nullable_columns(self):
        """Verify nullable column settings."""
        cols = {c.name: c.nullable for c in Synth.__table__.columns}
        assert cols["nome"] is False
        assert cols["synth_group_id"] is True
        assert cols["descricao"] is True
        assert cols["link_photo"] is True
        assert cols["avatar_path"] is True
        assert cols["data"] is True
        assert cols["created_at"] is False

    def test_has_foreign_key_to_synth_groups(self):
        """Synth should have optional foreign key to synth_groups table."""
        fks = [fk.target_fullname for fk in Synth.__table__.foreign_keys]
        assert "synth_groups.id" in fks


class TestSynthGroupCRUD:
    """Tests for SynthGroup CRUD operations."""

    def test_create_synth_group(self, session: Session):
        """Create a new synth group."""
        group = SynthGroup(
            id="grp_12345678",
            name="Test Group",
            description="A test group",
            created_at=datetime.now().isoformat(),
        )
        session.add(group)
        session.commit()

        result = session.get(SynthGroup, "grp_12345678")
        assert result is not None
        assert result.name == "Test Group"
        assert result.description == "A test group"

    def test_create_synth_group_without_description(self, session: Session):
        """Create synth group without optional description."""
        group = SynthGroup(
            id="grp_22222222",
            name="No Description",
            created_at=datetime.now().isoformat(),
        )
        session.add(group)
        session.commit()

        result = session.get(SynthGroup, "grp_22222222")
        assert result.description is None


class TestSynthCRUD:
    """Tests for Synth CRUD operations."""

    def test_create_synth(self, session: Session):
        """Create a new synth."""
        synth = Synth(
            id="syn001",
            nome="Maria Silva",
            descricao="Uma pesquisadora",
            created_at=datetime.now().isoformat(),
            version="2.0.0",
        )
        session.add(synth)
        session.commit()

        result = session.get(Synth, "syn001")
        assert result is not None
        assert result.nome == "Maria Silva"
        assert result.version == "2.0.0"

    def test_create_synth_with_json_data(self, session: Session):
        """Create synth with JSON data attribute."""
        data = {
            "demografia": {
                "idade": 35,
                "genero_biologico": "feminino",
                "localizacao": {"cidade": "São Paulo", "estado": "SP"},
            },
            "psicografia": {
                "interesses": ["tecnologia", "inovação"],
            },
        }
        synth = Synth(
            id="syn002",
            nome="João Santos",
            data=data,
            created_at=datetime.now().isoformat(),
            version="2.3.0",
        )
        session.add(synth)
        session.commit()

        result = session.get(Synth, "syn002")
        assert result.data == data
        assert result.data["demografia"]["idade"] == 35

    def test_create_synth_in_group(self, session: Session):
        """Create synth as part of a group."""
        # Create group first
        group = SynthGroup(
            id="grp_33333333",
            name="Test Group",
            created_at=datetime.now().isoformat(),
        )
        session.add(group)
        session.commit()

        # Create synth in group
        synth = Synth(
            id="syn003",
            nome="Ana Costa",
            synth_group_id="grp_33333333",
            created_at=datetime.now().isoformat(),
            version="2.0.0",
        )
        session.add(synth)
        session.commit()

        result = session.get(Synth, "syn003")
        assert result.synth_group_id == "grp_33333333"

    def test_synth_group_relationship(self, session: Session):
        """Test N:1 relationship between Synth and SynthGroup."""
        group = SynthGroup(
            id="grp_44444444",
            name="Relationship Test",
            created_at=datetime.now().isoformat(),
        )
        session.add(group)
        session.commit()

        synth = Synth(
            id="syn004",
            nome="Pedro Lima",
            synth_group_id="grp_44444444",
            created_at=datetime.now().isoformat(),
            version="2.0.0",
        )
        session.add(synth)
        session.commit()

        # Access via relationship
        synth = session.get(Synth, "syn004")
        assert synth.synth_group is not None
        assert synth.synth_group.name == "Relationship Test"

        # Access synths from group
        group = session.get(SynthGroup, "grp_44444444")
        assert len(group.synths) == 1
        assert group.synths[0].nome == "Pedro Lima"

    def test_synth_without_group(self, session: Session):
        """Synth can exist without a group."""
        synth = Synth(
            id="syn005",
            nome="Sem Grupo",
            created_at=datetime.now().isoformat(),
            version="2.0.0",
        )
        session.add(synth)
        session.commit()

        result = session.get(Synth, "syn005")
        assert result.synth_group_id is None
        assert result.synth_group is None

    def test_cascade_delete_synths_with_group(self, session: Session):
        """Synths should be deleted when parent group is deleted."""
        group = SynthGroup(
            id="grp_55555555",
            name="To Delete",
            created_at=datetime.now().isoformat(),
        )
        session.add(group)
        session.commit()

        synth = Synth(
            id="syn006",
            nome="Will Be Deleted",
            synth_group_id="grp_55555555",
            created_at=datetime.now().isoformat(),
            version="2.0.0",
        )
        session.add(synth)
        session.commit()

        # Delete group
        session.delete(group)
        session.commit()

        # Synth should also be deleted
        result = session.get(Synth, "syn006")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
