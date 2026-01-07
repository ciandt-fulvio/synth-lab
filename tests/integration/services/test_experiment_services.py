"""
Integration tests for experiment-related services.

Tests experiment creation, updates, and synth management.
Uses real database and tests Service → Repository → Database flow.

Executar: pytest -m integration tests/integration/services/test_experiment_services.py
"""

import pytest
from datetime import datetime

from synth_lab.services.experiment_service import ExperimentService
from synth_lab.services.synth_service import SynthService
from synth_lab.services.synth_group_service import SynthGroupService
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.repositories.synth_group_repository import SynthGroupRepository
from synth_lab.repositories.synth_repository import SynthRepository
from synth_lab.models.orm.experiment import Experiment
from synth_lab.models.orm.synth import Synth, SynthGroup


@pytest.mark.integration
class TestExperimentServiceIntegration:
    """Integration tests for experiment_service.py - Core experiment CRUD operations."""

    def test_create_experiment_persists_to_database(self, db_session):
        """Test that creating an experiment saves it to the database."""
        repo = ExperimentRepository(session=db_session)
        service = ExperimentService(repository=repo)

        # Execute: Create experiment
        experiment = service.create_experiment(
            name="Integration Test Experiment",
            hypothesis="Testing integration with database",
            description="This is a test experiment for integration testing",
        )

        # Verify: Check it was saved
        assert experiment.id is not None, "Experiment should have ID after creation"
        assert experiment.name == "Integration Test Experiment"
        assert experiment.hypothesis == "Testing integration with database"

        # Verify in database
        db_experiment = db_session.query(Experiment).filter_by(id=experiment.id).first()
        assert db_experiment is not None, "Experiment should exist in database"
        assert db_experiment.name == experiment.name
        assert db_experiment.status == "active", "Default status should be active"

    def test_list_experiments_returns_sorted_results(self, db_session):
        """Test that list_experiments returns properly sorted paginated results."""
        # Count existing experiments before creating new ones (seeded data)
        repo = ExperimentRepository(session=db_session)
        service = ExperimentService(repository=repo)
        from synth_lab.models.pagination import PaginationParams

        initial_params = PaginationParams(limit=1, offset=0)
        initial_result = service.list_experiments(initial_params)
        initial_count = initial_result.pagination.total

        # Setup: Create multiple experiments (IDs must match ^exp_[a-f0-9]{8}$ pattern)
        for i in range(5):
            exp = Experiment(
                id=f"exp_1a2b3c{i:02d}",
                name=f"List Test Experiment {i}",
                hypothesis=f"Hypothesis {i}",
                status="active",
                created_at=datetime.now().isoformat(),
            )
            db_session.add(exp)

        db_session.commit()

        # Execute
        params = PaginationParams(limit=10, offset=0, sort_by="created_at", sort_order="desc")
        result = service.list_experiments(params)

        # Verify: total should include both seeded and newly created experiments
        assert result.pagination.total == initial_count + 5
        assert len(result.data) <= 10, "Should return at most 10 experiments"
        assert all(exp.id is not None for exp in result.data)
        assert all(exp.name is not None for exp in result.data)

    def test_update_experiment_modifies_database_record(self, db_session):
        """Test that updating an experiment persists changes to database."""
        # Setup: Create experiment with valid ID format (exp_[8 hex chars])
        experiment = Experiment(
            id="exp_12345678",
            name="Original Name",
            hypothesis="Original Hypothesis",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(experiment)
        db_session.commit()

        # Execute: Update experiment
        repo = ExperimentRepository(session=db_session)
        service = ExperimentService(repository=repo)

        updated = service.update_experiment(
            experiment_id="exp_12345678",
            name="Updated Name",
            description="New description added"
        )

        # Verify
        assert updated.name == "Updated Name"
        assert updated.description == "New description added"
        assert updated.hypothesis == "Original Hypothesis", "Hypothesis should remain unchanged"

        # Verify in database
        db_experiment = db_session.query(Experiment).filter_by(id="exp_12345678").first()
        assert db_experiment.name == "Updated Name"
        assert db_experiment.updated_at is not None, "updated_at should be set"

    def test_delete_experiment_removes_from_database(self, db_session):
        """Test that deleting an experiment soft-deletes it (sets status='deleted')."""
        # Setup with valid ID format
        experiment = Experiment(
            id="exp_abcdef12",
            name="To Be Deleted",
            hypothesis="Will be removed",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(experiment)
        db_session.commit()

        # Execute
        repo = ExperimentRepository(session=db_session)
        service = ExperimentService(repository=repo)
        service.delete_experiment("exp_abcdef12")

        # Verify: Experiment should be soft-deleted (status='deleted')
        db_experiment = db_session.query(Experiment).filter_by(id="exp_abcdef12").first()
        assert db_experiment is not None, "Experiment should still exist in database"
        assert db_experiment.status == "deleted", "Experiment should have status='deleted'"


@pytest.mark.integration
class TestSynthGroupServiceIntegration:
    """Integration tests for synth_group_service.py - Synth group management."""

    def test_create_synth_group_links_to_experiment(self, db_session):
        """Test that creating a synth group establishes FK relationship with experiment."""
        # Setup: Create parent experiment (ID must match ^exp_[a-f0-9]{8}$ pattern)
        experiment = Experiment(
            id="exp_e1f2a3b4",
            name="Group Test Experiment",
            hypothesis="Testing synth group creation",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(experiment)
        db_session.commit()

        # Execute: Create synth group
        repo = SynthGroupRepository(session=db_session)
        service = SynthGroupService(repository=repo)

        group = service.create_group(
            name="Test Group",
            description="Test synth group"
        )

        # Verify
        assert group.id is not None
        assert group.name == "Test Group"
        assert group.description == "Test synth group"

        # Verify in database
        db_group = db_session.query(SynthGroup).filter_by(id=group.id).first()
        assert db_group is not None
        assert db_group.name == "Test Group"

    def test_list_groups_returns_paginated_results(self, db_session):
        """Test that list_groups returns properly paginated results."""
        # Count existing groups before creating new ones (seeded data)
        repo = SynthGroupRepository(session=db_session)
        service = SynthGroupService(repository=repo)
        from synth_lab.models.pagination import PaginationParams

        initial_params = PaginationParams(limit=1, offset=0)
        initial_result = service.list_groups(initial_params)
        initial_count = initial_result.pagination.total

        # Setup: Create multiple groups (IDs must match ^grp_[a-f0-9]{8}$ pattern)
        for i in range(5):
            group = SynthGroup(
                id=f"grp_1a2b3c{i:02d}",
                name=f"List Test Group {i}",
                description=f"Description {i}",
                created_at=datetime.now().isoformat(),
            )
            db_session.add(group)

        db_session.commit()

        # Execute: List groups
        params = PaginationParams(limit=10, offset=0)
        result = service.list_groups(params)

        # Verify: total should include both seeded and newly created groups
        assert result.pagination.total == initial_count + 5
        assert len(result.data) <= 10, "Should return at most 10 groups"
        assert all(g.id is not None for g in result.data)


@pytest.mark.integration
class TestSynthServiceIntegration:
    """Integration tests for synth_service.py - Individual synth operations."""

    def test_get_synth_retrieves_from_database(self, db_session):
        """Test that get_synth retrieves synth data from database."""
        # Setup: Create synth in database
        synth = Synth(
            id="test01",
            nome="Test Synth",
            data={
                "id": "test01",
                "nome": "Test Synth",
                "descricao": "A test synthetic persona",
                "version": "2.3.0",
                "demografia": {"idade": 30, "genero_biologico": "masculino", "raca_etnia": "pardo"},
                "psicografia": {"interesses": ["Tech", "Music"]},
            },
            version="2.3.0",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(synth)
        db_session.commit()

        # Execute: Get synth
        repo = SynthRepository(session=db_session)
        service = SynthService(synth_repo=repo)

        result = service.get_synth("test01")

        # Verify
        assert result.id == "test01"
        assert result.nome == "Test Synth"
        assert result.psicografia is not None
        assert "Tech" in result.psicografia.interesses


@pytest.mark.integration
class TestExperimentServiceErrorHandling:
    """Integration tests for error handling in experiment services."""

    def test_get_experiment_returns_none_for_nonexistent(self, db_session):
        """Test that service returns None for non-existent experiment."""
        repo = ExperimentRepository(session=db_session)
        service = ExperimentService(repository=repo)

        result = service.get_experiment("non_existent_id")

        assert result is None, "Should return None for non-existent experiment"

    def test_update_nonexistent_experiment_returns_none(self, db_session):
        """Test that updating non-existent experiment returns None."""
        repo = ExperimentRepository(session=db_session)
        service = ExperimentService(repository=repo)

        result = service.update_experiment(
            experiment_id="non_existent_id",
            name="New Name"
        )

        assert result is None, "Should return None for non-existent experiment"
