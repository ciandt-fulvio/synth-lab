#!/usr/bin/env python3
"""
Basic conversation example for trace visualizer.

Demonstrates multi-turn conversation recording with LLM calls and tool calls.
Generates a sample trace file that can be visualized in the browser.

Usage:
    uv run examples/trace_visualizer/basic_conversation.py

Output:
    data/traces/basic_conversation.trace.json

Next steps:
    1. Open logui/index.html in browser
    2. Load the generated trace file
    3. Explore waterfall visualization
"""

import time
from synth_lab.trace_visualizer import Tracer, SpanType, SpanStatus


def main():
    """Generate a basic multi-turn conversation trace."""
    print("🔧 Creating trace for basic weather conversation...")

    tracer = Tracer(
        trace_id="basic-conversation-demo",
        metadata={"user_id": "demo-user", "session": "example"}
    )

    # Turn 1: User asks about weather in Paris
    print("  📝 Recording Turn 1: Weather query for Paris")
    with tracer.start_turn(turn_number=1):
        # User input processing
        with tracer.start_span(
            span_type=SpanType.LOGIC,
            attributes={"operation": "Parse user input"}
        ) as span:
            time.sleep(0.01)  # Simulate processing
            span.set_attribute("input", "What is the weather in Paris?")
            span.set_status(SpanStatus.SUCCESS)

        # LLM call to understand intent
        with tracer.start_span(
            span_type=SpanType.LLM_CALL,
            attributes={
                "prompt": "What is the weather in Paris?",
                "model": "claude-sonnet-4-5"
            }
        ) as span:
            time.sleep(0.5)  # Simulate LLM latency
            response = "I'll check the weather in Paris for you."
            span.set_attribute("response", response)
            span.set_attribute("tokens_input", 8)
            span.set_attribute("tokens_output", 12)
            span.set_status(SpanStatus.SUCCESS)

        # Tool call to get weather
        with tracer.start_span(
            span_type=SpanType.TOOL_CALL,
            attributes={
                "tool_name": "get_weather",
                "arguments": {"city": "Paris", "units": "celsius"}
            }
        ) as span:
            time.sleep(1.0)  # Simulate API call
            result = {
                "temperature": 15,
                "condition": "cloudy",
                "humidity": 65
            }
            span.set_attribute("result", result)
            span.set_status(SpanStatus.SUCCESS)

        # LLM call to format response
        with tracer.start_span(
            span_type=SpanType.LLM_CALL,
            attributes={
                "prompt": "Format weather response for Paris: 15°C, cloudy",
                "model": "claude-sonnet-4-5"
            }
        ) as span:
            time.sleep(0.3)  # Simulate LLM latency
            response = "The weather in Paris is currently 15°C and cloudy with 65% humidity."
            span.set_attribute("response", response)
            span.set_attribute("tokens_input", 15)
            span.set_attribute("tokens_output", 20)
            span.set_status(SpanStatus.SUCCESS)

    # Turn 2: User asks about tomorrow's forecast
    print("  📝 Recording Turn 2: Forecast query")
    with tracer.start_turn(turn_number=2):
        # LLM call
        with tracer.start_span(
            span_type=SpanType.LLM_CALL,
            attributes={
                "prompt": "What about tomorrow?",
                "model": "claude-sonnet-4-5"
            }
        ) as span:
            time.sleep(0.4)  # Simulate LLM latency
            response = "I don't have access to forecast data, only current weather."
            span.set_attribute("response", response)
            span.set_attribute("tokens_input", 5)
            span.set_attribute("tokens_output", 15)
            span.set_status(SpanStatus.SUCCESS)

    # Turn 3: User asks about London
    print("  📝 Recording Turn 3: London query (with error)")
    with tracer.start_turn(turn_number=3):
        # LLM call
        with tracer.start_span(
            span_type=SpanType.LLM_CALL,
            attributes={
                "prompt": "How about London?",
                "model": "claude-sonnet-4-5"
            }
        ) as span:
            time.sleep(0.4)
            response = "Let me check London's weather."
            span.set_attribute("response", response)
            span.set_status(SpanStatus.SUCCESS)

        # Tool call with error
        with tracer.start_span(
            span_type=SpanType.TOOL_CALL,
            attributes={
                "tool_name": "get_weather",
                "arguments": {"city": "London"}
            }
        ) as span:
            time.sleep(0.5)  # Simulate API timeout
            span.set_status(SpanStatus.ERROR)
            span.set_attribute("error_message", "API timeout after 500ms")

        # Error span
        with tracer.start_span(
            span_type=SpanType.ERROR,
            attributes={
                "error_type": "APITimeoutError",
                "error_message": "Weather API did not respond in time"
            }
        ) as span:
            span.set_status(SpanStatus.ERROR)

    # Save trace
    output_path = "data/traces/basic_conversation.trace.json"
    tracer.save_trace(output_path)

    # Print summary
    trace = tracer.trace
    total_steps = sum(len(turn.steps) for turn in trace.turns)

    print(f"\n✅ Trace saved: {output_path}")
    print(f"   Trace ID: {trace.trace_id}")
    print(f"   Duration: {trace.duration_ms}ms")
    print(f"   Turns: {len(trace.turns)}")
    print(f"   Total steps: {total_steps}")
    print(f"\n📊 Next: Open logui/index.html and load the trace file!")


if __name__ == "__main__":
    main()
