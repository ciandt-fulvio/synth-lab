"""
Integration tests for chat API endpoint.

Tests the full chat flow from API request to response.

References:
    - Chat Router: src/synth_lab/api/routers/chat.py
    - Chat Service: src/synth_lab/services/chat/service.py
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app
from synth_lab.models.synth import Demographics, SynthDetail


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_synth_detail():
    """Create a mock SynthDetail."""
    return SynthDetail(
        id="syn123",
        nome="Maria",
        arquetipo="Profissional",
        descricao="Uma profissional dedicada",
        created_at=datetime.now(),
        demografia=Demographics(idade=35),
    )


@pytest.fixture
def mock_transcript():
    """Create a mock transcript."""
    return MagicMock(
        messages=[
            MagicMock(speaker="Interviewer", text="Como foi sua experiência?"),
            MagicMock(speaker="Interviewee", text="Foi muito boa!"),
        ]
    )


class TestChatAPI:
    """Integration tests for chat API."""

    def test_chat_endpoint_returns_response(self, client, mock_synth_detail, mock_transcript):
        """Test that POST /synths/{id}/chat returns a valid response."""
        with (
            patch("synth_lab.services.chat.service.get_llm_client") as mock_llm,
            patch("synth_lab.services.chat.service.ResearchRepository") as mock_research_repo,
            patch("synth_lab.services.chat.service.SynthRepository") as mock_synths_repo,
        ):
            # Setup mocks
            mock_llm.return_value.complete.return_value = "Olá! Como posso ajudar?"
            mock_research_repo.return_value.get_transcript.return_value = mock_transcript
            mock_synths_repo.return_value.get_by_id.return_value = mock_synth_detail

            response = client.post(
                "/synths/syn123/chat",
                json={
                    "exec_id": "batch_123",
                    "message": "Oi, tudo bem?",
                    "chat_history": [],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "timestamp" in data
            assert data["message"] == "Olá! Como posso ajudar?"

    def test_chat_endpoint_with_history(self, client, mock_synth_detail, mock_transcript):
        """Test that chat history is included in the request."""
        with (
            patch("synth_lab.services.chat.service.get_llm_client") as mock_llm,
            patch("synth_lab.services.chat.service.ResearchRepository") as mock_research_repo,
            patch("synth_lab.services.chat.service.SynthRepository") as mock_synths_repo,
        ):
            # Setup mocks
            mock_llm.return_value.complete.return_value = "Sim, a panela era ótima!"
            mock_research_repo.return_value.get_transcript.return_value = mock_transcript
            mock_synths_repo.return_value.get_by_id.return_value = mock_synth_detail

            response = client.post(
                "/synths/syn123/chat",
                json={
                    "exec_id": "batch_123",
                    "message": "Você gostou da panela?",
                    "chat_history": [
                        {
                            "role": "user",
                            "content": "Oi!",
                            "timestamp": "2024-01-01T10:00:00",
                        },
                        {
                            "role": "synth",
                            "content": "Olá!",
                            "timestamp": "2024-01-01T10:00:01",
                        },
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Sim, a panela era ótima!"

    def test_chat_endpoint_synth_not_found(self, client):
        """Test that 404 is returned when synth is not found."""
        from synth_lab.repositories.synth_repository import SynthNotFoundError

        with (
            patch("synth_lab.services.chat.service.get_llm_client"),
            patch("synth_lab.services.chat.service.ResearchRepository"),
            patch("synth_lab.services.chat.service.SynthRepository") as mock_synths_repo,
        ):
            mock_synths_repo.return_value.get_by_id.side_effect = SynthNotFoundError("xyz999")

            response = client.post(
                "/synths/xyz999/chat",
                json={
                    "exec_id": "batch_123",
                    "message": "Oi!",
                    "chat_history": [],
                },
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_chat_endpoint_validation_error(self, client):
        """Test that 422 is returned for invalid request."""
        response = client.post(
            "/synths/syn123/chat",
            json={
                "exec_id": "batch_123",
                # Missing required "message" field
                "chat_history": [],
            },
        )

        assert response.status_code == 422

    def test_chat_endpoint_empty_message_rejected(self, client):
        """Test that empty message is rejected."""
        response = client.post(
            "/synths/syn123/chat",
            json={
                "exec_id": "batch_123",
                "message": "",  # Empty message
                "chat_history": [],
            },
        )

        assert response.status_code == 422
