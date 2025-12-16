"""
Unit tests for Pydantic models.

Tests validation rules, enums, and model structure for:
- SessionStatus enum
- Speaker enum
- InterviewResponse model
- Message model
- InterviewSession model
- Transcript model
"""

import sys
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from synth_lab.research.models import (
    InterviewResponse,
    InterviewSession,
    Message,
    SessionStatus,
    Speaker,
    Transcript,
)


class TestSessionStatus:
    """Tests for SessionStatus enum."""

    def test_all_status_values_exist(self):
        """Test that all expected status values are defined."""
        assert SessionStatus.CREATED == "created"
        assert SessionStatus.IN_PROGRESS == "in_progress"
        assert SessionStatus.COMPLETED == "completed"
        assert SessionStatus.INTERRUPTED == "interrupted"
        assert SessionStatus.ERROR == "error"


class TestSpeaker:
    """Tests for Speaker enum."""

    def test_all_speaker_values_exist(self):
        """Test that all expected speaker values are defined."""
        assert Speaker.INTERVIEWER == "interviewer"
        assert Speaker.SYNTH == "synth"


class TestInterviewResponse:
    """Tests for InterviewResponse Pydantic model."""

    def test_valid_response(self):
        """Test creating valid InterviewResponse."""
        response = InterviewResponse(
            message="Test message",
            should_end=False,
            internal_notes="Test notes"
        )
        assert response.message == "Test message"
        assert response.should_end is False
        assert response.internal_notes == "Test notes"

    def test_response_with_defaults(self):
        """Test InterviewResponse with default values."""
        response = InterviewResponse(message="Test")
        assert response.message == "Test"
        assert response.should_end is False
        assert response.internal_notes is None

    def test_empty_message_fails(self):
        """Test that empty message fails validation."""
        with pytest.raises(ValidationError):
            InterviewResponse(message="")

    def test_should_end_must_be_boolean(self):
        """Test that should_end must be boolean."""
        with pytest.raises(ValidationError):
            InterviewResponse(message="Test", should_end="yes")


class TestMessage:
    """Tests for Message Pydantic model."""

    def test_valid_message(self):
        """Test creating valid Message."""
        now = datetime.now(timezone.utc)
        msg = Message(
            speaker=Speaker.INTERVIEWER,
            content="Hello",
            timestamp=now,
            round_number=1
        )
        assert msg.speaker == Speaker.INTERVIEWER
        assert msg.content == "Hello"
        assert msg.timestamp == now
        assert msg.round_number == 1

    def test_empty_content_fails(self):
        """Test that empty content fails validation."""
        with pytest.raises(ValidationError):
            Message(
                speaker=Speaker.SYNTH,
                content="",
                timestamp=datetime.now(timezone.utc),
                round_number=1
            )

    def test_round_number_must_be_positive(self):
        """Test that round_number must be >= 1."""
        with pytest.raises(ValidationError):
            Message(
                speaker=Speaker.INTERVIEWER,
                content="Test",
                timestamp=datetime.now(timezone.utc),
                round_number=0
            )


class TestInterviewSession:
    """Tests for InterviewSession Pydantic model."""

    def test_valid_session(self):
        """Test creating valid InterviewSession."""
        session_id = str(uuid4())
        now = datetime.now(timezone.utc)

        session = InterviewSession(
            id=session_id,
            synth_id="abc123",
            topic_guide_path="/path/to/guide.md",
            max_rounds=10,
            start_time=now,
            model_used="gpt-4.1"
        )

        assert session.id == session_id
        assert session.synth_id == "abc123"
        assert session.max_rounds == 10
        assert session.status == SessionStatus.CREATED

    def test_session_with_defaults(self):
        """Test session with default values."""
        session = InterviewSession(
            id=str(uuid4()),
            synth_id="xyz789",
            start_time=datetime.now(timezone.utc),
            model_used="gpt-4.1"
        )

        assert session.max_rounds == 10  # default
        assert session.topic_guide_path is None
        assert session.end_time is None
        assert session.status == SessionStatus.CREATED

    def test_invalid_synth_id_fails(self):
        """Test that invalid synth_id format fails."""
        with pytest.raises(ValidationError):
            InterviewSession(
                id=str(uuid4()),
                synth_id="invalid-id-too-long",
                start_time=datetime.now(timezone.utc),
                model_used="gpt-4.1"
            )

    def test_max_rounds_limits(self):
        """Test max_rounds validation limits."""
        # Too low
        with pytest.raises(ValidationError):
            InterviewSession(
                id=str(uuid4()),
                synth_id="abc123",
                max_rounds=0,
                start_time=datetime.now(timezone.utc),
                model_used="gpt-4.1"
            )

        # Too high
        with pytest.raises(ValidationError):
            InterviewSession(
                id=str(uuid4()),
                synth_id="abc123",
                max_rounds=101,
                start_time=datetime.now(timezone.utc),
                model_used="gpt-4.1"
            )


class TestTranscript:
    """Tests for Transcript Pydantic model."""

    def test_valid_transcript(self):
        """Test creating valid Transcript."""
        session = InterviewSession(
            id=str(uuid4()),
            synth_id="abc123",
            start_time=datetime.now(timezone.utc),
            model_used="gpt-4.1"
        )

        synth_snapshot = {"id": "abc123", "nome": "Test Synth"}
        messages = [
            Message(
                speaker=Speaker.INTERVIEWER,
                content="Hello",
                timestamp=datetime.now(timezone.utc),
                round_number=1
            )
        ]

        transcript = Transcript(
            session=session,
            synth_snapshot=synth_snapshot,
            messages=messages
        )

        assert transcript.session.synth_id == "abc123"
        assert len(transcript.messages) == 1
        assert transcript.synth_snapshot["id"] == "abc123"

    def test_empty_transcript(self):
        """Test transcript with no messages."""
        session = InterviewSession(
            id=str(uuid4()),
            synth_id="abc123",
            start_time=datetime.now(timezone.utc),
            model_used="gpt-4.1"
        )

        transcript = Transcript(
            session=session,
            synth_snapshot={},
            messages=[]
        )

        assert len(transcript.messages) == 0


if __name__ == "__main__":
    """Validation with real test execution."""
    print("=== Pydantic Models Test Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Run pytest programmatically
    try:
        exit_code = pytest.main([__file__, "-v", "--tb=short"])

        if exit_code == 0:
            print("\n✅ VALIDATION PASSED - All model tests are ready to fail")
            print("Models can now be implemented to make these tests pass")
            sys.exit(0)
        else:
            print(
                f"\n❌ VALIDATION FAILED - Test setup has issues (exit code: {exit_code})")
            sys.exit(1)
    except Exception as e:
        print(f"❌ VALIDATION FAILED - Error running tests: {e}")
        sys.exit(1)
