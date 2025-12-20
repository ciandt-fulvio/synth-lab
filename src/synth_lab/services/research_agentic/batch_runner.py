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
import json
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

from .runner import InterviewResult, run_interview
from .summarizer import summarize_interviews

# GMT-3 timezone (São Paulo)
TZ_GMT_MINUS_3 = timezone(timedelta(hours=-3))

console = Console()


@dataclass
class BatchResult:
    """Result of a batch interview run."""

    successful_interviews: list[tuple[InterviewResult, dict[str, Any]]]
    failed_interviews: list[tuple[str, str, Exception]]  # (synth_id, synth_name, error)
    transcript_paths: list[str]  # Paths to individual transcripts
    summary: str | None
    summary_path: str | None
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
    synths_path = Path("output/synths/synths.json")
    if not synths_path.exists():
        raise FileNotFoundError(f"Synths file not found: {synths_path}")

    with open(synths_path, encoding="utf-8") as f:
        synths = json.load(f)

    return synths


def get_timestamp_gmt3() -> str:
    """Get current timestamp in GMT-3 format for file names."""
    return datetime.now(TZ_GMT_MINUS_3).strftime("%Y%m%d_%H%M%S")


def save_individual_transcript(
    result: InterviewResult,
    synth: dict[str, Any],
    topic_guide_name: str,
    model: str,
    max_turns: int,
    batch_id: str,
) -> str:
    """
    Save individual interview transcript to JSON file.

    Args:
        result: Interview result
        synth: Synth data dictionary
        topic_guide_name: Name of the topic guide
        model: Model used
        max_turns: Max turns configured
        batch_id: Batch identifier for grouping

    Returns:
        Path where transcript was saved
    """
    timestamp = get_timestamp_gmt3()
    transcript_path = f"output/transcripts/batch_{batch_id}/{result.synth_id}_{timestamp}.json"

    # Ensure directory exists
    Path(transcript_path).parent.mkdir(parents=True, exist_ok=True)

    # Build transcript data
    transcript_data = {
        "metadata": {
            "batch_id": batch_id,
            "synth_id": result.synth_id,
            "synth_name": result.synth_name,
            "topic_guide": topic_guide_name,
            "model": model,
            "max_turns": max_turns,
            "total_turns": result.total_turns,
            "timestamp": datetime.now(TZ_GMT_MINUS_3).isoformat(),
            "timezone": "GMT-3",
        },
        "messages": [
            {
                "speaker": msg.speaker,
                "text": msg.text,
                "internal_notes": msg.internal_notes,
            }
            for msg in result.messages
        ],
    }

    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(transcript_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved transcript to {transcript_path}")
    return transcript_path


async def run_single_interview_safe(
    synth: dict[str, Any],
    topic_guide_name: str,
    model: str,
    max_turns: int,
    semaphore: asyncio.Semaphore,
    progress: Progress,
    task_id: TaskID,
    batch_id: str,
) -> tuple[InterviewResult | None, dict[str, Any], str | None, Exception | None]:
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

    Returns:
        Tuple of (result or None, synth_data, transcript_path or None, error or None)
    """
    synth_id = synth.get("id", "unknown")
    synth_name = synth.get("nome", "Unknown")

    async with semaphore:
        logger.info(f"Starting interview with {synth_name} ({synth_id})")
        progress.update(task_id, description=f"[cyan]Entrevistando {synth_name}...")

        try:
            # Generate trace path
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
            )

            # Save individual transcript
            transcript_path = save_individual_transcript(
                result=result,
                synth=synth,
                topic_guide_name=topic_guide_name,
                model=model,
                max_turns=max_turns,
                batch_id=batch_id,
            )

            logger.info(f"Completed interview with {synth_name} ({synth_id})")
            progress.advance(task_id)
            return result, synth, transcript_path, None

        except Exception as e:
            logger.error(f"Failed interview with {synth_name} ({synth_id}): {e}")
            progress.advance(task_id)
            return None, synth, None, e


async def run_batch_interviews(
    topic_guide_name: str,
    max_interviews: int = 10,
    max_concurrent: int = 10,
    max_turns: int = 6,
    model: str = "gpt-5-mini",
    generate_summary: bool = True,
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
    # Generate batch ID for grouping outputs
    batch_id = f"{topic_guide_name}_{get_timestamp_gmt3()}"

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
    transcript_paths: list[str] = []

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
            )
            for synth in synths_to_interview
        ]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Process results
        for result, synth, transcript_path, error in results:
            if error is None and result is not None:
                successful_interviews.append((result, synth))
                if transcript_path:
                    transcript_paths.append(transcript_path)
            else:
                synth_id = synth.get("id", "unknown")
                synth_name = synth.get("nome", "Unknown")
                failed_interviews.append((synth_id, synth_name, error))

    # Log summary
    logger.info(
        f"Batch complete: {len(successful_interviews)} successful, "
        f"{len(failed_interviews)} failed"
    )

    # Generate summary if requested and we have successful interviews
    summary = None
    summary_path = None
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

            # Save summary to file
            summary_path = f"output/reports/batch_{batch_id}.md"
            Path(summary_path).parent.mkdir(parents=True, exist_ok=True)
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
            logger.info(f"Summary saved to {summary_path}")

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            summary = f"Erro ao gerar síntese: {e}"

    return BatchResult(
        successful_interviews=successful_interviews,
        failed_interviews=failed_interviews,
        transcript_paths=transcript_paths,
        summary=summary,
        summary_path=summary_path,
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
            total_requested=5,
            total_completed=3,
            total_failed=2,
        )
        assert result.total_requested == 5
        assert result.total_completed == 3
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
