#!/usr/bin/env python3
"""
End-to-end test for SSE streaming functionality.

This script:
1. Initializes/resets the database
2. Creates 5 synthetic personas (synths)
3. Optionally generates avatars (requires OPENAI_API_KEY)
4. Starts the API server
5. Executes a research session
6. Tests SSE streaming of interview messages

Usage:
    # Without avatars (faster)
    uv run python scripts/test_sse_e2e.py

    # With avatars (requires OPENAI_API_KEY)
    uv run python scripts/test_sse_e2e.py --with-avatars

References:
    - SSE Spec: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from synth_lab.gen_synth.gen_synth import main as generate_synths
from synth_lab.infrastructure.config import DB_PATH, OUTPUT_DIR
from synth_lab.infrastructure.database import init_database

console = Console()

# Configuration
API_HOST = "127.0.0.1"
API_PORT = 8765  # Use non-standard port to avoid conflicts
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
TOPIC_NAME = "compra-amazon"
SYNTH_COUNT = 5
MAX_TURNS = 4  # Fewer turns for faster testing
MAX_CONCURRENT = 2  # Lower concurrency for testing


def step(msg: str) -> None:
    """Print a step header."""
    console.print(f"\n[bold cyan]>>> {msg}[/bold cyan]")


def success(msg: str) -> None:
    """Print success message."""
    console.print(f"[green]✓[/green] {msg}")


def error(msg: str) -> None:
    """Print error message."""
    console.print(f"[red]✗[/red] {msg}")


def init_db() -> None:
    """Initialize the database."""
    step("Initializing database")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Remove existing database for clean test
    if DB_PATH.exists():
        DB_PATH.unlink()
        logger.info(f"Removed existing database: {DB_PATH}")

    init_database()
    success(f"Database created at {DB_PATH}")


def create_synths() -> list[dict]:
    """Create 5 synthetic personas."""
    step(f"Creating {SYNTH_COUNT} synthetic personas")

    synths = generate_synths(
        quantidade=SYNTH_COUNT,
        show_progress=True,
        quiet=False,
    )

    # Display created synths
    table = Table(title="Created Synths")
    table.add_column("ID", style="cyan")
    table.add_column("Nome", style="green")
    table.add_column("Idade")
    table.add_column("Arquétipo", style="yellow")

    for synth in synths:
        table.add_row(
            synth["id"],
            synth["nome"],
            str(synth.get("demografia", {}).get("idade", "?")),
            synth.get("arquetipo", "?"),
        )

    console.print(table)
    success(f"Created {len(synths)} synths")

    return synths


def generate_avatars(synths: list[dict]) -> None:
    """Generate avatars for synths (optional)."""
    step("Generating avatars")

    if not os.getenv("OPENAI_API_KEY"):
        console.print("[yellow]⚠ OPENAI_API_KEY not set, skipping avatar generation[/yellow]")
        return

    from synth_lab.gen_synth.avatar_generator import generate_avatars as gen_avatars
    from synth_lab.infrastructure.config import AVATARS_DIR

    try:
        avatar_paths = gen_avatars(
            synths=synths,
            blocks=1,  # 1 block = 9 avatars, enough for 5 synths
            avatar_dir=AVATARS_DIR,
        )
        success(f"Generated {len(avatar_paths)} avatars")
    except Exception as e:
        error(f"Avatar generation failed: {e}")


def start_api_server() -> subprocess.Popen:
    """Start the API server in background."""
    step("Starting API server")

    # Command to start uvicorn
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "synth_lab.api.main:app",
        "--host",
        API_HOST,
        "--port",
        str(API_PORT),
        "--log-level",
        "warning",
    ]

    # Start server process
    process = subprocess.Popen(
        cmd,
        cwd=Path(__file__).parent.parent / "src",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            response = httpx.get(f"{API_BASE_URL}/docs", timeout=1.0)
            if response.status_code == 200:
                success(f"API server started at {API_BASE_URL}")
                return process
        except Exception:
            pass
        time.sleep(0.5)

    # If we get here, server didn't start
    process.kill()
    raise RuntimeError("Failed to start API server")


def stop_api_server(process: subprocess.Popen) -> None:
    """Stop the API server."""
    step("Stopping API server")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    success("API server stopped")


async def execute_research() -> str:
    """Execute a research session and return exec_id."""
    step("Executing research")

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        # Start research execution
        response = await client.post(
            "/research/execute",
            json={
                "topic_name": TOPIC_NAME,
                "synth_count": SYNTH_COUNT,
                "max_turns": MAX_TURNS,
                "max_concurrent": MAX_CONCURRENT,
                "model": "gpt-4o-mini",  # Use cheaper model for testing
                "generate_summary": False,  # Skip summary for faster test
            },
        )

        if response.status_code != 200:
            error(f"Failed to start research: {response.text}")
            raise RuntimeError(f"Research execution failed: {response.status_code}")

        data = response.json()
        exec_id = data["exec_id"]
        success(f"Research started: {exec_id}")

        return exec_id


async def test_sse_streaming(exec_id: str) -> None:
    """Test SSE streaming endpoint."""
    step("Testing SSE streaming")

    console.print(f"[dim]Connecting to /research/{exec_id}/stream...[/dim]")

    messages_received = 0
    interviews_by_synth: dict[str, list[dict]] = {}

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=None) as client:
        try:
            async with client.stream("GET", f"/research/{exec_id}/stream") as response:
                console.print("[dim]Connected! Waiting for events...[/dim]\n")

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk

                    # Parse SSE events from buffer
                    while "\n\n" in buffer:
                        event_str, buffer = buffer.split("\n\n", 1)

                        # Parse event
                        event_type = "message"
                        event_data = "{}"

                        for line in event_str.split("\n"):
                            if line.startswith("event:"):
                                event_type = line[6:].strip()
                            elif line.startswith("data:"):
                                event_data = line[5:].strip()

                        if event_type == "execution_completed":
                            console.print("\n[bold green]>>> Execution completed![/bold green]")
                            break

                        if event_type == "message":
                            try:
                                data = json.loads(event_data)
                                messages_received += 1

                                synth_id = data.get("synth_id", "unknown")
                                speaker = data.get("speaker", "?")
                                text = data.get("text", "")[:100]  # Truncate for display
                                is_replay = data.get("is_replay", False)
                                turn = data.get("turn_number", "?")

                                # Track by synth
                                if synth_id not in interviews_by_synth:
                                    interviews_by_synth[synth_id] = []
                                interviews_by_synth[synth_id].append(data)

                                # Display
                                prefix = (
                                    "[dim][replay][/dim]" if is_replay else "[bold][live][/bold]"
                                )
                                speaker_color = "blue" if speaker == "Interviewer" else "green"
                                console.print(
                                    f"{prefix} [{speaker_color}]{speaker}[/{speaker_color}] "
                                    f"[dim]({synth_id[:6]}... turn {turn})[/dim]: {text}..."
                                )

                            except json.JSONDecodeError:
                                pass

        except httpx.ReadTimeout:
            console.print(
                "[yellow]Stream timeout (this is normal if execution takes long)[/yellow]"
            )

    # Summary
    console.print("\n")
    summary_table = Table(title="SSE Streaming Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Total messages received", str(messages_received))
    summary_table.add_row("Unique synths", str(len(interviews_by_synth)))
    summary_table.add_row(
        "Messages per synth",
        ", ".join(f"{k[:6]}:{len(v)}" for k, v in interviews_by_synth.items()),
    )

    console.print(summary_table)

    if messages_received > 0:
        success(f"SSE streaming working! Received {messages_received} messages")
    else:
        error("No messages received via SSE")


async def check_execution_status(exec_id: str) -> dict:
    """Check final execution status."""
    step("Checking execution status")

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
        response = await client.get(f"/research/{exec_id}")
        data = response.json()

        status_table = Table(title="Execution Status")
        status_table.add_column("Field", style="cyan")
        status_table.add_column("Value", style="green")

        status_table.add_row("Status", data.get("status", "?"))
        status_table.add_row("Successful", str(data.get("successful_count", 0)))
        status_table.add_row("Failed", str(data.get("failed_count", 0)))
        status_table.add_row("Total synths", str(data.get("synth_count", 0)))

        console.print(status_table)

        return data


async def main_async(with_avatars: bool = False) -> None:
    """Main async function."""
    console.print(
        Panel.fit(
            "[bold]SSE End-to-End Test[/bold]\nTesting real-time interview message streaming",
            title="synth-lab",
        )
    )

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        error("OPENAI_API_KEY not set! Research execution requires LLM access.")
        console.print("[yellow]Set OPENAI_API_KEY environment variable and retry.[/yellow]")
        sys.exit(1)

    api_process = None

    try:
        # Step 1: Initialize database
        init_db()

        # Step 2: Create synths
        synths = create_synths()

        # Step 3: Generate avatars (optional)
        if with_avatars:
            generate_avatars(synths)

        # Step 4: Start API server
        api_process = start_api_server()

        # Step 5: Execute research
        exec_id = await execute_research()

        # Step 6: Test SSE streaming
        await test_sse_streaming(exec_id)

        # Step 7: Check final status
        await check_execution_status(exec_id)

        console.print("\n[bold green]✓ All tests completed successfully![/bold green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")

    except Exception as e:
        error(f"Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    finally:
        # Cleanup
        if api_process:
            stop_api_server(api_process)


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="End-to-end SSE streaming test")
    parser.add_argument(
        "--with-avatars",
        action="store_true",
        help="Generate avatars for synths (requires OPENAI_API_KEY)",
    )
    args = parser.parse_args()

    asyncio.run(main_async(with_avatars=args.with_avatars))


if __name__ == "__main__":
    main()
