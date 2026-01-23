"""Integration tests for experiment ownership.

Tests ownership assignment and persistence with real database.
"""
import pytest
from uuid import uuid4

from synth_lab.services.experiment_service import ExperimentService
from synth_lab.repositories.experiment_repository import ExperimentRepository


@pytest.mark.slow
class TestExperimentOwnership:
    """Test experiment ownership integration - T068."""

    def test_create_experiment_with_owner(self, db_session, create_test_user):
        """Should create experiment with owner_id and persist to database.

        Integration test covering:
        - Owner assignment during creation
        - Persistence to database
        - Retrieval with owner_id
        """
        # Setup
        repository = ExperimentRepository(db_session)
        experiment_service = ExperimentService(repository)
        # Create user first (required by FK constraint)
        owner_id = create_test_user(email="owner@example.com")

        # Create experiment with owner using correct service method
        created_exp = experiment_service.create_experiment(
            name="Owned Experiment",
            hypothesis="Test hypothesis",
            synth_group_id="grp_00000001",
            owner_id=owner_id,
        )

        # Verify owner assigned
        assert created_exp.owner_id == owner_id

        # Verify persisted to database
        from sqlalchemy import text
        query = text("SELECT owner_id FROM experiments WHERE id = :id")
        result = db_session.execute(query, {"id": created_exp.id})
        row = result.fetchone()

        assert row is not None
        assert row[0] == owner_id

    def test_retrieve_experiments_by_owner(self, db_session, create_test_user):
        """Should retrieve all experiments owned by a user.

        Integration test covering:
        - Multiple experiments with same owner
        - Filtering by owner_id
        """
        # Setup
        repository = ExperimentRepository(db_session)
        experiment_service = ExperimentService(repository)
        # Create users first (required by FK constraint)
        owner_id = create_test_user(email="owner1@example.com")
        other_owner_id = create_test_user(email="owner2@example.com")

        # Create experiments for owner
        experiment_service.create_experiment(
            name="Experiment 1",
            hypothesis="Hypothesis 1",
            synth_group_id="grp_00000001",
            owner_id=owner_id,
        )
        experiment_service.create_experiment(
            name="Experiment 2",
            hypothesis="Hypothesis 2",
            synth_group_id="grp_00000001",
            owner_id=owner_id,
        )

        # Create experiment for different owner
        experiment_service.create_experiment(
            name="Other Experiment",
            hypothesis="Hypothesis 3",
            synth_group_id="grp_00000001",
            owner_id=other_owner_id,
        )

        # Query experiments by owner
        from sqlalchemy import text
        query = text("SELECT id FROM experiments WHERE owner_id = :owner_id")
        result = db_session.execute(query, {"owner_id": owner_id})
        rows = result.fetchall()

        # Should have exactly 2 experiments
        assert len(rows) == 2

    def test_update_experiment_preserves_owner(self, db_session, create_test_user):
        """Should preserve owner_id when updating experiment.

        Integration test covering:
        - Owner_id immutability during updates
        """
        # Setup
        repository = ExperimentRepository(db_session)
        experiment_service = ExperimentService(repository)
        # Create user first (required by FK constraint)
        owner_id = create_test_user(email="owner@example.com")

        # Create experiment
        created_exp = experiment_service.create_experiment(
            name="Original Name",
            hypothesis="Original hypothesis",
            synth_group_id="grp_00000001",
            owner_id=owner_id,
        )

        # Update experiment using correct method
        experiment_service.update_experiment(
            experiment_id=created_exp.id,
            name="Updated Name",
        )

        # Verify owner_id unchanged
        from sqlalchemy import text
        query = text("SELECT owner_id FROM experiments WHERE id = :id")
        result = db_session.execute(query, {"id": created_exp.id})
        row = result.fetchone()

        assert row[0] == owner_id
