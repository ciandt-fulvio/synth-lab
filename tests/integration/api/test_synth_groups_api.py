"""
T022 [TEST] [BDD] Integration tests for Synth Groups API.

Tests for synth groups management endpoints.

References:
    - Spec: specs/018-experiment-hub/spec.md
    - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app
from synth_lab.infrastructure.database import DatabaseManager, init_database


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with schema."""
    db_path = tmp_path / "test.db"
    init_database(db_path)
    db = DatabaseManager(db_path)
    yield db
    db.close()


@pytest.fixture
def client(test_db, monkeypatch):
    """Create test client with test database."""
    import synth_lab.infrastructure.database as db_module

    # Reset global database instance to None
    monkeypatch.setattr(db_module, "_db", None)

    # Create a patched get_database that always returns test_db
    def get_test_database(db_path=None):
        return test_db

    monkeypatch.setattr(db_module, "get_database", get_test_database)

    # Also patch in repositories that import get_database directly
    import synth_lab.repositories.base as base_repo
    monkeypatch.setattr(base_repo, "get_database", get_test_database)

    return TestClient(app)


class TestCreateSynthGroup:
    """Tests for POST /synth-groups."""

    def test_create_synth_group_with_valid_data(self, client) -> None:
        """Verify synth group can be created with valid data."""
        response = client.post(
            "/synth-groups",
            json={
                "name": "Geração Dezembro 2025",
                "description": "Synths para testes de checkout",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"].startswith("grp_")
        assert data["name"] == "Geração Dezembro 2025"
        assert data["description"] == "Synths para testes de checkout"

    def test_create_synth_group_with_custom_id(self, client) -> None:
        """Verify synth group can be created with custom ID."""
        response = client.post(
            "/synth-groups",
            json={
                "id": "grp_12345678",
                "name": "Custom ID Group",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "grp_12345678"

    def test_create_synth_group_without_name_returns_422(self, client) -> None:
        """Verify name is required."""
        response = client.post(
            "/synth-groups",
            json={
                "description": "Test description",
            },
        )

        assert response.status_code == 422

    def test_create_synth_group_with_empty_name_returns_422(self, client) -> None:
        """Verify empty name is rejected."""
        response = client.post(
            "/synth-groups",
            json={
                "name": "",
            },
        )

        assert response.status_code == 422


class TestListSynthGroups:
    """Tests for GET /synth-groups/list."""

    def test_list_synth_groups_with_synth_count(self, client, test_db) -> None:
        """Verify groups are listed with synth counts."""
        # Create group
        response = client.post(
            "/synth-groups",
            json={"name": "Test Group"},
        )
        grp_id = response.json()["id"]

        # Add synths to the group
        for i in range(3):
            test_db.execute(
                """
                INSERT INTO synths (id, synth_group_id, nome, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    f"syn{i:03d}",
                    grp_id,
                    f"Synth {i}",
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        # List groups
        response = client.get("/synth-groups/list")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["synth_count"] == 3

    def test_list_synth_groups_empty_returns_empty_list(self, client) -> None:
        """Verify empty list is returned when no groups exist."""
        response = client.get("/synth-groups/list")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    def test_list_synth_groups_with_pagination(self, client) -> None:
        """Verify pagination parameters work."""
        # Create 5 groups
        for i in range(5):
            client.post(
                "/synth-groups",
                json={"name": f"Group {i}"},
            )

        # Get first page
        response = client.get("/synth-groups/list?limit=3&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3
        assert data["pagination"]["total"] == 5
        assert data["pagination"]["has_next"] is True


class TestGetSynthGroup:
    """Tests for GET /synth-groups/{id}."""

    def test_get_synth_group_by_id(self, client) -> None:
        """Verify group can be retrieved by ID."""
        # Create group
        response = client.post(
            "/synth-groups",
            json={
                "name": "Test Group",
                "description": "Test description",
            },
        )
        grp_id = response.json()["id"]

        # Get group
        response = client.get(f"/synth-groups/{grp_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == grp_id
        assert data["name"] == "Test Group"

    def test_get_synth_group_includes_synths(self, client, test_db) -> None:
        """Verify group detail includes list of synths."""
        # Create group
        response = client.post(
            "/synth-groups",
            json={"name": "Group with Synths"},
        )
        grp_id = response.json()["id"]

        # Add synth
        test_db.execute(
            """
            INSERT INTO synths (id, synth_group_id, nome, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                "syn001",
                grp_id,
                "Test Synth",
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        # Get group detail
        response = client.get(f"/synth-groups/{grp_id}")

        assert response.status_code == 200
        data = response.json()
        assert "synths" in data
        assert len(data["synths"]) == 1
        assert data["synths"][0]["nome"] == "Test Synth"

    def test_get_synth_group_not_found_returns_404(self, client) -> None:
        """Verify 404 for non-existent group."""
        response = client.get("/synth-groups/grp_nonexist")

        assert response.status_code == 404


class TestDeleteSynthGroup:
    """Tests for DELETE /synth-groups/{id}."""

    def test_delete_synth_group_success(self, client) -> None:
        """Verify group can be deleted."""
        # Create group
        response = client.post(
            "/synth-groups",
            json={"name": "To Delete"},
        )
        grp_id = response.json()["id"]

        # Delete group
        response = client.delete(f"/synth-groups/{grp_id}")

        assert response.status_code == 204

        # Verify deleted
        response = client.get(f"/synth-groups/{grp_id}")
        assert response.status_code == 404

    def test_delete_nonexistent_group_returns_404(self, client) -> None:
        """Verify 404 for non-existent group."""
        response = client.delete("/synth-groups/grp_nonexist")

        assert response.status_code == 404
