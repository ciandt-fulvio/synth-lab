"""
Research domain models for synth-lab.

Pydantic models for research execution and transcript data.

References:
    - Schema definition: specs/010-rest-api/data-model.md
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Status of a research execution."""

    PENDING = "pending"
    RUNNING = "running"
    GENERATING_SUMMARY = "generating_summary"
    COMPLETED = "completed"
    FAILED = "failed"


class Message(BaseModel):
    """A single message in an interview transcript."""

    speaker: str = Field(..., description="Speaker name (Interviewer or synth name)")
    text: str = Field(..., description="Message text")
    internal_notes: str | None = Field(default=None, description="Interviewer notes")


class ResearchExecutionBase(BaseModel):
    """Base research execution model."""

    exec_id: str = Field(..., description="Execution ID (e.g., batch_topic_timestamp)")
    topic_name: str = Field(..., description="Topic guide name")
    status: ExecutionStatus = Field(..., description="Execution status")
    synth_count: int = Field(..., description="Number of synths in execution")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")


class ResearchExecutionSummary(ResearchExecutionBase):
    """Summary research execution for list endpoints."""

    pass


class ResearchExecutionDetail(ResearchExecutionBase):
    """Full research execution with all details."""

    successful_count: int = Field(default=0, description="Completed interviews")
    failed_count: int = Field(default=0, description="Failed interviews")
    model: str = Field(default="gpt-5-mini", description="LLM model used")
    max_turns: int = Field(default=6, description="Max interview turns")
    summary_available: bool = Field(default=False, description="Summary exists")
    prfaq_available: bool = Field(default=False, description="PR-FAQ exists")


class TranscriptSummary(BaseModel):
    """Summary transcript for list endpoints."""

    synth_id: str = Field(..., description="Synth ID")
    synth_name: str | None = Field(default=None, description="Synth name")
    turn_count: int = Field(default=0, description="Number of turns")
    timestamp: datetime = Field(..., description="Interview timestamp")
    status: str = Field(default="completed", description="Transcript status")


class TranscriptDetail(BaseModel):
    """Full transcript with messages."""

    exec_id: str = Field(..., description="Execution ID")
    synth_id: str = Field(..., description="Synth ID")
    synth_name: str | None = Field(default=None, description="Synth name")
    turn_count: int = Field(default=0, description="Number of turns")
    timestamp: datetime = Field(..., description="Interview timestamp")
    status: str = Field(default="completed", description="Transcript status")
    messages: list[Message] = Field(default_factory=list, description="Interview messages")


class ResearchExecuteRequest(BaseModel):
    """Request model for executing research."""

    topic_name: str = Field(..., description="Topic guide name")
    additional_context: str | None = Field(
        default=None,
        description="Additional context to complement the research scenario",
    )
    synth_ids: list[str] | None = Field(
        default=None,
        description="Specific synth IDs to interview",
    )
    synth_count: int | None = Field(
        default=None,
        description="Number of random synths (if synth_ids not provided)",
    )
    max_turns: int = Field(
        default=6,
        ge=1,
        le=20,
        description="Max interview turns (each turn = 1 question + 1 answer)",
    )
    max_concurrent: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max concurrent interviews",
    )
    model: str = Field(default="gpt-5-mini", description="LLM model to use")
    generate_summary: bool = Field(default=True, description="Generate summary after completion")
    skip_interviewee_review: bool = Field(
        default=True,
        description="Skip interviewee response reviewer for faster execution",
    )


class ResearchExecuteResponse(BaseModel):
    """Response model for research execution."""

    exec_id: str = Field(..., description="Execution ID")
    status: ExecutionStatus = Field(..., description="Execution status")
    topic_name: str = Field(..., description="Topic guide name")
    synth_count: int = Field(..., description="Number of synths")
    started_at: datetime = Field(..., description="Start timestamp")


class SummaryGenerateRequest(BaseModel):
    """Request model for generating summary."""

    model: str = Field(default="gpt-5", description="LLM model to use for summarization")


class SummaryGenerateResponse(BaseModel):
    """Response model for summary generation."""

    exec_id: str = Field(..., description="Execution ID")
    status: str = Field(..., description="Generation status (generating, completed, failed)")
    message: str | None = Field(default=None, description="Status message")
    generated_at: datetime | None = Field(default=None, description="Completion timestamp")


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: ExecutionStatus enum
    total_tests += 1
    try:
        status = ExecutionStatus.COMPLETED
        if status.value != "completed":
            all_validation_failures.append(f"Status value mismatch: {status.value}")
        if ExecutionStatus("pending") != ExecutionStatus.PENDING:
            all_validation_failures.append("Status from string failed")
    except Exception as e:
        all_validation_failures.append(f"ExecutionStatus test failed: {e}")

    # Test 2: Message model
    total_tests += 1
    try:
        msg = Message(speaker="Interviewer", text="Como você compra online?")
        if msg.speaker != "Interviewer":
            all_validation_failures.append(f"Speaker mismatch: {msg.speaker}")
        if msg.internal_notes is not None:
            all_validation_failures.append(f"Default notes should be None: {msg.internal_notes}")

        msg_with_notes = Message(
            speaker="Interviewer",
            text="Question",
            internal_notes="Strategy note",
        )
        if msg_with_notes.internal_notes != "Strategy note":
            all_validation_failures.append(f"Notes mismatch: {msg_with_notes.internal_notes}")
    except Exception as e:
        all_validation_failures.append(f"Message test failed: {e}")

    # Test 3: ResearchExecutionBase
    total_tests += 1
    try:
        execution = ResearchExecutionBase(
            exec_id="batch_test_20251219_120000",
            topic_name="compra-amazon",
            status=ExecutionStatus.COMPLETED,
            synth_count=5,
            started_at=datetime.now(),
        )
        if execution.exec_id != "batch_test_20251219_120000":
            all_validation_failures.append(f"Exec ID mismatch: {execution.exec_id}")
        if execution.completed_at is not None:
            all_validation_failures.append(
                f"Default completed_at should be None: {execution.completed_at}"
            )
    except Exception as e:
        all_validation_failures.append(f"ResearchExecutionBase test failed: {e}")

    # Test 4: ResearchExecutionDetail
    total_tests += 1
    try:
        detail = ResearchExecutionDetail(
            exec_id="batch_test_20251219_120000",
            topic_name="compra-amazon",
            status=ExecutionStatus.COMPLETED,
            synth_count=5,
            started_at=datetime.now(),
            successful_count=4,
            failed_count=1,
            summary_available=True,
        )
        if detail.successful_count != 4:
            all_validation_failures.append(f"Successful count mismatch: {detail.successful_count}")
        if detail.summary_available is not True:
            all_validation_failures.append(
                f"summary_available should be True: {detail.summary_available}"
            )
    except Exception as e:
        all_validation_failures.append(f"ResearchExecutionDetail test failed: {e}")

    # Test 5: TranscriptSummary
    total_tests += 1
    try:
        summary = TranscriptSummary(
            synth_id="abc123",
            synth_name="Test Synth",
            turn_count=6,
            timestamp=datetime.now(),
        )
        if summary.synth_id != "abc123":
            all_validation_failures.append(f"Synth ID mismatch: {summary.synth_id}")
        if summary.turn_count != 6:
            all_validation_failures.append(f"Turn count mismatch: {summary.turn_count}")
    except Exception as e:
        all_validation_failures.append(f"TranscriptSummary test failed: {e}")

    # Test 6: TranscriptDetail with messages
    total_tests += 1
    try:
        detail = TranscriptDetail(
            exec_id="batch_test_20251219_120000",
            synth_id="abc123",
            timestamp=datetime.now(),
            messages=[
                Message(speaker="Interviewer", text="Q1"),
                Message(speaker="Test Synth", text="A1"),
            ],
        )
        if len(detail.messages) != 2:
            all_validation_failures.append(f"Messages length mismatch: {len(detail.messages)}")
        if detail.messages[0].speaker != "Interviewer":
            all_validation_failures.append(
                f"First speaker mismatch: {detail.messages[0].speaker}"
            )
    except Exception as e:
        all_validation_failures.append(f"TranscriptDetail test failed: {e}")

    # Test 7: ResearchExecuteRequest validation
    total_tests += 1
    try:
        from pydantic import ValidationError

        req = ResearchExecuteRequest(topic_name="test")
        if req.max_turns != 6:
            all_validation_failures.append(f"Default max_turns should be 6: {req.max_turns}")

        try:
            ResearchExecuteRequest(topic_name="test", max_turns=0)
            all_validation_failures.append("Should reject max_turns=0")
        except ValidationError:
            pass  # Expected

        try:
            ResearchExecuteRequest(topic_name="test", max_turns=21)
            all_validation_failures.append("Should reject max_turns=21")
        except ValidationError:
            pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"ResearchExecuteRequest validation failed: {e}")

    # Test 8: ResearchExecuteResponse
    total_tests += 1
    try:
        response = ResearchExecuteResponse(
            exec_id="batch_test_20251219_120000",
            status=ExecutionStatus.RUNNING,
            topic_name="test",
            synth_count=3,
            started_at=datetime.now(),
        )
        if response.status != ExecutionStatus.RUNNING:
            all_validation_failures.append(f"Status mismatch: {response.status}")
    except Exception as e:
        all_validation_failures.append(f"ResearchExecuteResponse test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
