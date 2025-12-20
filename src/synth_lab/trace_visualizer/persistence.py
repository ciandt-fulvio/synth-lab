"""
Persistence layer for trace storage and retrieval.

Provides functions to save and load traces as JSON files.
JSON format is self-contained, portable, and versionable.

References:
- JSON schema: specs/008-trace-visualizer/data-model.md
- File format spec: specs/008-trace-visualizer/data-model.md#file-naming-convention

Sample usage:
```python
from synth_lab.trace_visualizer import Tracer
from synth_lab.trace_visualizer.persistence import save_trace, load_trace

# Save trace
tracer = Tracer()
# ... record traces ...
save_trace(tracer.trace, "output/traces/weather.trace.json")

# Load trace
trace = load_trace("output/traces/weather.trace.json")
print(f"Loaded trace: {trace.trace_id}")
```
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .models import SpanStatus, SpanType, Step, Trace, Turn


def save_trace(trace: Trace, path: str) -> None:
    """
    Save trace to JSON file.

    Creates parent directories if they don't exist.
    Overwrites existing file.

    Args:
        trace: Trace object to save
        path: Output file path (recommend .trace.json extension)

    Example:
        save_trace(trace, "output/traces/conv-123.trace.json")

    Raises:
        OSError: If file cannot be written (permissions, disk full, etc.)
    """
    file_path = Path(path)

    # Create parent directories if needed
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert trace to JSON-serializable dict
    data = trace.to_dict()

    # Write JSON file with pretty formatting
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_trace(path: str) -> Trace:
    """
    Load trace from JSON file.

    Deserializes JSON back to Trace object with all entities.

    Args:
        path: Path to .trace.json file

    Returns:
        Trace object reconstructed from JSON

    Example:
        trace = load_trace("output/traces/conv-123.trace.json")
        print(f"Trace has {len(trace.turns)} turns")

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        ValueError: If JSON structure is invalid
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Trace file not found: {path}")

    # Load JSON data
    with open(file_path) as f:
        data = json.load(f)

    # Deserialize to Trace object
    return _deserialize_trace(data)


def _deserialize_trace(data: Dict[str, Any]) -> Trace:
    """
    Deserialize JSON dict to Trace object.

    Internal helper function.

    Args:
        data: JSON dict from trace file

    Returns:
        Trace object

    Raises:
        ValueError: If required fields are missing or invalid
    """
    try:
        # Deserialize turns
        turns = [_deserialize_turn(turn_data) for turn_data in data["turns"]]

        # Create Trace object
        trace = Trace(
            trace_id=data["trace_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            duration_ms=data["duration_ms"],
            turns=turns,
            metadata=data.get("metadata", {}),
        )

        return trace

    except KeyError as e:
        raise ValueError(f"Invalid trace JSON: missing field {e}")
    except ValueError as e:
        raise ValueError(f"Invalid trace JSON: {e}")


def _deserialize_turn(data: Dict[str, Any]) -> Turn:
    """
    Deserialize JSON dict to Turn object.

    Internal helper function.

    Args:
        data: JSON dict for turn

    Returns:
        Turn object

    Raises:
        ValueError: If required fields are missing or invalid
    """
    try:
        # Deserialize steps
        steps = [_deserialize_step(step_data) for step_data in data["steps"]]

        # Create Turn object
        turn = Turn(
            turn_id=data["turn_id"],
            turn_number=data["turn_number"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            duration_ms=data["duration_ms"],
            steps=steps,
        )

        return turn

    except KeyError as e:
        raise ValueError(f"Invalid turn JSON: missing field {e}")
    except ValueError as e:
        raise ValueError(f"Invalid turn JSON: {e}")


def _deserialize_step(data: Dict[str, Any]) -> Step:
    """
    Deserialize JSON dict to Step object.

    Internal helper function.

    Args:
        data: JSON dict for step

    Returns:
        Step object

    Raises:
        ValueError: If required fields are missing or invalid
    """
    try:
        # Create Step object
        step = Step(
            span_id=data["span_id"],
            type=SpanType(data["type"]),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            duration_ms=data["duration_ms"],
            status=SpanStatus(data["status"]),
            attributes=data["attributes"],
        )

        return step

    except KeyError as e:
        raise ValueError(f"Invalid step JSON: missing field {e}")
    except ValueError as e:
        raise ValueError(f"Invalid step JSON: {e}")
