"""
Contract tests for Research API endpoints.

Validates that Research API maintains expected schemas for frontend consumption.
Tests verify response structure, required fields, and data types - NOT business logic.

Executar: pytest -m contract tests/contract/test_research_api_contracts.py
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
class TestResearchListContracts:
    """Contract tests for research listing endpoints."""

    def test_list_research_returns_valid_schema(self, client: TestClient):
        """GET /research/list returns valid paginated list schema."""
        response = client.get("/research/list")

        # Accept 200 with or without data
        assert response.status_code == 200, "Endpoint should be available"

        data = response.json()
        assert "data" in data, "Response must have 'data' field"
        assert "pagination" in data, "Response must have 'pagination' field"

        executions = data["data"]
        assert isinstance(executions, list), "data must be a list"

        # Validate pagination structure
        pagination = data["pagination"]
        assert "total" in pagination
        assert "limit" in pagination
        assert "offset" in pagination
        assert isinstance(pagination["total"], int)
        assert isinstance(pagination["limit"], int)
        assert isinstance(pagination["offset"], int)

        # If there are executions, validate first item schema
        if len(executions) > 0:
            execution = executions[0]

            # Required fields for ResearchExecutionSummary
            required_fields = ["id", "experiment_id", "synth_group_id", "status", "started_at", "synth_count"]
            for field in required_fields:
                assert field in execution, f"Execution must have '{field}' field. Frontend breaks without it!"

            # Validate types
            assert isinstance(execution["id"], str), "id must be string"
            assert isinstance(execution["experiment_id"], str), "experiment_id must be string"
            assert isinstance(execution["synth_group_id"], str), "synth_group_id must be string"
            assert isinstance(execution["status"], str), "status must be string"
            assert isinstance(execution["synth_count"], int), "synth_count must be integer"

            # Validate status enum
            valid_statuses = ["pending", "in_progress", "completed", "failed"]
            assert execution["status"] in valid_statuses, f"status must be one of {valid_statuses}"

            # Validate timestamp
            assert validate_timestamp(execution["started_at"]), "started_at must be valid ISO 8601 timestamp"

            # Optional timestamp fields
            if "completed_at" in execution and execution["completed_at"] is not None:
                assert validate_timestamp(execution["completed_at"]), "completed_at must be valid ISO 8601 timestamp"


@pytest.mark.contract
class TestResearchExecutionContracts:
    """Contract tests for research execution detail endpoints."""

    def test_get_research_execution_returns_valid_schema(self, client: TestClient):
        """GET /research/{exec_id} returns valid execution detail schema."""
        # Try with a non-existent ID - accept 404 or 200
        response = client.get("/research/exec_test_001")

        assert response.status_code in [200, 404], "Should return 200 (found) or 404 (not found)"

        if response.status_code == 200:
            execution = response.json()

            # Required fields for ResearchExecutionDetail
            required_fields = [
                "id",
                "experiment_id",
                "synth_group_id",
                "status",
                "started_at",
                "synth_count",
                "completed_count",
                "has_summary",
                "has_prfaq",
            ]
            for field in required_fields:
                assert field in execution, f"Execution detail must have '{field}' field"

            # Validate types
            assert isinstance(execution["id"], str)
            assert isinstance(execution["experiment_id"], str)
            assert isinstance(execution["synth_group_id"], str)
            assert isinstance(execution["status"], str)
            assert isinstance(execution["synth_count"], int)
            assert isinstance(execution["completed_count"], int)
            assert isinstance(execution["has_summary"], bool)
            assert isinstance(execution["has_prfaq"], bool)

            # Validate timestamps
            assert validate_timestamp(execution["started_at"])


@pytest.mark.contract
class TestResearchTranscriptContracts:
    """Contract tests for transcript endpoints."""

    def test_get_transcripts_returns_valid_schema(self, client: TestClient):
        """GET /research/{exec_id}/transcripts returns valid paginated transcript list."""
        # Try with a non-existent ID - accept 404 or 200
        response = client.get("/research/exec_test_001/transcripts")

        assert response.status_code in [200, 404], "Should return 200 (found) or 404 (not found)"

        if response.status_code == 200:
            data = response.json()

            assert "data" in data, "Response must have 'data' field"
            assert "pagination" in data, "Response must have 'pagination' field"

            transcripts = data["data"]
            assert isinstance(transcripts, list), "data must be a list"

            # If there are transcripts, validate first item schema
            if len(transcripts) > 0:
                transcript = transcripts[0]

                # Required fields for TranscriptSummary
                required_fields = ["synth_id", "synth_name", "message_count", "created_at"]
                for field in required_fields:
                    assert field in transcript, f"Transcript summary must have '{field}' field"

                # Validate types
                assert isinstance(transcript["synth_id"], str)
                assert isinstance(transcript["synth_name"], str)
                assert isinstance(transcript["message_count"], int)
                assert validate_timestamp(transcript["created_at"])

    def test_get_transcript_detail_returns_valid_schema(self, client: TestClient):
        """GET /research/{exec_id}/transcripts/{synth_id} returns valid transcript detail schema."""
        # Try with non-existent IDs - accept 404 or 200
        response = client.get("/research/exec_test_001/transcripts/synth_001")

        assert response.status_code in [200, 404], "Should return 200 (found) or 404 (not found)"

        if response.status_code == 200:
            transcript = response.json()

            # Required fields for TranscriptDetail
            required_fields = ["synth_id", "synth_name", "messages", "created_at"]
            for field in required_fields:
                assert field in transcript, f"Transcript detail must have '{field}' field"

            # Validate types
            assert isinstance(transcript["synth_id"], str)
            assert isinstance(transcript["synth_name"], str)
            assert isinstance(transcript["messages"], list), "messages must be a list"
            assert validate_timestamp(transcript["created_at"])

            # If there are messages, validate first message schema
            if len(transcript["messages"]) > 0:
                message = transcript["messages"][0]

                # Required message fields
                message_fields = ["role", "content"]
                for field in message_fields:
                    assert field in message, f"Message must have '{field}' field"

                assert isinstance(message["role"], str)
                assert isinstance(message["content"], str)

                # Validate role enum
                valid_roles = ["user", "assistant", "system"]
                assert message["role"] in valid_roles, f"role must be one of {valid_roles}"


@pytest.mark.contract
class TestResearchDocumentContracts:
    """Contract tests for research document endpoints."""

    def test_get_research_summary_returns_valid_schema(self, client: TestClient):
        """GET /research/{exec_id}/documents/summary returns valid document schema."""
        # Try with non-existent ID - accept 404 or 200
        response = client.get("/research/exec_test_001/documents/summary")

        assert response.status_code in [200, 404], "Should return 200 (found) or 404 (not found)"

        if response.status_code == 200:
            document = response.json()

            # Required fields for DocumentDetailResponse
            required_fields = ["id", "type", "status", "content", "created_at"]
            for field in required_fields:
                assert field in document, f"Document must have '{field}' field"

            # Validate types
            assert isinstance(document["id"], str)
            assert isinstance(document["type"], str)
            assert isinstance(document["status"], str)
            assert validate_timestamp(document["created_at"])

            # Validate type enum
            assert document["type"] == "research_summary", "Document type should be research_summary"

            # Validate status enum
            valid_statuses = ["generating", "completed", "failed"]
            assert document["status"] in valid_statuses, f"status must be one of {valid_statuses}"

            # If completed, content should be present
            if document["status"] == "completed":
                assert document["content"] is not None, "Completed document must have content"
                assert isinstance(document["content"], str), "content must be string"

    def test_get_research_prfaq_returns_valid_schema(self, client: TestClient):
        """GET /research/{exec_id}/documents/prfaq returns valid PRFAQ document schema."""
        # Try with non-existent ID - accept 404 or 200
        response = client.get("/research/exec_test_001/documents/prfaq")

        assert response.status_code in [200, 404], "Should return 200 (found) or 404 (not found)"

        if response.status_code == 200:
            document = response.json()

            # Required fields for DocumentDetailResponse
            required_fields = ["id", "type", "status", "content", "created_at"]
            for field in required_fields:
                assert field in document, f"PRFAQ document must have '{field}' field"

            # Validate type
            assert document["type"] == "research_prfaq", "Document type should be research_prfaq"

            # Validate status
            valid_statuses = ["generating", "completed", "failed"]
            assert document["status"] in valid_statuses

    def test_get_interview_guide_returns_valid_schema(self, client: TestClient):
        """GET /research/{exec_id}/documents/interview-guide returns valid interview guide schema."""
        # Try with non-existent ID - accept 404 or 200
        response = client.get("/research/exec_test_001/documents/interview-guide")

        assert response.status_code in [200, 404], "Should return 200 (found) or 404 (not found)"

        if response.status_code == 200:
            document = response.json()

            # Required fields
            required_fields = ["id", "type", "status", "content", "created_at"]
            for field in required_fields:
                assert field in document, f"Interview guide must have '{field}' field"

            # Validate type
            assert document["type"] == "research_interview_guide", "Document type should be research_interview_guide"


@pytest.mark.contract
class TestResearchExecuteContracts:
    """Contract tests for research execution endpoints."""

    def test_execute_research_accepts_valid_request(self, client: TestClient):
        """POST /research/execute accepts valid research execution request."""
        # This test validates the endpoint accepts the request format
        # We don't actually execute (would need real data), just check 400/422 vs 500
        request_data = {
            "experiment_id": "exp_test_001",
            "synth_group_id": "group_test_001",
        }

        response = client.post("/research/execute", json=request_data)

        # Accept 422 (validation error), 404 (not found), 409 (conflict), but NOT 500
        assert response.status_code in [
            201,
            404,
            409,
            422,
        ], f"Should return 201/404/409/422, not 500. Got {response.status_code}"

        # If successful, validate response schema
        if response.status_code == 201:
            data = response.json()

            required_fields = ["execution_id", "status"]
            for field in required_fields:
                assert field in data, f"Execute response must have '{field}' field"

            assert isinstance(data["execution_id"], str)
            assert isinstance(data["status"], str)
