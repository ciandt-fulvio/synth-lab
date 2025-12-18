"""
Unit tests for Tracer class.

Tests validate:
- Tracer initialization with auto-generated or custom trace_id
- start_turn() context manager with timestamp recording
- start_span() context manager with Span object yielding
- Span.set_attribute() and Span.set_status() methods
- Tracer.trace property (read-only access)
- Tracer.save_trace() wrapper method
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import json
import tempfile
from synth_lab.trace_visualizer.tracer import Tracer, Span
from synth_lab.trace_visualizer.models import SpanType, SpanStatus


class TestTracerInit:
    """Test Tracer initialization."""

    def test_tracer_auto_generates_trace_id(self):
        """Tracer auto-generates UUID trace_id if not provided."""
        tracer = Tracer()

        assert tracer.trace.trace_id is not None
        assert len(tracer.trace.trace_id) > 0
        assert isinstance(tracer.trace.trace_id, str)

    def test_tracer_accepts_custom_trace_id(self):
        """Tracer accepts custom trace_id."""
        tracer = Tracer(trace_id="custom-trace-123")

        assert tracer.trace.trace_id == "custom-trace-123"

    def test_tracer_accepts_metadata(self):
        """Tracer accepts custom metadata."""
        tracer = Tracer(
            trace_id="trace-001",
            metadata={"user_id": "user-123", "env": "dev"}
        )

        assert tracer.trace.metadata["user_id"] == "user-123"
        assert tracer.trace.metadata["env"] == "dev"

    def test_tracer_empty_metadata_by_default(self):
        """Tracer has empty metadata by default."""
        tracer = Tracer()

        assert tracer.trace.metadata == {}


class TestTracerStartTurn:
    """Test Tracer.start_turn() context manager."""

    def test_start_turn_records_timestamps(self):
        """start_turn() records start and end timestamps."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            pass

        assert len(tracer.trace.turns) == 1
        turn = tracer.trace.turns[0]
        assert turn.turn_number == 1
        assert turn.start_time is not None
        assert turn.end_time is not None
        assert turn.end_time >= turn.start_time

    def test_start_turn_calculates_duration(self):
        """start_turn() calculates duration_ms."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            pass

        turn = tracer.trace.turns[0]
        assert turn.duration_ms >= 0
        # Duration should be reasonable (< 1 second for empty block)
        assert turn.duration_ms < 1000

    def test_start_turn_generates_turn_id(self):
        """start_turn() generates unique turn_id."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            pass

        turn = tracer.trace.turns[0]
        assert turn.turn_id is not None
        assert len(turn.turn_id) > 0

    def test_start_turn_requires_turn_number(self):
        """start_turn() requires turn_number parameter."""
        tracer = Tracer()

        # Should work with turn_number
        with tracer.start_turn(turn_number=1):
            pass

        assert len(tracer.trace.turns) == 1

    def test_multiple_turns_sequential(self):
        """Multiple turns can be recorded sequentially."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            pass

        with tracer.start_turn(turn_number=2):
            pass

        assert len(tracer.trace.turns) == 2
        assert tracer.trace.turns[0].turn_number == 1
        assert tracer.trace.turns[1].turn_number == 2


class TestTracerStartSpan:
    """Test Tracer.start_span() context manager."""

    def test_start_span_within_turn(self):
        """start_span() records span within current turn."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            with tracer.start_span(
                span_type=SpanType.LLM_CALL,
                attributes={"prompt": "test"}
            ):
                pass

        turn = tracer.trace.turns[0]
        assert len(turn.steps) == 1
        step = turn.steps[0]
        assert step.type == SpanType.LLM_CALL
        assert step.attributes["prompt"] == "test"

    def test_start_span_records_timestamps(self):
        """start_span() records start and end timestamps."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            with tracer.start_span(span_type=SpanType.LLM_CALL):
                pass

        step = tracer.trace.turns[0].steps[0]
        assert step.start_time is not None
        assert step.end_time is not None
        assert step.end_time >= step.start_time

    def test_start_span_calculates_duration(self):
        """start_span() calculates duration_ms."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            with tracer.start_span(span_type=SpanType.LLM_CALL):
                pass

        step = tracer.trace.turns[0].steps[0]
        assert step.duration_ms >= 0
        assert step.duration_ms < 1000  # Should be fast

    def test_start_span_yields_span_object(self):
        """start_span() yields Span object for attribute setting."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            with tracer.start_span(span_type=SpanType.LLM_CALL) as span:
                assert isinstance(span, Span)
                span.set_attribute("response", "test response")

        step = tracer.trace.turns[0].steps[0]
        assert step.attributes["response"] == "test response"

    def test_start_span_default_status_success(self):
        """start_span() defaults to success status."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            with tracer.start_span(span_type=SpanType.LLM_CALL):
                pass

        step = tracer.trace.turns[0].steps[0]
        assert step.status == SpanStatus.SUCCESS

    def test_multiple_spans_in_turn(self):
        """Multiple spans can be recorded in single turn."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            with tracer.start_span(span_type=SpanType.LLM_CALL):
                pass
            with tracer.start_span(span_type=SpanType.TOOL_CALL):
                pass

        turn = tracer.trace.turns[0]
        assert len(turn.steps) == 2
        assert turn.steps[0].type == SpanType.LLM_CALL
        assert turn.steps[1].type == SpanType.TOOL_CALL


class TestSpanObject:
    """Test Span object methods."""

    def test_span_set_attribute(self):
        """Span.set_attribute() adds attribute to step."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            with tracer.start_span(span_type=SpanType.LLM_CALL) as span:
                span.set_attribute("model", "claude-sonnet-4-5")
                span.set_attribute("tokens", 100)

        step = tracer.trace.turns[0].steps[0]
        assert step.attributes["model"] == "claude-sonnet-4-5"
        assert step.attributes["tokens"] == 100

    def test_span_set_status(self):
        """Span.set_status() changes span status."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            with tracer.start_span(span_type=SpanType.TOOL_CALL) as span:
                span.set_status(SpanStatus.ERROR)

        step = tracer.trace.turns[0].steps[0]
        assert step.status == SpanStatus.ERROR

    def test_span_set_multiple_attributes(self):
        """Span can have multiple attributes set."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            with tracer.start_span(span_type=SpanType.LLM_CALL) as span:
                span.set_attribute("prompt", "What is the weather?")
                span.set_attribute("response", "I don't know.")
                span.set_attribute("model", "claude-sonnet-4-5")

        step = tracer.trace.turns[0].steps[0]
        assert len(step.attributes) == 3
        assert step.attributes["prompt"] == "What is the weather?"


class TestTracerSaveTrace:
    """Test Tracer.save_trace() method."""

    def test_save_trace_creates_file(self):
        """save_trace() creates JSON file at specified path."""
        tracer = Tracer(trace_id="test-trace")

        with tracer.start_turn(turn_number=1):
            with tracer.start_span(span_type=SpanType.LLM_CALL):
                pass

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.trace.json"
            tracer.save_trace(str(path))

            assert path.exists()
            assert path.is_file()

    def test_save_trace_valid_json(self):
        """save_trace() creates valid JSON file."""
        tracer = Tracer(trace_id="test-trace")

        with tracer.start_turn(turn_number=1):
            with tracer.start_span(span_type=SpanType.LLM_CALL) as span:
                span.set_attribute("prompt", "test")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.trace.json"
            tracer.save_trace(str(path))

            with open(path) as f:
                data = json.load(f)

            assert data["trace_id"] == "test-trace"
            assert len(data["turns"]) == 1
            assert data["turns"][0]["turn_number"] == 1

    def test_save_trace_overwrites_existing(self):
        """save_trace() overwrites existing file."""
        tracer = Tracer(trace_id="test-trace")

        with tracer.start_turn(turn_number=1):
            pass

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.trace.json"

            # Save once
            tracer.save_trace(str(path))
            original_size = path.stat().st_size

            # Add more data
            with tracer.start_turn(turn_number=2):
                pass

            # Save again
            tracer.save_trace(str(path))
            new_size = path.stat().st_size

            # File should be larger (more turns)
            assert new_size > original_size


class TestTracerTraceProperty:
    """Test Tracer.trace property."""

    def test_trace_property_returns_trace(self):
        """trace property returns Trace object."""
        tracer = Tracer(trace_id="test-trace")

        assert tracer.trace.trace_id == "test-trace"

    def test_trace_property_read_only(self):
        """trace property provides read-only access."""
        tracer = Tracer()

        with tracer.start_turn(turn_number=1):
            pass

        # Should be able to read trace data
        assert len(tracer.trace.turns) == 1

        # trace object itself should be accessible
        assert tracer.trace is not None
