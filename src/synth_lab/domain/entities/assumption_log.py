"""
Assumption log entities for synth-lab.

Defines models for audit logging of simulation activities.

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Data model: specs/016-feature-impact-simulation/data-model.md
"""

import secrets
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def generate_log_id() -> str:
    """Generate a log entry ID."""
    return f"log_{secrets.token_hex(4)}"


class LogEntry(BaseModel):
    """A single entry in the assumption log."""

    id: str = Field(
        default_factory=generate_log_id,
        description="Unique log entry identifier.",
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Entry timestamp.",
    )

    action: str = Field(
        description="Action type. Ex: 'create_scorecard', 'run_simulation', 'analyze_region'",
    )

    # References
    scorecard_id: str | None = Field(
        default=None,
        description="Related scorecard ID if applicable.",
    )

    simulation_id: str | None = Field(
        default=None,
        description="Related simulation ID if applicable.",
    )

    # Data
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional data for the entry. Ex: {'scorecard_version': '1.0.0'}",
    )

    # User
    user: str | None = Field(
        default=None,
        description="User who performed the action if applicable.",
    )


class AssumptionLog(BaseModel):
    """Historical record of decisions and actions."""

    entries: list[LogEntry] = Field(
        default_factory=list,
        description="List of log entries.",
    )

    def add_entry(
        self,
        action: str,
        scorecard_id: str | None = None,
        simulation_id: str | None = None,
        data: dict[str, Any] | None = None,
        user: str | None = None,
    ) -> LogEntry:
        """
        Add a new entry to the log.

        Args:
            action: The action being logged.
            scorecard_id: Related scorecard ID.
            simulation_id: Related simulation ID.
            data: Additional data for the entry.
            user: User performing the action.

        Returns:
            The created LogEntry.
        """
        entry = LogEntry(
            action=action,
            scorecard_id=scorecard_id,
            simulation_id=simulation_id,
            data=data or {},
            user=user,
        )
        self.entries.append(entry)
        return entry


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create valid LogEntry
    total_tests += 1
    try:
        entry = LogEntry(
            action="create_scorecard",
            scorecard_id="abc12345",
            data={"version": "1.0.0"},
            user="pm_joao",
        )
        if entry.action != "create_scorecard":
            all_validation_failures.append(f"action mismatch: {entry.action}")
        if entry.id is None or not entry.id.startswith("log_"):
            all_validation_failures.append(f"ID should start with log_: {entry.id}")
    except Exception as e:
        all_validation_failures.append(f"LogEntry creation failed: {e}")

    # Test 2: LogEntry timestamp default
    total_tests += 1
    try:
        entry = LogEntry(action="test")
        if entry.timestamp is None:
            all_validation_failures.append("timestamp should be set automatically")
    except Exception as e:
        all_validation_failures.append(f"timestamp default test failed: {e}")

    # Test 3: ID generation uniqueness
    total_tests += 1
    try:
        id1 = generate_log_id()
        id2 = generate_log_id()
        if id1 == id2:
            all_validation_failures.append("Generated IDs should be unique")
        if not id1.startswith("log_"):
            all_validation_failures.append(f"ID should start with log_: {id1}")
    except Exception as e:
        all_validation_failures.append(f"ID generation test failed: {e}")

    # Test 4: Create empty AssumptionLog
    total_tests += 1
    try:
        log = AssumptionLog()
        if len(log.entries) != 0:
            all_validation_failures.append("New log should be empty")
    except Exception as e:
        all_validation_failures.append(f"AssumptionLog creation failed: {e}")

    # Test 5: Add entry to log
    total_tests += 1
    try:
        log = AssumptionLog()
        entry = log.add_entry(
            action="run_simulation",
            simulation_id="sim_abc12345",
            data={"n_synths": 500},
        )
        if len(log.entries) != 1:
            all_validation_failures.append("Log should have 1 entry")
        if entry.action != "run_simulation":
            all_validation_failures.append(f"Entry action mismatch: {entry.action}")
    except Exception as e:
        all_validation_failures.append(f"add_entry test failed: {e}")

    # Test 6: Multiple entries
    total_tests += 1
    try:
        log = AssumptionLog()
        log.add_entry(action="action1")
        log.add_entry(action="action2")
        log.add_entry(action="action3")
        if len(log.entries) != 3:
            all_validation_failures.append(f"Log should have 3 entries: {len(log.entries)}")
    except Exception as e:
        all_validation_failures.append(f"Multiple entries test failed: {e}")

    # Test 7: Entry with all fields
    total_tests += 1
    try:
        entry = LogEntry(
            action="analyze_region",
            scorecard_id="sc_123",
            simulation_id="sim_456",
            data={"min_failure_rate": 0.5, "max_depth": 4},
            user="analyst_maria",
        )
        if entry.scorecard_id != "sc_123":
            all_validation_failures.append(f"scorecard_id mismatch: {entry.scorecard_id}")
        if entry.user != "analyst_maria":
            all_validation_failures.append(f"user mismatch: {entry.user}")
    except Exception as e:
        all_validation_failures.append(f"Full entry test failed: {e}")

    # Test 8: Model dump
    total_tests += 1
    try:
        log = AssumptionLog()
        log.add_entry(action="test", data={"key": "value"})
        dump = log.model_dump()
        if "entries" not in dump:
            all_validation_failures.append("model_dump missing entries")
        if len(dump["entries"]) != 1:
            all_validation_failures.append("model_dump entries count mismatch")
        if dump["entries"][0]["data"]["key"] != "value":
            all_validation_failures.append("model_dump data mismatch")
    except Exception as e:
        all_validation_failures.append(f"model_dump test failed: {e}")

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
