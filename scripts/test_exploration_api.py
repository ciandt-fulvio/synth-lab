#!/usr/bin/env python3
"""
Test script for exploration API.

Usage:
    uv run python scripts/test_exploration_api.py
"""

import sys
import time

import httpx

BASE_URL = "http://localhost:8000"
TIMEOUT = 120.0


def main():
    client = httpx.Client(base_url=BASE_URL, timeout=TIMEOUT)

    print("=" * 60)
    print("EXPLORATION API TEST")
    print("=" * 60)

    # 1. Get experiment with scorecard
    print("\n[1] Finding experiment with scorecard...")
    resp = client.get("/experiments/list")
    resp.raise_for_status()

    experiments = resp.json()["data"]
    experiment = next((e for e in experiments if e.get("has_scorecard")), None)

    if not experiment:
        print("  ERROR: No experiment with scorecard")
        return 1

    experiment_id = experiment["id"]
    print(f"  Using: {experiment['name']} ({experiment_id})")

    # 2. Create exploration
    print("\n[2] Creating exploration...")
    resp = client.post("/explorations", json={
        "experiment_id": experiment_id,
        "goal_type": "min_success_rate",
        "goal_value": 0.60,
        "max_depth": 5,
        "beam_width": 4,
    })
    resp.raise_for_status()

    exploration_id = resp.json()["id"]
    print(f"  Created: {exploration_id}")

    # 3. Run exploration
    print("\n[3] Starting exploration...")
    resp = client.post(f"/explorations/{exploration_id}/run")
    resp.raise_for_status()
    print("  Started in background")

    # 4. Poll until done
    print("\n[4] Waiting for completion...")
    for i in range(60):
        time.sleep(5)
        resp = client.get(f"/explorations/{exploration_id}")
        resp.raise_for_status()

        data = resp.json()
        status = data["status"]
        depth = data.get("current_depth", 0)
        best = data.get("best_success_rate") or 0

        print(f"  [{i+1}] status={status} depth={depth} best={best:.2%}")

        if status not in ["pending", "running"]:
            break

    # 5. Show tree
    print("\n[5] Exploration tree:")
    resp = client.get(f"/explorations/{exploration_id}/tree")
    resp.raise_for_status()

    nodes = resp.json().get("nodes", [])
    actions = []

    for node in sorted(nodes, key=lambda n: (n["depth"], n["id"])):
        d = node["depth"]
        action = node.get("short_action") or "(root)"
        success = node.get("simulation_results", {}).get("success_rate", 0)
        status = node.get("node_status", "?")

        print(f"  {'  ' * d}[D{d}] {action} - {success:.2%} ({status})")

        if node.get("short_action"):
            actions.append(node["short_action"])

    # 6. Check diversity
    print("\n[6] Diversity check:")
    unique = set(actions)
    print(f"  Actions: {len(actions)}, Unique: {len(unique)}")

    if actions:
        ratio = len(unique) / len(actions)
        print(f"  Diversity: {ratio:.0%}")

        for a in sorted(unique):
            print(f"    - {a} (x{actions.count(a)})")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except httpx.ConnectError:
        print("ERROR: Backend not running on localhost:8000")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
