"""
T015 Unit tests for ExperimentService.

Tests for the experiment business logic layer following TDD methodology.
Write tests first, then implement service to make them pass.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - Data model: specs/018-experiment-hub/data-model.md
"""

from datetime import datetime, timezone

import pytest

from synth_lab.domain.entities.experiment import Experiment
from synth_lab.infrastructure.database import DatabaseManager, init_database
from synth_lab.models.pagination import PaginationParams
from synth_lab.repositories.experiment_repository import ExperimentRepository


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
    return ExperimentRepository(test_db)


@pytest.fixture
def experiment_service(experiment_repo):
    """Create ExperimentService with test repository."""
    from synth_lab.services.experiment_service import ExperimentService

    return ExperimentService(experiment_repo)


class TestExperimentServiceCreate:
    """Tests for experiment creation validation."""

    def test_create_experiment_validates_name_required(
        self, experiment_service
    ) -> None:
        """Verify name is required for experiment creation."""
        with pytest.raises(ValueError, match="name"):
            experiment_service.create_experiment(
                name="",
                hypothesis="Valid hypothesis",
            )

    def test_create_experiment_validates_hypothesis_required(
        self, experiment_service
    ) -> None:
        """Verify hypothesis is required for experiment creation."""
        with pytest.raises(ValueError, match="hypothesis"):
            experiment_service.create_experiment(
                name="Valid Name",
                hypothesis="",
            )

    def test_create_experiment_validates_name_max_length(
        self, experiment_service
    ) -> None:
        """Verify name max length is enforced."""
        with pytest.raises(ValueError, match="100"):
            experiment_service.create_experiment(
                name="x" * 101,
                hypothesis="Valid hypothesis",
            )

    def test_create_experiment_validates_hypothesis_max_length(
        self, experiment_service
    ) -> None:
        """Verify hypothesis max length is enforced."""
        with pytest.raises(ValueError, match="500"):
            experiment_service.create_experiment(
                name="Valid name",
                hypothesis="x" * 501,
            )

    def test_create_experiment_success(self, experiment_service) -> None:
        """Verify experiment is created with valid data."""
        result = experiment_service.create_experiment(
            name="Test Feature",
            hypothesis="Users will prefer this approach",
            description="Additional context",
        )

        assert result is not None
        assert result.id.startswith("exp_")
        assert result.name == "Test Feature"
        assert result.hypothesis == "Users will prefer this approach"
        assert result.description == "Additional context"


class TestExperimentServiceGet:
    """Tests for experiment retrieval with nested data."""

    def test_get_experiment_by_id(self, experiment_service) -> None:
        """Verify experiment can be retrieved by ID."""
        created = experiment_service.create_experiment(
            name="Test Feature",
            hypothesis="Test hypothesis",
        )

        result = experiment_service.get_experiment(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Test Feature"

    def test_get_experiment_not_found_returns_none(
        self, experiment_service
    ) -> None:
        """Verify get returns None for non-existent experiment."""
        result = experiment_service.get_experiment("exp_nonexist")

        assert result is None

    def test_get_experiment_with_analysis_and_interviews(
        self, experiment_service, test_db
    ) -> None:
        """Verify experiment detail includes analysis and interviews."""
        created = experiment_service.create_experiment(
            name="Test Feature",
            hypothesis="Test hypothesis",
        )

        # Add analysis run
        test_db.execute(
            """
            INSERT INTO analysis_runs (id, experiment_id, config, status, started_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "ana_12345678",
                created.id,
                '{"scenario": "baseline"}',
                "completed",
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        # Add interview (research_execution)
        test_db.execute(
            """
            INSERT INTO research_executions
            (exec_id, experiment_id, topic_name, status, synth_count, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "exec_001",
                created.id,
                "Test Topic",
                "completed",
                5,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        result = experiment_service.get_experiment_detail(created.id)

        assert result is not None
        assert result.has_analysis is True  # Summary returns has_analysis flag
        assert result.interview_count == 1


class TestExperimentServiceList:
    """Tests for experiment listing."""

    def test_list_experiments_with_pagination(self, experiment_service) -> None:
        """Verify experiments are listed with pagination."""
        # Create 5 experiments
        for i in range(5):
            experiment_service.create_experiment(
                name=f"Feature {i}",
                hypothesis=f"Hypothesis {i}",
            )

        params = PaginationParams(limit=3, offset=0)
        result = experiment_service.list_experiments(params)

        assert len(result.data) == 3
        assert result.pagination.total == 5

    def test_list_experiments_empty_returns_empty_list(
        self, experiment_service
    ) -> None:
        """Verify empty list is returned when no experiments exist."""
        params = PaginationParams(limit=10, offset=0)
        result = experiment_service.list_experiments(params)

        assert len(result.data) == 0
        assert result.pagination.total == 0


class TestExperimentServiceUpdate:
    """Tests for experiment updates."""

    def test_update_experiment_success(self, experiment_service) -> None:
        """Verify experiment can be updated."""
        created = experiment_service.create_experiment(
            name="Original Name",
            hypothesis="Original hypothesis",
        )

        updated = experiment_service.update_experiment(
            created.id,
            name="Updated Name",
        )

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.hypothesis == "Original hypothesis"

    def test_update_experiment_validates_name_max_length(
        self, experiment_service
    ) -> None:
        """Verify update validates name max length."""
        created = experiment_service.create_experiment(
            name="Original Name",
            hypothesis="Original hypothesis",
        )

        with pytest.raises(ValueError, match="100"):
            experiment_service.update_experiment(
                created.id,
                name="x" * 101,
            )

    def test_update_nonexistent_experiment_returns_none(
        self, experiment_service
    ) -> None:
        """Verify update returns None for non-existent experiment."""
        result = experiment_service.update_experiment(
            "exp_nonexist",
            name="Updated",
        )

        assert result is None


class TestExperimentServiceDelete:
    """Tests for experiment deletion."""

    def test_delete_experiment_success(self, experiment_service) -> None:
        """Verify experiment can be deleted."""
        created = experiment_service.create_experiment(
            name="To Delete",
            hypothesis="Test hypothesis",
        )

        result = experiment_service.delete_experiment(created.id)

        assert result is True
        assert experiment_service.get_experiment(created.id) is None

    def test_delete_nonexistent_experiment_returns_false(
        self, experiment_service
    ) -> None:
        """Verify delete returns False for non-existent experiment."""
        result = experiment_service.delete_experiment("exp_nonexist")

        assert result is False
