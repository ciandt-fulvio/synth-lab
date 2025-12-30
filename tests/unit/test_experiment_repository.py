"""
T011 Unit tests for ExperimentRepository.

Tests for the experiment data access layer following TDD methodology.
Write tests first, then implement repository to make them pass.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - Data model: specs/018-experiment-hub/data-model.md
"""

from datetime import datetime, timezone

import pytest

from synth_lab.domain.entities.experiment import Experiment
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
def experiment_repo(test_db):
    """Create ExperimentRepository with test database."""
    from synth_lab.repositories.experiment_repository import ExperimentRepository

    return ExperimentRepository(test_db)


class TestExperimentRepositoryCreate:
    """Tests for experiment creation."""

    def test_create_experiment_success(self, experiment_repo) -> None:
        """Verify experiment is created and persisted."""
        experiment = Experiment(
            name="Test Feature",
            hypothesis="Users will prefer this approach",
        )

        result = experiment_repo.create(experiment)

        assert result is not None
        assert result.id == experiment.id
        assert result.name == "Test Feature"
        assert result.hypothesis == "Users will prefer this approach"
        assert result.created_at is not None

    def test_create_experiment_generates_id(self, experiment_repo) -> None:
        """Verify experiment ID is generated when not provided."""
        experiment = Experiment(
            name="Test Feature",
            hypothesis="Test hypothesis",
        )

        result = experiment_repo.create(experiment)

        assert result.id.startswith("exp_")
        assert len(result.id) == 12  # exp_ + 8 hex chars

    def test_create_experiment_with_all_fields(self, experiment_repo) -> None:
        """Verify experiment is created with all optional fields."""
        experiment = Experiment(
            name="Complete Feature",
            hypothesis="Full hypothesis",
            description="Detailed description with context",
        )

        result = experiment_repo.create(experiment)

        assert result.description == "Detailed description with context"

    def test_create_experiment_with_custom_id(self, experiment_repo) -> None:
        """Verify experiment is created with custom ID."""
        experiment = Experiment(
            id="exp_12345678",
            name="Custom ID Feature",
            hypothesis="Test hypothesis",
        )

        result = experiment_repo.create(experiment)

        assert result.id == "exp_12345678"


class TestExperimentRepositoryGet:
    """Tests for experiment retrieval."""

    def test_get_experiment_by_id(self, experiment_repo) -> None:
        """Verify experiment can be retrieved by ID."""
        experiment = Experiment(
            name="Test Feature",
            hypothesis="Test hypothesis",
        )
        experiment_repo.create(experiment)

        result = experiment_repo.get_by_id(experiment.id)

        assert result is not None
        assert result.id == experiment.id
        assert result.name == "Test Feature"

    def test_get_experiment_not_found_returns_none(self, experiment_repo) -> None:
        """Verify get returns None for non-existent experiment."""
        result = experiment_repo.get_by_id("exp_nonexist")

        assert result is None

    def test_get_experiment_includes_timestamps(self, experiment_repo) -> None:
        """Verify retrieved experiment includes timestamps."""
        experiment = Experiment(
            name="Test Feature",
            hypothesis="Test hypothesis",
        )
        experiment_repo.create(experiment)

        result = experiment_repo.get_by_id(experiment.id)

        assert result.created_at is not None
        assert isinstance(result.created_at, datetime)


class TestExperimentRepositoryList:
    """Tests for experiment listing."""

    def test_list_experiments_with_pagination(self, experiment_repo) -> None:
        """Verify experiments are listed with pagination."""
        # Create 5 experiments
        for i in range(5):
            experiment = Experiment(
                name=f"Feature {i}",
                hypothesis=f"Hypothesis {i}",
            )
            experiment_repo.create(experiment)

        params = PaginationParams(limit=3, offset=0)
        result = experiment_repo.list_experiments(params)

        assert len(result.data) == 3
        assert result.pagination.total == 5
        assert result.pagination.has_next is True

    def test_list_experiments_empty_database(self, experiment_repo) -> None:
        """Verify empty list is returned when no experiments exist."""
        params = PaginationParams(limit=10, offset=0)
        result = experiment_repo.list_experiments(params)

        assert len(result.data) == 0
        assert result.pagination.total == 0

    def test_list_experiments_includes_counters(self, experiment_repo, test_db) -> None:
        """Verify experiments include has_analysis and interview counters."""
        # Create experiment
        experiment = Experiment(
            name="Feature with Runs",
            hypothesis="Test hypothesis",
        )
        experiment_repo.create(experiment)

        # Add analysis run
        test_db.execute(
            """
            INSERT INTO analysis_runs (id, experiment_id, config, status, started_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "ana_12345678",
                experiment.id,
                '{"scenario": "baseline"}',
                "completed",
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        # Add interviews (research_executions)
        test_db.execute(
            """
            INSERT INTO research_executions
            (exec_id, experiment_id, topic_name, status, synth_count, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "exec_001",
                experiment.id,
                "Test Topic",
                "completed",
                1,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        params = PaginationParams(limit=10, offset=0)
        result = experiment_repo.list_experiments(params)

        assert len(result.data) == 1
        assert result.data[0].has_analysis is True
        assert result.data[0].interview_count == 1

    def test_list_experiments_sorted_by_created_at_desc(self, experiment_repo) -> None:
        """Verify experiments are sorted by created_at descending."""
        exp1 = Experiment(name="First", hypothesis="H1")
        exp2 = Experiment(name="Second", hypothesis="H2")
        exp3 = Experiment(name="Third", hypothesis="H3")

        experiment_repo.create(exp1)
        experiment_repo.create(exp2)
        experiment_repo.create(exp3)

        params = PaginationParams(limit=10, offset=0)
        result = experiment_repo.list_experiments(params)

        # Most recent first (default sort)
        assert result.data[0].name == "Third"
        assert result.data[2].name == "First"


class TestExperimentRepositoryUpdate:
    """Tests for experiment updates."""

    def test_update_experiment_success(self, experiment_repo) -> None:
        """Verify experiment can be updated."""
        experiment = Experiment(
            name="Original Name",
            hypothesis="Original hypothesis",
        )
        experiment_repo.create(experiment)

        updated = experiment_repo.update(
            experiment.id,
            name="Updated Name",
            hypothesis="Updated hypothesis",
        )

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.hypothesis == "Updated hypothesis"

    def test_update_experiment_sets_updated_at(self, experiment_repo) -> None:
        """Verify update sets updated_at timestamp."""
        experiment = Experiment(
            name="Test Feature",
            hypothesis="Test hypothesis",
        )
        created = experiment_repo.create(experiment)

        assert created.updated_at is None

        updated = experiment_repo.update(
            experiment.id,
            name="Updated Name",
        )

        assert updated.updated_at is not None
        assert isinstance(updated.updated_at, datetime)

    def test_update_experiment_partial_fields(self, experiment_repo) -> None:
        """Verify only specified fields are updated."""
        experiment = Experiment(
            name="Original Name",
            hypothesis="Original hypothesis",
            description="Original description",
        )
        experiment_repo.create(experiment)

        updated = experiment_repo.update(
            experiment.id,
            name="Updated Name",
        )

        assert updated.name == "Updated Name"
        assert updated.hypothesis == "Original hypothesis"
        assert updated.description == "Original description"

    def test_update_nonexistent_experiment_returns_none(self, experiment_repo) -> None:
        """Verify update returns None for non-existent experiment."""
        result = experiment_repo.update(
            "exp_nonexist",
            name="Updated",
        )

        assert result is None


class TestExperimentRepositoryDelete:
    """Tests for experiment deletion."""

    def test_delete_experiment_success(self, experiment_repo) -> None:
        """Verify experiment can be deleted."""
        experiment = Experiment(
            name="To Delete",
            hypothesis="Test hypothesis",
        )
        experiment_repo.create(experiment)

        result = experiment_repo.delete(experiment.id)

        assert result is True
        assert experiment_repo.get_by_id(experiment.id) is None

    def test_delete_nonexistent_experiment_returns_false(self, experiment_repo) -> None:
        """Verify delete returns False for non-existent experiment."""
        result = experiment_repo.delete("exp_nonexist")

        assert result is False
