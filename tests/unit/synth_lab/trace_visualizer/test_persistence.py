"""
Unit tests for persistence layer (JSON save/load).

Tests validate:
- save_trace() creates valid JSON files
- load_trace() deserializes JSON back to Trace objects
- Roundtrip: save → load → identical trace
- Error handling for corrupted/missing files
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from synth_lab.trace_visualizer.models import (
    SpanStatus,
    SpanType,
    Step,
    Trace,
    Turn,
)
from synth_lab.trace_visualizer.persistence import load_trace, save_trace


class TestSaveTrace:
    """Test save_trace() function."""

    def test_save_trace_creates_file(self):
        """save_trace() creates JSON file at specified path."""
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

        turn = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=end,
            duration_ms=3000,
            steps=[step],
        )

        trace = Trace(
            trace_id="trace-001",
            start_time=start,
            end_time=end,
            duration_ms=3000,
            turns=[turn],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.trace.json"
            save_trace(trace, str(path))

            assert path.exists()
            assert path.is_file()

    def test_save_trace_valid_json_structure(self):
        """save_trace() creates valid JSON with correct structure."""
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

        turn = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=end,
            duration_ms=3000,
            steps=[step],
        )

        trace = Trace(
            trace_id="trace-001",
            start_time=start,
            end_time=end,
            duration_ms=3000,
            turns=[turn],
            metadata={"user_id": "user-123"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.trace.json"
            save_trace(trace, str(path))

            with open(path) as f:
                data = json.load(f)

            assert data["trace_id"] == "trace-001"
            assert data["start_time"] == "2025-12-17T10:00:00+00:00"
            assert data["end_time"] == "2025-12-17T10:00:03+00:00"
            assert data["duration_ms"] == 3000
            assert len(data["turns"]) == 1
            assert data["turns"][0]["turn_id"] == "turn-001"
            assert data["turns"][0]["steps"][0]["span_id"] == "step-001"
            assert data["metadata"]["user_id"] == "user-123"

    def test_save_trace_creates_parent_directories(self):
        """save_trace() creates parent directories if they don't exist."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc)

        step = Step(
            span_id="step-001",
            type=SpanType.LLM_CALL,
            start_time=start,
            end_time=end,
            duration_ms=3000,
            status=SpanStatus.SUCCESS,
            attributes={},
        )

        turn = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=end,
            duration_ms=3000,
            steps=[step],
        )

        trace = Trace(
            trace_id="trace-001",
            start_time=start,
            end_time=end,
            duration_ms=3000,
            turns=[turn],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # Path with nested directories that don't exist
            path = Path(tmpdir) / "subdir" / "nested" / "test.trace.json"
            save_trace(trace, str(path))

            assert path.exists()
            assert path.parent.exists()

    def test_save_trace_overwrites_existing(self):
        """save_trace() overwrites existing file."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc)

        step = Step(
            span_id="step-001",
            type=SpanType.LLM_CALL,
            start_time=start,
            end_time=end,
            duration_ms=3000,
            status=SpanStatus.SUCCESS,
            attributes={},
        )

        turn1 = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=end,
            duration_ms=3000,
            steps=[step],
        )

        trace1 = Trace(
            trace_id="trace-001",
            start_time=start,
            end_time=end,
            duration_ms=3000,
            turns=[turn1],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.trace.json"

            # Save first trace
            save_trace(trace1, str(path))

            # Create second trace with more data
            turn2 = Turn(
                turn_id="turn-002",
                turn_number=2,
                start_time=start,
                end_time=end,
                duration_ms=3000,
                steps=[step],
            )

            trace2 = Trace(
                trace_id="trace-002",
                start_time=start,
                end_time=end,
                duration_ms=6000,
                turns=[turn1, turn2],
            )

            # Save second trace (overwrite)
            save_trace(trace2, str(path))

            # Load and verify it's the second trace
            with open(path) as f:
                data = json.load(f)

            assert data["trace_id"] == "trace-002"
            assert len(data["turns"]) == 2


class TestLoadTrace:
    """Test load_trace() function."""

    def test_load_trace_from_file(self):
        """load_trace() deserializes JSON file to Trace object."""
        # Create and save a trace
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

        turn = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=end,
            duration_ms=3000,
            steps=[step],
        )

        original_trace = Trace(
            trace_id="trace-001",
            start_time=start,
            end_time=end,
            duration_ms=3000,
            turns=[turn],
            metadata={"user_id": "user-123"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.trace.json"
            save_trace(original_trace, str(path))

            # Load the trace
            loaded_trace = load_trace(str(path))

            assert loaded_trace.trace_id == "trace-001"
            assert loaded_trace.duration_ms == 3000
            assert len(loaded_trace.turns) == 1
            assert loaded_trace.turns[0].turn_id == "turn-001"
            assert loaded_trace.metadata["user_id"] == "user-123"

    def test_load_trace_preserves_all_fields(self):
        """load_trace() preserves all trace fields."""
        start = datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 12, 17, 10, 0, 5, tzinfo=timezone.utc)

        step1 = Step(
            span_id="step-001",
            type=SpanType.LLM_CALL,
            start_time=start,
            end_time=datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc),
            duration_ms=3000,
            status=SpanStatus.SUCCESS,
            attributes={"prompt": "test", "model": "claude"},
        )

        step2 = Step(
            span_id="step-002",
            type=SpanType.TOOL_CALL,
            start_time=datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc),
            end_time=end,
            duration_ms=2000,
            status=SpanStatus.SUCCESS,
            attributes={"tool_name": "get_weather"},
        )

        turn = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=end,
            duration_ms=5000,
            steps=[step1, step2],
        )

        original_trace = Trace(
            trace_id="trace-001",
            start_time=start,
            end_time=end,
            duration_ms=5000,
            turns=[turn],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.trace.json"
            save_trace(original_trace, str(path))

            loaded_trace = load_trace(str(path))

            # Verify all fields preserved
            turn = loaded_trace.turns[0]
            assert len(turn.steps) == 2
            assert turn.steps[0].type == SpanType.LLM_CALL
            assert turn.steps[0].attributes["prompt"] == "test"
            assert turn.steps[1].type == SpanType.TOOL_CALL
            assert turn.steps[1].attributes["tool_name"] == "get_weather"

    def test_load_trace_roundtrip(self):
        """Roundtrip: save → load → save → load produces identical trace."""
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

        turn = Turn(
            turn_id="turn-001",
            turn_number=1,
            start_time=start,
            end_time=end,
            duration_ms=3000,
            steps=[step],
        )

        original_trace = Trace(
            trace_id="trace-001",
            start_time=start,
            end_time=end,
            duration_ms=3000,
            turns=[turn],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path1 = Path(tmpdir) / "test1.trace.json"
            path2 = Path(tmpdir) / "test2.trace.json"

            # Save → Load → Save → Load
            save_trace(original_trace, str(path1))
            loaded_trace1 = load_trace(str(path1))
            save_trace(loaded_trace1, str(path2))
            loaded_trace2 = load_trace(str(path2))

            # Compare JSON representations
            with open(path1) as f1, open(path2) as f2:
                data1 = json.load(f1)
                data2 = json.load(f2)

            assert data1 == data2

    def test_load_trace_missing_file(self):
        """load_trace() raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_trace("/nonexistent/path/trace.json")

    def test_load_trace_invalid_json(self):
        """load_trace() raises JSONDecodeError for invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "invalid.json"
            path.write_text("not valid json {")

            with pytest.raises(json.JSONDecodeError):
                load_trace(str(path))
