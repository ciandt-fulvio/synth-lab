"""
SSE event models for real-time interview streaming.

Pydantic models for Server-Sent Events during research execution.

References:
    - SSE Spec: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class InterviewMessageEvent(BaseModel):
    """Event for a single interview message (interviewer or interviewee turn)."""

    event_type: Literal[
        "message",
        "interview_started",
        "interview_completed",
        "transcription_completed",
        "execution_completed",
        "avatar_generation_completed",
        "error",
    ] = Field(..., description="Type of event")
    exec_id: str = Field(..., description="Execution ID")
    synth_id: str | None = Field(default=None, description="Synth ID")
    turn_number: int | None = Field(default=None, description="Turn number in interview")
    speaker: Literal["Interviewer", "Interviewee"] | None = Field(
        default=None, description="Speaker role"
    )
    text: str | None = Field(default=None, description="Message text")
    sentiment: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description="Sentiment score 1-5 (only for Interviewer messages)",
    )
    timestamp: datetime = Field(..., description="Event timestamp")
    is_replay: bool = Field(default=False, description="True if from history replay")

    def to_sse(self) -> str:
        """Format event as SSE string."""
        return f"event: {self.event_type}\ndata: {self.model_dump_json()}\n\n"


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: Basic message event
    total_tests += 1
    try:
        event = InterviewMessageEvent(
            event_type="message",
            exec_id="batch_test_20251219_120000",
            synth_id="synth_001",
            turn_number=1,
            speaker="Interviewer",
            text="How do you shop online?",
            timestamp=datetime.now(),
        )
        if event.event_type != "message":
            all_validation_failures.append(f"Event type mismatch: {event.event_type}")
        if event.is_replay is not False:
            all_validation_failures.append(f"Default is_replay should be False: {event.is_replay}")
    except Exception as e:
        all_validation_failures.append(f"Basic message event test failed: {e}")

    # Test 2: Replay message event
    total_tests += 1
    try:
        event = InterviewMessageEvent(
            event_type="message",
            exec_id="batch_test_20251219_120000",
            synth_id="synth_001",
            speaker="Interviewee",
            text="I usually use Amazon.",
            timestamp=datetime.now(),
            is_replay=True,
        )
        if event.is_replay is not True:
            all_validation_failures.append(f"is_replay should be True: {event.is_replay}")
        if event.turn_number is not None:
            all_validation_failures.append(f"turn_number should be None: {event.turn_number}")
    except Exception as e:
        all_validation_failures.append(f"Replay message event test failed: {e}")

    # Test 3: Execution completed event
    total_tests += 1
    try:
        event = InterviewMessageEvent(
            event_type="execution_completed",
            exec_id="batch_test_20251219_120000",
            timestamp=datetime.now(),
        )
        if event.synth_id is not None:
            all_validation_failures.append(f"synth_id should be None: {event.synth_id}")
        if event.text is not None:
            all_validation_failures.append(f"text should be None: {event.text}")
    except Exception as e:
        all_validation_failures.append(f"Execution completed event test failed: {e}")

    # Test 4: to_sse() format
    total_tests += 1
    try:
        event = InterviewMessageEvent(
            event_type="message",
            exec_id="test",
            timestamp=datetime.now(),
        )
        sse_output = event.to_sse()
        if not sse_output.startswith("event: message\n"):
            all_validation_failures.append(f"SSE should start with event line: {sse_output[:30]}")
        if "data: {" not in sse_output:
            all_validation_failures.append(f"SSE should contain data line: {sse_output}")
        if not sse_output.endswith("\n\n"):
            all_validation_failures.append("SSE should end with double newline")
    except Exception as e:
        all_validation_failures.append(f"to_sse() test failed: {e}")

    # Test 5: Speaker literal validation
    total_tests += 1
    try:
        from pydantic import ValidationError

        try:
            InterviewMessageEvent(
                event_type="message",
                exec_id="test",
                speaker="InvalidSpeaker",  # type: ignore
                timestamp=datetime.now(),
            )
            all_validation_failures.append("Should reject invalid speaker value")
        except ValidationError:
            pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Speaker validation test failed: {e}")

    # Test 6: Event type literal validation
    total_tests += 1
    try:
        from pydantic import ValidationError

        try:
            InterviewMessageEvent(
                event_type="invalid_type",  # type: ignore
                exec_id="test",
                timestamp=datetime.now(),
            )
            all_validation_failures.append("Should reject invalid event_type value")
        except ValidationError:
            pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Event type validation test failed: {e}")

    # Test 7: Transcription completed event
    total_tests += 1
    try:
        event = InterviewMessageEvent(
            event_type="transcription_completed",
            exec_id="batch_test_20251219_120000",
            timestamp=datetime.now(),
        )
        if event.event_type != "transcription_completed":
            all_validation_failures.append(f"Event type mismatch: {event.event_type}")
        sse_output = event.to_sse()
        if "transcription_completed" not in sse_output:
            all_validation_failures.append(f"SSE should contain event type: {sse_output}")
    except Exception as e:
        all_validation_failures.append(f"Transcription completed event test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
