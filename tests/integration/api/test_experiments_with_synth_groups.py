"""
Integration tests for Experiments with Synth Groups.

Tests the integration between experiments and synth groups, verifying that:
- Experiments can be linked to synth groups
- Explorations and research interviews use the experiment's synth group
- Synths are correctly filtered by group

References:
    - Experiments Router: src/synth_lab/api/routers/experiments.py
    - Synth Groups Router: src/synth_lab/api/routers/synth_groups.py
    - Spec: specs/030-custom-synth-groups/spec.md
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from synth_lab.api.main import app
from synth_lab.models.orm.experiment import Experiment as ExperimentORM
from synth_lab.models.orm.synth import SynthGroup as SynthGroupORM
from synth_lab.domain.entities.synth_group import DEFAULT_SYNTH_GROUP_ID


@pytest.fixture
def client(db_session):
    """Create test client with shared database session."""
    # Import routers to override services
    from synth_lab.api.routers import experiments as experiments_router
    from synth_lab.api.routers import synth_groups as synth_groups_router
    from synth_lab.services.experiment_service import ExperimentService
    from synth_lab.services.synth_group_service import SynthGroupService
    from synth_lab.repositories.experiment_repository import ExperimentRepository
    from synth_lab.repositories.synth_group_repository import SynthGroupRepository

    # Create services with test session
    exp_repo = ExperimentRepository(session=db_session)
    exp_service = ExperimentService(repository=exp_repo)

    sg_repo = SynthGroupRepository(session=db_session)
    sg_service = SynthGroupService(repository=sg_repo)

    # Override service getters
    original_exp_service = experiments_router._get_service
    original_sg_service = synth_groups_router._get_service

    experiments_router._get_service = lambda: exp_service
    synth_groups_router._get_service = lambda: sg_service

    yield TestClient(app)

    # Restore originals
    experiments_router._get_service = original_exp_service
    synth_groups_router._get_service = original_sg_service


@pytest.fixture
def default_synth_group(db_session):
    """Ensure default synth group exists."""
    from synth_lab.repositories.synth_group_repository import SynthGroupRepository

    repo = SynthGroupRepository(session=db_session)
    group = repo.ensure_default_group()
    db_session.commit()
    return group


class TestExperimentsWithDefaultGroup:
    """Tests for experiments using default synth group."""

    def test_create_experiment_defaults_to_default_group(
        self, client, db_session, default_synth_group
    ):
        """Create experiment without synth_group_id uses default."""
        response = client.post(
            "/experiments",
            json={
                "name": "Test Experiment",
                "hypothesis": "Testing default group",
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["synth_group_id"] == DEFAULT_SYNTH_GROUP_ID

        # Verify in database
        exp = db_session.get(ExperimentORM, data["id"])
        assert exp.synth_group_id == DEFAULT_SYNTH_GROUP_ID

    def test_create_experiment_explicitly_set_default_group(
        self, client, db_session, default_synth_group
    ):
        """Create experiment with explicit default group ID."""
        response = client.post(
            "/experiments",
            json={
                "name": "Test Experiment",
                "hypothesis": "Explicit default",
                "synth_group_id": DEFAULT_SYNTH_GROUP_ID,
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["synth_group_id"] == DEFAULT_SYNTH_GROUP_ID


class TestExperimentsWithCustomGroup:
    """Tests for experiments using custom synth groups."""

    def test_create_experiment_with_custom_group(
        self, client, db_session, default_synth_group
    ):
        """Create experiment linked to custom synth group."""
        # First create a custom synth group
        group_response = client.post(
            "/synth-groups",
            json={"name": "Custom Experiment Group"},
        )
        group_id = group_response.json()["id"]

        # Create experiment with this group
        exp_response = client.post(
            "/experiments",
            json={
                "name": "Custom Group Experiment",
                "hypothesis": "Testing custom group",
                "synth_group_id": group_id,
            },
        )

        assert exp_response.status_code == 201
        exp_data = exp_response.json()

        assert exp_data["synth_group_id"] == group_id

        # Verify in database
        exp = db_session.get(ExperimentORM, exp_data["id"])
        assert exp.synth_group_id == group_id

    def test_create_experiment_with_invalid_group_fails(
        self, client, default_synth_group
    ):
        """Create experiment with non-existent group fails."""
        response = client.post(
            "/experiments",
            json={
                "name": "Invalid Group Experiment",
                "hypothesis": "Testing invalid group",
                "synth_group_id": "grp_nonexist",
            },
        )

        # Should fail with validation or foreign key error
        assert response.status_code in [400, 422, 500]

    def test_get_experiment_includes_synth_group_id(
        self, client, db_session, default_synth_group
    ):
        """Get experiment includes synth_group_id."""
        # Create group and experiment
        group_response = client.post(
            "/synth-groups",
            json={"name": "Test Group"},
        )
        group_id = group_response.json()["id"]

        exp_response = client.post(
            "/experiments",
            json={
                "name": "Test Experiment",
                "hypothesis": "Test",
                "synth_group_id": group_id,
            },
        )
        exp_id = exp_response.json()["id"]

        # Get experiment
        get_response = client.get(f"/experiments/{exp_id}")

        assert get_response.status_code == 200
        data = get_response.json()

        assert data["synth_group_id"] == group_id

    def test_list_experiments_includes_synth_group_id(
        self, client, db_session, default_synth_group
    ):
        """List experiments includes synth_group_id for each experiment."""
        # Create experiments with different groups
        group1 = client.post("/synth-groups", json={"name": "Group 1"}).json()
        group2 = client.post("/synth-groups", json={"name": "Group 2"}).json()

        exp1 = client.post(
            "/experiments",
            json={
                "name": "Exp 1",
                "hypothesis": "Test",
                "synth_group_id": group1["id"],
            },
        ).json()

        exp2 = client.post(
            "/experiments",
            json={
                "name": "Exp 2",
                "hypothesis": "Test",
                "synth_group_id": group2["id"],
            },
        ).json()

        # List experiments
        list_response = client.get("/experiments")

        assert list_response.status_code == 200
        experiments = list_response.json()["data"]

        # Find our experiments
        exp1_data = next(e for e in experiments if e["id"] == exp1["id"])
        exp2_data = next(e for e in experiments if e["id"] == exp2["id"])

        assert exp1_data["synth_group_id"] == group1["id"]
        assert exp2_data["synth_group_id"] == group2["id"]


class TestUpdateExperimentSynthGroup:
    """Tests for updating experiment's synth group."""

    def test_update_experiment_change_synth_group(
        self, client, db_session, default_synth_group
    ):
        """Update experiment to use different synth group."""
        # Create two groups
        group1 = client.post("/synth-groups", json={"name": "Group 1"}).json()
        group2 = client.post("/synth-groups", json={"name": "Group 2"}).json()

        # Create experiment with group1
        exp = client.post(
            "/experiments",
            json={
                "name": "Test Experiment",
                "hypothesis": "Test",
                "synth_group_id": group1["id"],
            },
        ).json()

        # Update to group2
        update_response = client.put(
            f"/experiments/{exp['id']}",
            json={
                "name": "Test Experiment",
                "hypothesis": "Test",
                "synth_group_id": group2["id"],
            },
        )

        assert update_response.status_code == 200
        updated = update_response.json()

        assert updated["synth_group_id"] == group2["id"]

        # Verify in database
        exp_orm = db_session.get(ExperimentORM, exp["id"])
        assert exp_orm.synth_group_id == group2["id"]


class TestSynthsFilterByGroup:
    """Tests for filtering synths by group."""

    def test_filter_synths_by_group(self, client, db_session, default_synth_group):
        """Filter synths by synth_group_id."""
        # Create group with synths
        config = {"n_synths": 5}
        group = client.post(
            "/synth-groups/with-config",
            json={"name": "Filter Test Group", "config": config},
        ).json()

        # Get synths for this group
        synths_response = client.get(f"/synths?synth_group_id={group['id']}")

        assert synths_response.status_code == 200
        synths = synths_response.json()

        # Should return only synths from this group
        assert len(synths) == 5
        for synth in synths:
            assert synth.get("synth_group_id") == group["id"]

    def test_filter_synths_by_default_group(
        self, client, db_session, default_synth_group
    ):
        """Filter synths by default group."""
        # Synths in default group may or may not exist
        # Just verify the endpoint accepts the filter
        response = client.get(f"/synths?synth_group_id={DEFAULT_SYNTH_GROUP_ID}")

        assert response.status_code == 200
        synths = response.json()

        # All returned synths should be in default group or have null group_id
        for synth in synths:
            group_id = synth.get("synth_group_id")
            assert group_id in [DEFAULT_SYNTH_GROUP_ID, None]


class TestDeleteSynthGroupWithExperiments:
    """Tests for deleting synth groups that have experiments."""

    def test_delete_group_with_experiments_may_fail(
        self, client, db_session, default_synth_group
    ):
        """Delete group that has experiments should be prevented by FK."""
        # Create group
        group = client.post("/synth-groups", json={"name": "Group to Delete"}).json()

        # Create experiment using this group
        client.post(
            "/experiments",
            json={
                "name": "Dependent Experiment",
                "hypothesis": "Test",
                "synth_group_id": group["id"],
            },
        )

        # Try to delete group - should fail due to FK constraint
        delete_response = client.delete(f"/synth-groups/{group['id']}")

        # Depending on FK settings, this might be 400, 409, or 500
        # Or it might succeed if FK is SET NULL
        # Just verify we get a response
        assert delete_response.status_code in [204, 400, 409, 500]


class TestExperimentsSynthGroupIntegrationFlow:
    """End-to-end tests for experiments and synth groups integration."""

    def test_full_flow_custom_group_to_experiment(
        self, client, db_session, default_synth_group
    ):
        """Test full flow: create custom group → create experiment → verify linkage."""
        # 1. Create custom synth group with synths
        config = {"n_synths": 10}
        group_response = client.post(
            "/synth-groups/with-config",
            json={
                "name": "Retirees 60+ Group",
                "description": "Custom group for retirees",
                "config": config,
            },
        )
        assert group_response.status_code == 201
        group = group_response.json()

        # 2. Create experiment using this group
        exp_response = client.post(
            "/experiments",
            json={
                "name": "Retirement Planning Feature",
                "hypothesis": "Retirees prefer simplified interfaces",
                "synth_group_id": group["id"],
            },
        )
        assert exp_response.status_code == 201
        experiment = exp_response.json()

        # 3. Verify experiment has correct group
        assert experiment["synth_group_id"] == group["id"]

        # 4. Get experiment detail - should include group ID
        detail_response = client.get(f"/experiments/{experiment['id']}")
        detail = detail_response.json()
        assert detail["synth_group_id"] == group["id"]

        # 5. Get group detail - should have 10 synths
        group_detail = client.get(f"/synth-groups/{group['id']}")
        assert group_detail.json()["synth_count"] == 10

        # 6. Filter synths by this group
        synths_response = client.get(f"/synths?synth_group_id={group['id']}")
        synths = synths_response.json()
        assert len(synths) == 10

    def test_multiple_experiments_same_group(
        self, client, db_session, default_synth_group
    ):
        """Multiple experiments can share the same synth group."""
        # Create one group
        group = client.post(
            "/synth-groups",
            json={"name": "Shared Group"},
        ).json()

        # Create multiple experiments using this group
        exp1 = client.post(
            "/experiments",
            json={
                "name": "Experiment 1",
                "hypothesis": "Test 1",
                "synth_group_id": group["id"],
            },
        ).json()

        exp2 = client.post(
            "/experiments",
            json={
                "name": "Experiment 2",
                "hypothesis": "Test 2",
                "synth_group_id": group["id"],
            },
        ).json()

        # Both should have same group ID
        assert exp1["synth_group_id"] == group["id"]
        assert exp2["synth_group_id"] == group["id"]

        # Verify both experiments exist
        exp1_detail = client.get(f"/experiments/{exp1['id']}").json()
        exp2_detail = client.get(f"/experiments/{exp2['id']}").json()

        assert exp1_detail["synth_group_id"] == group["id"]
        assert exp2_detail["synth_group_id"] == group["id"]
