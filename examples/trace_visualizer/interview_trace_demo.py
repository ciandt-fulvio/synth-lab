#!/usr/bin/env python3
"""
Interview Trace Demo

This example demonstrates how the trace visualizer is integrated with the
research interview module. When you run an interview using:

    synthlab research <synth_id> <topic_guide_name>

The system automatically generates a trace file in data/traces/ that you can
visualize in the trace visualizer UI.

The trace captures:
- Each conversation round as a turn
- Each LLM call (interviewer and synth responses) as llm_call spans
- Each tool call (e.g., load_image_for_analysis) as tool_call spans
- Token usage and timing information

Usage:
    # Run this demo to see how traces are structured
    uv run examples/trace_visualizer/interview_trace_demo.py

    # Run a real interview (requires OPENAI_API_KEY)
    # synthlab research fhynws compra-amazon --max-rounds 2

    # Then visualize the generated trace:
    # 1. Open logui/index.html in browser
    # 2. Load the trace from data/traces/interview-{synth_id}-{session_id}.trace.json
"""

from synth_lab.trace_visualizer import Tracer, SpanType, SpanStatus
import time


def simulate_interview_trace():
    """
    Simulate a trace similar to what's generated during an actual interview.

    This shows the structure without making real API calls.
    """
    print("=== Interview Trace Demo ===\n")

    # Create tracer with metadata similar to real interview
    tracer = Tracer(
        trace_id="interview-demo-abc123",
        metadata={
            "synth_id": "fhynws",
            "session_id": "abc123",
            "topic_guide": "compra-amazon",
            "model": "gpt-5-mini",
            "synth_name": "João Lucas Barros",
        }
    )

    # Simulate Round 1: Interviewer asks question, synth responds
    print("Simulating Round 1...")
    with tracer.start_turn(turn_number=1):
        # Interviewer LLM call
        with tracer.start_span(SpanType.LLM_CALL, attributes={
            "prompt": "Starting interview...",
            "model": "gpt-5-mini",
            "speaker": "interviewer",
            "system_prompt": "You are a UX researcher conducting interviews...",
        }) as span:
            time.sleep(0.5)  # Simulate API latency
            span.set_attribute(
                "response", "Olá! Vamos conversar sobre sua experiência com compras online na Amazon.")
            span.set_attribute("tokens_input", 120)
            span.set_attribute("tokens_output", 45)
            span.set_status(SpanStatus.SUCCESS)

        # Synth LLM call
        with tracer.start_span(SpanType.LLM_CALL, attributes={
            "prompt": "Olá! Vamos conversar sobre sua experiência com compras online na Amazon.",
            "model": "gpt-5-mini",
            "speaker": "synth",
            "system_prompt": "You are João Lucas Barros, 85 years old...",
        }) as span:
            time.sleep(0.6)  # Simulate API latency
            span.set_attribute(
                "response", "Olá! Sim, eu uso a Amazon de vez em quando.")
            span.set_attribute("tokens_input", 150)
            span.set_attribute("tokens_output", 32)
            span.set_status(SpanStatus.SUCCESS)

    # Simulate Round 2: Tool call for loading image
    print("Simulating Round 2 (with image loading)...")
    with tracer.start_turn(turn_number=2):
        # Interviewer asks about a screen
        with tracer.start_span(SpanType.LLM_CALL, attributes={
            "prompt": "Olá! Sim, eu uso a Amazon de vez em quando.",
            "model": "gpt-5-mini",
            "speaker": "interviewer",
        }) as span:
            time.sleep(0.4)
            span.set_attribute(
                "response", "Você poderia descrever como você busca produtos?")
            span.set_attribute("tokens_input", 80)
            span.set_attribute("tokens_output", 28)
            span.set_status(SpanStatus.SUCCESS)

        # Tool call to load image
        with tracer.start_span(SpanType.TOOL_CALL, attributes={
            "tool_name": "load_image_for_analysis",
            "arguments": {"filename": "01_amazon_homepage.PNG"},
        }) as span:
            time.sleep(0.8)  # Simulate image loading
            span.set_attribute(
                "result", "Image loaded: 01_amazon_homepage.PNG (431935 bytes)")
            span.set_status(SpanStatus.SUCCESS)

        # Synth responds after seeing image
        with tracer.start_span(SpanType.LLM_CALL, attributes={
            "prompt": "Você poderia descrever como você busca produtos? [Image: homepage]",
            "model": "gpt-5-mini",
            "speaker": "synth",
        }) as span:
            time.sleep(0.7)
            span.set_attribute(
                "response", "Eu uso a barra de busca no topo da página.")
            span.set_attribute("tokens_input", 180)
            span.set_attribute("tokens_output", 35)
            span.set_status(SpanStatus.SUCCESS)

    # Simulate Round 3: Error scenario (tool call fails)
    print("Simulating Round 3 (with error)...")
    with tracer.start_turn(turn_number=3):
        # Interviewer asks to see another screen
        with tracer.start_span(SpanType.LLM_CALL, attributes={
            "prompt": "Eu uso a barra de busca no topo da página.",
            "model": "gpt-5-mini",
            "speaker": "interviewer",
        }) as span:
            time.sleep(0.3)
            span.set_attribute("response", "Podemos ver a tela de resultados?")
            span.set_attribute("tokens_input", 75)
            span.set_attribute("tokens_output", 22)
            span.set_status(SpanStatus.SUCCESS)

        # Tool call fails (image not found)
        with tracer.start_span(SpanType.TOOL_CALL, attributes={
            "tool_name": "load_image_for_analysis",
            "arguments": {"filename": "nonexistent_image.PNG"},
        }) as span:
            time.sleep(0.2)
            span.set_status(SpanStatus.ERROR)
            span.set_attribute(
                "error_message", "Image file 'nonexistent_image.PNG' not found")

        # Synth continues despite error
        with tracer.start_span(SpanType.LLM_CALL, attributes={
            "prompt": "Podemos ver a tela de resultados? [Error loading image]",
            "model": "gpt-5-mini",
            "speaker": "synth",
        }) as span:
            time.sleep(0.5)
            span.set_attribute(
                "response", "Desculpe, não consigo ver a tela agora.")
            span.set_attribute("tokens_input", 95)
            span.set_attribute("tokens_output", 18)
            span.set_status(SpanStatus.SUCCESS)

    # Save trace
    trace_path = "data/traces/interview_demo.trace.json"
    tracer.save_trace(trace_path)

    print(f"\n✅ Demo trace saved: {trace_path}")
    print(f"   Turns: {len(tracer.trace.turns)}")
    print(f"   Total spans: {sum(len(t.steps) for t in tracer.trace.turns)}")
    print(f"   Duration: {tracer.trace.duration_ms}ms")

    print("\n📊 To visualize:")
    print("   1. Open logui/index.html in browser")
    print("   2. Load data/traces/interview_demo.trace.json")
    print("   3. Click on spans to see details")

    print("\n💡 To generate a real interview trace:")
    print("   synthlab research fhynws compra-amazon --max-rounds 2")
    print("   (Trace will be saved to data/traces/interview-fhynws-*.trace.json)")


if __name__ == "__main__":
    simulate_interview_trace()
