"""
Bridge between OpenAI Agents SDK tracing and synth_lab trace_visualizer.

This module provides a custom TracingProcessor that captures all events from
the OpenAI Agents SDK and records them to our trace_visualizer format for
unified visualization and debugging.

References:
- OpenAI Agents SDK Tracing: https://openai.github.io/openai-agents-python/tracing/
- Trace Visualizer: src/synth_lab/trace_visualizer/

Sample usage:
```python
from agents import add_trace_processor
from .tracing_bridge import TraceVisualizerProcessor

# Create processor with our tracer
processor = TraceVisualizerProcessor(tracer)
add_trace_processor(processor)

# Now all agent runs will be captured in trace_visualizer format
```
"""

from typing import Any

from agents.tracing import Span, Trace, TracingProcessor
from loguru import logger

from synth_lab.trace_visualizer import SpanStatus, SpanType, Tracer


class TraceVisualizerProcessor(TracingProcessor):
    """
    Custom tracing processor that bridges OpenAI Agents SDK traces to trace_visualizer.

    Captures all trace and span events from the Agents SDK and records them
    using the trace_visualizer Tracer API.

    Sample input:
    ```python
    tracer = Tracer(trace_id="interview-001")
    processor = TraceVisualizerProcessor(tracer, turn_number=1)
    ```

    Expected behavior:
    - on_trace_start: Logs trace metadata
    - on_span_start: Creates corresponding span in trace_visualizer
    - on_span_end: Records span results and timing
    - on_trace_end: Finalizes trace data
    """

    def __init__(
        self,
        tracer: Tracer,
        turn_number: int = 1,
        verbose: bool = True,
    ):
        """
        Initialize the processor.

        Args:
            tracer: trace_visualizer Tracer instance to record to
            turn_number: Current turn number in the conversation
            verbose: Whether to log detailed trace information
        """
        self._tracer = tracer
        self._turn_number = turn_number
        self._verbose = verbose
        self._active_spans: dict[str, Any] = {}  # Track SDK spans to our spans
        self._turn_context_active = False

    def set_turn_number(self, turn_number: int) -> None:
        """Update the current turn number."""
        self._turn_number = turn_number

    def on_trace_start(self, trace: Trace) -> None:
        """
        Called when a new trace begins execution.

        Args:
            trace: The trace that started
        """
        if self._verbose:
            logger.debug(f"[TraceVisualizerProcessor] Trace started: {trace.name}")
            logger.debug(f"  trace_id: {trace.trace_id}")
            if hasattr(trace, 'metadata') and trace.metadata:
                logger.debug(f"  metadata: {trace.metadata}")

    def on_trace_end(self, trace: Trace) -> None:
        """
        Called when a trace completes execution.

        Args:
            trace: The completed trace
        """
        if self._verbose:
            logger.debug(f"[TraceVisualizerProcessor] Trace ended: {trace.name}")

    def on_span_start(self, span: Span[Any]) -> None:
        """
        Called when a new span begins execution.

        Args:
            span: The span that started
        """
        span_type_name = type(span.span_data).__name__ if hasattr(span, 'span_data') else 'unknown'

        if self._verbose:
            logger.debug(f"[TraceVisualizerProcessor] Span started: {span_type_name}")

            # Log span details
            if hasattr(span, 'span_data'):
                span_data = span.span_data
                for key in dir(span_data):
                    if not key.startswith('_'):
                        try:
                            value = getattr(span_data, key)
                            if not callable(value):
                                # Truncate long values for logging
                                str_value = str(value)
                                if len(str_value) > 200:
                                    str_value = str_value[:200] + "..."
                                logger.debug(f"    {key}: {str_value}")
                        except Exception:
                            pass

        # Check if this is a tool call span and log/persist it
        if self._is_tool_span(span):
            self._handle_tool_span_start(span)

    def on_span_end(self, span: Span[Any]) -> None:
        """
        Called when a span completes execution.

        Args:
            span: The completed span
        """
        span_type_name = type(span.span_data).__name__ if hasattr(span, 'span_data') else 'unknown'

        if self._verbose:
            logger.debug(f"[TraceVisualizerProcessor] Span ended: {span_type_name}")

            # Log span results
            if hasattr(span, 'span_data'):
                span_data = span.span_data
                if hasattr(span_data, 'output'):
                    output = str(span_data.output)
                    if len(output) > 300:
                        output = output[:300] + "..."
                    logger.debug(f"    output: {output}")

        # Handle tool span completion
        if self._is_tool_span(span):
            self._handle_tool_span_end(span)

    def _is_tool_span(self, span: Span[Any]) -> bool:
        """Check if the span is a tool/function call span."""
        if not hasattr(span, 'span_data'):
            return False
        span_data_type = type(span.span_data).__name__.lower()
        return 'function' in span_data_type or 'tool' in span_data_type

    def _handle_tool_span_start(self, span: Span[Any]) -> None:
        """
        Handle the start of a tool call span.

        Logs the tool call and creates a span in our tracer.
        """
        span_data = span.span_data
        span_id = id(span)

        # Extract tool information
        tool_name = getattr(span_data, 'name', 'unknown_tool')
        tool_input = getattr(span_data, 'input', None)

        # Log tool call (always, not just verbose)
        logger.info(f"[Tool Call] {tool_name} started")
        if tool_input:
            input_str = str(tool_input)
            if len(input_str) > 500:
                input_str = input_str[:500] + "..."
            logger.debug(f"[Tool Call] {tool_name} input: {input_str}")

        # Create span in our tracer if we have an active turn
        if self._tracer._current_turn is not None:
            tracer_span = self._tracer.start_span(
                SpanType.TOOL_CALL,
                attributes={
                    "tool_name": tool_name,
                    "input": str(tool_input) if tool_input else None,
                    "sdk_span_type": type(span_data).__name__,
                },
            )
            # Enter the context manager
            tracer_span.__enter__()
            self._active_spans[span_id] = tracer_span

    def _handle_tool_span_end(self, span: Span[Any]) -> None:
        """
        Handle the completion of a tool call span.

        Logs the result and finalizes the tracer span.
        """
        span_data = span.span_data
        span_id = id(span)

        # Extract tool information
        tool_name = getattr(span_data, 'name', 'unknown_tool')
        tool_output = getattr(span_data, 'output', None)
        tool_error = getattr(span_data, 'error', None)

        # Log tool completion (always, not just verbose)
        if tool_error:
            logger.warning(f"[Tool Call] {tool_name} failed: {tool_error}")
        else:
            logger.info(f"[Tool Call] {tool_name} completed")
            if tool_output:
                output_str = str(tool_output)
                if len(output_str) > 500:
                    output_str = output_str[:500] + "..."
                logger.debug(f"[Tool Call] {tool_name} output: {output_str}")

        # Finalize the tracer span if we created one
        if span_id in self._active_spans:
            tracer_span = self._active_spans.pop(span_id)

            # Set output/error attributes
            if tool_output:
                output_str = str(tool_output)
                # Truncate very long outputs (like base64 images)
                if len(output_str) > 1000:
                    output_str = output_str[:1000] + f"... (truncated, {len(str(tool_output))} chars total)"
                tracer_span.set_attribute("output", output_str)

            if tool_error:
                tracer_span.set_attribute("error", str(tool_error))
                tracer_span.set_status(SpanStatus.ERROR)
            else:
                tracer_span.set_status(SpanStatus.SUCCESS)

            # Exit the context manager
            tracer_span.__exit__(None, None, None)

    def shutdown(self) -> None:
        """Called when the application stops."""
        if self._verbose:
            logger.debug("[TraceVisualizerProcessor] Shutting down")
        self._active_spans.clear()

    def force_flush(self) -> None:
        """Force processing of any queued items."""
        pass  # No buffering in this implementation


def extract_span_attributes(span: Span[Any]) -> dict[str, Any]:
    """
    Extract attributes from an OpenAI Agents SDK span for trace_visualizer.

    Args:
        span: The SDK span to extract attributes from

    Returns:
        Dictionary of attributes suitable for trace_visualizer
    """
    attributes: dict[str, Any] = {}

    if not hasattr(span, 'span_data'):
        return attributes

    span_data = span.span_data

    # Extract common attributes
    for key in ['name', 'input', 'output', 'error', 'model', 'agent_name']:
        if hasattr(span_data, key):
            value = getattr(span_data, key)
            if value is not None:
                # Ensure JSON-serializable
                try:
                    if isinstance(value, (str, int, float, bool, list, dict)):
                        attributes[key] = value
                    else:
                        attributes[key] = str(value)
                except Exception:
                    attributes[key] = repr(value)

    return attributes


def map_span_type(span: Span[Any]) -> SpanType:
    """
    Map OpenAI Agents SDK span type to trace_visualizer SpanType.

    Args:
        span: The SDK span

    Returns:
        Corresponding SpanType enum value
    """
    if not hasattr(span, 'span_data'):
        return SpanType.LOGIC

    span_data_type = type(span.span_data).__name__.lower()

    # Map known span types
    if 'llm' in span_data_type or 'generation' in span_data_type or 'model' in span_data_type:
        return SpanType.LLM_CALL
    elif 'tool' in span_data_type or 'function' in span_data_type:
        return SpanType.TOOL_CALL
    elif 'error' in span_data_type:
        return SpanType.ERROR
    else:
        return SpanType.LOGIC
