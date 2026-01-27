#!/usr/bin/env python3
"""
Test script for Causal Simulation System.

Runs through the complete simulation workflow to verify all features work.

Usage:
    # With backend running on localhost:8000
    uv run python scripts/test_causal_simulation.py

    # With custom base URL
    BASE_URL=http://localhost:8001 uv run python scripts/test_causal_simulation.py

References:
    - Spec: specs/035-causal-simulation/spec.md
    - API: src/synth_lab/api/routers/simulations.py
"""

import os
import sys
import time
import requests
from typing import Any

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_URL = f"{BASE_URL}/api"


def log(msg: str, level: str = "INFO") -> None:
    """Print formatted log message."""
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "ERROR": "\033[91m",
        "WARNING": "\033[93m",
    }
    reset = "\033[0m"
    print(f"{colors.get(level, '')}{level}: {msg}{reset}")


def api_call(
    method: str, endpoint: str, data: dict | None = None, expected_status: int = 200
) -> dict[str, Any] | None:
    """Make API call and return response."""
    url = f"{API_URL}{endpoint}"
    log(f"{method} {url}")

    try:
        if method == "GET":
            response = requests.get(url, timeout=120)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=120)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=120)
        elif method == "DELETE":
            response = requests.delete(url, timeout=120)
        else:
            raise ValueError(f"Unknown method: {method}")

        if response.status_code != expected_status:
            log(
                f"Expected {expected_status}, got {response.status_code}: {response.text}",
                "ERROR",
            )
            return None

        if response.status_code == 204:
            return {}

        return response.json()

    except requests.exceptions.ConnectionError:
        log(f"Could not connect to {BASE_URL}. Is the backend running?", "ERROR")
        return None
    except Exception as e:
        log(f"Request failed: {e}", "ERROR")
        return None


def test_create_simulation() -> str | None:
    """Test creating a simulation from a question."""
    log("=" * 60)
    log("TEST 1: Create Simulation from Question")
    log("=" * 60)

    data = {
        "question_text": "What will be the adoption rate for a new weekly meal subscription service targeting busy professionals in urban areas?",
        "n_worlds": 100,  # Use fewer worlds for faster testing
        "random_seed": 42,
    }

    result = api_call("POST", "/simulations", data, expected_status=201)

    if result:
        log(f"Created simulation: {result.get('id')}", "SUCCESS")
        log(f"Status: {result.get('status')}")
        log(f"Problem decomposition: {result.get('problem_decomposition')}")
        return result.get("id")

    return None


def test_get_simulation(simulation_id: str) -> bool:
    """Test getting simulation details."""
    log("=" * 60)
    log("TEST 2: Get Simulation Details")
    log("=" * 60)

    result = api_call("GET", f"/simulations/{simulation_id}")

    if result:
        log(f"Simulation status: {result.get('status')}", "SUCCESS")
        return True

    return False


def test_get_dag(simulation_id: str) -> bool:
    """Test getting the DAG for a simulation."""
    log("=" * 60)
    log("TEST 3: Get Causal DAG")
    log("=" * 60)

    result = api_call("GET", f"/dag/{simulation_id}")

    if result:
        nodes = result.get("nodes", [])
        edges = result.get("edges", [])
        log(f"DAG has {len(nodes)} nodes and {len(edges)} edges", "SUCCESS")
        log(f"Variables: {[n.get('name') for n in nodes[:5]]}...")
        return True

    return False


def test_get_hypotheses(simulation_id: str) -> bool:
    """Test getting hypotheses for a simulation."""
    log("=" * 60)
    log("TEST 4: Get Hypotheses")
    log("=" * 60)

    result = api_call("GET", f"/hypotheses/{simulation_id}")

    if result and isinstance(result, list):
        log(f"Found {len(result)} hypotheses", "SUCCESS")
        for h in result[:3]:
            log(f"  - {h.get('variable_name')}: {h.get('distribution_type')}")
        return True

    return False


def test_run_simulation(simulation_id: str) -> bool:
    """Test running a simulation."""
    log("=" * 60)
    log("TEST 5: Run Simulation")
    log("=" * 60)

    result = api_call("POST", f"/simulations/{simulation_id}/run")

    if result:
        log(f"Simulation completed!", "SUCCESS")
        log(f"Worlds generated: {result.get('n_worlds')}")
        log(f"Insights generated: {result.get('n_insights')}")
        log(f"Outcome distributions: {list(result.get('outcome_distributions', {}).keys())}")
        return True

    return False


def test_get_evidence(simulation_id: str) -> bool:
    """Test getting evidence for a simulation."""
    log("=" * 60)
    log("TEST 6: Get Evidence (Percentiles, Sensitivity, Failures, Clusters)")
    log("=" * 60)

    result = api_call("GET", f"/simulations/{simulation_id}/evidence")

    if result:
        log("Evidence retrieved!", "SUCCESS")
        log(f"Outcome distributions: {len(result.get('outcome_distributions', {}))}")
        log(f"Variance explained: {len(result.get('variance_explained', []))}")
        log(f"Failure modes: {len(result.get('failure_modes', []))}")
        log(f"Clusters: {len(result.get('clusters', []))}")
        return True

    return False


def test_get_insights(simulation_id: str) -> str | None:
    """Test getting insights for a simulation."""
    log("=" * 60)
    log("TEST 7: Get Insights")
    log("=" * 60)

    result = api_call("GET", f"/simulations/{simulation_id}/insights")

    if result and isinstance(result, list):
        log(f"Found {len(result)} insights", "SUCCESS")
        for ins in result[:3]:
            log(f"  - [{ins.get('insight_type')}] {ins.get('title')}")
        return result[0].get("id") if result else None

    return None


def test_get_insight_trace(insight_id: str) -> bool:
    """Test getting traceability for an insight."""
    log("=" * 60)
    log("TEST 8: Get Insight Traceability")
    log("=" * 60)

    result = api_call("GET", f"/insights/{insight_id}/trace")

    if result:
        log("Trace retrieved!", "SUCCESS")
        log(f"Statistical support: {list(result.get('statistical_support', {}).keys())}")
        log(f"Affected worlds: {len(result.get('affected_worlds', []))}")
        return True

    return False


def test_get_audit_trail(simulation_id: str) -> bool:
    """Test getting audit trail for a simulation."""
    log("=" * 60)
    log("TEST 9: Get Audit Trail")
    log("=" * 60)

    result = api_call("GET", f"/simulations/{simulation_id}/audit")

    if result:
        log("Audit trail retrieved!", "SUCCESS")
        log(f"Random seed: {result.get('random_seed')}")
        log(f"Worlds: {result.get('n_worlds')}")
        log(f"Hypotheses: {result.get('n_hypotheses')}")
        log(f"Insights: {result.get('n_insights')}")
        return True

    return False


def test_replay_simulation(simulation_id: str) -> bool:
    """Test replaying a simulation."""
    log("=" * 60)
    log("TEST 10: Replay Simulation")
    log("=" * 60)

    result = api_call("POST", f"/simulations/{simulation_id}/replay")

    if result:
        log("Replay completed!", "SUCCESS")
        log(f"Status: {result.get('status')}")
        log(f"Message: {result.get('message')}")
        return True

    return False


def test_export_audit(simulation_id: str) -> bool:
    """Test exporting audit trail."""
    log("=" * 60)
    log("TEST 11: Export Audit Trail")
    log("=" * 60)

    result = api_call("GET", f"/simulations/{simulation_id}/audit/export")

    if result:
        log("Audit export retrieved!", "SUCCESS")
        package = result.get("export_package", {})
        log(f"Export package keys: {list(package.keys())}")
        return True

    return False


def test_list_simulations() -> bool:
    """Test listing all simulations."""
    log("=" * 60)
    log("TEST 12: List Simulations")
    log("=" * 60)

    result = api_call("GET", "/simulations")

    if result and isinstance(result, list):
        log(f"Found {len(result)} simulations", "SUCCESS")
        return True

    return False


def test_delete_simulation(simulation_id: str) -> bool:
    """Test deleting a simulation."""
    log("=" * 60)
    log("TEST 13: Delete Simulation")
    log("=" * 60)

    result = api_call("DELETE", f"/simulations/{simulation_id}", expected_status=204)

    if result is not None:
        log("Simulation deleted!", "SUCCESS")
        return True

    return False


def main() -> int:
    """Run all tests."""
    log("=" * 60)
    log("CAUSAL SIMULATION SYSTEM - TEST SUITE")
    log(f"API Base URL: {API_URL}")
    log("=" * 60)

    # Track results
    passed = 0
    failed = 0
    tests_run = 0

    # Test health check
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            log("Backend health check failed. Is the server running?", "ERROR")
            return 1
        log("Backend is healthy!", "SUCCESS")
    except requests.exceptions.ConnectionError:
        log(f"Could not connect to {BASE_URL}. Start the backend first:", "ERROR")
        log("  uv run uvicorn synth_lab.api.main:app --reload", "WARNING")
        return 1

    # Run tests
    simulation_id = None
    insight_id = None

    # Test 1: Create simulation
    tests_run += 1
    simulation_id = test_create_simulation()
    if simulation_id:
        passed += 1
    else:
        failed += 1
        log("Cannot continue without simulation ID", "ERROR")
        return 1

    # Test 2: Get simulation
    tests_run += 1
    if test_get_simulation(simulation_id):
        passed += 1
    else:
        failed += 1

    # Test 3: Get DAG
    tests_run += 1
    if test_get_dag(simulation_id):
        passed += 1
    else:
        failed += 1

    # Test 4: Get hypotheses
    tests_run += 1
    if test_get_hypotheses(simulation_id):
        passed += 1
    else:
        failed += 1

    # Test 5: Run simulation
    tests_run += 1
    if test_run_simulation(simulation_id):
        passed += 1
    else:
        failed += 1

    # Test 6: Get evidence
    tests_run += 1
    if test_get_evidence(simulation_id):
        passed += 1
    else:
        failed += 1

    # Test 7: Get insights
    tests_run += 1
    insight_id = test_get_insights(simulation_id)
    if insight_id:
        passed += 1
    else:
        failed += 1

    # Test 8: Get insight trace
    if insight_id:
        tests_run += 1
        if test_get_insight_trace(insight_id):
            passed += 1
        else:
            failed += 1

    # Test 9: Get audit trail
    tests_run += 1
    if test_get_audit_trail(simulation_id):
        passed += 1
    else:
        failed += 1

    # Test 10: Replay simulation
    tests_run += 1
    if test_replay_simulation(simulation_id):
        passed += 1
    else:
        failed += 1

    # Test 11: Export audit
    tests_run += 1
    if test_export_audit(simulation_id):
        passed += 1
    else:
        failed += 1

    # Test 12: List simulations
    tests_run += 1
    if test_list_simulations():
        passed += 1
    else:
        failed += 1

    # Test 13: Delete simulation (cleanup)
    tests_run += 1
    if test_delete_simulation(simulation_id):
        passed += 1
    else:
        failed += 1

    # Summary
    log("=" * 60)
    log("TEST SUMMARY")
    log("=" * 60)
    log(f"Tests run: {tests_run}")
    log(f"Passed: {passed}", "SUCCESS" if passed == tests_run else "INFO")
    log(f"Failed: {failed}", "ERROR" if failed > 0 else "INFO")

    if failed == 0:
        log("ALL TESTS PASSED!", "SUCCESS")
        return 0
    else:
        log(f"{failed} TESTS FAILED!", "ERROR")
        return 1


if __name__ == "__main__":
    sys.exit(main())
