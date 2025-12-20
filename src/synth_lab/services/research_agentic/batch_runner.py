"""
Batch runner for parallel interview execution.

This module provides functionality to run multiple interviews in parallel,
with configurable concurrency limits and progress tracking.

References:
- asyncio Semaphore: https://docs.python.org/3/library/asyncio-sync.html
- Rich Progress: https://rich.readthedocs.io/en/latest/progress.html

Sample usage:
```python
from .batch_runner import run_batch_interviews

results, summary = await run_batch_interviews(
    topic_guide_name="compra-amazon",
    max_interviews=10,
    max_concurrent=5,
    model="gpt-5-mini"
)
```
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)

from .runner import ConversationMessage, InterviewResult, run_interview
from .summarizer import summarize_interviews

# GMT-3 timezone (São Paulo)
TZ_GMT_MINUS_3 = timezone(timedelta(hours=-3))

console = Console()


@dataclass
class BatchResult:
    """Result of a batch interview run."""

    successful_interviews: list[tuple[InterviewResult, dict[str, Any]]]
    failed_interviews: list[tuple[str, str, Exception]]  # (synth_id, synth_name, error)
    summary: str | None
    batch_id: str
    total_requested: int
    total_completed: int
    total_failed: int


def load_all_synths() -> list[dict[str, Any]]:
    """
    Load all synths from the database.

    Returns:
        List of synth dictionaries
    """
    from synth_lab.gen_synth.storage import load_synths

    return load_synths()


def get_timestamp_gmt3() -> str:
    """Get current timestamp in GMT-3 format for file names."""
    return datetime.now(TZ_GMT_MINUS_3).strftime("%Y%m%d_%H%M%S")


async def run_single_interview_safe(
    synth: dict[str, Any],
    topic_guide_name: str,
    model: str,
    max_turns: int,
    semaphore: asyncio.Semaphore,
    progress: Progress,
    task_id: TaskID,
    batch_id: str,
    exec_id: str | None = None,
    message_callback: Callable[[str, str, int, ConversationMessage], Awaitable[None]] | None = None,
) -> tuple[InterviewResult | None, dict[str, Any], Exception | None]:
    """
    Run a single interview with error handling and semaphore control.

    Args:
        synth: Synth data dictionary
        topic_guide_name: Name of the topic guide
        model: LLM model to use
        max_turns: Maximum conversation turns
        semaphore: Semaphore for concurrency control
        progress: Rich progress bar
        task_id: Task ID for progress updates
        batch_id: Batch identifier for grouping outputs
        exec_id: Execution ID for SSE streaming (optional)
        message_callback: Async callback for real-time message streaming (optional)

    Returns:
        Tuple of (result or None, synth_data, error or None)
    """
    synth_id = synth.get("id", "unknown")
    synth_name = synth.get("nome", "Unknown")

    async with semaphore:
        logger.info(f"Starting interview with {synth_name} ({synth_id})")
        progress.update(task_id, description=f"[cyan]Entrevistando {synth_name}...")

        try:
            # Generate trace path for debugging (still saved to filesystem)
            timestamp = get_timestamp_gmt3()
            trace_path = f"output/traces/batch_{batch_id}/{synth_id}_{timestamp}.trace.json"

            # Ensure trace directory exists
            Path(trace_path).parent.mkdir(parents=True, exist_ok=True)

            result = await run_interview(
                synth_id=synth_id,
                topic_guide_name=topic_guide_name,
                max_turns=max_turns,
                trace_path=trace_path,
                model=model,
                verbose=False,  # Suppress individual interview output in batch mode
                exec_id=exec_id,
                message_callback=message_callback,
            )

            logger.info(f"Completed interview with {synth_name} ({synth_id})")
            progress.advance(task_id)
            return result, synth, None

        except Exception as e:
            logger.error(f"Failed interview with {synth_name} ({synth_id}): {e}")
            progress.advance(task_id)
            return None, synth, e


async def run_batch_interviews(
    topic_guide_name: str,
    max_interviews: int = 10,
    max_concurrent: int = 10,
    max_turns: int = 6,
    model: str = "gpt-5-mini",
    generate_summary: bool = True,
    exec_id: str | None = None,
    message_callback: Callable[[str, str, int, ConversationMessage], Awaitable[None]] | None = None,
    on_transcription_completed: Callable[[str, int, int], Awaitable[None]] | None = None,
) -> BatchResult:
    """
    Run multiple interviews in parallel with progress tracking.

    Args:
        topic_guide_name: Name of the topic guide to use
        max_interviews: Maximum number of interviews to run
        max_concurrent: Maximum concurrent interviews (default 10)
        max_turns: Maximum turns per interview
        model: LLM model to use
        generate_summary: Whether to generate a summary after all interviews
        exec_id: Optional execution ID from caller. If not provided, generates one.
        message_callback: Async callback for real-time message streaming (optional)
            Signature: (exec_id, synth_id, turn_number, message) -> None
        on_transcription_completed: Callback when all transcriptions done
            Signature: (exec_id, successful_count, failed_count) -> None

    Returns:
        BatchResult with all interview results and summary

    Sample usage:
    ```python
    result = await run_batch_interviews(
        topic_guide_name="compra-amazon",
        max_interviews=5,
        max_concurrent=3
    )
    print(f"Completed: {result.total_completed}")
    print(result.summary)
    ```
    """
    # Use provided exec_id or generate batch ID for grouping outputs
    batch_id = exec_id if exec_id else f"batch_{topic_guide_name}_{get_timestamp_gmt3()}"

    # Load synths
    all_synths = load_all_synths()
    synths_to_interview = all_synths[:max_interviews]

    logger.info(
        f"Starting batch {batch_id}: {len(synths_to_interview)} synths, "
        f"max {max_concurrent} concurrent"
    )

    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)

    # Track results
    successful_interviews: list[tuple[InterviewResult, dict[str, Any]]] = []
    failed_interviews: list[tuple[str, str, Exception]] = []

    # Run interviews with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task(
            "[cyan]Iniciando entrevistas...",
            total=len(synths_to_interview),
        )

        # Create tasks for all interviews
        tasks = [
            run_single_interview_safe(
                synth=synth,
                topic_guide_name=topic_guide_name,
                model=model,
                max_turns=max_turns,
                semaphore=semaphore,
                progress=progress,
                task_id=task_id,
                batch_id=batch_id,
                exec_id=batch_id,
                message_callback=message_callback,
            )
            for synth in synths_to_interview
        ]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Process results
        for result, synth, error in results:
            if error is None and result is not None:
                successful_interviews.append((result, synth))
            else:
                synth_id = synth.get("id", "unknown")
                synth_name = synth.get("nome", "Unknown")
                failed_interviews.append((synth_id, synth_name, error))

    # Log summary
    logger.info(
        f"Batch complete: {len(successful_interviews)} successful, "
        f"{len(failed_interviews)} failed"
    )

    # Notify that all transcriptions are complete (before summary generation)
    if on_transcription_completed and batch_id:
        await on_transcription_completed(
            batch_id,
            len(successful_interviews),
            len(failed_interviews),
        )

    # Generate summary if requested and we have successful interviews
    summary = None
    if generate_summary and successful_interviews:
        console.print()
        console.print("[cyan]Gerando síntese das entrevistas...[/cyan]")

        try:
            # Summarizer always uses gpt-5 with reasoning medium for better analysis
            summary = await summarize_interviews(
                interview_results=successful_interviews,
                topic_guide_name=topic_guide_name,
                model="gpt-5",
            )
            logger.info("Summary generated successfully")

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            summary = f"Erro ao gerar síntese: {e}"

    return BatchResult(
        successful_interviews=successful_interviews,
        failed_interviews=failed_interviews,
        summary=summary,
        batch_id=batch_id,
        total_requested=len(synths_to_interview),
        total_completed=len(successful_interviews),
        total_failed=len(failed_interviews),
    )


def run_batch_interviews_sync(
    topic_guide_name: str,
    max_interviews: int = 10,
    max_concurrent: int = 10,
    max_turns: int = 6,
    model: str = "gpt-5-mini",
    generate_summary: bool = True,
    exec_id: str | None = None,
    message_callback: Callable[[str, str, int, ConversationMessage], Awaitable[None]] | None = None,
    on_transcription_completed: Callable[[str, int, int], Awaitable[None]] | None = None,
) -> BatchResult:
    """
    Synchronous wrapper for run_batch_interviews.

    Args:
        topic_guide_name: Name of the topic guide to use
        max_interviews: Maximum number of interviews to run
        max_concurrent: Maximum concurrent interviews
        max_turns: Maximum turns per interview
        model: LLM model to use
        generate_summary: Whether to generate summary
        exec_id: Optional execution ID from caller.
        message_callback: Async callback for real-time message streaming (optional)
        on_transcription_completed: Callback when all transcriptions done (exec_id, success, failed)

    Returns:
        BatchResult with all interview results and summary
    """
    return asyncio.run(
        run_batch_interviews(
            topic_guide_name=topic_guide_name,
            max_interviews=max_interviews,
            max_concurrent=max_concurrent,
            max_turns=max_turns,
            model=model,
            generate_summary=generate_summary,
            exec_id=exec_id,
            message_callback=message_callback,
            on_transcription_completed=on_transcription_completed,
        )
    )


if __name__ == "__main__":
    """Validation of batch runner module."""
    import sys

    print("=== Batch Runner Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Import works
    total_tests += 1
    try:
        from .batch_runner import (
            BatchResult,
            load_all_synths,
            run_batch_interviews,
        )
        print("✓ All imports successful")
    except Exception as e:
        all_validation_failures.append(f"Import: {e}")

    # Test 2: load_all_synths works
    total_tests += 1
    try:
        synths = load_all_synths()
        assert isinstance(synths, list)
        assert len(synths) > 0
        assert "id" in synths[0]
        print(f"✓ load_all_synths loaded {len(synths)} synths")
    except FileNotFoundError:
        print("⚠ Skipping load_all_synths - synths.json not found")
    except Exception as e:
        all_validation_failures.append(f"load_all_synths: {e}")

    # Test 3: BatchResult dataclass works
    total_tests += 1
    try:
        result = BatchResult(
            successful_interviews=[],
            failed_interviews=[],
            summary="Test summary",
            batch_id="test_batch_001",
            total_requested=5,
            total_completed=3,
            total_failed=2,
        )
        assert result.total_requested == 5
        assert result.total_completed == 3
        assert result.batch_id == "test_batch_001"
        print("✓ BatchResult dataclass works correctly")
    except Exception as e:
        all_validation_failures.append(f"BatchResult: {e}")

    # Test 4: get_timestamp_gmt3 works
    total_tests += 1
    try:
        timestamp = get_timestamp_gmt3()
        assert len(timestamp) == 15  # YYYYMMDD_HHMMSS
        assert "_" in timestamp
        print(f"✓ get_timestamp_gmt3 returns valid timestamp: {timestamp}")
    except Exception as e:
        all_validation_failures.append(f"get_timestamp_gmt3: {e}")

    # Final validation result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results"
        )
        print("Batch runner module is validated and ready for use")
        sys.exit(0)
