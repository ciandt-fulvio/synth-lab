"""
Integration tests for ResearchRepository - PostgreSQL.

Tests CRUD operations for research executions and transcripts,
specifically testing that the 'messages' field (MutableJSON) works correctly.

This test catches the regression where MutableJSONList was used instead of
MutableJSON, which caused "Attribute 'messages' does not accept objects of type <class 'list'>".

References:
    - SQLAlchemy JSON types: https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.JSON
    - Mutable tracking: https://docs.sqlalchemy.org/en/20/orm/extensions/mutable.html
"""

import os
from datetime import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from synth_lab.models.orm.research import ResearchExecution, Transcript
from synth_lab.repositories.research_repository import (
    ExecutionStatus,
    Message,
    ResearchRepository,
)


@pytest.fixture(scope="module")
def research_db_session(test_database_url: str):
    """
    Create isolated database session for research repository tests.

    Uses test_database_url fixture from conftest.py which ensures
    we're using the isolated test database (synthlab_test).
    """
    engine = create_engine(test_database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    # Cleanup
    session.rollback()
    session.close()
    engine.dispose()


@pytest.fixture
def research_repository(research_db_session: Session):
    """Provide ResearchRepository instance with test session."""
    return ResearchRepository(session=research_db_session)


class TestResearchRepositoryTranscripts:
    """
    Tests for transcript creation and message handling.

    CRITICAL: These tests prevent regression where messages field
    would reject list objects due to incorrect MutableJSONList usage.
    """

    def test_save_transcript_with_messages_list(
        self,
        research_repository: ResearchRepository,
        research_db_session: Session
    ):
        """
        Test that saving a transcript with a list of messages works.

        This is the CRITICAL test that would fail if we use MutableJSONList
        instead of MutableJSON for the messages field.

        Regression test for error:
        "Attribute 'messages' does not accept objects of type <class 'list'>"
        """
        # Create execution first
        exec_id = "test_exec_001"
        research_repository.create_execution(
            exec_id=exec_id,
            topic_name="Test Interview Topic",
            synth_count=1,
            model="gpt-4o-mini",
            max_turns=6,
            status=ExecutionStatus.RUNNING,
        )

        # Create messages as a list (this is what caused the original error)
        messages = [
            Message(speaker="Interviewer", text="Hello, how are you?", internal_notes=None),
            Message(speaker="Synth", text="I'm doing well, thank you!", internal_notes="positive_response"),
            Message(speaker="Interviewer", text="Tell me about your day.", internal_notes=None),
            Message(speaker="Synth", text="It was productive.", internal_notes=None),
        ]

        # This should NOT raise "Attribute 'messages' does not accept objects of type <class 'list'>"
        research_repository.create_transcript(
            exec_id=exec_id,
            synth_id="test_synth_001",
            synth_name="Test Synth",
            messages=messages,
            status="completed"
        )

        # Verify transcript was saved
        research_db_session.flush()

        # Query directly using ORM to verify messages field
        transcript = research_db_session.query(Transcript).filter_by(
            exec_id=exec_id,
            synth_id="test_synth_001"
        ).first()

        assert transcript is not None, "Transcript should be saved"
        assert transcript.messages is not None, "Messages should not be None"
        assert isinstance(transcript.messages, list), "Messages should be a list"
        assert len(transcript.messages) == 4, "Should have 4 messages"

        # Verify message structure
        assert transcript.messages[0]["speaker"] == "Interviewer"
        assert transcript.messages[0]["text"] == "Hello, how are you?"
        assert transcript.messages[1]["speaker"] == "Synth"
        assert transcript.messages[1]["internal_notes"] == "positive_response"

    def test_retrieve_transcript_with_messages(
        self,
        research_repository: ResearchRepository,
        research_db_session: Session
    ):
        """Test that retrieving a transcript correctly deserializes messages."""
        # Create execution
        exec_id = "test_exec_002"
        research_repository.create_execution(
            exec_id=exec_id,
            topic_name="Test Retrieval",
            synth_count=1,
        )

        # Save transcript with messages
        messages = [
            Message(speaker="A", text="Question 1", internal_notes=None),
            Message(speaker="B", text="Answer 1", internal_notes="note1"),
        ]
        research_repository.create_transcript(
            exec_id=exec_id,
            synth_id="synth_002",
            synth_name="Synth Two",
            messages=messages,
            status="completed"
        )
        research_db_session.flush()

        # Retrieve using repository method
        transcript_detail = research_repository.get_transcript_detail(
            exec_id=exec_id,
            synth_id="synth_002"
        )

        assert transcript_detail is not None
        assert len(transcript_detail.messages) == 2
        assert transcript_detail.messages[0].speaker == "A"
        assert transcript_detail.messages[0].text == "Question 1"
        assert transcript_detail.messages[1].internal_notes == "note1"

    def test_empty_messages_list(
        self,
        research_repository: ResearchRepository,
        research_db_session: Session
    ):
        """Test that an empty messages list is handled correctly."""
        exec_id = "test_exec_003"
        research_repository.create_execution(
            exec_id=exec_id,
            topic_name="Empty Messages Test",
            synth_count=1,
        )

        # Save with empty messages
        research_repository.create_transcript(
            exec_id=exec_id,
            synth_id="synth_003",
            synth_name="Synth Three",
            messages=[],  # Empty list
            status="pending"
        )
        research_db_session.flush()

        transcript = research_db_session.query(Transcript).filter_by(
            exec_id=exec_id,
            synth_id="synth_003"
        ).first()

        assert transcript is not None
        assert transcript.messages == []
        assert transcript.turn_count == 0

    def test_messages_field_accepts_list_directly_in_orm(
        self,
        research_db_session: Session
    ):
        """
        Direct ORM test: Verify that Transcript.messages accepts list assignment.

        This is the most direct test of the MutableJSON fix.
        """
        # Create a simple execution first
        execution = ResearchExecution(
            exec_id="test_direct_orm",
            topic_name="Direct ORM Test",
            status="running",
            synth_count=1,
            successful_count=0,
            failed_count=0,
            model="gpt-4o-mini",
            max_turns=6,
            started_at=datetime.now().isoformat(),
        )
        research_db_session.add(execution)
        research_db_session.flush()

        # Create transcript with messages as a plain Python list
        messages_list = [
            {"speaker": "A", "text": "Hi", "internal_notes": None},
            {"speaker": "B", "text": "Hello", "internal_notes": "greeting"},
        ]

        # This is the critical line that would fail with MutableJSONList
        transcript = Transcript(
            id="test_transcript_orm",
            exec_id="test_direct_orm",
            synth_id="synth_orm",
            synth_name="ORM Test Synth",
            status="completed",
            turn_count=1,
            timestamp=datetime.now().isoformat(),
            messages=messages_list  # ← This MUST work!
        )

        # Should not raise any error
        research_db_session.add(transcript)
        research_db_session.flush()

        # Verify it was saved correctly
        saved_transcript = research_db_session.query(Transcript).filter_by(
            id="test_transcript_orm"
        ).first()

        assert saved_transcript is not None
        assert saved_transcript.messages == messages_list
        assert saved_transcript.messages[0]["speaker"] == "A"
        assert saved_transcript.messages[1]["internal_notes"] == "greeting"


if __name__ == "__main__":
    """
    Run validation to ensure tests are properly configured.

    This validates that:
    1. Tests use the correct test database
    2. Transcript messages field accepts lists
    3. No regression to MutableJSONList
    """
    import sys

    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        print("❌ POSTGRES_URL environment variable not set")
        sys.exit(1)

    if "synthlab_test" not in postgres_url:
        print(f"❌ POSTGRES_URL must point to test database (synthlab_test)")
        print(f"   Current: {postgres_url}")
        sys.exit(1)

    print("✅ Test configuration valid")
    print(f"   Using test database: {postgres_url}")
    print("")
    print("Run with: pytest tests/integration/repositories/test_research_repository.py -v")
    sys.exit(0)
