# API Contract: Trace Visualizer SDK

**Feature**: 008-trace-visualizer | **Date**: 2025-12-17 | **Phase**: 1 (Design)

## Overview

This document defines the public API surface of the trace visualizer Python SDK.

**Stability**: Experimental (MVP) - API may change before 1.0

**Dependencies**: Python 3.13+, stdlib only

---

## Public API Surface

### Module: `synth_lab.trace_visualizer`

**Import**:
```python
from synth_lab.trace_visualizer import Tracer
```

**Exports**:
- `Tracer` (class)
- `SpanType` (enum) - Optional, for type hints
- `SpanStatus` (enum) - Optional, for type hints

---

## Class: `Tracer`

**Purpose**: Main interface for recording conversation traces.

### Constructor

```python
Tracer(
    trace_id: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> Tracer
```

**Parameters**:
| Name | Type | Required | Description | Default |
|------|------|----------|-------------|---------|
| `trace_id` | `str` | No | Unique trace identifier | Auto-generated UUID |
| `metadata` | `Dict[str, str]` | No | Custom metadata for trace | `{}` |

**Returns**: `Tracer` instance

**Example**:
```python
# Auto-generated trace_id
tracer = Tracer()

# Custom trace_id
tracer = Tracer(trace_id="conv-weather-123")

# With metadata
tracer = Tracer(
    trace_id="conv-123",
    metadata={"user_id": "user-456", "session": "abc"}
)
```

**Raises**:
- `ValueError`: If `trace_id` is empty string

---

### Method: `start_turn`

```python
start_turn(turn_number: int) -> ContextManager[None]
```

**Purpose**: Start a new conversation turn (iteration).

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `turn_number` | `int` | Yes | Sequential turn number (1-indexed) |

**Returns**: Context manager (use with `with` statement)

**Usage**:
```python
with tracer.start_turn(turn_number=1):
    # Record steps within turn
    pass
```

**Behavior**:
- Records `start_time` on entry
- Records `end_time` on exit
- Calculates `duration_ms` automatically
- Generates `turn_id` (UUID)

**Raises**:
- `ValueError`: If `turn_number < 1`
- `RuntimeError`: If turn is started inside another turn (no nesting)

**Invariants**:
- Turns must be sequential (turn 2 cannot start before turn 1 exits)
- At least one step must be recorded within turn

---

### Method: `start_span`

```python
start_span(
    span_type: Union[str, SpanType],
    attributes: Optional[Dict[str, Any]] = None
) -> ContextManager[Span]
```

**Purpose**: Start a new span (step) within current turn.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `span_type` | `str` or `SpanType` | Yes | Span type: `"llm_call"`, `"tool_call"`, `"logic"`, `"error"` |
| `attributes` | `Dict[str, Any]` | No | Initial span attributes | `{}` |

**Returns**: Context manager yielding `Span` object

**Usage**:
```python
with tracer.start_span(
    span_type="llm_call",
    attributes={"prompt": "...", "model": "..."}
) as span:
    # Perform operation
    span.set_attribute("response", "...")
    span.set_status("success")
```

**Behavior**:
- Records `start_time` on entry
- Records `end_time` on exit
- Calculates `duration_ms` automatically
- Generates `span_id` (UUID)
- Default status: `"success"` (can be overridden with `span.set_status()`)

**Raises**:
- `ValueError`: If `span_type` is invalid
- `RuntimeError`: If called outside `start_turn()` context

**Valid Span Types**:
- `"llm_call"`: LLM API invocation
- `"tool_call"`: Tool/function execution
- `"logic"`: Business logic operation
- `"error"`: Explicit error span

---

### Span Object API

The `Span` object returned by `start_span()` has these methods:

#### `set_attribute(key: str, value: Any) -> None`

**Purpose**: Add or update span attribute.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `key` | `str` | Yes | Attribute name |
| `value` | `Any` | Yes | Attribute value (JSON-serializable) |

**Usage**:
```python
with tracer.start_span("llm_call", attributes={"prompt": "..."}) as span:
    response = call_llm()
    span.set_attribute("response", response)
    span.set_attribute("tokens_output", 42)
```

**Raises**:
- `TypeError`: If `value` is not JSON-serializable

---

#### `set_status(status: Union[str, SpanStatus]) -> None`

**Purpose**: Set span execution status.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | `str` or `SpanStatus` | Yes | Status: `"success"`, `"error"`, `"pending"` |

**Usage**:
```python
with tracer.start_span("tool_call", attributes={...}) as span:
    try:
        result = call_tool()
        span.set_attribute("result", result)
        span.set_status("success")
    except Exception as e:
        span.set_attribute("error_message", str(e))
        span.set_status("error")
```

**Raises**:
- `ValueError`: If status is invalid

**Valid Statuses**:
- `"success"`: Operation completed successfully
- `"error"`: Operation failed
- `"pending"`: Operation in progress (rare, use for async operations)

---

### Method: `save_trace`

```python
save_trace(path: Union[str, Path]) -> None
```

**Purpose**: Save trace to JSON file.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `str` or `Path` | Yes | Output file path (`.trace.json` recommended) |

**Usage**:
```python
tracer.save_trace("data/traces/weather-demo.trace.json")
```

**Behavior**:
- Serializes trace to JSON (see [data-model.md](../data-model.md))
- Creates parent directories if needed
- Overwrites existing file

**Raises**:
- `RuntimeError`: If no turns recorded (trace is empty)
- `OSError`: If file cannot be written (permissions, disk full, etc.)

**File Format**: See [data-model.md](../data-model.md#complete-json-schema-example)

---

### Property: `trace`

```python
@property
trace() -> Trace
```

**Purpose**: Access underlying `Trace` object (read-only).

**Returns**: `Trace` dataclass with trace data

**Usage**:
```python
tracer = Tracer()
# ... record turns and spans ...

print(f"Trace ID: {tracer.trace.trace_id}")
print(f"Duration: {tracer.trace.duration_ms}ms")
print(f"Turns: {len(tracer.trace.turns)}")
```

**Use Cases**:
- Inspect trace metadata before saving
- Debug trace structure
- Calculate statistics (total duration, step count, etc.)

---

## Enums

### `SpanType`

```python
from enum import Enum

class SpanType(str, Enum):
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    LOGIC = "logic"
    ERROR = "error"
```

**Usage**:
```python
from synth_lab.trace_visualizer import Tracer, SpanType

with tracer.start_span(span_type=SpanType.LLM_CALL, attributes={...}):
    pass
```

---

### `SpanStatus`

```python
from enum import Enum

class SpanStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
```

**Usage**:
```python
from synth_lab.trace_visualizer import Tracer, SpanStatus

with tracer.start_span("tool_call", attributes={...}) as span:
    span.set_status(SpanStatus.SUCCESS)
```

---

## Usage Patterns

### Pattern 1: Basic Conversation

```python
tracer = Tracer(trace_id="conv-123")

with tracer.start_turn(turn_number=1):
    with tracer.start_span("llm_call", attributes={
        "prompt": "Hello",
        "model": "claude-sonnet-4-5"
    }) as span:
        span.set_attribute("response", "Hi there!")

tracer.save_trace("trace.json")
```

---

### Pattern 2: Multi-Turn with Tool Calls

```python
tracer = Tracer()

# Turn 1: Initial query
with tracer.start_turn(turn_number=1):
    with tracer.start_span("llm_call", attributes={...}) as span:
        span.set_attribute("response", "Let me check.")

    with tracer.start_span("tool_call", attributes={
        "tool_name": "get_weather",
        "arguments": {"city": "Paris"}
    }) as span:
        result = get_weather("Paris")
        span.set_attribute("result", result)
        span.set_status("success")

# Turn 2: Follow-up query
with tracer.start_turn(turn_number=2):
    with tracer.start_span("llm_call", attributes={...}) as span:
        span.set_attribute("response", "...")

tracer.save_trace("multi-turn.trace.json")
```

---

### Pattern 3: Error Handling

```python
tracer = Tracer()

with tracer.start_turn(turn_number=1):
    try:
        with tracer.start_span("tool_call", attributes={
            "tool_name": "get_data"
        }) as span:
            result = risky_operation()
            span.set_attribute("result", result)
            span.set_status("success")
    except Exception as e:
        with tracer.start_span("error", attributes={
            "error_type": type(e).__name__,
            "error_message": str(e)
        }):
            pass

tracer.save_trace("error-trace.trace.json")
```

---

### Pattern 4: Metadata and Inspection

```python
tracer = Tracer(
    trace_id="debug-session",
    metadata={"user_id": "user-123", "env": "dev"}
)

with tracer.start_turn(turn_number=1):
    with tracer.start_span("llm_call", attributes={...}):
        pass

# Inspect before saving
print(f"Trace ID: {tracer.trace.trace_id}")
print(f"Metadata: {tracer.trace.metadata}")
print(f"Duration: {tracer.trace.duration_ms}ms")

if tracer.trace.duration_ms > 5000:
    print("⚠️ Slow trace detected!")

tracer.save_trace("debug.trace.json")
```

---

## Type Hints

Full type signature for `Tracer`:

```python
from typing import Optional, Dict, Any, ContextManager
from pathlib import Path
from datetime import datetime

class Tracer:
    def __init__(
        self,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> None: ...

    def start_turn(self, turn_number: int) -> ContextManager[None]: ...

    def start_span(
        self,
        span_type: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> ContextManager['Span']: ...

    def save_trace(self, path: str | Path) -> None: ...

    @property
    def trace(self) -> 'Trace': ...


class Span:
    def set_attribute(self, key: str, value: Any) -> None: ...
    def set_status(self, status: str) -> None: ...
```

---

## Error Reference

| Exception | Trigger | Mitigation |
|-----------|---------|------------|
| `ValueError` | Invalid `span_type` or `status` | Use valid types from enum |
| `RuntimeError` | `start_span()` outside `start_turn()` | Always wrap spans in turn |
| `RuntimeError` | Nested turns | Complete turn before starting next |
| `RuntimeError` | Save empty trace (no turns) | Record at least one turn |
| `OSError` | Cannot write file | Check permissions, disk space |
| `TypeError` | Non-serializable attribute value | Use JSON-compatible types |

---

## Backward Compatibility

**Version**: 1.0 (MVP)

**Guarantees**:
- API surface is stable for 1.x releases
- JSON schema will not break (may add optional fields)
- Existing traces will load in future versions

**Breaking Changes** (require 2.0):
- Removing methods
- Changing required parameters
- Changing JSON schema structure (not just adding fields)

---

## Testing Contract

All SDK methods MUST have:
1. Unit tests (pytest)
2. Type hint coverage
3. Docstrings with examples

**Test Coverage Target**: >90% line coverage for SDK modules.

---

## Future API Extensions (Phase 2+)

Potential additions (NOT in MVP):

```python
# Load existing trace
tracer = Tracer.load_trace("trace.json")

# Export to OTel format
tracer.export_otel("otel.json")

# Merge traces
merged = Tracer.merge([tracer1, tracer2])

# Filter spans
filtered = tracer.filter_spans(lambda s: s.type == "llm_call")
```

**Status**: Not implemented in MVP. Subject to design review.
