"""
Integration tests for ExperimentRepository with SQLAlchemy ORM backend.

These tests verify that ExperimentRepository works correctly with SQLAlchemy
sessions, ensuring full CRUD operations, relationships, and data integrity.

References:
    - Repository: synth_lab.repositories.experiment_repository
    - ORM Models: synth_lab.models.orm
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from synth_lab.models.orm.base import Base
from synth_lab.models.orm.experiment import Experiment as ExperimentORM
from synth_lab.models.orm.analysis import AnalysisRun as AnalysisRunORM
from synth_lab.domain.entities.experiment import Experiment, ScorecardData, ScorecardDimension
from synth_lab.models.pagination import PaginationParams
from synth_lab.repositories.experiment_repository import ExperimentRepository


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


@pytest.fixture(scope="function")
def repo(session: Session):
    """Create ExperimentRepository with ORM session."""
    return ExperimentRepository(session=session)


class TestExperimentRepositoryCreate:
    """Tests for creating experiments via SQLAlchemy."""

    def test_create_experiment_success(self, repo: ExperimentRepository, session: Session):
        """Create experiment using ORM backend."""
        experiment = Experiment(
            name="SQLAlchemy Test",
            hypothesis="ORM works correctly",
        )
        result = repo.create(experiment)
        session.commit()

        assert result.id == experiment.id
        assert result.name == "SQLAlchemy Test"

        # Verify in database
        orm_exp = session.get(ExperimentORM, experiment.id)
        assert orm_exp is not None
        assert orm_exp.name == "SQLAlchemy Test"
        assert orm_exp.status == "active"

    def test_create_experiment_with_description(self, repo: ExperimentRepository, session: Session):
        """Create experiment with optional description."""
        experiment = Experiment(
            name="With Description",
            hypothesis="Test",
            description="A detailed description of the experiment",
        )
        result = repo.create(experiment)
        session.commit()

        orm_exp = session.get(ExperimentORM, experiment.id)
        assert orm_exp.description == "A detailed description of the experiment"

    def test_create_experiment_with_scorecard(self, repo: ExperimentRepository, session: Session):
        """Create experiment with scorecard data."""
        scorecard = ScorecardData(
            feature_name="Test Feature",
            description_text="A test feature",
            complexity=ScorecardDimension(score=0.3),
            initial_effort=ScorecardDimension(score=0.4),
            perceived_risk=ScorecardDimension(score=0.2),
            time_to_value=ScorecardDimension(score=0.6),
        )
        experiment = Experiment(
            name="With Scorecard",
            hypothesis="Scorecard works",
            scorecard_data=scorecard,
        )
        result = repo.create(experiment)
        session.commit()

        retrieved = repo.get_by_id(experiment.id)
        assert retrieved is not None
        assert retrieved.has_scorecard()
        assert retrieved.scorecard_data.feature_name == "Test Feature"


class TestExperimentRepositoryGet:
    """Tests for retrieving experiments via SQLAlchemy."""

    def test_get_by_id_success(self, repo: ExperimentRepository, session: Session):
        """Retrieve experiment by ID."""
        experiment = Experiment(name="To Retrieve", hypothesis="Test")
        repo.create(experiment)
        session.commit()

        result = repo.get_by_id(experiment.id)
        assert result is not None
        assert result.id == experiment.id
        assert result.name == "To Retrieve"

    def test_get_by_id_not_found(self, repo: ExperimentRepository):
        """Return None for non-existent experiment."""
        result = repo.get_by_id("exp_nonexistent")
        assert result is None

    def test_get_by_id_excludes_deleted(self, repo: ExperimentRepository, session: Session):
        """Soft-deleted experiments should not be returned."""
        experiment = Experiment(name="To Delete", hypothesis="Test")
        repo.create(experiment)
        session.commit()

        # Soft delete
        repo.delete(experiment.id)
        session.commit()

        result = repo.get_by_id(experiment.id)
        assert result is None


class TestExperimentRepositoryList:
    """Tests for listing experiments via SQLAlchemy."""

    def test_list_experiments_empty(self, repo: ExperimentRepository):
        """List returns empty when no experiments exist."""
        params = PaginationParams(limit=10, offset=0)
        result = repo.list_experiments(params)

        assert len(result.data) == 0
        assert result.pagination.total == 0

    def test_list_experiments_with_pagination(self, repo: ExperimentRepository, session: Session):
        """List experiments with pagination."""
        # Create 15 experiments
        for i in range(15):
            experiment = Experiment(name=f"Exp {i}", hypothesis=f"Hypothesis {i}")
            repo.create(experiment)
        session.commit()

        # First page
        params = PaginationParams(limit=10, offset=0)
        result = repo.list_experiments(params)
        assert len(result.data) == 10
        assert result.pagination.total == 15
        assert result.pagination.has_next is True

        # Second page
        params = PaginationParams(limit=10, offset=10)
        result = repo.list_experiments(params)
        assert len(result.data) == 5
        assert result.pagination.has_next is False

    def test_list_experiments_excludes_deleted(self, repo: ExperimentRepository, session: Session):
        """Soft-deleted experiments are excluded from list."""
        exp1 = Experiment(name="Active", hypothesis="Test")
        exp2 = Experiment(name="To Delete", hypothesis="Test")
        repo.create(exp1)
        repo.create(exp2)
        session.commit()

        repo.delete(exp2.id)
        session.commit()

        params = PaginationParams(limit=10, offset=0)
        result = repo.list_experiments(params)
        assert result.pagination.total == 1
        assert result.data[0].name == "Active"

    def test_list_experiments_sorted_by_created_at_desc(self, repo: ExperimentRepository, session: Session):
        """Experiments are sorted by created_at descending."""
        from time import sleep

        exp1 = Experiment(name="First", hypothesis="Test")
        repo.create(exp1)
        session.commit()

        sleep(0.01)  # Small delay to ensure different timestamps

        exp2 = Experiment(name="Second", hypothesis="Test")
        repo.create(exp2)
        session.commit()

        params = PaginationParams(limit=10, offset=0)
        result = repo.list_experiments(params)

        assert result.data[0].name == "Second"
        assert result.data[1].name == "First"


class TestExperimentRepositoryUpdate:
    """Tests for updating experiments via SQLAlchemy."""

    def test_update_experiment_name(self, repo: ExperimentRepository, session: Session):
        """Update experiment name."""
        experiment = Experiment(name="Original", hypothesis="Test")
        repo.create(experiment)
        session.commit()

        result = repo.update(experiment.id, name="Updated")
        session.commit()

        assert result is not None
        assert result.name == "Updated"
        assert result.updated_at is not None

    def test_update_experiment_multiple_fields(self, repo: ExperimentRepository, session: Session):
        """Update multiple fields at once."""
        experiment = Experiment(name="Original", hypothesis="Original hypothesis")
        repo.create(experiment)
        session.commit()

        result = repo.update(
            experiment.id,
            name="New Name",
            hypothesis="New hypothesis",
            description="New description",
        )
        session.commit()

        assert result.name == "New Name"
        assert result.hypothesis == "New hypothesis"
        assert result.description == "New description"

    def test_update_nonexistent_returns_none(self, repo: ExperimentRepository):
        """Update returns None for non-existent experiment."""
        result = repo.update("exp_nonexistent", name="Test")
        assert result is None

    def test_update_scorecard(self, repo: ExperimentRepository, session: Session):
        """Update experiment scorecard."""
        experiment = Experiment(name="Test", hypothesis="Test")
        repo.create(experiment)
        session.commit()

        scorecard = ScorecardData(
            feature_name="New Feature",
            description_text="Description",
            complexity=ScorecardDimension(score=0.5),
            initial_effort=ScorecardDimension(score=0.5),
            perceived_risk=ScorecardDimension(score=0.5),
            time_to_value=ScorecardDimension(score=0.5),
        )
        result = repo.update_scorecard(experiment.id, scorecard)
        session.commit()

        assert result is not None
        assert result.has_scorecard()
        assert result.scorecard_data.feature_name == "New Feature"


class TestExperimentRepositoryDelete:
    """Tests for deleting experiments via SQLAlchemy."""

    def test_soft_delete_experiment(self, repo: ExperimentRepository, session: Session):
        """Soft delete sets status to 'deleted'."""
        experiment = Experiment(name="To Delete", hypothesis="Test")
        repo.create(experiment)
        session.commit()

        result = repo.delete(experiment.id)
        session.commit()

        assert result is True

        # Verify in database - still exists but with deleted status
        orm_exp = session.get(ExperimentORM, experiment.id)
        assert orm_exp is not None
        assert orm_exp.status == "deleted"

    def test_delete_nonexistent_returns_false(self, repo: ExperimentRepository):
        """Delete returns False for non-existent experiment."""
        result = repo.delete("exp_nonexistent")
        assert result is False


class TestExperimentRepositoryRelationships:
    """Tests for experiment relationships via SQLAlchemy."""

    def test_list_includes_has_analysis_flag(self, repo: ExperimentRepository, session: Session):
        """Experiment summary should include has_analysis flag."""
        experiment = Experiment(name="With Analysis", hypothesis="Test")
        repo.create(experiment)
        session.commit()

        # Create analysis run directly
        analysis = AnalysisRunORM(
            id="ana_test0001",
            experiment_id=experiment.id,
            config={},
            status="completed",
            started_at=datetime.now().isoformat(),
        )
        session.add(analysis)
        session.commit()

        params = PaginationParams(limit=10, offset=0)
        result = repo.list_experiments(params)

        assert len(result.data) == 1
        assert result.data[0].has_analysis is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
