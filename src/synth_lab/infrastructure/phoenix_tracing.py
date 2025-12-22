"""
Phoenix/OpenTelemetry tracing integration for synth-lab.

Provides LLM observability with automatic instrumentation of OpenAI SDK
and OpenAI Agents SDK calls. All traces are sent to a Phoenix collector
for visualization and analysis.

References:
- Arize Phoenix: https://docs.arize.com/phoenix
- OpenInference: https://github.com/Arize-ai/openinference
- OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/

Sample usage:
```python
from synth_lab.infrastructure.phoenix_tracing import setup_phoenix_tracing

# Enable tracing (call once at startup)
setup_phoenix_tracing(project_name="synth-lab")

# All OpenAI calls are now automatically traced
client = OpenAI()
response = client.chat.completions.create(...)
```

Expected output:
- Traces visible in Phoenix UI at http://localhost:6006
- Each LLM call shows: latency, tokens, prompts, responses
"""

import os
from typing import Any

from loguru import logger

# Global state for tracing
_tracer_provider: Any = None
_tracing_enabled: bool = False


def is_tracing_enabled() -> bool:
    """Check if Phoenix tracing is currently enabled."""
    return _tracing_enabled


def setup_phoenix_tracing(
    project_name: str = "synth-lab",
    endpoint: str | None = None,
    batch: bool = True,
) -> bool:
    """
    Configure Phoenix tracing for all OpenAI calls.

    This function instruments the OpenAI SDK and OpenAI Agents SDK
    to automatically capture all LLM calls and send traces to Phoenix.

    Args:
        project_name: Project name shown in Phoenix UI
        endpoint: Phoenix collector endpoint. Defaults to PHOENIX_COLLECTOR_ENDPOINT
                  env var or http://127.0.0.1:6006/v1/traces
        batch: Use batch processing for production (recommended)

    Returns:
        bool: True if tracing was successfully enabled, False otherwise

    Sample input:
        setup_phoenix_tracing(project_name="my-project")

    Expected output:
        True (tracing enabled)
        Logs: "Phoenix tracing enabled - Dashboard: http://localhost:6006"
    """
    global _tracer_provider, _tracing_enabled

    if _tracing_enabled:
        logger.debug("Phoenix tracing already enabled")
        return True

    # Get endpoint from env or use default
    endpoint = endpoint or os.getenv(
        "PHOENIX_COLLECTOR_ENDPOINT",
        "http://127.0.0.1:6006/v1/traces",
    )

    try:
        from openinference.instrumentation.openai import OpenAIInstrumentor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk import trace as trace_sdk
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

        # Configure resource with project name
        resource = Resource.create({"service.name": project_name})
        _tracer_provider = trace_sdk.TracerProvider(resource=resource)

        # Configure exporter
        exporter = OTLPSpanExporter(endpoint=endpoint)

        # Use batch or simple processor
        if batch:
            processor = BatchSpanProcessor(exporter)
        else:
            processor = SimpleSpanProcessor(exporter)

        _tracer_provider.add_span_processor(processor)

        # Instrument OpenAI SDK
        OpenAIInstrumentor().instrument(tracer_provider=_tracer_provider)
        logger.debug("OpenAI SDK instrumented")

        # Try to instrument OpenAI Agents SDK (optional)
        try:
            from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor

            OpenAIAgentsInstrumentor().instrument(tracer_provider=_tracer_provider)
            logger.debug("OpenAI Agents SDK instrumented")
        except ImportError:
            logger.debug("OpenAI Agents instrumentation not available")

        _tracing_enabled = True
        logger.info("Phoenix tracing enabled - Dashboard: http://localhost:6006")
        logger.debug(f"Traces sent to: {endpoint}")
        return True

    except ImportError as e:
        logger.warning(f"Phoenix tracing not available (missing dependency): {e}")
        return False
    except Exception as e:
        logger.warning(f"Failed to enable Phoenix tracing: {e}")
        return False


def setup_phoenix_auto(project_name: str = "synth-lab") -> bool:
    """
    Setup using phoenix-otel auto-instrumentation.

    This is a simpler alternative that uses Phoenix's built-in
    auto-instrumentation capabilities.

    Args:
        project_name: Project name shown in Phoenix UI

    Returns:
        bool: True if tracing was successfully enabled
    """
    global _tracing_enabled

    if _tracing_enabled:
        logger.debug("Phoenix tracing already enabled")
        return True

    try:
        from phoenix.otel import register

        register(
            auto_instrument=True,
            batch=True,
            project_name=project_name,
        )

        _tracing_enabled = True
        logger.info("Phoenix tracing enabled (auto) - Dashboard: http://localhost:6006")
        return True

    except ImportError as e:
        logger.warning(f"Phoenix auto-tracing not available: {e}")
        return False
    except Exception as e:
        logger.warning(f"Failed to enable Phoenix auto-tracing: {e}")
        return False


def shutdown_tracing() -> None:
    """
    Shutdown tracing and flush pending spans.

    Call this before application exit to ensure all traces are sent.
    """
    global _tracer_provider, _tracing_enabled

    if _tracer_provider is not None:
        try:
            _tracer_provider.shutdown()
            logger.debug("Phoenix tracing shutdown complete")
        except Exception as e:
            logger.warning(f"Error shutting down tracing: {e}")

    _tracer_provider = None
    _tracing_enabled = False


def maybe_setup_tracing() -> bool:
    """
    Setup tracing if PHOENIX_ENABLED environment variable is set.

    This is a convenience function for conditional tracing setup.
    Set PHOENIX_ENABLED=true to enable tracing.

    Returns:
        bool: True if tracing was enabled, False otherwise
    """
    if os.getenv("PHOENIX_ENABLED", "").lower() in ("true", "1", "yes"):
        project_name = os.getenv("PHOENIX_PROJECT_NAME", "synth-lab")
        return setup_phoenix_tracing(project_name=project_name)
    return False


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Initial state
    total_tests += 1
    if is_tracing_enabled():
        all_validation_failures.append("Tracing should be disabled initially")

    # Test 2: maybe_setup_tracing without env var
    total_tests += 1
    os.environ.pop("PHOENIX_ENABLED", None)
    result = maybe_setup_tracing()
    if result:
        all_validation_failures.append("maybe_setup_tracing should return False without env var")

    # Test 3: is_tracing_enabled still False
    total_tests += 1
    if is_tracing_enabled():
        all_validation_failures.append("Tracing should still be disabled")

    # Test 4: shutdown_tracing should not raise
    total_tests += 1
    try:
        shutdown_tracing()
    except Exception as e:
        all_validation_failures.append(f"shutdown_tracing raised: {e}")

    # Test 5: Module attributes exist
    total_tests += 1
    required_attrs = [
        "setup_phoenix_tracing",
        "setup_phoenix_auto",
        "shutdown_tracing",
        "maybe_setup_tracing",
        "is_tracing_enabled",
    ]
    for attr in required_attrs:
        if attr not in dir():
            all_validation_failures.append(f"Missing attribute: {attr}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
