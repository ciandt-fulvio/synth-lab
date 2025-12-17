"""
Unit tests for trace visualizer data models.

Tests validate:
- Enum definitions (SpanType, SpanStatus)
- Dataclass structure and validation (Step, Turn, Trace)
- JSON serialization/deserialization
- Invariants (durations, timestamps, cardinality)
"""

import pytest
from datetime import datetime, timezone
from synth_lab.trace_visualizer.models import (
    SpanType,
    SpanStatus,
    Step,
    Turn,
    Trace,
)


class TestEnums:
    """Test enum definitions."""

    def test_span_type_values(self):
        """SpanType enum has all required values."""
        assert SpanType.LLM_CALL == "llm_call"
        assert SpanType.TOOL_CALL == "tool_call"
        assert SpanType.TURN == "turn"
        assert SpanType.ERROR == "error"
        assert SpanType.LOGIC == "logic"

    def test_span_status_values(self):
        """SpanStatus enum has all required values."""
        assert SpanStatus.SUCCESS == "success"
        assert SpanStatus.ERROR == "error"
        assert SpanStatus.PENDING == "pending"


class TestStep:
    """Test Step dataclass."""

    def test_step_creation(self):
        """Step dataclass can be created with required fields."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc)

        step = Step(
            span_id="step-001",
            type=SpanType.LLM_CALL,
            start_time=start,
            end_time=end,
            duration_ms=3000,
            status=SpanStatus.SUCCESS,
            attributes={"prompt": "test", "model": "claude-sonnet-4-5"},
        )

        assert step.span_id == "step-001"
        assert step.type == SpanType.LLM_CALL
        assert step.start_time == start
        assert step.end_time == end
        assert step.duration_ms == 3000
        assert step.status == SpanStatus.SUCCESS
        assert step.attributes["prompt"] == "test"

    def test_step_to_dict(self):
        """Step can be serialized to dict for JSON export."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc)

        step = Step(
            span_id="step-001",
            type=SpanType.LLM_CALL,
            start_time=start,
            end_time=end,
            duration_ms=3000,
            status=SpanStatus.SUCCESS,
            attributes={"prompt": "test"},
        )

        data = step.to_dict()

        assert data["span_id"] == "step-001"
        assert data["type"] == "llm_call"
        assert data["start_time"] == "2025-12-17T10:00:00+00:00"
        assert data["end_time"] == "2025-12-17T10:00:03+00:00"
        assert data["duration_ms"] == 3000
        assert data["status"] == "success"
        assert data["attributes"]["prompt"] == "test"

    def test_step_with_error_status(self):
        """Step with error status includes error attributes."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 12, 17, 10, 0, 1, tzinfo=timezone.utc)

        step = Step(
            span_id="step-error",
            type=SpanType.ERROR,
            start_time=start,
            end_time=end,
            duration_ms=1000,
            status=SpanStatus.ERROR,
            attributes={
                "error_type": "ValueError",
                "error_message": "Invalid input",
            },
        )

        assert step.status == SpanStatus.ERROR
        assert step.attributes["error_type"] == "ValueError"


class TestTurn:
    """Test Turn dataclass."""

    def test_turn_creation(self):
        """Turn dataclass can be created with required fields."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 12, 17, 10, 2, 15, tzinfo=timezone.utc)

        step1 = Step(
            span_id="step-001",
            type=SpanType.LLM_CALL,
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc),
            duration_ms=3000,
            status=SpanStatus.SUCCESS,
            attributes={"prompt": "test"},
        )

        turn = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=end,
            duration_ms=135000,
            steps=[step1],
        )

        assert turn.turn_id == "turn-001"
        assert turn.turn_number == 1
        assert turn.start_time == start
        assert turn.end_time == end
        assert turn.duration_ms == 135000
        assert len(turn.steps) == 1
        assert turn.steps[0].span_id == "step-001"

    def test_turn_to_dict(self):
        """Turn can be serialized to dict for JSON export."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 12, 17, 10, 2, 15, tzinfo=timezone.utc)

        step1 = Step(
            span_id="step-001",
            type=SpanType.LLM_CALL,
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc),
            duration_ms=3000,
            status=SpanStatus.SUCCESS,
            attributes={"prompt": "test"},
        )

        turn = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=end,
            duration_ms=135000,
            steps=[step1],
        )

        data = turn.to_dict()

        assert data["turn_id"] == "turn-001"
        assert data["turn_number"] == 1
        assert data["start_time"] == "2025-12-17T10:00:00+00:00"
        assert data["end_time"] == "2025-12-17T10:02:15+00:00"
        assert data["duration_ms"] == 135000
        assert len(data["steps"]) == 1
        assert data["steps"][0]["span_id"] == "step-001"

    def test_turn_with_multiple_steps(self):
        """Turn can contain multiple steps."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)

        step1 = Step(
            span_id="step-001",
            type=SpanType.LLM_CALL,
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc),
            duration_ms=3000,
            status=SpanStatus.SUCCESS,
            attributes={"prompt": "test"},
        )

        step2 = Step(
            span_id="step-002",
            type=SpanType.TOOL_CALL,
            start_time=datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 17, 10, 0, 5, tzinfo=timezone.utc),
            duration_ms=2000,
            status=SpanStatus.SUCCESS,
            attributes={"tool_name": "get_weather"},
        )

        turn = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 0, 5, tzinfo=timezone.utc),
            duration_ms=5000,
            steps=[step1, step2],
        )

        assert len(turn.steps) == 2
        assert turn.steps[0].type == SpanType.LLM_CALL
        assert turn.steps[1].type == SpanType.TOOL_CALL


class TestTrace:
    """Test Trace dataclass."""

    def test_trace_creation(self):
        """Trace dataclass can be created with required fields."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 12, 17, 10, 5, 30, tzinfo=timezone.utc)

        step1 = Step(
            span_id="step-001",
            type=SpanType.LLM_CALL,
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc),
            duration_ms=3000,
            status=SpanStatus.SUCCESS,
            attributes={"prompt": "test"},
        )

        turn1 = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 2, 15, tzinfo=timezone.utc),
            duration_ms=135000,
            steps=[step1],
        )

        trace = Trace(
            trace_id="trace-001",
            start_time=start,
            end_time=end,
            duration_ms=330000,
            turns=[turn1],
            metadata={"user_id": "user-123"},
        )

        assert trace.trace_id == "trace-001"
        assert trace.start_time == start
        assert trace.end_time == end
        assert trace.duration_ms == 330000
        assert len(trace.turns) == 1
        assert trace.turns[0].turn_id == "turn-001"
        assert trace.metadata["user_id"] == "user-123"

    def test_trace_to_dict(self):
        """Trace can be serialized to dict for JSON export."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 12, 17, 10, 5, 30, tzinfo=timezone.utc)

        step1 = Step(
            span_id="step-001",
            type=SpanType.LLM_CALL,
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc),
            duration_ms=3000,
            status=SpanStatus.SUCCESS,
            attributes={"prompt": "test"},
        )

        turn1 = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 2, 15, tzinfo=timezone.utc),
            duration_ms=135000,
            steps=[step1],
        )

        trace = Trace(
            trace_id="trace-001",
            start_time=start,
            end_time=end,
            duration_ms=330000,
            turns=[turn1],
            metadata={"user_id": "user-123"},
        )

        data = trace.to_dict()

        assert data["trace_id"] == "trace-001"
        assert data["start_time"] == "2025-12-17T10:00:00+00:00"
        assert data["end_time"] == "2025-12-17T10:05:30+00:00"
        assert data["duration_ms"] == 330000
        assert len(data["turns"]) == 1
        assert data["turns"][0]["turn_id"] == "turn-001"
        assert data["metadata"]["user_id"] == "user-123"

    def test_trace_with_multiple_turns(self):
        """Trace can contain multiple turns."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)

        step1 = Step(
            span_id="step-001",
            type=SpanType.LLM_CALL,
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc),
            duration_ms=3000,
            status=SpanStatus.SUCCESS,
            attributes={"prompt": "test"},
        )

        turn1 = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 2, 15, tzinfo=timezone.utc),
            duration_ms=135000,
            steps=[step1],
        )

        turn2 = Turn(
            turn_id="turn-002",
            turn_number=2,
            start_time=datetime(2025, 12, 17, 10, 3, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 12, 17, 10, 5, 30, tzinfo=timezone.utc),
            duration_ms=150000,
            steps=[step1],
        )

        trace = Trace(
            trace_id="trace-001",
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 5, 30, tzinfo=timezone.utc),
            duration_ms=330000,
            turns=[turn1, turn2],
        )

        assert len(trace.turns) == 2
        assert trace.turns[0].turn_number == 1
        assert trace.turns[1].turn_number == 2

    def test_trace_without_metadata(self):
        """Trace can be created without metadata."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 12, 17, 10, 5, 30, tzinfo=timezone.utc)

        step1 = Step(
            span_id="step-001",
            type=SpanType.LLM_CALL,
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc),
            duration_ms=3000,
            status=SpanStatus.SUCCESS,
            attributes={"prompt": "test"},
        )

        turn1 = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=end,
            duration_ms=330000,
            steps=[step1],
        )

        trace = Trace(
            trace_id="trace-001",
            start_time=start,
            end_time=end,
            duration_ms=330000,
            turns=[turn1],
        )

        assert trace.metadata == {}
        data = trace.to_dict()
        assert data["metadata"] == {}
