"""
Test script for executive summary v16 (markdown format).

Usage:
    uv run python scripts/test_executive_summary_v16.py <experiment_id>

Example:
    uv run python scripts/test_executive_summary_v16.py exp_12345678

Prerequisites:
    1. Experiment must have completed simulation (synths with results)
    2. Analysis must have been run (analysis_runs table entry)
    3. At least 2 chart insights must exist (from generating insights on charts)
"""

import sys
import time

import requests

BASE_URL = "http://localhost:8000"


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_executive_summary_v16.py <experiment_id>")
        print("\nTo find experiment IDs:")
        print("  psql postgresql://synthlab:synthlab_dev@localhost:5432/synthlab -c 'SELECT id, name FROM experiments LIMIT 10'")
        sys.exit(1)

    experiment_id = sys.argv[1]
    print(f"\n📋 Testing Executive Summary v16 for: {experiment_id}")
    print("=" * 60)

    # Step 1: Check if experiment exists
    print("\n1️⃣ Checking experiment...")
    try:
        resp = requests.get(f"{BASE_URL}/experiments/{experiment_id}")
        if resp.status_code == 404:
            print(f"   ❌ Experiment not found: {experiment_id}")
            sys.exit(1)
        exp = resp.json()
        print(f"   ✅ Found: {exp.get('name', 'N/A')}")
    except requests.ConnectionError:
        print("   ❌ Cannot connect to API. Is the server running?")
        print("   Run: uv run uvicorn synth_lab.api.main:app --reload")
        sys.exit(1)

    # Step 2: Check document availability
    print("\n2️⃣ Checking document availability...")
    resp = requests.get(f"{BASE_URL}/experiments/{experiment_id}/documents/availability")
    avail = resp.json()
    print(f"   Summary: {avail['summary']}")
    print(f"   PRFAQ: {avail['prfaq']}")
    print(f"   Executive Summary: {avail['executive_summary']}")

    # Step 3: Check existing documents
    print("\n3️⃣ Listing existing documents...")
    resp = requests.get(f"{BASE_URL}/experiments/{experiment_id}/documents")
    docs = resp.json()
    if docs:
        for doc in docs:
            print(f"   - {doc['document_type']}: {doc['status']} ({doc['generated_at']})")
    else:
        print("   No documents yet.")

    # Step 4: Generate executive summary
    print("\n4️⃣ Generating executive summary...")
    resp = requests.post(
        f"{BASE_URL}/experiments/{experiment_id}/documents/executive_summary/generate"
    )
    if resp.status_code == 400:
        print(f"   ❌ Error: {resp.json()['detail']}")
        print("\n   📌 Make sure you have:")
        print("      - Run quantitative analysis (analysis_runs table)")
        print("      - Generated at least 2 chart insights")
        sys.exit(1)
    elif resp.status_code != 200:
        print(f"   ❌ Unexpected error: {resp.status_code} - {resp.text}")
        sys.exit(1)

    result = resp.json()
    print(f"   ✅ {result['message']}")

    # Step 5: Poll for completion
    print("\n5️⃣ Waiting for generation to complete...")
    max_attempts = 30
    for i in range(max_attempts):
        time.sleep(2)
        resp = requests.get(
            f"{BASE_URL}/experiments/{experiment_id}/documents/executive_summary"
        )
        if resp.status_code == 404:
            print(f"   ⏳ Attempt {i+1}/{max_attempts}: Not ready yet...")
            continue

        doc = resp.json()
        status = doc.get("status")

        if status == "completed":
            print(f"   ✅ Completed!")
            break
        elif status == "failed":
            print(f"   ❌ Generation failed: {doc.get('error_message')}")
            sys.exit(1)
        elif status == "generating":
            print(f"   ⏳ Attempt {i+1}/{max_attempts}: Still generating...")
        else:
            print(f"   ⏳ Attempt {i+1}/{max_attempts}: Status = {status}")
    else:
        print("   ⚠️ Timeout waiting for generation")
        sys.exit(1)

    # Step 6: Display result
    print("\n6️⃣ Fetching markdown content...")
    resp = requests.get(
        f"{BASE_URL}/experiments/{experiment_id}/documents/executive_summary/markdown"
    )
    if resp.status_code == 200:
        markdown = resp.text
        print("\n" + "=" * 60)
        print("📄 EXECUTIVE SUMMARY (Markdown)")
        print("=" * 60)
        print(markdown[:2000])
        if len(markdown) > 2000:
            print(f"\n... (truncated, total {len(markdown)} chars)")
        print("=" * 60)
    else:
        print(f"   ❌ Error fetching markdown: {resp.status_code}")

    print("\n✅ Test completed!")
    print(f"\n📌 View in browser: http://localhost:5173/experiments/{experiment_id}")


if __name__ == "__main__":
    main()
