"""
Trace Visualizer - Mini-Jaeger Local for LLM Conversations.

Public API for recording and visualizing multi-turn LLM conversation traces.

Example usage:
```python
from synth_lab.trace_visualizer import Tracer, SpanType, SpanStatus

tracer = Tracer(trace_id="conv-weather")

with tracer.start_turn(turn_number=1):
    with tracer.start_span(
        span_type=SpanType.LLM_CALL,
        attributes={"prompt": "What is the weather?", "model": "claude-sonnet-4-5"}
    ) as span:
        response = "I don't have access to weather data."
        span.set_attribute("response", response)
        span.set_status(SpanStatus.SUCCESS)

tracer.save_trace("data/traces/weather.trace.json")
```

For more examples, see: examples/trace_visualizer/
For documentation, see: specs/008-trace-visualizer/quickstart.md
"""

from .tracer import Tracer, Span
from .models import SpanType, SpanStatus, Trace, Turn, Step
from .persistence import save_trace, load_trace

__all__ = [
    "Tracer",
    "Span",
    "SpanType",
    "SpanStatus",
    "Trace",
    "Turn",
    "Step",
    "save_trace",
    "load_trace",
]
