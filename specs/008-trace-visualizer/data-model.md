# Data Model: Mini-Jaeger Local para Conversas LLM Multi-turn

**Feature**: 008-trace-visualizer | **Date**: 2025-12-17 | **Phase**: 1 (Design)

## Entity Relationship Diagram

```
Trace (1)
  ├─ trace_id: UUID
  ├─ start_time: ISO 8601
  ├─ end_time: ISO 8601
  ├─ duration_ms: int
  └─ turns: List[Turn] (1..N)
        │
        Turn (N)
        ├─ turn_id: UUID
        ├─ turn_number: int (1-indexed)
        ├─ start_time: ISO 8601
        ├─ end_time: ISO 8601
        ├─ duration_ms: int
        └─ steps: List[Step] (1..N)
              │
              Step/Span (N)
              ├─ span_id: UUID
              ├─ type: SpanType enum
              ├─ start_time: ISO 8601
              ├─ end_time: ISO 8601
              ├─ duration_ms: int
              ├─ status: SpanStatus enum
              └─ attributes: Dict[str, Any]
```

**Cardinality**:
- 1 Trace : N Turns (minimum 1)
- 1 Turn : N Steps (minimum 1)
- Steps are flat (no nesting in MVP)

---

## Entity Definitions

### Trace

**Purpose**: Root entity representing entire conversation session.

**Attributes**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `trace_id` | UUID string | Yes | Unique trace identifier | `"550e8400-e29b-41d4-a716-446655440000"` |
| `start_time` | ISO 8601 string | Yes | Trace start timestamp | `"2025-12-17T10:00:00.000Z"` |
| `end_time` | ISO 8601 string | Yes | Trace end timestamp | `"2025-12-17T10:05:30.250Z"` |
| `duration_ms` | integer | Yes | Total duration in milliseconds | `330250` |
| `turns` | List[Turn] | Yes | Ordered list of turns | `[{...}, {...}]` |
| `metadata` | Dict[str, str] | No | Optional trace metadata | `{"conversation_id": "abc"}` |

**Invariants**:
- `end_time >= start_time`
- `duration_ms = (end_time - start_time) in milliseconds`
- `len(turns) >= 1` (at least one turn)
- Turns are ordered by `turn_number`

**Python Dataclass**:
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional

@dataclass
class Trace:
    trace_id: str
    start_time: datetime
    end_time: datetime
    duration_ms: int
    turns: List['Turn']
    metadata: Optional[Dict[str, str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "trace_id": self.trace_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "turns": [turn.to_dict() for turn in self.turns],
            "metadata": self.metadata
        }
```

---

### Turn

**Purpose**: First-class entity representing one iteration of conversation (user input → processing → output).

**Attributes**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `turn_id` | UUID string | Yes | Unique turn identifier | `"a1b2c3d4-..."` |
| `turn_number` | integer | Yes | Sequential turn number (1-indexed) | `1` |
| `start_time` | ISO 8601 string | Yes | Turn start timestamp | `"2025-12-17T10:00:00.000Z"` |
| `end_time` | ISO 8601 string | Yes | Turn end timestamp | `"2025-12-17T10:02:15.500Z"` |
| `duration_ms` | integer | Yes | Turn duration in milliseconds | `135500` |
| `steps` | List[Step] | Yes | Ordered list of steps within turn | `[{...}, {...}]` |

**Invariants**:
- `end_time >= start_time`
- `duration_ms = (end_time - start_time) in milliseconds`
- `len(steps) >= 1` (at least one step)
- `turn_number` starts at 1 and increments sequentially

**Python Dataclass**:
```python
@dataclass
class Turn:
    turn_id: str
    turn_number: int
    start_time: datetime
    end_time: datetime
    duration_ms: int
    steps: List['Step']

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "turn_id": self.turn_id,
            "turn_number": self.turn_number,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "steps": [step.to_dict() for step in self.steps]
        }
```

---

### Step (Span)

**Purpose**: Atomic operation within a turn (LLM call, tool call, logic execution).

**Attributes**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `span_id` | UUID string | Yes | Unique span identifier | `"x9y8z7w6-..."` |
| `type` | SpanType | Yes | Semantic span type | `"llm_call"` |
| `start_time` | ISO 8601 string | Yes | Span start timestamp | `"2025-12-17T10:00:01.000Z"` |
| `end_time` | ISO 8601 string | Yes | Span end timestamp | `"2025-12-17T10:00:04.250Z"` |
| `duration_ms` | integer | Yes | Span duration in milliseconds | `3250` |
| `status` | SpanStatus | Yes | Execution status | `"success"` |
| `attributes` | Dict[str, Any] | Yes | Type-specific metadata | `{"prompt": "...", "model": "..."}` |

**Invariants**:
- `end_time >= start_time`
- `duration_ms = (end_time - start_time) in milliseconds`
- `attributes` keys depend on `type` (see Attributes Schema below)

**Python Dataclass**:
```python
from enum import Enum

class SpanType(str, Enum):
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    TURN = "turn"
    ERROR = "error"
    LOGIC = "logic"

class SpanStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"

@dataclass
class Step:
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
            "attributes": self.attributes
        }
```

---

## Attributes Schema by Span Type

Attributes are type-specific and stored in `attributes` dict.

### `llm_call` Attributes

| Key | Type | Required | Description | Example |
|-----|------|----------|-------------|---------|
| `prompt` | string | Yes | User/system prompt | `"What is the weather?"` |
| `response` | string | Yes | LLM response | `"I don't have access to weather data."` |
| `model` | string | Yes | Model identifier | `"claude-sonnet-4-5"` |
| `tokens_input` | integer | No | Input token count | `15` |
| `tokens_output` | integer | No | Output token count | `32` |

**Example**:
```json
{
  "span_id": "abc-123",
  "type": "llm_call",
  "start_time": "2025-12-17T10:00:01.000Z",
  "end_time": "2025-12-17T10:00:04.250Z",
  "duration_ms": 3250,
  "status": "success",
  "attributes": {
    "prompt": "What is the weather in Paris?",
    "response": "I don't have access to real-time weather data.",
    "model": "claude-sonnet-4-5"
  }
}
```

---

### `tool_call` Attributes

| Key | Type | Required | Description | Example |
|-----|------|----------|-------------|---------|
| `tool_name` | string | Yes | Tool/function name | `"get_weather"` |
| `arguments` | object | Yes | Tool input arguments | `{"city": "Paris"}` |
| `result` | any | No | Tool output (if success) | `{"temp": 15, "condition": "cloudy"}` |
| `error_message` | string | No | Error message (if error) | `"API timeout"` |

**Example (Success)**:
```json
{
  "span_id": "def-456",
  "type": "tool_call",
  "start_time": "2025-12-17T10:00:05.000Z",
  "end_time": "2025-12-17T10:00:07.100Z",
  "duration_ms": 2100,
  "status": "success",
  "attributes": {
    "tool_name": "get_weather",
    "arguments": {"city": "Paris"},
    "result": {"temp": 15, "condition": "cloudy"}
  }
}
```

**Example (Error)**:
```json
{
  "span_id": "ghi-789",
  "type": "tool_call",
  "start_time": "2025-12-17T10:00:05.000Z",
  "end_time": "2025-12-17T10:00:06.000Z",
  "duration_ms": 1000,
  "status": "error",
  "attributes": {
    "tool_name": "get_weather",
    "arguments": {"city": "Paris"},
    "error_message": "API timeout after 1000ms"
  }
}
```

---

### `logic` Attributes

| Key | Type | Required | Description | Example |
|-----|------|----------|-------------|---------|
| `operation` | string | Yes | Operation description | `"Validate input format"` |
| `details` | object | No | Additional context | `{"valid": true}` |

**Example**:
```json
{
  "span_id": "jkl-012",
  "type": "logic",
  "start_time": "2025-12-17T10:00:00.500Z",
  "end_time": "2025-12-17T10:00:00.550Z",
  "duration_ms": 50,
  "status": "success",
  "attributes": {
    "operation": "Validate user input",
    "details": {"valid": true, "format": "text"}
  }
}
```

---

### `error` Attributes

| Key | Type | Required | Description | Example |
|-----|------|----------|-------------|---------|
| `error_type` | string | Yes | Error class/type | `"TimeoutError"` |
| `error_message` | string | Yes | Error description | `"Request timed out after 30s"` |
| `stack_trace` | string | No | Stack trace (if available) | `"Traceback (most recent call last)..."` |

**Example**:
```json
{
  "span_id": "mno-345",
  "type": "error",
  "start_time": "2025-12-17T10:00:08.000Z",
  "end_time": "2025-12-17T10:00:08.010Z",
  "duration_ms": 10,
  "status": "error",
  "attributes": {
    "error_type": "ValueError",
    "error_message": "Invalid temperature format",
    "stack_trace": "Traceback (most recent call last):\n  File ..."
  }
}
```

---

## Complete JSON Schema Example

```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_time": "2025-12-17T10:00:00.000Z",
  "end_time": "2025-12-17T10:05:30.250Z",
  "duration_ms": 330250,
  "turns": [
    {
      "turn_id": "a1b2c3d4-e5f6-4789-a1b2-c3d4e5f67890",
      "turn_number": 1,
      "start_time": "2025-12-17T10:00:00.000Z",
      "end_time": "2025-12-17T10:02:15.500Z",
      "duration_ms": 135500,
      "steps": [
        {
          "span_id": "step-001",
          "type": "logic",
          "start_time": "2025-12-17T10:00:00.000Z",
          "end_time": "2025-12-17T10:00:00.100Z",
          "duration_ms": 100,
          "status": "success",
          "attributes": {
            "operation": "Parse user input"
          }
        },
        {
          "span_id": "step-002",
          "type": "llm_call",
          "start_time": "2025-12-17T10:00:00.100Z",
          "end_time": "2025-12-17T10:00:03.500Z",
          "duration_ms": 3400,
          "status": "success",
          "attributes": {
            "prompt": "What is the weather in Paris?",
            "response": "Let me check the weather for you.",
            "model": "claude-sonnet-4-5"
          }
        },
        {
          "span_id": "step-003",
          "type": "tool_call",
          "start_time": "2025-12-17T10:00:03.500Z",
          "end_time": "2025-12-17T10:02:15.400Z",
          "duration_ms": 131900,
          "status": "success",
          "attributes": {
            "tool_name": "get_weather",
            "arguments": {"city": "Paris"},
            "result": {"temp": 15, "condition": "cloudy"}
          }
        },
        {
          "span_id": "step-004",
          "type": "llm_call",
          "start_time": "2025-12-17T10:02:15.400Z",
          "end_time": "2025-12-17T10:02:15.500Z",
          "duration_ms": 100,
          "status": "success",
          "attributes": {
            "prompt": "Format weather response",
            "response": "The weather in Paris is 15°C and cloudy.",
            "model": "claude-sonnet-4-5"
          }
        }
      ]
    },
    {
      "turn_id": "b2c3d4e5-f6a7-4890-b2c3-d4e5f6a78901",
      "turn_number": 2,
      "start_time": "2025-12-17T10:03:00.000Z",
      "end_time": "2025-12-17T10:05:30.250Z",
      "duration_ms": 150250,
      "steps": [
        {
          "span_id": "step-005",
          "type": "llm_call",
          "start_time": "2025-12-17T10:03:00.000Z",
          "end_time": "2025-12-17T10:05:30.250Z",
          "duration_ms": 150250,
          "status": "success",
          "attributes": {
            "prompt": "What about tomorrow?",
            "response": "I don't have access to forecast data.",
            "model": "claude-sonnet-4-5"
          }
        }
      ]
    }
  ],
  "metadata": {
    "conversation_id": "conv-12345",
    "user_id": "user-67890"
  }
}
```

---

## JSON Schema Validation

For schema validation, use the following JSON Schema (draft-07):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["trace_id", "start_time", "end_time", "duration_ms", "turns"],
  "properties": {
    "trace_id": {
      "type": "string",
      "format": "uuid"
    },
    "start_time": {
      "type": "string",
      "format": "date-time"
    },
    "end_time": {
      "type": "string",
      "format": "date-time"
    },
    "duration_ms": {
      "type": "integer",
      "minimum": 0
    },
    "turns": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["turn_id", "turn_number", "start_time", "end_time", "duration_ms", "steps"],
        "properties": {
          "turn_id": {"type": "string", "format": "uuid"},
          "turn_number": {"type": "integer", "minimum": 1},
          "start_time": {"type": "string", "format": "date-time"},
          "end_time": {"type": "string", "format": "date-time"},
          "duration_ms": {"type": "integer", "minimum": 0},
          "steps": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "required": ["span_id", "type", "start_time", "end_time", "duration_ms", "status", "attributes"],
              "properties": {
                "span_id": {"type": "string"},
                "type": {"type": "string", "enum": ["llm_call", "tool_call", "turn", "error", "logic"]},
                "start_time": {"type": "string", "format": "date-time"},
                "end_time": {"type": "string", "format": "date-time"},
                "duration_ms": {"type": "integer", "minimum": 0},
                "status": {"type": "string", "enum": ["success", "error", "pending"]},
                "attributes": {"type": "object"}
              }
            }
          }
        }
      }
    },
    "metadata": {
      "type": "object"
    }
  }
}
```

---

## File Naming Convention

**Format**: `<conversation_id>_<timestamp>.trace.json`

**Examples**:
- `conv-12345_20251217T100000Z.trace.json`
- `debug-session_20251217T153045Z.trace.json`
- `user-67890_turn-3_20251217T203000Z.trace.json`

**Storage Location**: `data/traces/` (configurable)

---

## Size Constraints

| Constraint | Target | Hard Limit | Mitigation |
|------------|--------|------------|------------|
| Max turns per trace | 20 | 50 | Split long conversations |
| Max steps per turn | 10 | 30 | Simplify workflow |
| Max file size | 1 MB | 5 MB | Warn in UI |
| Max prompt length | 10 KB | 100 KB | Truncate in UI (FR-006) |

---

## Version History

| Schema Version | Date | Changes |
|----------------|------|---------|
| 1.0 | 2025-12-17 | Initial schema for MVP |

**Future Versioning**: Add `"schema_version": "1.0"` field to root object in Phase 2+.
