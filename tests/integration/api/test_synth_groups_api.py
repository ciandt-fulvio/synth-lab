"""
Integration tests for Synth Groups API endpoints.

Tests the full synth groups flow from API request to database persistence.

References:
    - Router: src/synth_lab/api/routers/synth_groups.py
    - Service: src/synth_lab/services/synth_group_service.py
    - Spec: specs/030-custom-synth-groups/spec.md
"""

import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app
from synth_lab.api.routers import synth_groups as synth_groups_router
from synth_lab.services.synth_group_service import SynthGroupService
from synth_lab.repositories.synth_group_repository import SynthGroupRepository
from synth_lab.models.orm.synth import SynthGroup as SynthGroupORM, Synth as SynthORM
from synth_lab.models.orm.experiment import Experiment as ExperimentORM


@pytest.fixture
def initial_group_count(db_session) -> int:
    """Get initial count of synth groups (from seed data)."""
    return db_session.query(SynthGroupORM).count()


@pytest.fixture
def valid_config() -> dict:
    """Return a valid synth group config with all required fields."""
    return {
        "n_synths": 5,
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


@pytest.fixture
def client(db_session):
    """Create test client with shared database session."""
    # Create repository and service with the test session
    repository = SynthGroupRepository(session=db_session)
    service = SynthGroupService(repository=repository)

    # Override service getter (use actual function name from router)
    original_get_service = synth_groups_router.get_synth_group_service
    synth_groups_router.get_synth_group_service = lambda: service

    yield TestClient(app)

    # Restore original
    synth_groups_router.get_synth_group_service = original_get_service


class TestCreateSynthGroupBasic:
    """Integration tests for POST /synth-groups endpoint."""

    def test_create_basic_group_success(self, client, db_session):
        """Create basic synth group without config."""
        response = client.post(
            "/synth-groups",
            json={"name": "API Test Group", "description": "Created via API"},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "API Test Group"
        assert data["description"] == "Created via API"
        assert data["id"].startswith("grp_")
        assert data["synth_count"] == 0

        # Verify in database
        group = db_session.get(SynthGroupORM, data["id"])
        assert group is not None
        assert group.name == "API Test Group"

    def test_create_basic_group_without_description(self, client, db_session):
        """Create basic group with only name."""
        response = client.post("/synth-groups", json={"name": "Minimal Group"})

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "Minimal Group"
        assert data["description"] is None

    def test_create_basic_group_custom_id(self, client, db_session):
        """Create basic group with custom ID."""
        # ID must match pattern: grp_[a-f0-9]{8}
        custom_id = "grp_abc12345"
        response = client.post(
            "/synth-groups",
            json={"name": "Custom ID Group", "id": custom_id},
        )

        assert response.status_code == 201, f"Failed to create group: {response.json()}"
        data = response.json()

        assert data["id"] == custom_id

    def test_create_basic_group_validates_name(self, client):
        """Create fails with empty name."""
        response = client.post("/synth-groups", json={"name": ""})

        assert response.status_code == 422

    def test_create_basic_group_requires_name(self, client):
        """Create fails without name field."""
        response = client.post("/synth-groups", json={"description": "No name"})

        assert response.status_code == 422


class TestCreateSynthGroupWithConfig:
    """Integration tests for POST /synth-groups/with-config endpoint."""

    def test_create_with_config_generates_synths(self, client, db_session):
        """Create with config generates synths."""
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

        response = client.post(
            "/synth-groups/with-config",
            json={
                "name": "Custom Config Group",
                "description": "With distributions",
                "config": config,
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "Custom Config Group"
        assert data["synths_count"] == 10

        # Verify config stored
        group = db_session.get(SynthGroupORM, data["id"])
        assert group.config is not None
        assert group.config["n_synths"] == 10

    def test_create_with_config_validates_n_synths(self, client):
        """Create with config validates n_synths range."""
        config = {"n_synths": 0}

        response = client.post(
            "/synth-groups/with-config",
            json={"name": "Invalid", "config": config},
        )

        assert response.status_code == 422

        config = {"n_synths": 1001}

        response = client.post(
            "/synth-groups/with-config",
            json={"name": "Invalid", "config": config},
        )

        assert response.status_code == 422

    def test_create_with_config_validates_distributions_sum(self, client):
        """Create with config validates distributions sum to ~1.0."""
        config = {
            "n_synths": 5,
            "distributions": {
                "idade": {"15-29": 0.5, "30-44": 0.5, "45-59": 0.5, "60+": 0.5},  # Sum = 2.0
            },
        }

        response = client.post(
            "/synth-groups/with-config",
            json={"name": "Invalid Distributions", "config": config},
        )

        assert response.status_code == 422

    def test_create_with_config_requires_name(self, client):
        """Create with config requires name."""
        config = {"n_synths": 5}

        response = client.post(
            "/synth-groups/with-config",
            json={"config": config},
        )

        assert response.status_code == 422


class TestListSynthGroups:
    """Integration tests for GET /synth-groups/list endpoint."""

    def test_list_returns_seeded_groups(self, client, db_session, initial_group_count):
        """List returns seed data groups."""
        response = client.get("/synth-groups/list")

        assert response.status_code == 200
        data = response.json()

        # Should have at least the seeded groups
        assert data["pagination"]["total"] >= initial_group_count

    def test_list_with_new_groups(self, client, db_session, initial_group_count):
        """List returns seed + newly created groups."""
        # Create groups via API
        for i in range(3):
            client.post("/synth-groups", json={"name": f"Group {i}"})

        response = client.get("/synth-groups/list")

        assert response.status_code == 200
        data = response.json()

        # Should have seed groups + 3 new ones
        assert len(data["data"]) == initial_group_count + 3
        assert data["pagination"]["total"] == initial_group_count + 3

    def test_list_pagination(self, client, db_session, initial_group_count):
        """List respects pagination parameters."""
        # Create 5 groups
        for i in range(5):
            client.post("/synth-groups", json={"name": f"Group {i}"})

        total_expected = initial_group_count + 5

        # Get first 2
        response = client.get("/synth-groups/list?limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == total_expected
        assert data["pagination"]["limit"] == 2
        assert data["pagination"]["offset"] == 0

    def test_list_sorted_by_created_at_desc(self, client, db_session):
        """List returns groups sorted by created_at descending."""
        # Create groups
        client.post("/synth-groups", json={"name": "First"})
        client.post("/synth-groups", json={"name": "Second"})
        client.post("/synth-groups", json={"name": "Third"})

        response = client.get("/synth-groups/list")
        data = response.json()

        # Should be newest first
        assert data["data"][0]["name"] == "Third"
        assert data["data"][1]["name"] == "Second"
        assert data["data"][2]["name"] == "First"

    def test_list_includes_synth_count(self, client, db_session, valid_config):
        """List includes synth count for each group."""
        # Create group with synths
        response = client.post(
            "/synth-groups/with-config",
            json={"name": "Group with Synths", "config": valid_config},
        )
        assert response.status_code == 201, f"Failed to create group: {response.json()}"
        group_id = response.json()["id"]

        # List groups
        response = client.get("/synth-groups/list")
        assert response.status_code == 200
        data = response.json()

        group = next(g for g in data["data"] if g["id"] == group_id)
        assert group["synth_count"] == 5


class TestGetSynthGroupDetail:
    """Integration tests for GET /synth-groups/{group_id} endpoint."""

    def test_get_detail_success(self, client, db_session, valid_config):
        """Get detail returns group with synths list."""
        # Create group with synths (use 3 synths)
        config = {**valid_config, "n_synths": 3}
        create_response = client.post(
            "/synth-groups/with-config",
            json={"name": "Detailed Group", "config": config},
        )
        assert create_response.status_code == 201, f"Failed to create group: {create_response.json()}"
        group_id = create_response.json()["id"]

        # Get detail
        response = client.get(f"/synth-groups/{group_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == group_id
        assert data["name"] == "Detailed Group"
        assert data["synth_count"] == 3
        assert len(data["synths"]) == 3

    def test_get_detail_not_found(self, client):
        """Get detail returns 404 for non-existent group."""
        response = client.get("/synth-groups/grp_nonexist")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_detail_includes_config(self, client, db_session, valid_config):
        """Get detail includes config if present."""
        create_response = client.post(
            "/synth-groups/with-config",
            json={"name": "Config Group", "config": valid_config},
        )
        assert create_response.status_code == 201, f"Failed to create group: {create_response.json()}"
        group_id = create_response.json()["id"]

        response = client.get(f"/synth-groups/{group_id}")
        data = response.json()

        assert data["config"] is not None
        assert data["config"]["n_synths"] == 5


class TestDeleteSynthGroup:
    """Integration tests for DELETE /synth-groups/{group_id} endpoint."""

    def test_delete_success(self, client, db_session):
        """Delete removes group."""
        # Create group
        create_response = client.post(
            "/synth-groups",
            json={"name": "To Delete"},
        )
        assert create_response.status_code == 201, f"Failed to create group: {create_response.json()}"
        group_id = create_response.json()["id"]

        # Delete
        response = client.delete(f"/synth-groups/{group_id}")

        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/synth-groups/{group_id}")
        assert get_response.status_code == 404

    def test_delete_not_found(self, client):
        """Delete returns 404 for non-existent group."""
        response = client.delete("/synth-groups/grp_nonexist")

        assert response.status_code == 404

    def test_delete_preserves_synths(self, client, db_session, valid_config):
        """Delete nullifies synth group_id but keeps synths."""
        from synth_lab.models.orm.synth import Synth as SynthORM

        # Create group with synths
        config = {**valid_config, "n_synths": 3}
        create_response = client.post(
            "/synth-groups/with-config",
            json={"name": "To Delete", "config": config},
        )
        assert create_response.status_code == 201, f"Failed to create group: {create_response.json()}"
        group_id = create_response.json()["id"]

        # Get synth IDs
        detail_response = client.get(f"/synth-groups/{group_id}")
        assert detail_response.status_code == 200
        synth_ids = [s["id"] for s in detail_response.json()["synths"]]

        # Delete group
        client.delete(f"/synth-groups/{group_id}")

        # Refresh session to see changes from API call
        db_session.expire_all()

        # Verify synths still exist but with null group_id
        for synth_id in synth_ids:
            synth = db_session.get(SynthORM, synth_id)
            assert synth is not None
            assert synth.synth_group_id is None


class TestSynthGroupsFullFlow:
    """End-to-end integration tests for synth groups."""

    def test_create_list_detail_delete_flow(self, client, db_session, valid_config):
        """Test complete CRUD flow."""
        # 1. Create group with config
        create_response = client.post(
            "/synth-groups/with-config",
            json={
                "name": "Flow Test Group",
                "description": "Testing full flow",
                "config": valid_config,
            },
        )
        assert create_response.status_code == 201, f"Failed to create group: {create_response.json()}"
        group_id = create_response.json()["id"]

        # 2. List groups - should appear
        list_response = client.get("/synth-groups/list")
        assert list_response.status_code == 200
        groups = list_response.json()["data"]
        assert any(g["id"] == group_id for g in groups)

        # 3. Get detail - should have synths (valid_config has n_synths=5)
        detail_response = client.get(f"/synth-groups/{group_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["synth_count"] == 5  # valid_config default
        assert len(detail["synths"]) == 5

        # 4. Delete group
        delete_response = client.delete(f"/synth-groups/{group_id}")
        assert delete_response.status_code == 204

        # 5. Verify deleted
        get_response = client.get(f"/synth-groups/{group_id}")
        assert get_response.status_code == 404

    def test_create_basic_then_add_synths_separate_group(self, client, db_session, initial_group_count, valid_config):
        """Create basic group, then create separate group with synths."""
        # 1. Create basic group
        basic_response = client.post(
            "/synth-groups",
            json={"name": "Basic Group"},
        )
        assert basic_response.status_code == 201, f"Failed to create basic group: {basic_response.json()}"
        basic_id = basic_response.json()["id"]

        # 2. Create group with synths (3 synths)
        config = {**valid_config, "n_synths": 3}
        config_response = client.post(
            "/synth-groups/with-config",
            json={"name": "Config Group", "config": config},
        )
        assert config_response.status_code == 201, f"Failed to create config group: {config_response.json()}"
        config_id = config_response.json()["id"]

        # 3. Verify both new groups exist (plus any seeded ones)
        list_response = client.get("/synth-groups/list")
        groups = list_response.json()["data"]
        assert len(groups) == initial_group_count + 2

        # 4. Verify correct synth counts
        basic_detail = client.get(f"/synth-groups/{basic_id}").json()
        assert basic_detail["synth_count"] == 0

        config_detail = client.get(f"/synth-groups/{config_id}").json()
        assert config_detail["synth_count"] == 3
