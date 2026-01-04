"""
Integration tests for AI-related services.

Tests the full flow: Service → Repository → Database → LLM Client
Uses real database (isolated_db_session) and mocks only external LLM/Image API calls.

Executar: pytest -m integration tests/integration/services/test_ai_services.py
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
from pathlib import Path

from synth_lab.services.avatar_service import AvatarService
from synth_lab.services.interview_guide_generator_service import (
    InterviewGuideGeneratorService,
)
from synth_lab.services.chat.service import ChatService
from synth_lab.models.orm.experiment import Experiment
from synth_lab.models.orm.synth import Synth, SynthGroup
from synth_lab.models.orm.research import ResearchExecution, Transcript
from synth_lab.models.chat import ChatRequest


@pytest.mark.integration
class TestAvatarServiceIntegration:
    """Integration tests for avatar_service.py - Avatar generation."""

    @pytest.mark.asyncio
    async def test_ensure_avatars_detects_missing_avatars(
        self, isolated_db_session, tmp_path
    ):
        """Test that ensure_avatars identifies synths without avatar files."""
        # Setup: Create synths in database
        experiment = Experiment(
            id="exp_avatar_001",
            name="Avatar Test",
            hypothesis="Testing avatar generation",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        group = SynthGroup(
            id="group_avatar_001",
            name="Avatar Group",
            
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add_all([experiment, group])

        synths_data = []
        for i in range(3):
            synth = Synth(
                id=f"av{i:04d}",  # Max 6 chars
                nome=f"Test Synth {i}",
                data={
                    "id": f"av{i:04d}",
                    "nome": f"Test Synth {i}",
                    "version": "2.3.0",
                },
                version="2.3.0",
                created_at=datetime.now().isoformat(),
            )
            isolated_db_session.add(synth)
            synths_data.append({"id": f"av{i:04d}", "nome": f"Test Synth {i}"})
        isolated_db_session.commit()

        # Execute: Check which synths need avatars
        avatars_dir = tmp_path / "avatars"
        service = AvatarService(avatars_dir=avatars_dir)

        # Mock avatar generation to avoid OpenAI API call
        with patch(
            "synth_lab.gen_synth.avatar_generator.generate_avatars"
        ) as mock_generate:
            # Mock the avatar generation to create dummy files
            def mock_avatar_gen(synths=None, **kwargs):
                result_paths = []
                for synth in synths or []:
                    avatar_file = avatars_dir / f"{synth['id']}.png"
                    avatar_file.parent.mkdir(parents=True, exist_ok=True)
                    avatar_file.write_text("dummy avatar")
                    result_paths.append(str(avatar_file))
                return result_paths

            mock_generate.side_effect = mock_avatar_gen

            # Execute
            result = await service.ensure_avatars_for_synths(synths_data)

            # Verify: All 3 synths should have avatars generated
            assert len(result) == 3
            for synth_data in synths_data:
                assert synth_data["id"] in result
                assert result[synth_data["id"]].exists()

    @pytest.mark.asyncio
    async def test_ensure_avatars_skips_existing_avatars(
        self, isolated_db_session, tmp_path
    ):
        """Test that ensure_avatars does not regenerate existing avatar files."""
        # Setup: Create synths and one existing avatar
        synths_data = [
            {"id": "synth_existing_001", "nome": "Existing Avatar"},
            {"id": "synth_new_001", "nome": "New Avatar"},
        ]

        avatars_dir = tmp_path / "avatars"
        avatars_dir.mkdir(parents=True, exist_ok=True)

        # Create existing avatar file
        existing_avatar = avatars_dir / "synth_existing_001.png"
        existing_avatar.write_text("existing avatar")

        service = AvatarService(avatars_dir=avatars_dir)

        # Mock avatar generation
        with patch(
            "synth_lab.gen_synth.avatar_generator.generate_avatars"
        ) as mock_generate:

            def mock_avatar_gen(synths=None, **kwargs):
                result_paths = []
                for synth in synths or []:
                    avatar_file = avatars_dir / f"{synth['id']}.png"
                    avatar_file.write_text("new avatar")
                    result_paths.append(str(avatar_file))
                return result_paths

            mock_generate.side_effect = mock_avatar_gen

            # Execute
            result = await service.ensure_avatars_for_synths(synths_data)

            # Verify: Only new synth should be in result
            assert len(result) == 1
            assert "synth_new_001" in result
            assert "synth_existing_001" not in result

            # Verify existing avatar was not overwritten
            assert existing_avatar.read_text() == "existing avatar"

    @pytest.mark.asyncio
    async def test_ensure_avatars_calls_callbacks(self, tmp_path):
        """Test that ensure_avatars calls generation start/complete callbacks."""
        synths_data = [{"id": "synth_callback_001", "nome": "Callback Test"}]

        avatars_dir = tmp_path / "avatars"
        service = AvatarService(avatars_dir=avatars_dir)

        # Create mock callbacks
        start_callback = AsyncMock()
        complete_callback = AsyncMock()

        # Mock avatar generation
        with patch("synth_lab.gen_synth.avatar_generator.generate_avatars") as mock_gen:
            # Mock should return list of paths
            mock_gen.return_value = [str(avatars_dir / "synth_callback_001.png")]

            await service.ensure_avatars_for_synths(
                synths_data,
                on_generation_start=start_callback,
                on_generation_complete=complete_callback,
            )

            # Verify callbacks were called
            start_callback.assert_called_once_with(1)  # 1 synth to generate
            complete_callback.assert_called_once_with(1)


@pytest.mark.integration
class TestInterviewGuideGeneratorIntegration:
    """Integration tests for interview_guide_generator_service.py - Guide generation."""

    @pytest.mark.asyncio
    @patch("synth_lab.services.interview_guide_generator_service._tracer")
    async def test_generate_for_experiment_creates_guide(
        self, mock_tracer, isolated_db_session
    ):
        """Test that generate_for_experiment creates InterviewGuide in database."""
        # Setup mock tracer
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = (
            mock_span
        )

        # Setup: Create experiment
        experiment = Experiment(
            id="exp_guide_001",
            name="Guide Test Experiment",
            hypothesis="Testing guide generation",
            description="This is a test experiment for interview guide generation",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add(experiment)
        isolated_db_session.commit()

        # Mock LLM response
        mock_llm_response = {
            "questions": "1. Como você avalia a experiência?\n2. O que poderia melhorar?",
            "context_definition": "Contexto sobre o experimento de teste",
            "context_examples": "Exemplo 1: ...\nExemplo 2: ...",
        }

        from synth_lab.repositories.interview_guide_repository import InterviewGuideRepository
        repo = InterviewGuideRepository(session=isolated_db_session)
        service = InterviewGuideGeneratorService(interview_guide_repo=repo)

        # Mock the LLM client's complete_json method
        with patch.object(
            service.llm, "complete_json"
        ) as mock_llm:
            # Configure mock to return JSON string
            import json
            mock_llm.return_value = json.dumps(mock_llm_response)

            # Execute: Generate guide
            guide = await service.generate_for_experiment(
                experiment_id="exp_guide_001",
                name="Guide Test Experiment",
                hypothesis="Testing guide generation",
                description="This is a test experiment",
            )

            # Verify: Guide created
            assert guide.experiment_id == "exp_guide_001"
            assert guide.questions is not None
            assert guide.context_definition is not None

            # Verify LLM was called
            mock_llm.assert_called_once()

    @pytest.mark.asyncio
    @patch("synth_lab.services.interview_guide_generator_service._tracer")
    async def test_generate_for_experiment_uses_phoenix_tracing(
        self, mock_tracer, isolated_db_session
    ):
        """Test that generate_for_experiment creates Phoenix trace spans."""
        # Setup mock tracer
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = (
            mock_span
        )

        # Setup experiment
        experiment = Experiment(
            id="exp_tracing_001",
            name="Tracing Test",
            hypothesis="Testing Phoenix tracing",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add(experiment)
        isolated_db_session.commit()

        from synth_lab.repositories.interview_guide_repository import InterviewGuideRepository
        repo = InterviewGuideRepository(session=isolated_db_session)
        service = InterviewGuideGeneratorService(interview_guide_repo=repo)

        # Mock LLM response
        with patch.object(
            service.llm, "complete_json"
        ) as mock_llm:
            import json
            mock_llm.return_value = json.dumps({
                "questions": "Q1",
                "context_definition": "C1",
                "context_examples": "E1"
            })

            await service.generate_for_experiment(
                experiment_id="exp_tracing_001",
                name="Tracing Test",
                hypothesis="Testing Phoenix tracing",
            )

            # Verify: Tracer was called
            mock_tracer.start_as_current_span.assert_called()


@pytest.mark.integration
class TestChatServiceIntegration:
    """Integration tests for chat/service.py - Chat conversation."""

    @patch("synth_lab.services.chat.service._tracer")
    def test_generate_response_retrieves_synth_and_transcript(
        self, mock_tracer, isolated_db_session
    ):
        """Test that generate_response loads synth profile and interview transcript."""
        # Setup mock tracer
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = (
            mock_span
        )

        # Setup: Create experiment, synth group, synth, research execution, and transcript
        experiment = Experiment(
            id="exp_chat_001",
            name="Chat Test",
            hypothesis="Testing chat service",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        group = SynthGroup(
            id="group_chat_001",
            name="Chat Group",
            
            created_at=datetime.now().isoformat(),
        )
        synth = Synth(
            id="chat01",
            nome="João Silva",
            data={
                "id": "chat01",
                "nome": "João Silva",
                "version": "2.3.0",
                "demografia": {
                    "idade": 30,
                    "genero_biologico": "masculino",
                    "localizacao": {"cidade": "São Paulo", "estado": "SP"},
                },
                "psicografia": {
                    "interesses": ["tecnologia", "inovação"],
                    "contrato_cognitivo": {
                        "tipo": "analítico",
                        "perfil_cognitivo": "lógico",
                        "regras": ["Pensar antes de agir"],
                        "efeito_esperado": "Decisões racionais",
                    },
                },
            },
            version="2.3.0",
            created_at=datetime.now().isoformat(),
        )
        execution = ResearchExecution(
            exec_id="exec_chat_001",
            experiment_id="exp_chat_001",
            topic_name="Chat Test Topic",
            status="completed",
            started_at=datetime.now().isoformat(),
            synth_count=1,
            successful_count=1,
        )
        transcript = Transcript(
            id="transcript_chat_001",
            exec_id="exec_chat_001",
            synth_id="chat01",
            synth_name="João Silva",
            status="completed",
            turn_count=1,
            timestamp=datetime.now().isoformat(),
            messages=[
                {"role": "user", "content": "Como você avalia a experiência?"},
                {"role": "assistant", "content": "Achei muito interessante."},
            ],
        )
        isolated_db_session.add_all(
            [experiment, group, synth, execution, transcript]
        )
        isolated_db_session.commit()

        # Execute: Generate chat response
        from synth_lab.repositories.research_repository import ResearchRepository
        from synth_lab.repositories.synth_repository import SynthRepository

        research_repo = ResearchRepository(session=isolated_db_session)
        synths_repo = SynthRepository(session=isolated_db_session)
        service = ChatService(research_repo=research_repo, synths_repo=synths_repo)

        request = ChatRequest(
            exec_id="exec_chat_001",
            message="E o que você mais gostou?",
            history=[],
        )

        # Mock LLM response
        with patch.object(
            service.llm_client, "complete"
        ) as mock_llm:
            mock_llm.return_value = "Gostei da simplicidade."

            response = service.generate_response("chat01", request)

            # Verify: Response generated
            assert response.message is not None
            assert len(response.message) > 0

            # Verify LLM was called with context
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args[1]
            messages = call_args["messages"]

            # Should have system prompt with synth context
            assert any(msg["role"] == "system" for msg in messages)

    @patch("synth_lab.services.chat.service._tracer")
    def test_generate_response_uses_phoenix_tracing(
        self, mock_tracer, isolated_db_session
    ):
        """Test that generate_response creates Phoenix trace spans."""
        # Setup mock tracer
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = (
            mock_span
        )

        # Setup minimal data
        experiment = Experiment(
            id="exp_tracing_chat",
            name="Tracing Chat Test",
            hypothesis="Testing tracing",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        group = SynthGroup(
            id="group_tracing_chat",
            name="Tracing Group",
            
            created_at=datetime.now().isoformat(),
        )
        synth = Synth(
            id="chat02",
            nome="Test Synth",
            data={"id": "chat02", "nome": "Test Synth", "version": "2.3.0"},
            version="2.3.0",
            created_at=datetime.now().isoformat(),
        )
        execution = ResearchExecution(
            exec_id="exec_tracing_chat",
            experiment_id="exp_tracing_chat",
            topic_name="Tracing Test Topic",
            status="completed",
            started_at=datetime.now().isoformat(),
            synth_count=1,
        )
        transcript = Transcript(
            id="transcript_tracing_chat",
            exec_id="exec_tracing_chat",
            synth_id="chat02",
            synth_name="Test Synth",
            status="completed",
            turn_count=0,
            timestamp=datetime.now().isoformat(),
            messages=[],
        )
        isolated_db_session.add_all([experiment, group, synth, execution, transcript])
        isolated_db_session.commit()

        # Execute: Generate chat response with tracing
        from synth_lab.repositories.research_repository import ResearchRepository
        from synth_lab.repositories.synth_repository import SynthRepository

        research_repo = ResearchRepository(session=isolated_db_session)
        synths_repo = SynthRepository(session=isolated_db_session)
        service = ChatService(research_repo=research_repo, synths_repo=synths_repo)

        request = ChatRequest(
            exec_id="exec_tracing_chat", message="Test message", history=[]
        )

        # Mock LLM
        with patch.object(
            service.llm_client, "complete"
        ) as mock_llm:
            mock_llm.return_value = "Test response"

            service.generate_response("chat02", request)

            # Verify: Tracer was called
            mock_tracer.start_as_current_span.assert_called()


@pytest.mark.integration
class TestAIServicesErrorHandling:
    """Integration tests for error handling in AI services."""

    @pytest.mark.asyncio
    async def test_avatar_service_handles_missing_synth_ids(self, tmp_path):
        """Test that avatar service handles synths without IDs gracefully."""
        synths_data = [
            {"id": "synth_valid_001", "nome": "Valid Synth"},
            {"nome": "No ID Synth"},  # Missing ID
        ]

        avatars_dir = tmp_path / "avatars"
        service = AvatarService(avatars_dir=avatars_dir)

        # Mock avatar generation
        with patch("synth_lab.gen_synth.avatar_generator.generate_avatars"):
            result = await service.ensure_avatars_for_synths(synths_data)

            # Should only generate for synth with ID
            assert len(result) <= 1

    def test_chat_service_handles_missing_synth(self, isolated_db_session):
        """Test that chat service raises error for non-existent synth."""
        service = ChatService()
        request = ChatRequest(
            exec_id="exec_nonexistent", message="Test", history=[]
        )

        # Should raise error when synth not found
        with pytest.raises(Exception):  # Could be AttributeError or custom error
            service.generate_response("non_existent_synth", request)
