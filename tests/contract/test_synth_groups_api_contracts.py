"""
Contract tests - Validates synth groups API contracts expected by frontend.

These tests ensure API changes don't break the frontend by validating:
- Response structure (required fields present)
- Correct data types
- Valid values for enums/constants
- Nested structures maintained

Run: pytest tests/contract/test_synth_groups_api_contracts.py -v

Note: Uses shared 'client' fixture from tests/contract/conftest.py
      which ensures tests run against DATABASE_TEST_URL.
"""

import pytest
from fastapi.testclient import TestClient


def validate_timestamp(value: str) -> bool:
    """Validate that string is ISO 8601 timestamp."""
    from datetime import datetime

    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


@pytest.mark.contract
class TestSynthGroupsListContract:
    """Validates contracts for GET /synth-groups/list endpoint."""

    def test_list_returns_paginated_response(self, client: TestClient):
        """GET /synth-groups/list returns paginated response schema."""
        response = client.get("/synth-groups/list")

        assert response.status_code == 200, "Endpoint must be available"

        data = response.json()
        assert "data" in data, "Response must have 'data' field"
        assert "pagination" in data, "Response must have 'pagination' field"
        assert isinstance(data["data"], list), "'data' must be a list"

    def test_list_pagination_schema(self, client: TestClient):
        """GET /synth-groups/list pagination matches frontend expectations."""
        response = client.get("/synth-groups/list")

        assert response.status_code == 200
        pagination = response.json()["pagination"]

        required_fields = ["total", "limit", "offset"]
        for field in required_fields:
            assert field in pagination, f"pagination.{field} expected by frontend"
            assert isinstance(pagination[field], int), f"pagination.{field} must be int"

    def test_list_group_summary_schema(self, client: TestClient):
        """Each group in list has required SynthGroupSummary fields."""
        response = client.get("/synth-groups/list")

        assert response.status_code == 200
        groups = response.json()["data"]

        if len(groups) > 0:
            group = groups[0]

            # Required fields for SynthGroupSummary
            required_fields = ["id", "name", "synth_count", "created_at"]
            for field in required_fields:
                assert field in group, f"Group must have '{field}'. Frontend expects it!"

            # Type validations
            assert isinstance(group["id"], str), "id must be string"
            assert isinstance(group["name"], str), "name must be string"
            assert isinstance(group["synth_count"], int), "synth_count must be int"
            assert validate_timestamp(group["created_at"]), "created_at must be ISO 8601"

            # Optional fields
            if "description" in group:
                assert group["description"] is None or isinstance(
                    group["description"], str
                ), "description must be string or null"

            if "config" in group:
                assert group["config"] is None or isinstance(
                    group["config"], dict
                ), "config must be dict or null"

    def test_list_accepts_pagination_params(self, client: TestClient):
        """GET /synth-groups/list accepts limit and offset parameters."""
        response = client.get("/synth-groups/list?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["limit"] == 10
        assert data["pagination"]["offset"] == 0


@pytest.mark.contract
class TestSynthGroupDetailContract:
    """Validates contracts for GET /synth-groups/{group_id} endpoint."""

    def test_detail_returns_404_for_nonexistent(self, client: TestClient):
        """GET /synth-groups/{id} returns 404 for non-existent group."""
        response = client.get("/synth-groups/grp_nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data, "404 response must have 'detail' field"

    def test_detail_schema_with_synths(self, client: TestClient):
        """GET /synth-groups/{id} returns full detail schema."""
        # First get a valid group ID
        list_response = client.get("/synth-groups/list")
        groups = list_response.json()["data"]

        if len(groups) == 0:
            pytest.skip("No groups available for testing")

        group_id = groups[0]["id"]
        response = client.get(f"/synth-groups/{group_id}")

        assert response.status_code == 200
        detail = response.json()

        # Required fields for SynthGroupDetailResponse
        required_fields = ["id", "name", "synth_count", "created_at", "synths"]
        for field in required_fields:
            assert field in detail, f"Detail must have '{field}'. Frontend expects it!"

        # Type validations
        assert isinstance(detail["id"], str)
        assert isinstance(detail["name"], str)
        assert isinstance(detail["synth_count"], int)
        assert isinstance(detail["synths"], list)
        assert validate_timestamp(detail["created_at"])

        # Config field (added for custom groups)
        if "config" in detail:
            assert detail["config"] is None or isinstance(detail["config"], dict)

    def test_detail_synth_summary_schema(self, client: TestClient):
        """Synths in detail response have correct schema."""
        list_response = client.get("/synth-groups/list")
        groups = list_response.json()["data"]

        if len(groups) == 0:
            pytest.skip("No groups available for testing")

        group_id = groups[0]["id"]
        response = client.get(f"/synth-groups/{group_id}")
        synths = response.json()["synths"]

        if len(synths) > 0:
            synth = synths[0]

            required_fields = ["id", "nome", "created_at"]
            for field in required_fields:
                assert field in synth, f"Synth must have '{field}'"

            assert isinstance(synth["id"], str)
            assert isinstance(synth["nome"], str)


@pytest.mark.contract
class TestSynthGroupCreateContract:
    """Validates contracts for POST /synth-groups endpoints."""

    def test_create_basic_returns_group_response(self, client: TestClient):
        """POST /synth-groups returns created group schema."""
        response = client.post(
            "/synth-groups",
            json={"name": "Contract Test Group", "description": "Test description"},
        )

        assert response.status_code == 201, "Create should return 201"
        data = response.json()

        required_fields = ["id", "name", "synth_count", "created_at"]
        for field in required_fields:
            assert field in data, f"Response must have '{field}'"

        assert data["name"] == "Contract Test Group"
        assert isinstance(data["id"], str)
        assert data["id"].startswith("grp_")

    def test_create_with_config_returns_response(self, client: TestClient):
        """POST /synth-groups/with-config returns created group with synth count."""
        config = {
            "n_synths": 5,  # Small number for test
            "distributions": {
                "idade": {"15-29": 0.25, "30-44": 0.25, "45-59": 0.25, "60+": 0.25},
                "escolaridade": {
                    "sem_instrucao": 0.1,
                    "fundamental": 0.3,
                    "medio": 0.3,
                    "superior": 0.3,
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
                "name": "Test Custom Group",
                "description": "Test with config",
                "config": config,
            },
        )

        assert response.status_code == 201, f"Create should return 201, got {response.status_code}"
        data = response.json()

        required_fields = ["id", "name", "created_at", "synths_count"]
        for field in required_fields:
            assert field in data, f"Response must have '{field}'"

        assert data["synths_count"] == 5, "Should have created 5 synths"
        assert data["name"] == "Test Custom Group"

    def test_create_with_config_validates_distributions(self, client: TestClient):
        """POST /synth-groups/with-config returns 422 for invalid distributions."""
        # Distributions don't sum to 1.0
        config = {
            "n_synths": 5,
            "distributions": {
                "idade": {"15-29": 0.5, "30-44": 0.5, "45-59": 0.5, "60+": 0.5},  # Sum = 2.0
                "escolaridade": {
                    "sem_instrucao": 0.25,
                    "fundamental": 0.25,
                    "medio": 0.25,
                    "superior": 0.25,
                },
                "deficiencias": {"taxa_com_deficiencia": 0.1},
                "composicao_familiar": {"unipessoal": 1.0},
                "domain_expertise": {"alpha": 3, "beta": 3},
            },
        }

        response = client.post(
            "/synth-groups/with-config",
            json={
                "name": "Invalid Group",
                "config": config,
            },
        )

        assert response.status_code == 422, "Should return 422 for invalid distributions"

    def test_create_requires_name(self, client: TestClient):
        """POST /synth-groups requires name field."""
        response = client.post("/synth-groups", json={"description": "No name"})

        assert response.status_code == 422, "Should return 422 when name is missing"


@pytest.mark.contract
class TestSynthGroupDeleteContract:
    """Validates contracts for DELETE /synth-groups/{group_id} endpoint."""

    def test_delete_returns_204(self, client: TestClient):
        """DELETE /synth-groups/{id} returns 204 on success."""
        # First create a group
        create_response = client.post(
            "/synth-groups",
            json={"name": "Group to Delete", "description": "Will be deleted"},
        )
        group_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/synth-groups/{group_id}")

        assert response.status_code == 204, "Delete should return 204"

    def test_delete_returns_404_for_nonexistent(self, client: TestClient):
        """DELETE /synth-groups/{id} returns 404 for non-existent group."""
        response = client.delete("/synth-groups/grp_nonexist")

        assert response.status_code == 404
