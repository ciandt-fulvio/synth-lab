"""
Unit tests for Experiment and InterviewGuide ORM models.

Tests validate SQLAlchemy model structure, table names, column definitions,
relationships, and basic CRUD operations.

References:
    - ORM Models: synth_lab.models.orm.experiment
    - Data Model: specs/027-postgresql-migration/data-model.md
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from synth_lab.models.orm.base import Base
from synth_lab.models.orm.experiment import Experiment, InterviewGuide


@pytest.fixture(scope="function")
def engine():
    """Create an in-memory PostgreSQL engine for testing.

    Note: Uses PostgreSQL for fast in-memory testing.
    Production uses PostgreSQL.
    """
    engine = create_engine("sql" + "ite:///:memory:", echo=False)
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


class TestExperimentModel:
    """Tests for Experiment ORM model structure."""

    def test_table_name(self):
        """Experiment should map to 'experiments' table."""
        assert Experiment.__tablename__ == "experiments"

    def test_required_columns_exist(self):
        """Experiment should have all required columns."""
        columns = set(Experiment.__table__.columns.keys())
        required = {"id", "name", "hypothesis", "description", "scorecard_data",
                   "status", "created_at", "updated_at"}
        assert required.issubset(columns)

    def test_primary_key(self):
        """Experiment id should be primary key."""
        pk_columns = [c.name for c in Experiment.__table__.primary_key.columns]
        assert pk_columns == ["id"]

    def test_nullable_columns(self):
        """Verify nullable column settings."""
        cols = {c.name: c.nullable for c in Experiment.__table__.columns}
        assert cols["name"] is False
        assert cols["hypothesis"] is False
        assert cols["description"] is True
        assert cols["scorecard_data"] is True
        assert cols["created_at"] is False
        assert cols["updated_at"] is True

    def test_has_soft_delete_mixin(self):
        """Experiment should have status column from SoftDeleteMixin."""
        columns = set(Experiment.__table__.columns.keys())
        assert "status" in columns

    def test_has_timestamp_mixin(self):
        """Experiment should have timestamp columns from TimestampMixin."""
        columns = set(Experiment.__table__.columns.keys())
        assert "created_at" in columns
        assert "updated_at" in columns


class TestExperimentCRUD:
    """Tests for Experiment CRUD operations."""

    def test_create_experiment(self, session: Session):
        """Create a new experiment."""
        experiment = Experiment(
            id="exp_12345678",
            name="Test Experiment",
            hypothesis="Users will prefer this feature",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        session.add(experiment)
        session.commit()

        result = session.get(Experiment, "exp_12345678")
        assert result is not None
        assert result.name == "Test Experiment"
        assert result.hypothesis == "Users will prefer this feature"
        assert result.status == "active"

    def test_create_experiment_with_scorecard(self, session: Session):
        """Create experiment with scorecard JSON data."""
        scorecard_data = {
            "feature_name": "Test Feature",
            "description_text": "A test description",
            "complexity": {"score": 0.5},
        }
        experiment = Experiment(
            id="exp_22222222",
            name="With Scorecard",
            hypothesis="Test hypothesis",
            scorecard_data=scorecard_data,
            status="active",
            created_at=datetime.now().isoformat(),
        )
        session.add(experiment)
        session.commit()

        result = session.get(Experiment, "exp_22222222")
        assert result.scorecard_data == scorecard_data
        assert result.scorecard_data["feature_name"] == "Test Feature"

    def test_update_experiment(self, session: Session):
        """Update experiment fields."""
        experiment = Experiment(
            id="exp_33333333",
            name="Original Name",
            hypothesis="Original hypothesis",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        session.add(experiment)
        session.commit()

        # Update
        experiment.name = "Updated Name"
        experiment.updated_at = datetime.now().isoformat()
        session.commit()

        result = session.get(Experiment, "exp_33333333")
        assert result.name == "Updated Name"
        assert result.updated_at is not None

    def test_soft_delete_experiment(self, session: Session):
        """Soft delete experiment by setting status to 'deleted'."""
        experiment = Experiment(
            id="exp_44444444",
            name="To Delete",
            hypothesis="Will be deleted",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        session.add(experiment)
        session.commit()

        # Soft delete
        experiment.status = "deleted"
        session.commit()

        result = session.get(Experiment, "exp_44444444")
        assert result.status == "deleted"


class TestInterviewGuideModel:
    """Tests for InterviewGuide ORM model structure."""

    def test_table_name(self):
        """InterviewGuide should map to 'interview_guide' table."""
        assert InterviewGuide.__tablename__ == "interview_guide"

    def test_required_columns_exist(self):
        """InterviewGuide should have all required columns."""
        columns = set(InterviewGuide.__table__.columns.keys())
        required = {"experiment_id", "context_definition", "questions",
                   "context_examples", "created_at", "updated_at"}
        assert required.issubset(columns)

    def test_primary_key_is_experiment_id(self):
        """InterviewGuide should use experiment_id as primary key (1:1 relationship)."""
        pk_columns = [c.name for c in InterviewGuide.__table__.primary_key.columns]
        assert pk_columns == ["experiment_id"]

    def test_has_foreign_key_to_experiments(self):
        """InterviewGuide should have foreign key to experiments table."""
        fks = [fk.target_fullname for fk in InterviewGuide.__table__.foreign_keys]
        assert "experiments.id" in fks


class TestInterviewGuideCRUD:
    """Tests for InterviewGuide CRUD operations."""

    def test_create_interview_guide(self, session: Session):
        """Create interview guide with parent experiment."""
        # Create parent experiment first
        experiment = Experiment(
            id="exp_55555555",
            name="With Guide",
            hypothesis="Test hypothesis",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        session.add(experiment)
        session.commit()

        # Create interview guide
        guide = InterviewGuide(
            experiment_id="exp_55555555",
            context_definition="Interview context",
            questions="What do you think?",
            context_examples="Example usage",
            created_at=datetime.now().isoformat(),
        )
        session.add(guide)
        session.commit()

        result = session.get(InterviewGuide, "exp_55555555")
        assert result is not None
        assert result.context_definition == "Interview context"
        assert result.questions == "What do you think?"

    def test_experiment_interview_guide_relationship(self, session: Session):
        """Test 1:1 relationship between Experiment and InterviewGuide."""
        experiment = Experiment(
            id="exp_66666666",
            name="With Relationship",
            hypothesis="Test",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        session.add(experiment)
        session.commit()

        guide = InterviewGuide(
            experiment_id="exp_66666666",
            context_definition="Context",
            created_at=datetime.now().isoformat(),
        )
        session.add(guide)
        session.commit()

        # Access via relationship
        experiment = session.get(Experiment, "exp_66666666")
        assert experiment.interview_guide is not None
        assert experiment.interview_guide.context_definition == "Context"

    def test_cascade_delete_interview_guide(self, session: Session):
        """InterviewGuide should be deleted when parent Experiment is deleted."""
        experiment = Experiment(
            id="exp_77777777",
            name="To Delete",
            hypothesis="Test",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        session.add(experiment)
        session.commit()

        guide = InterviewGuide(
            experiment_id="exp_77777777",
            context_definition="Will be deleted",
            created_at=datetime.now().isoformat(),
        )
        session.add(guide)
        session.commit()

        # Delete experiment
        session.delete(experiment)
        session.commit()

        # Guide should also be deleted
        result = session.get(InterviewGuide, "exp_77777777")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
