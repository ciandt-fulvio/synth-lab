"""
Data models for trace visualizer.

This module defines the core entities for recording and visualizing LLM conversation traces:
- SpanType: Semantic types for span classification
- SpanStatus: Execution status for spans
- Step: Individual operation within a turn
- Turn: Conversation iteration (user input → processing → output)
- Trace: Complete conversation session

References:
- OpenTelemetry span model: https://opentelemetry.io/docs/concepts/signals/traces/
- JSON schema defined in: specs/008-trace-visualizer/data-model.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class SpanType(str, Enum):
    """Semantic types for spans to enable color-coded visualization."""

    LLM_CALL = "llm_call"  # LLM API invocation (Blue)
    TOOL_CALL = "tool_call"  # Tool/function execution (Green)
    TURN = "turn"  # Conversation iteration
    ERROR = "error"  # Failed operation (Red)
    LOGIC = "logic"  # Business logic execution (Yellow)


class SpanStatus(str, Enum):
    """Execution status for spans."""

    SUCCESS = "success"  # Operation completed successfully
    ERROR = "error"  # Operation failed
    PENDING = "pending"  # Operation in progress (rare, for async ops)


@dataclass
class Step:
    """
    Individual operation within a turn (LLM call, tool call, logic).

    Represents atomic span in trace hierarchy.

    Sample input:
    ```python
    Step(
        span_id="step-001",
        type=SpanType.LLM_CALL,
        start_time=datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2025, 12, 17, 10, 0, 3, tzinfo=timezone.utc),
        duration_ms=3000,
        status=SpanStatus.SUCCESS,
        attributes={"prompt": "test", "response": "result"}
    )
    ```

    Expected output (to_dict):
    ```json
    {
      "span_id": "step-001",
      "type": "llm_call",
      "start_time": "2025-12-17T10:00:00+00:00",
      "end_time": "2025-12-17T10:00:03+00:00",
      "duration_ms": 3000,
      "status": "success",
      "attributes": {"prompt": "test", "response": "result"}
    }
    ```
    """

    span_id: str
    type: SpanType
    start_time: datetime
    end_time: datetime
    duration_ms: int
    status: SpanStatus
    attributes: Dict[str, Any]

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "span_id": self.span_id,
            "type": self.type.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "attributes": self.attributes,
        }


@dataclass
class Turn:
    """
    Conversation iteration (user input → processing → output).

    First-class concept between Trace and Step levels.

    Sample input:
    ```python
    Turn(
        turn_id="turn-001",
        turn_number=1,
        start_time=datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2025, 12, 17, 10, 2, 15, tzinfo=timezone.utc),
        duration_ms=135000,
        steps=[step1, step2]
    )
    ```

    Expected output (to_dict):
    ```json
    {
      "turn_id": "turn-001",
      "turn_number": 1,
      "start_time": "2025-12-17T10:00:00+00:00",
      "end_time": "2025-12-17T10:02:15+00:00",
      "duration_ms": 135000,
      "steps": [{...}, {...}]
    }
    ```
    """

    turn_id: str
    turn_number: int
    start_time: datetime
    end_time: datetime
    duration_ms: int
    steps: List[Step]

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "turn_id": self.turn_id,
            "turn_number": self.turn_number,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass
class Trace:
    """
    Complete conversation session (root span).

    Contains metadata and ordered list of turns.

    Sample input:
    ```python
    Trace(
        trace_id="trace-001",
        start_time=datetime(2025, 12, 17, 10, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2025, 12, 17, 10, 5, 30, tzinfo=timezone.utc),
        duration_ms=330000,
        turns=[turn1, turn2],
        metadata={"user_id": "user-123"}
    )
    ```

    Expected output (to_dict):
    ```json
    {
      "trace_id": "trace-001",
      "start_time": "2025-12-17T10:00:00+00:00",
      "end_time": "2025-12-17T10:05:30+00:00",
      "duration_ms": 330000,
      "turns": [{...}, {...}],
      "metadata": {"user_id": "user-123"}
    }
    ```
    """

    trace_id: str
    start_time: datetime
    end_time: datetime
    duration_ms: int
    turns: List[Turn]
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "trace_id": self.trace_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "turns": [turn.to_dict() for turn in self.turns],
            "metadata": self.metadata,
        }
