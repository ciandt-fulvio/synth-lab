"""
Tracer SDK for recording LLM conversation traces.

This module provides the main API for instrumenting code to record traces:
- Tracer: Main class for recording conversation sessions
- Span: Context object for recording individual operations

References:
- OpenTelemetry Tracing API: https://opentelemetry.io/docs/concepts/signals/traces/
- API contract: specs/008-trace-visualizer/contracts/sdk-api.md

Sample usage:
```python
from synth_lab.trace_visualizer import Tracer, SpanType

tracer = Tracer(trace_id="conv-weather")

with tracer.start_turn(turn_number=1):
    with tracer.start_span(span_type=SpanType.LLM_CALL, attributes={
        "prompt": "What is the weather?",
        "model": "claude-sonnet-4-5"
    }) as span:
        response = call_llm()
        span.set_attribute("response", response)
        span.set_status("success")

tracer.save_trace("output/traces/weather.trace.json")
```
"""

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Generator
import uuid

from .models import Trace, Turn, Step, SpanType, SpanStatus


class Span:
    """
    Context object for recording span attributes and status.

    Yielded by Tracer.start_span() context manager.
    Provides methods to set attributes and status during span execution.
    """

    def __init__(self, step: Step):
        """Initialize span with reference to Step being recorded."""
        self._step = step

    def set_attribute(self, key: str, value: Any) -> None:
        """
        Add or update span attribute.

        Args:
            key: Attribute name
            value: Attribute value (must be JSON-serializable)

        Example:
            span.set_attribute("response", "The weather is sunny")
            span.set_attribute("tokens_output", 42)
        """
        self._step.attributes[key] = value

    def set_status(self, status: str | SpanStatus) -> None:
        """
        Set span execution status.

        Args:
            status: "success", "error", or "pending"

        Example:
            span.set_status("success")
            span.set_status(SpanStatus.ERROR)
        """
        if isinstance(status, str):
            self._step.status = SpanStatus(status)
        else:
            self._step.status = status


class Tracer:
    """
    Main interface for recording conversation traces.

    Manages trace lifecycle and provides context managers for recording
    turns and spans with automatic timestamp recording and duration calculation.

    Sample input:
    ```python
    tracer = Tracer(trace_id="conv-123", metadata={"user_id": "user-456"})

    with tracer.start_turn(turn_number=1):
        with tracer.start_span(SpanType.LLM_CALL, {"prompt": "test"}) as span:
            span.set_attribute("response", "result")

    tracer.save_trace("trace.json")
    ```

    Expected output:
    - Trace object with recorded turns and spans
    - JSON file at specified path
    """

    def __init__(
        self,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize tracer.

        Args:
            trace_id: Unique trace identifier (auto-generated if None)
            metadata: Optional trace metadata

        Example:
            tracer = Tracer()  # Auto-generate ID
            tracer = Tracer(trace_id="custom-id")
            tracer = Tracer(metadata={"user_id": "123"})
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        self._trace_id = trace_id
        self._metadata = metadata or {}
        self._turns: list[Turn] = []
        self._current_turn: Optional[Turn] = None
        self._trace_start_time: Optional[datetime] = None
        self._trace_end_time: Optional[datetime] = None

    @property
    def trace(self) -> Trace:
        """
        Access underlying Trace object (read-only).

        Returns:
            Trace object with current trace data

        Example:
            print(f"Trace ID: {tracer.trace.trace_id}")
            print(f"Duration: {tracer.trace.duration_ms}ms")
        """
        # Calculate trace timestamps and duration
        if self._turns:
            start_time = self._turns[0].start_time
            end_time = self._turns[-1].end_time
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
        else:
            # No turns yet - use current time
            now = datetime.now(timezone.utc)
            start_time = now
            end_time = now
            duration_ms = 0

        return Trace(
            trace_id=self._trace_id,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            turns=self._turns,
            metadata=self._metadata,
        )

    @contextmanager
    def start_turn(self, turn_number: int) -> Generator[None, None, None]:
        """
        Start a new conversation turn (context manager).

        Records start_time on entry, end_time on exit, calculates duration_ms.

        Args:
            turn_number: Sequential turn number (1-indexed)

        Yields:
            None

        Example:
            with tracer.start_turn(turn_number=1):
                # Record spans within turn
                pass

        Raises:
            ValueError: If turn_number < 1
            RuntimeError: If turn is started inside another turn
        """
        if turn_number < 1:
            raise ValueError("turn_number must be >= 1")

        if self._current_turn is not None:
            raise RuntimeError("Cannot nest turns - complete current turn first")

        # Generate turn_id
        turn_id = str(uuid.uuid4())

        # Record start time
        start_time = datetime.now(timezone.utc)

        # Create turn object (will be populated during context)
        turn = Turn(
            turn_id=turn_id,
            turn_number=turn_number,
            start_time=start_time,
            end_time=start_time,  # Will be updated on exit
            duration_ms=0,  # Will be calculated on exit
            steps=[],
        )

        self._current_turn = turn

        try:
            yield
        finally:
            # Record end time and calculate duration
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            turn.end_time = end_time
            turn.duration_ms = duration_ms

            # Add turn to trace
            self._turns.append(turn)
            self._current_turn = None

    @contextmanager
    def start_span(
        self,
        span_type: str | SpanType,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Generator[Span, None, None]:
        """
        Start a new span within current turn (context manager).

        Records start_time on entry, end_time on exit, calculates duration_ms.
        Yields Span object for attribute setting during execution.

        Args:
            span_type: Span type (llm_call, tool_call, logic, error)
            attributes: Initial span attributes

        Yields:
            Span object with set_attribute() and set_status() methods

        Example:
            with tracer.start_span(SpanType.LLM_CALL, {
                "prompt": "test",
                "model": "claude-sonnet-4-5"
            }) as span:
                response = call_llm()
                span.set_attribute("response", response)
                span.set_status("success")

        Raises:
            ValueError: If span_type is invalid
            RuntimeError: If called outside start_turn() context
        """
        if self._current_turn is None:
            raise RuntimeError("start_span() must be called within start_turn() context")

        # Convert string to enum if needed
        if isinstance(span_type, str):
            span_type = SpanType(span_type)

        # Generate span_id
        span_id = str(uuid.uuid4())

        # Record start time
        start_time = datetime.now(timezone.utc)

        # Create step object
        step = Step(
            span_id=span_id,
            type=span_type,
            start_time=start_time,
            end_time=start_time,  # Will be updated on exit
            duration_ms=0,  # Will be calculated on exit
            status=SpanStatus.SUCCESS,  # Default status
            attributes=attributes or {},
        )

        # Create Span wrapper
        span = Span(step)

        try:
            yield span
        finally:
            # Record end time and calculate duration
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            step.end_time = end_time
            step.duration_ms = duration_ms

            # Add step to current turn
            self._current_turn.steps.append(step)

    def save_trace(self, path: str) -> None:
        """
        Save trace to JSON file.

        Wrapper around persistence.save_trace() for convenience.

        Args:
            path: Output file path (.trace.json recommended)

        Example:
            tracer.save_trace("output/traces/weather.trace.json")

        Raises:
            RuntimeError: If no turns recorded (empty trace)
            OSError: If file cannot be written
        """
        from .persistence import save_trace

        if not self._turns:
            raise RuntimeError("Cannot save empty trace - record at least one turn")

        save_trace(self.trace, path)
