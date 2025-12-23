"""
Unit tests for chat service.

Tests for ChatService that generates synth responses in chat context.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from synth_lab.models.chat import ChatMessageModel, ChatRequest, ChatResponse
from synth_lab.models.synth import Demographics, SynthDetail


class TestChatService:
    """Tests for ChatService."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = MagicMock()
        client.complete.return_value = "Olá! Prazer em conversar com você."
        return client

    @pytest.fixture
    def mock_research_repo(self):
        """Create a mock research repository."""
        repo = MagicMock()
        repo.get_transcript.return_value = MagicMock(
            messages=[
                MagicMock(speaker="Interviewer", text="Como foi sua experiência?"),
                MagicMock(speaker="Interviewee", text="Foi ótima, comprei uma panela."),
            ]
        )
        return repo

    @pytest.fixture
    def mock_synth_detail(self):
        """Create a mock SynthDetail."""
        return SynthDetail(
            id="syn123",
            nome="Stephany",
            arquetipo="Dona de Casa",
            descricao="Uma dona de casa dedicada",
            created_at=datetime.now(),
            demografia=Demographics(idade=56),
        )

    @pytest.fixture
    def mock_synths_repo(self, mock_synth_detail):
        """Create a mock synths repository."""
        repo = MagicMock()
        repo.get_by_id.return_value = mock_synth_detail
        return repo

    def test_generate_response_returns_chat_response(
        self, mock_llm_client, mock_research_repo, mock_synths_repo
    ):
        """Test that generate_response returns a ChatResponse."""
        from synth_lab.services.chat.service import ChatService

        with patch(
            "synth_lab.services.chat.service.get_llm_client",
            return_value=mock_llm_client,
        ), patch(
            "synth_lab.services.chat.service.ResearchRepository",
            return_value=mock_research_repo,
        ), patch(
            "synth_lab.services.chat.service.SynthRepository",
            return_value=mock_synths_repo,
        ):
            service = ChatService()
            request = ChatRequest(
                exec_id="batch_test_123",
                message="Oi, tudo bem?",
                chat_history=[],
            )

            response = service.generate_response("synth_123", request)

            assert isinstance(response, ChatResponse)
            assert response.message == "Olá! Prazer em conversar com você."
            assert isinstance(response.timestamp, datetime)

    def test_generate_response_uses_chat_history(
        self, mock_llm_client, mock_research_repo, mock_synths_repo
    ):
        """Test that chat history is included in context."""
        from synth_lab.services.chat.service import ChatService

        with patch(
            "synth_lab.services.chat.service.get_llm_client",
            return_value=mock_llm_client,
        ), patch(
            "synth_lab.services.chat.service.ResearchRepository",
            return_value=mock_research_repo,
        ), patch(
            "synth_lab.services.chat.service.SynthRepository",
            return_value=mock_synths_repo,
        ):
            service = ChatService()
            request = ChatRequest(
                exec_id="batch_test_123",
                message="E a panela?",
                chat_history=[
                    ChatMessageModel(
                        role="user",
                        content="Oi!",
                        timestamp=datetime.now(),
                    ),
                    ChatMessageModel(
                        role="synth",
                        content="Olá!",
                        timestamp=datetime.now(),
                    ),
                ],
            )

            service.generate_response("synth_123", request)

            # Verify LLM was called with messages that include history
            mock_llm_client.complete.assert_called_once()
            call_args = mock_llm_client.complete.call_args
            messages = call_args.kwargs.get("messages", [])
            # Should have system prompt + 2 history messages + current message
            assert len(messages) >= 4

    def test_generate_response_loads_transcript(
        self, mock_llm_client, mock_research_repo, mock_synths_repo
    ):
        """Test that interview transcript is loaded for context."""
        from synth_lab.services.chat.service import ChatService

        with patch(
            "synth_lab.services.chat.service.get_llm_client",
            return_value=mock_llm_client,
        ), patch(
            "synth_lab.services.chat.service.ResearchRepository",
            return_value=mock_research_repo,
        ), patch(
            "synth_lab.services.chat.service.SynthRepository",
            return_value=mock_synths_repo,
        ):
            service = ChatService()
            request = ChatRequest(
                exec_id="batch_test_123",
                message="Oi!",
                chat_history=[],
            )

            service.generate_response("synth_123", request)

            # Verify transcript was loaded
            mock_research_repo.get_transcript.assert_called_once_with(
                "batch_test_123", "synth_123"
            )

    def test_generate_response_loads_synth_profile(
        self, mock_llm_client, mock_research_repo, mock_synths_repo
    ):
        """Test that synth profile is loaded for persona context."""
        from synth_lab.services.chat.service import ChatService

        with patch(
            "synth_lab.services.chat.service.get_llm_client",
            return_value=mock_llm_client,
        ), patch(
            "synth_lab.services.chat.service.ResearchRepository",
            return_value=mock_research_repo,
        ), patch(
            "synth_lab.services.chat.service.SynthRepository",
            return_value=mock_synths_repo,
        ):
            service = ChatService()
            request = ChatRequest(
                exec_id="batch_test_123",
                message="Oi!",
                chat_history=[],
            )

            service.generate_response("synth_123", request)

            # Verify synth profile was loaded
            mock_synths_repo.get_by_id.assert_called_once_with("synth_123")

    def test_format_transcript_converts_speakers(
        self, mock_llm_client, mock_research_repo, mock_synths_repo
    ):
        """Test that transcript formatting converts speaker labels to Portuguese."""
        from synth_lab.services.chat.service import ChatService

        with patch(
            "synth_lab.services.chat.service.get_llm_client",
            return_value=mock_llm_client,
        ), patch(
            "synth_lab.services.chat.service.ResearchRepository",
            return_value=mock_research_repo,
        ), patch(
            "synth_lab.services.chat.service.SynthRepository",
            return_value=mock_synths_repo,
        ):
            service = ChatService()

            # Create transcript mock
            transcript = MagicMock(
                messages=[
                    MagicMock(speaker="Interviewer", text="Pergunta?"),
                    MagicMock(speaker="Interviewee", text="Resposta."),
                ]
            )

            formatted = service._format_transcript(transcript)

            assert "Entrevistador: Pergunta?" in formatted
            assert "Você: Resposta." in formatted
