"""
Transcript persistence - save/load interview transcripts.

This module handles:
- Creating transcript objects
- Generating transcript filenames
- Saving transcripts to JSON
- Loading transcripts from JSON

Functions:
- create_transcript(): Build transcript from session data
- generate_transcript_filename(): Create filename with timestamp
- save_transcript(): Persist transcript to JSON file
- load_transcript(): Load transcript from JSON file

Sample usage:
    from synth_lab.research.transcript import save_transcript

    save_transcript(session, messages, synth, "output/transcripts")

Expected output:
    JSON file at output/transcripts/{synth_id}_{timestamp}.json

Third-party Documentation:
- Python pathlib: https://docs.python.org/3/library/pathlib.html
"""

import json
from datetime import datetime
from pathlib import Path

from loguru import logger

from synth_lab.research.models import InterviewSession, Message, Transcript


def create_transcript(
    session: InterviewSession, messages: list[Message], synth_snapshot: dict
) -> Transcript:
    """
    Create transcript object from interview data.

    Args:
        session: Interview session metadata
        messages: List of messages exchanged
        synth_snapshot: Snapshot of synth data at interview time

    Returns:
        Complete Transcript object
    """
    return Transcript(
        session=session, synth_snapshot=synth_snapshot, messages=messages
    )


def generate_transcript_filename(synth_id: str, timestamp: datetime) -> str:
    """
    Generate transcript filename with synth ID and timestamp.

    Args:
        synth_id: Synth ID
        timestamp: Interview timestamp

    Returns:
        Filename like "abc123_20251216_143052.json"
    """
    date_str = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"{synth_id}_{date_str}.json"


def save_transcript(
    session: InterviewSession,
    messages: list[Message],
    synth_snapshot: dict,
    output_dir: str = "output/transcripts",
) -> Path:
    """
    Save transcript to JSON file.

    Args:
        session: Interview session
        messages: Interview messages
        synth_snapshot: Synth data snapshot
        output_dir: Output directory path

    Returns:
        Path to saved transcript file

    Raises:
        IOError: If file cannot be written
    """
    # Create transcript
    transcript = create_transcript(session, messages, synth_snapshot)

    # Generate filename
    filename = generate_transcript_filename(
        session.synth_id, session.start_time)

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Full file path
    file_path = output_path / filename

    # Save to JSON
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(transcript.model_dump(mode="json"),
                      f, indent=2, ensure_ascii=False)

        logger.info(f"Transcript saved to: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Failed to save transcript: {e}")
        raise IOError(f"Could not save transcript to {file_path}: {e}")


def load_transcript(file_path: str) -> Transcript:
    """
    Load transcript from JSON file.

    Args:
        file_path: Path to transcript file

    Returns:
        Loaded Transcript object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Transcript not found: {file_path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        return Transcript(**data)

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in transcript file: {e}")


if __name__ == "__main__":
    """Validation with real data."""
    import sys
    from datetime import timezone
    from uuid import uuid4

    from synth_lab.research.models import SessionStatus, Speaker

    print("=== Transcript Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Generate filename
    total_tests += 1
    try:
        now = datetime(2025, 12, 16, 14, 30, 52, tzinfo=timezone.utc)
        filename = generate_transcript_filename("abc123", now)
        assert filename == "abc123_20251216_143052.json"
        print(f"✓ Generate filename: {filename}")
    except Exception as e:
        all_validation_failures.append(f"Generate filename: {e}")

    # Test 2: Create transcript
    total_tests += 1
    try:
        session = InterviewSession(
            id=str(uuid4()),
            synth_id="abc123",
            start_time=datetime.now(timezone.utc),
            model_used="gpt-4.1",
        )
        messages = [
            Message(
                speaker=Speaker.INTERVIEWER,
                content="Test",
                timestamp=datetime.now(timezone.utc),
                round_number=1,
            )
        ]
        transcript = create_transcript(session, messages, {"id": "abc123"})
        assert len(transcript.messages) == 1
        print("✓ Create transcript object")
    except Exception as e:
        all_validation_failures.append(f"Create transcript: {e}")

    # Test 3: Save transcript (to temp directory)
    total_tests += 1
    try:
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            session = InterviewSession(
                id=str(uuid4()),
                synth_id="test01",
                start_time=datetime.now(timezone.utc),
                model_used="gpt-4.1",
                status=SessionStatus.COMPLETED,
                end_time=datetime.now(timezone.utc),
            )
            messages = []
            file_path = save_transcript(session, messages, {}, tmpdir)
            assert file_path.exists()
            print(f"✓ Save transcript to: {file_path.name}")
    except Exception as e:
        all_validation_failures.append(f"Save transcript: {e}")

    # Test 4: Load non-existent transcript fails
    total_tests += 1
    try:
        try:
            load_transcript("/nonexistent/transcript.json")
            all_validation_failures.append(
                "Load transcript: Should raise FileNotFoundError"
            )
        except FileNotFoundError:
            print("✓ Load transcript raises FileNotFoundError correctly")
    except Exception as e:
        all_validation_failures.append(f"Load transcript error handling: {e}")

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
            f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Transcript module is validated and ready for use")
        sys.exit(0)
