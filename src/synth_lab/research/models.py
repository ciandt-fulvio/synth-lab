"""
Pydantic data models for UX research interviews.

This module defines the core data structures for interview sessions, messages,
and responses using Pydantic for validation.

Models:
- SessionStatus: Enum for interview session states
- Speaker: Enum for conversation participants
- InterviewResponse: LLM response format with structured output
- Message: Individual conversation turn
- InterviewSession: Interview metadata and configuration
- Transcript: Complete interview record for persistence

Sample usage:
    from synth_lab.research.models import InterviewResponse, Speaker

    response = InterviewResponse(
        message="Hello, how are you?",
        should_end=False
    )

Expected output:
    Validated Pydantic models with automatic type checking

Third-party Documentation:
- Pydantic: https://docs.pydantic.dev/
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Status da sessão de entrevista."""

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    ERROR = "error"


class Speaker(str, Enum):
    """Identificador do participante da conversa."""

    INTERVIEWER = "interviewer"
    SYNTH = "synth"


class InterviewResponse(BaseModel):
    """
    Formato de resposta estruturada do LLM.

    Usado tanto pelo entrevistador quanto pelo synth para retornar mensagens
    estruturadas com controle de fluxo.
    """

    model_config = {"strict": True}

    message: str = Field(..., min_length=1, description="Texto da fala")
    should_end: bool = Field(
        default=False, description="Sinaliza fim da entrevista")
    internal_notes: str | None = Field(
        default=None, description="Notas internas opcionais"
    )


class Message(BaseModel):
    """
    Uma mensagem na conversa da entrevista.

    Representa um turno de conversação com timestamp e metadados.
    """

    speaker: Speaker
    content: str = Field(..., min_length=1)
    timestamp: datetime
    internal_notes: str | None = None
    round_number: int = Field(..., ge=1)


class InterviewSession(BaseModel):
    """
    Metadados de uma sessão de entrevista.

    Contém configuração e estado da entrevista.
    """

    id: str = Field(..., pattern=r"^[a-f0-9-]{36}$")
    synth_id: str = Field(..., pattern=r"^[a-zA-Z0-9]{6}$")
    topic_guide_path: str | None = None
    max_rounds: int = Field(default=10, ge=1, le=100)
    start_time: datetime
    end_time: datetime | None = None
    status: SessionStatus = SessionStatus.CREATED
    model_used: str = Field(..., min_length=1)


class Transcript(BaseModel):
    """
    Transcrição completa da entrevista.

    Inclui sessão, snapshot do synth e histórico de mensagens.
    """

    session: InterviewSession
    synth_snapshot: dict[str, Any]  # Full synth data at interview time
    messages: list[Message] = Field(default_factory=list)


if __name__ == "__main__":
    """Validation with real data."""
    import sys
    from uuid import uuid4
    from datetime import timezone

    print("=== Models Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create SessionStatus enum
    total_tests += 1
    try:
        assert SessionStatus.CREATED == "created"
        assert SessionStatus.IN_PROGRESS == "in_progress"
        print("✓ SessionStatus enum created successfully")
    except Exception as e:
        all_validation_failures.append(f"SessionStatus enum: {e}")

    # Test 2: Create Speaker enum
    total_tests += 1
    try:
        assert Speaker.INTERVIEWER == "interviewer"
        assert Speaker.SYNTH == "synth"
        print("✓ Speaker enum created successfully")
    except Exception as e:
        all_validation_failures.append(f"Speaker enum: {e}")

    # Test 3: Create InterviewResponse model
    total_tests += 1
    try:
        response = InterviewResponse(
            message="Test message", should_end=False, internal_notes="Notes"
        )
        assert response.message == "Test message"
        assert response.should_end is False
        print("✓ InterviewResponse model created successfully")
    except Exception as e:
        all_validation_failures.append(f"InterviewResponse model: {e}")

    # Test 4: Create Message model
    total_tests += 1
    try:
        now = datetime.now(timezone.utc)
        msg = Message(
            speaker=Speaker.INTERVIEWER,
            content="Hello",
            timestamp=now,
            round_number=1,
        )
        assert msg.content == "Hello"
        print("✓ Message model created successfully")
    except Exception as e:
        all_validation_failures.append(f"Message model: {e}")

    # Test 5: Create InterviewSession model
    total_tests += 1
    try:
        session_id = str(uuid4())
        now = datetime.now(timezone.utc)
        session = InterviewSession(
            id=session_id,
            synth_id="abc123",
            start_time=now,
            model_used="gpt-4.1",
        )
        assert session.synth_id == "abc123"
        assert session.max_rounds == 10  # default
        print("✓ InterviewSession model created successfully")
    except Exception as e:
        all_validation_failures.append(f"InterviewSession model: {e}")

    # Test 6: Create Transcript model
    total_tests += 1
    try:
        session = InterviewSession(
            id=str(uuid4()),
            synth_id="xyz789",
            start_time=datetime.now(timezone.utc),
            model_used="gpt-4.1",
        )
        transcript = Transcript(
            session=session, synth_snapshot={}, messages=[])
        assert len(transcript.messages) == 0
        print("✓ Transcript model created successfully")
    except Exception as e:
        all_validation_failures.append(f"Transcript model: {e}")

    # Test 7: Validate InterviewResponse with empty message fails
    total_tests += 1
    try:
        from pydantic import ValidationError

        try:
            InterviewResponse(message="", should_end=False)
            all_validation_failures.append(
                "Empty message validation: Should have raised ValidationError"
            )
        except ValidationError:
            print("✓ InterviewResponse validation works (empty message rejected)")
    except Exception as e:
        all_validation_failures.append(f"Validation test: {e}")

    # Test 8: Validate synth_id pattern
    total_tests += 1
    try:
        from pydantic import ValidationError

        try:
            InterviewSession(
                id=str(uuid4()),
                synth_id="invalid-too-long",
                start_time=datetime.now(timezone.utc),
                model_used="gpt-4.1",
            )
            all_validation_failures.append(
                "Synth ID validation: Should have raised ValidationError"
            )
        except ValidationError:
            print("✓ InterviewSession validation works (invalid synth_id rejected)")
    except Exception as e:
        all_validation_failures.append(f"Synth ID validation: {e}")

    # Final validation result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Models module is validated and ready for use")
        sys.exit(0)
