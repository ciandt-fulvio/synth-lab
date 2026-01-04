"""
Contract tests for Exploration API endpoints.

Validates that Exploration API maintains expected schemas for frontend consumption.
Tests verify response structure, required fields, and data types - NOT business logic.

Executar: pytest -m contract tests/contract/test_exploration_api_contracts.py
"""

import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


def validate_timestamp(value: str) -> bool:
    """Validate ISO 8601 timestamp string."""
    from datetime import datetime

    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


@pytest.mark.contract
class TestExplorationCreateContracts:
    """Contract tests for exploration creation endpoints."""

    def test_create_exploration_accepts_valid_request(self, client: TestClient):
        """POST /explorations accepts valid exploration creation request."""
        # This test validates the endpoint accepts the request format
        # We don't actually create (would need real data), just check 400/422 vs 500
        request_data = {
            "experiment_id": "exp_test_001",
            "goal_value": 0.8,
            "beam_width": 3,
            "max_depth": 5,
        }

        response = client.post("/explorations", json=request_data)

        # Accept 201 (created), 404 (not found), 422 (validation), but NOT 500
        assert response.status_code in [
            201,
            404,
            422,
        ], f"Should return 201/404/422, not 500. Got {response.status_code}"

        # If successful, validate response schema
        if response.status_code == 201:
            exploration = response.json()

            required_fields = ["id", "experiment_id", "status", "goal_value", "created_at"]
            for field in required_fields:
                assert field in exploration, f"Exploration must have '{field}' field"

            assert isinstance(exploration["id"], str)
            assert isinstance(exploration["experiment_id"], str)
            assert isinstance(exploration["status"], str)
            assert isinstance(exploration["goal_value"], (int, float))
            assert validate_timestamp(exploration["created_at"])

            # Validate status enum
            valid_statuses = ["pending", "running", "completed", "failed", "terminated"]
            assert exploration["status"] in valid_statuses


@pytest.mark.contract
class TestExplorationDetailContracts:
    """Contract tests for exploration detail endpoints."""

    def test_get_exploration_returns_valid_schema(self, client: TestClient):
        """GET /explorations/{exploration_id} returns valid exploration detail schema."""
        # Try with non-existent ID - accept 404 or 200
        response = client.get("/explorations/expl_test_001")

        assert response.status_code in [200, 404], "Should return 200 (found) or 404 (not found)"

        if response.status_code == 200:
            exploration = response.json()

            # Required fields for ExplorationResponse
            required_fields = [
                "id",
                "experiment_id",
                "status",
                "goal_value",
                "current_depth",
                "nodes_explored",
                "created_at",
            ]
            for field in required_fields:
                assert field in exploration, f"Exploration must have '{field}' field"

            # Validate types
            assert isinstance(exploration["id"], str)
            assert isinstance(exploration["experiment_id"], str)
            assert isinstance(exploration["status"], str)
            assert isinstance(exploration["goal_value"], (int, float))
            assert isinstance(exploration["current_depth"], int)
            assert isinstance(exploration["nodes_explored"], int)
            assert validate_timestamp(exploration["created_at"])

            # Validate status
            valid_statuses = ["pending", "running", "completed", "failed", "terminated"]
            assert exploration["status"] in valid_statuses

    def test_run_exploration_accepts_request(self, client: TestClient):
        """POST /explorations/{exploration_id}/run accepts run request."""
        # Try with non-existent ID - accept 404, 422, or 202
        response = client.post("/explorations/expl_test_001/run")

        # Accept 200/202 (started), 404 (not found), 422 (invalid state)
        assert response.status_code in [200, 202, 404, 422], f"Should not return 500. Got {response.status_code}"


@pytest.mark.contract
class TestExplorationTreeContracts:
    """Contract tests for exploration tree endpoints."""

    def test_get_exploration_tree_returns_valid_schema(self, client: TestClient):
        """GET /explorations/{exploration_id}/tree returns valid tree schema."""
        # Try with non-existent ID - accept 404 or 200
        response = client.get("/explorations/expl_test_001/tree")

        assert response.status_code in [200, 404], "Should return 200 (found) or 404 (not found)"

        if response.status_code == 200:
            tree = response.json()

            # Required fields for ExplorationTreeResponse
            required_fields = ["nodes", "edges"]
            for field in required_fields:
                assert field in tree, f"Tree must have '{field}' field"

            # Validate types
            assert isinstance(tree["nodes"], list), "nodes must be a list"
            assert isinstance(tree["edges"], list), "edges must be a list"

            # If there are nodes, validate first node schema
            if len(tree["nodes"]) > 0:
                node = tree["nodes"][0]

                node_fields = ["id", "depth", "value", "is_terminal"]
                for field in node_fields:
                    assert field in node, f"Node must have '{field}' field"

                assert isinstance(node["id"], str)
                assert isinstance(node["depth"], int)
                assert isinstance(node["is_terminal"], bool)

            # If there are edges, validate first edge schema
            if len(tree["edges"]) > 0:
                edge = tree["edges"][0]

                edge_fields = ["from_node_id", "to_node_id", "action"]
                for field in edge_fields:
                    assert field in edge, f"Edge must have '{field}' field"

                assert isinstance(edge["from_node_id"], str)
                assert isinstance(edge["to_node_id"], str)

    def test_get_winning_path_returns_valid_schema(self, client: TestClient):
        """GET /explorations/{exploration_id}/winning-path returns valid path schema."""
        # Try with non-existent ID - accept 404 or 200
        response = client.get("/explorations/expl_test_001/winning-path")

        assert response.status_code in [200, 404], "Should return 200 (found) or 404 (not found)"

        if response.status_code == 200:
            path = response.json()

            # Can be null if no winning path yet
            if path is not None:
                # Required fields for WinningPathResponse
                required_fields = ["nodes", "actions", "final_value"]
                for field in required_fields:
                    assert field in path, f"Winning path must have '{field}' field"

                assert isinstance(path["nodes"], list)
                assert isinstance(path["actions"], list)
                assert isinstance(path["final_value"], (int, float))


@pytest.mark.contract
class TestExplorationDocumentContracts:
    """Contract tests for exploration document endpoints."""

    def test_get_exploration_summary_returns_valid_schema(self, client: TestClient):
        """GET /explorations/{exploration_id}/documents/summary returns valid document schema."""
        # Try with non-existent ID - accept 404 or 200
        response = client.get("/explorations/expl_test_001/documents/summary")

        assert response.status_code in [200, 404], "Should return 200 (found) or 404 (not found)"

        if response.status_code == 200:
            document = response.json()

            # Required fields for DocumentDetailResponse
            required_fields = ["id", "type", "status", "content", "created_at"]
            for field in required_fields:
                assert field in document, f"Document must have '{field}' field"

            # Validate type
            assert document["type"] == "exploration_summary", "Document type should be exploration_summary"

            # Validate status
            valid_statuses = ["generating", "completed", "failed"]
            assert document["status"] in valid_statuses

    def test_get_exploration_prfaq_returns_valid_schema(self, client: TestClient):
        """GET /explorations/{exploration_id}/documents/prfaq returns valid PRFAQ document schema."""
        # Try with non-existent ID - accept 404 or 200
        response = client.get("/explorations/expl_test_001/documents/prfaq")

        assert response.status_code in [200, 404], "Should return 200 (found) or 404 (not found)"

        if response.status_code == 200:
            document = response.json()

            # Required fields
            required_fields = ["id", "type", "status", "content", "created_at"]
            for field in required_fields:
                assert field in document, f"PRFAQ document must have '{field}' field"

            # Validate type
            assert document["type"] == "exploration_prfaq", "Document type should be exploration_prfaq"


@pytest.mark.contract
class TestActionCatalogContracts:
    """Contract tests for action catalog endpoints."""

    def test_get_action_catalog_returns_valid_schema(self, client: TestClient):
        """GET /explorations/catalog/actions returns valid action catalog schema."""
        response = client.get("/explorations/catalog/actions")

        # This endpoint should always return 200 (catalog is static)
        assert response.status_code == 200, "Action catalog endpoint should always be available"

        catalog = response.json()

        # Required fields for ActionCatalogResponse
        assert "actions" in catalog, "Catalog must have 'actions' field"
        assert isinstance(catalog["actions"], list), "actions must be a list"

        # If there are actions, validate first action schema
        if len(catalog["actions"]) > 0:
            action = catalog["actions"][0]

            action_fields = ["id", "name", "description", "category"]
            for field in action_fields:
                assert field in action, f"Action must have '{field}' field"

            assert isinstance(action["id"], str)
            assert isinstance(action["name"], str)
            assert isinstance(action["description"], str)
            assert isinstance(action["category"], str)
