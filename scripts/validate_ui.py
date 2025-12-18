#!/usr/bin/env python3
"""
Automated UI Validation for Trace Visualizer

Validates what can be checked programmatically before manual BDD testing.
Does NOT replace manual testing - this only checks file integrity and data correctness.

Usage:
    uv run scripts/validate_ui.py
"""

import json
import sys
from pathlib import Path


def validate_file_exists(file_path: Path, description: str) -> bool:
    """Check if file exists and has content."""
    if not file_path.exists():
        print(f"❌ FAIL: {description} not found at {file_path}")
        return False

    size = file_path.stat().st_size
    if size == 0:
        print(f"❌ FAIL: {description} is empty (0 bytes)")
        return False

    print(f"✅ PASS: {description} exists ({size:,} bytes)")
    return True


def validate_json_structure(trace_path: Path) -> tuple[bool, dict]:
    """Validate trace JSON structure and return parsed data."""
    try:
        with open(trace_path) as f:
            trace = json.load(f)

        # Check required top-level fields
        required_fields = ["trace_id", "turns", "duration_ms"]
        for field in required_fields:
            if field not in trace:
                print(f"❌ FAIL: Missing required field '{field}' in trace")
                return False, {}

        # Check turns structure
        if not isinstance(trace["turns"], list):
            print("❌ FAIL: 'turns' must be an array")
            return False, {}

        turn_count = len(trace["turns"])
        if turn_count != 3:
            print(f"❌ FAIL: Expected 3 turns, found {turn_count}")
            return False, {}

        # Check each turn
        total_steps = 0
        for i, turn in enumerate(trace["turns"]):
            required_turn_fields = ["turn_id", "turn_number", "steps", "duration_ms"]
            for field in required_turn_fields:
                if field not in turn:
                    print(f"❌ FAIL: Turn {i+1} missing field '{field}'")
                    return False, {}

            if not isinstance(turn["steps"], list):
                print(f"❌ FAIL: Turn {i+1} steps must be an array")
                return False, {}

            total_steps += len(turn["steps"])

            # Check each step
            for j, step in enumerate(turn["steps"]):
                required_step_fields = ["span_id", "type", "status", "duration_ms"]
                for field in required_step_fields:
                    if field not in step:
                        print(f"❌ FAIL: Turn {i+1} Step {j+1} missing field '{field}'")
                        return False, {}

        print(f"✅ PASS: JSON structure valid ({turn_count} turns, {total_steps} steps)")
        return True, trace

    except json.JSONDecodeError as e:
        print(f"❌ FAIL: Invalid JSON - {e}")
        return False, {}
    except Exception as e:
        print(f"❌ FAIL: Error reading trace - {e}")
        return False, {}


def validate_trace_data(trace: dict) -> bool:
    """Validate trace data matches expected test values."""
    all_checks_passed = True

    # Check trace ID
    if trace["trace_id"] != "basic-conversation-demo":
        print(f"❌ FAIL: Expected trace_id 'basic-conversation-demo', got '{trace['trace_id']}'")
        all_checks_passed = False
    else:
        print("✅ PASS: Trace ID correct")

    # Check total duration
    if trace["duration_ms"] != 3137:
        print(f"❌ FAIL: Expected duration 3137ms, got {trace['duration_ms']}ms")
        all_checks_passed = False
    else:
        print("✅ PASS: Total duration correct (3137ms)")

    # Check turn count
    if len(trace["turns"]) != 3:
        print(f"❌ FAIL: Expected 3 turns, got {len(trace['turns'])}")
        all_checks_passed = False
    else:
        print("✅ PASS: Turn count correct (3 turns)")

    # Validate Turn 1 (should have 4 steps)
    turn1 = trace["turns"][0]
    if len(turn1["steps"]) != 4:
        print(f"❌ FAIL: Turn 1 should have 4 steps, has {len(turn1['steps'])}")
        all_checks_passed = False
    else:
        print("✅ PASS: Turn 1 has 4 steps")

    # Validate Turn 1 duration calculation
    turn1_step_sum = sum(step["duration_ms"] for step in turn1["steps"])
    turn1_duration = turn1["duration_ms"]
    variance = abs(turn1_step_sum - turn1_duration)

    if variance > 5:  # Allow 5ms variance
        print(f"❌ FAIL: Turn 1 duration mismatch - steps sum to {turn1_step_sum}ms, turn is {turn1_duration}ms (variance: {variance}ms)")
        all_checks_passed = False
    else:
        print(f"✅ PASS: Turn 1 duration sums correctly ({turn1_step_sum}ms ≈ {turn1_duration}ms, variance: {variance}ms)")

    # Find slowest step in Turn 1
    slowest_step = max(turn1["steps"], key=lambda s: s["duration_ms"])
    expected_slowest = {
        "type": "tool_call",
        "duration_ms": 1002,
        "tool_name": "get_weather"
    }

    if slowest_step["type"] != expected_slowest["type"]:
        print(f"❌ FAIL: Slowest step should be '{expected_slowest['type']}', is '{slowest_step['type']}'")
        all_checks_passed = False
    elif slowest_step["duration_ms"] != expected_slowest["duration_ms"]:
        print(f"❌ FAIL: Slowest step should be {expected_slowest['duration_ms']}ms, is {slowest_step['duration_ms']}ms")
        all_checks_passed = False
    else:
        print(f"✅ PASS: Slowest step correct (tool_call: get_weather, 1002ms)")

    # Check Turn 3 has error
    turn3 = trace["turns"][2]
    has_error = any(step["status"] == "error" for step in turn3["steps"])

    if not has_error:
        print("❌ FAIL: Turn 3 should contain at least one error step")
        all_checks_passed = False
    else:
        print("✅ PASS: Turn 3 contains error step")

    return all_checks_passed


def validate_html_references(html_path: Path) -> bool:
    """Check HTML file references to CSS and JS."""
    with open(html_path) as f:
        html_content = f.read()

    all_checks_passed = True

    # Check stylesheet reference
    if 'href="styles.css"' not in html_content:
        print("❌ FAIL: HTML missing reference to styles.css")
        all_checks_passed = False
    else:
        print("✅ PASS: HTML references styles.css")

    # Check JavaScript references
    if 'src="trace-renderer.js"' not in html_content:
        print("❌ FAIL: HTML missing reference to trace-renderer.js")
        all_checks_passed = False
    else:
        print("✅ PASS: HTML references trace-renderer.js")

    if 'src="waterfall.js"' not in html_content:
        print("❌ FAIL: HTML missing reference to waterfall.js")
        all_checks_passed = False
    else:
        print("✅ PASS: HTML references waterfall.js")

    # Check for required DOM elements
    required_ids = [
        "trace-file-input",
        "drop-zone",
        "waterfall-container",
        "trace-info",
        "error-message"
    ]

    for element_id in required_ids:
        if f'id="{element_id}"' not in html_content:
            print(f"❌ FAIL: HTML missing required element id='{element_id}'")
            all_checks_passed = False

    if all_checks_passed:
        print("✅ PASS: All required HTML elements present")

    return all_checks_passed


def main():
    """Run all automated validations."""
    print("=" * 70)
    print("AUTOMATED UI VALIDATION - Trace Visualizer")
    print("=" * 70)
    print()

    project_root = Path(__file__).parent.parent
    all_validations = []

    # Section 1: File Existence
    print("📁 FILE EXISTENCE CHECKS")
    print("-" * 70)

    files_to_check = [
        (project_root / "logui" / "index.html", "HTML file"),
        (project_root / "logui" / "styles.css", "CSS file"),
        (project_root / "logui" / "trace-renderer.js", "Trace renderer JS"),
        (project_root / "logui" / "waterfall.js", "Waterfall visualization JS"),
        (project_root / "data" / "traces" / "basic_conversation.trace.json", "Test trace file"),
    ]

    for file_path, description in files_to_check:
        all_validations.append(validate_file_exists(file_path, description))

    print()

    # Section 2: JSON Structure
    print("🔍 JSON STRUCTURE VALIDATION")
    print("-" * 70)

    trace_path = project_root / "data" / "traces" / "basic_conversation.trace.json"
    json_valid, trace_data = validate_json_structure(trace_path)
    all_validations.append(json_valid)

    print()

    # Section 3: Trace Data
    if json_valid:
        print("📊 TRACE DATA VALIDATION")
        print("-" * 70)

        data_valid = validate_trace_data(trace_data)
        all_validations.append(data_valid)

        print()

    # Section 4: HTML References
    print("🔗 HTML REFERENCE VALIDATION")
    print("-" * 70)

    html_path = project_root / "logui" / "index.html"
    html_valid = validate_html_references(html_path)
    all_validations.append(html_valid)

    print()

    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    total_checks = len(all_validations)
    passed_checks = sum(all_validations)
    failed_checks = total_checks - passed_checks

    print(f"Total checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {failed_checks}")
    print()

    if all(all_validations):
        print("✅ ALL AUTOMATED VALIDATIONS PASSED")
        print()
        print("Next Steps:")
        print("1. Open logui/index.html in browser")
        print("2. Load data/traces/basic_conversation.trace.json")
        print("3. Execute manual BDD tests T042-T044")
        print("4. Document results in docs/trace_visualizer/MANUAL_TEST_RESULTS.md")
        print()
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print()
        print("Fix the above issues before proceeding to manual BDD testing.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
