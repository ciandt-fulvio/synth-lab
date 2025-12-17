#!/usr/bin/env python3
"""
Comprehensive Trace Demo

Generates a comprehensive trace with:
- 20 turns
- 50+ steps
- All span types (LLM calls, tool calls, logic, errors)
- Realistic timings and data
- Mix of successful and failed operations

Usage:
    uv run examples/trace_visualizer/comprehensive_demo.py
"""

import time
from synth_lab.trace_visualizer import Tracer, SpanType, SpanStatus


def simulate_comprehensive_conversation():
    """Simulate a comprehensive multi-turn conversation with all span types."""

    tracer = Tracer(
        trace_id="comprehensive-demo-trace",
        metadata={
            "user_id": "demo-user",
            "session_id": "comprehensive-session",
            "scenario": "full-featured-demo"
        }
    )

    # Turn 1: Research task with multiple LLM calls and tool usage
    with tracer.start_turn(turn_number=1):
        with tracer.start_span(SpanType.LOGIC, attributes={"operation": "Parse research query"}) as span:
            time.sleep(0.01)
            span.set_attribute("input", "Research the history of artificial intelligence")

        with tracer.start_span(SpanType.LLM_CALL, attributes={
            "prompt": "Break down this research query into searchable topics: 'Research the history of artificial intelligence'",
            "model": "claude-sonnet-4-5"
        }) as span:
            time.sleep(0.4)
            span.set_attribute("response", "I'll break this into: 1) Early AI foundations (1950s-1960s), 2) AI winters and revivals, 3) Modern deep learning era")
            span.set_attribute("tokens_input", 25)
            span.set_attribute("tokens_output", 42)

        with tracer.start_span(SpanType.TOOL_CALL, attributes={
            "tool_name": "web_search",
            "arguments": {"query": "AI history 1950s foundations", "max_results": 5}
        }) as span:
            time.sleep(0.8)
            span.set_attribute("result", {
                "sources": ["Turing Test 1950", "Dartmouth Conference 1956", "Perceptron 1958"],
                "summary": "Early AI focused on symbolic reasoning and problem-solving"
            })

    # Turn 2: Data analysis with error handling
    with tracer.start_turn(turn_number=2):
        with tracer.start_span(SpanType.TOOL_CALL, attributes={
            "tool_name": "load_dataset",
            "arguments": {"dataset_id": "ai_papers_historical"}
        }) as span:
            time.sleep(0.5)
            span.set_attribute("result", {
                "rows": 1500,
                "columns": ["year", "title", "author", "citations"]
            })

        with tracer.start_span(SpanType.LOGIC, attributes={"operation": "Filter data by decade"}) as span:
            time.sleep(0.02)
            span.set_attribute("input", {"decade": "1980s"})
            span.set_attribute("output", {"filtered_rows": 245})

        with tracer.start_span(SpanType.LLM_CALL, attributes={
            "prompt": "Analyze this dataset of 245 AI papers from the 1980s and identify key trends",
            "model": "claude-sonnet-4-5"
        }) as span:
            time.sleep(0.6)
            span.set_attribute("response", "The 1980s saw the rise of expert systems, neural network renaissance with backpropagation, and increased commercial AI applications")
            span.set_attribute("tokens_input", 312)
            span.set_attribute("tokens_output", 89)

    # Turn 3: Failed tool call (timeout)
    with tracer.start_turn(turn_number=3):
        with tracer.start_span(SpanType.LLM_CALL, attributes={
            "prompt": "Should I fetch real-time AI news data?",
            "model": "claude-sonnet-4-5"
        }) as span:
            time.sleep(0.3)
            span.set_attribute("response", "Yes, let me fetch the latest AI news")
            span.set_attribute("tokens_input", 15)
            span.set_attribute("tokens_output", 18)

        with tracer.start_span(SpanType.TOOL_CALL, attributes={
            "tool_name": "fetch_news_api",
            "arguments": {"topic": "artificial intelligence", "days": 7}
        }) as span:
            time.sleep(1.2)
            span.set_status(SpanStatus.ERROR)
            span.set_attribute("error_message", "API timeout after 1000ms")

        with tracer.start_span(SpanType.ERROR, attributes={
            "error_type": "APITimeoutError",
            "error_message": "News API did not respond within timeout period"
        }) as span:
            time.sleep(0.001)

    # Turn 4-10: Various operations showcasing all span types
    for turn_num in range(4, 11):
        with tracer.start_turn(turn_number=turn_num):
            # Logic step
            with tracer.start_span(SpanType.LOGIC, attributes={
                "operation": f"Process turn {turn_num}"
            }) as span:
                time.sleep(0.01)
                span.set_attribute("input", f"Turn {turn_num} data")
                span.set_attribute("output", f"Processed turn {turn_num}")

            # LLM call
            with tracer.start_span(SpanType.LLM_CALL, attributes={
                "prompt": f"Generate response for turn {turn_num}",
                "model": "claude-sonnet-4-5"
            }) as span:
                time.sleep(0.3 + (turn_num % 3) * 0.1)
                span.set_attribute("response", f"Response for turn {turn_num}")
                span.set_attribute("tokens_input", 20 + turn_num)
                span.set_attribute("tokens_output", 30 + turn_num * 2)

            # Occasional tool call
            if turn_num % 2 == 0:
                with tracer.start_span(SpanType.TOOL_CALL, attributes={
                    "tool_name": "database_query",
                    "arguments": {"query": f"SELECT * FROM data WHERE turn={turn_num}"}
                }) as span:
                    time.sleep(0.15)
                    span.set_attribute("result", {"rows": turn_num * 10})

    # Turn 11-15: Heavy computation and caching
    for turn_num in range(11, 16):
        with tracer.start_turn(turn_number=turn_num):
            with tracer.start_span(SpanType.LOGIC, attributes={
                "operation": "Check cache"
            }) as span:
                time.sleep(0.005)
                span.set_attribute("input", f"key_{turn_num}")
                span.set_attribute("output", "cache_miss" if turn_num % 3 == 0 else "cache_hit")

            if turn_num % 3 == 0:  # Cache miss
                with tracer.start_span(SpanType.TOOL_CALL, attributes={
                    "tool_name": "compute_expensive_operation",
                    "arguments": {"complexity": "high", "input_size": 1000}
                }) as span:
                    time.sleep(1.5)
                    span.set_attribute("result", {"computed_value": turn_num * 1000})

                with tracer.start_span(SpanType.LOGIC, attributes={
                    "operation": "Write to cache"
                }) as span:
                    time.sleep(0.01)
                    span.set_attribute("input", {"key": f"key_{turn_num}", "value": turn_num * 1000})

            with tracer.start_span(SpanType.LLM_CALL, attributes={
                "prompt": f"Summarize computation result for turn {turn_num}",
                "model": "claude-sonnet-4-5"
            }) as span:
                time.sleep(0.25)
                span.set_attribute("response", f"Computation complete for turn {turn_num}")
                span.set_attribute("tokens_input", 45)
                span.set_attribute("tokens_output", 25)

    # Turn 16-18: Error scenarios
    for turn_num in range(16, 19):
        with tracer.start_turn(turn_number=turn_num):
            with tracer.start_span(SpanType.LLM_CALL, attributes={
                "prompt": f"Attempt risky operation {turn_num}",
                "model": "claude-sonnet-4-5"
            }) as span:
                time.sleep(0.2)
                span.set_attribute("response", "Proceeding with operation")
                span.set_attribute("tokens_input", 10)
                span.set_attribute("tokens_output", 8)

            if turn_num == 17:  # Simulate validation error
                with tracer.start_span(SpanType.LOGIC, attributes={
                    "operation": "Validate input"
                }) as span:
                    time.sleep(0.01)
                    span.set_status(SpanStatus.ERROR)
                    span.set_attribute("error_message", "Invalid input format")

                with tracer.start_span(SpanType.ERROR, attributes={
                    "error_type": "ValidationError",
                    "error_message": "Input failed schema validation"
                }) as span:
                    time.sleep(0.001)
            else:
                with tracer.start_span(SpanType.LOGIC, attributes={
                    "operation": "Execute operation"
                }) as span:
                    time.sleep(0.02)
                    span.set_attribute("result", "success")

    # Turn 19-20: Final summary turns
    for turn_num in range(19, 21):
        with tracer.start_turn(turn_number=turn_num):
            with tracer.start_span(SpanType.TOOL_CALL, attributes={
                "tool_name": "aggregate_results",
                "arguments": {"turns": list(range(1, turn_num))}
            }) as span:
                time.sleep(0.4)
                span.set_attribute("result", {
                    "total_turns": turn_num,
                    "successful_operations": turn_num - 2,
                    "errors": 2
                })

            with tracer.start_span(SpanType.LLM_CALL, attributes={
                "prompt": """Summarize the entire conversation history covering AI research,
                data analysis, news fetching, computations, and error handling across 20 turns""",
                "model": "claude-sonnet-4-5"
            }) as span:
                time.sleep(0.8)
                long_response = """Based on our comprehensive analysis:

1. Historical Research: Successfully researched AI history from 1950s foundations through modern deep learning
2. Data Analysis: Analyzed 1500 historical AI papers, identified key trends in expert systems and neural networks
3. Real-time Data: Encountered API timeout when fetching current news (handled gracefully)
4. Computation: Performed cache-optimized expensive operations with 67% cache hit rate
5. Error Handling: Successfully handled 2 errors (API timeout, validation failure) without disrupting workflow

Overall: Processed 20 turns with 50+ distinct operations, demonstrating robust multi-turn conversation handling."""
                span.set_attribute("response", long_response)
                span.set_attribute("tokens_input", 89)
                span.set_attribute("tokens_output", 156)

            with tracer.start_span(SpanType.LOGIC, attributes={
                "operation": "Finalize trace"
            }) as span:
                time.sleep(0.005)
                span.set_attribute("status", "complete")

    # Save trace
    output_path = "data/traces/comprehensive_demo.trace.json"
    tracer.save_trace(output_path)

    print(f"✅ Comprehensive trace generated: {output_path}")
    print(f"   Turns: {len(tracer.trace.turns)}")

    total_steps = sum(len(turn.steps) for turn in tracer.trace.turns)
    print(f"   Steps: {total_steps}")
    print(f"   Duration: {tracer.trace.duration_ms}ms")

    # Count span types
    span_type_counts = {}
    for turn in tracer.trace.turns:
        for step in turn.steps:
            span_type_counts[step.type] = span_type_counts.get(step.type, 0) + 1

    print(f"\n   Span types:")
    for span_type, count in sorted(span_type_counts.items()):
        print(f"   - {span_type}: {count}")


if __name__ == "__main__":
    simulate_comprehensive_conversation()
