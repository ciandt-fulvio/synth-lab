"""
Interview execution logic - core conversation loop.

This module handles:
- Loading synths from data
- OpenAI client wrapping with structured outputs
- Conversation turn execution
- Main interview loop

Functions:
- load_synth(): Load synth by ID from JSON
- validate_synth_exists(): Check if synth exists
- conversation_turn(): Execute single LLM call
- run_interview(): Main interview loop

Sample usage:
    from synth_lab.research.interview import run_interview

    session, messages = run_interview(
        synth_id="abc123",
        topic_guide_path=None,
        max_rounds=10
    )

Expected output:
    InterviewSession and list of Message objects

Third-party Documentation:
- OpenAI Python SDK: https://github.com/openai/openai-python
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from loguru import logger
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live

from synth_lab.research.models import (
    InterviewResponse,
    InterviewSession,
    Message,
    SessionStatus,
    Speaker,
)
from synth_lab.research.prompts import build_interviewer_prompt, build_synth_prompt, load_topic_guide
from synth_lab.topic_guides.summary_manager import load_topic_guide_context

console = Console()
SYNTHS_FILE = Path("data/synths/synths.json")


def load_synth(synth_id: str) -> dict | None:
    """
    Load synth by ID from synths.json.

    Args:
        synth_id: 6-character synth ID

    Returns:
        Synth data dict or None if not found
    """
    if not SYNTHS_FILE.exists():
        logger.error(f"Synths file not found: {SYNTHS_FILE}")
        return None

    with open(SYNTHS_FILE, encoding="utf-8") as f:
        synths = json.load(f)

    return next((s for s in synths if s["id"] == synth_id), None)


def validate_synth_exists(synth_id: str) -> bool:
    """
    Check if synth exists in database.

    Args:
        synth_id: Synth ID to validate

    Returns:
        True if synth exists, False otherwise
    """
    return load_synth(synth_id) is not None


def conversation_turn(
    client: OpenAI,
    messages: list[dict],
    system_prompt: str,
    model: str = "gpt-4o",
) -> InterviewResponse:
    """
    Execute single conversation turn with LLM.

    Args:
        client: OpenAI client instance
        messages: Conversation history
        system_prompt: System prompt for this participant
        model: Model name to use

    Returns:
        Parsed InterviewResponse from LLM

    Raises:
        Exception: If API call fails
    """
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[{"role": "system", "content": system_prompt}] + messages,
        response_format=InterviewResponse,
    )

    return completion.choices[0].message.parsed


def display_message(speaker: Speaker, content: str, synth_name: str | None = None):
    """
    Display message in terminal with Rich formatting.

    Args:
        speaker: Who is speaking
        content: Message content
        synth_name: Name of synth (for synth messages)
    """
    if speaker == Speaker.INTERVIEWER:
        panel = Panel(
            content,
            title="🎤 Entrevistador",
            border_style="blue",
            padding=(1, 2),
        )
    else:
        title = f"👤 {synth_name}" if synth_name else "👤 Synth"
        panel = Panel(
            content,
            title=title,
            border_style="green",
            padding=(1, 2),
        )

    console.print(panel)
    console.print()  # Add spacing


def display_interview_header(synth: dict):
    """
    Display interview header with synth info.

    Args:
        synth: Synth data dictionary
    """
    info = f"""
[bold]Entrevista de Pesquisa UX[/bold]

Participante: {synth['nome']}
Arquétipo: {synth['arquetipo']}
Idade: {synth['demografia']['idade']} anos
Localização: {synth['demografia']['localizacao']['cidade']}, {synth['demografia']['localizacao']['estado']}
"""
    panel = Panel(info, border_style="cyan", padding=(1, 2))
    console.print(panel)
    console.print()


def display_interview_summary(session: InterviewSession, message_count: int):
    """
    Display interview completion summary.

    Args:
        session: Interview session
        message_count: Number of messages exchanged
    """
    duration = (
        (session.end_time - session.start_time).total_seconds()
        if session.end_time
        else 0
    )
    minutes = int(duration // 60)
    seconds = int(duration % 60)

    summary = f"""
[bold green]✓ Entrevista Concluída![/bold green]

Status: {session.status.value}
Turnos de conversa: {message_count // 2}
Duração: {minutes}m {seconds}s
"""
    panel = Panel(summary, border_style="green", padding=(1, 2))
    console.print(panel)


def run_interview(
    synth_id: str,
    topic_guide_path: str | None = None,
    max_rounds: int = 10,
    model: str = "gpt-4o",
) -> tuple[InterviewSession, list[Message], dict]:
    """
    Execute complete interview loop.

    Args:
        synth_id: ID of synth to interview
        topic_guide_path: Optional path to topic guide
        max_rounds: Maximum conversation rounds
        model: LLM model to use

    Returns:
        Tuple of (session, messages, synth_snapshot)

    Raises:
        ValueError: If synth not found or OPENAI_API_KEY missing
        FileNotFoundError: If topic guide not found
    """
    # Validate API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Load synth
    synth = load_synth(synth_id)
    if not synth:
        raise ValueError(f"Synth with ID '{synth_id}' not found")

    # Load topic guide if provided
    topic_guide_content = None
    if topic_guide_path:
        # Check if it's a .md file (old style) or topic guide name (new style)
        if topic_guide_path.endswith('.md'):
            # Legacy: load markdown file directly
            topic_guide_content = load_topic_guide(topic_guide_path)
        else:
            # New: load topic guide context with AI-generated descriptions
            topic_guide_content = load_topic_guide_context(topic_guide_path)

    # Initialize session
    session = InterviewSession(
        id=str(uuid4()),
        synth_id=synth_id,
        topic_guide_path=topic_guide_path,
        max_rounds=max_rounds,
        start_time=datetime.now(timezone.utc),
        status=SessionStatus.IN_PROGRESS,
        model_used=model,
    )

    # Display header
    display_interview_header(synth)

    # Build system prompts
    interviewer_prompt = build_interviewer_prompt(topic_guide_content)
    synth_prompt = build_synth_prompt(synth)

    # Initialize OpenAI client
    client = OpenAI()

    # Conversation loop
    messages_list = []
    conversation_history = []
    round_number = 1

    logger.info(f"Starting interview with synth {synth_id}")

    try:
        while round_number <= max_rounds:
            # Interviewer turn
            with console.status(f"[blue]Entrevistador pensando... (turno {round_number})", spinner="dots"):
                interviewer_response = conversation_turn(
                    client, conversation_history, interviewer_prompt, model
                )

            # Display and record
            display_message(Speaker.INTERVIEWER, interviewer_response.message)
            msg = Message(
                speaker=Speaker.INTERVIEWER,
                content=interviewer_response.message,
                timestamp=datetime.now(timezone.utc),
                internal_notes=interviewer_response.internal_notes,
                round_number=round_number,
            )
            messages_list.append(msg)
            conversation_history.append(
                {"role": "assistant" if len(conversation_history) % 2 == 0 else "user", "content": interviewer_response.message}
            )

            # Check if interviewer wants to end
            if interviewer_response.should_end:
                logger.info("Interviewer signaled end of interview")
                break

            # Synth turn
            with console.status(f"[green]{synth['nome']} pensando...", spinner="dots"):
                synth_response = conversation_turn(
                    client, conversation_history, synth_prompt, model
                )

            # Display and record
            display_message(Speaker.SYNTH, synth_response.message, synth["nome"])
            msg = Message(
                speaker=Speaker.SYNTH,
                content=synth_response.message,
                timestamp=datetime.now(timezone.utc),
                internal_notes=synth_response.internal_notes,
                round_number=round_number,
            )
            messages_list.append(msg)
            conversation_history.append(
                {"role": "user" if len(conversation_history) % 2 == 0 else "assistant", "content": synth_response.message}
            )

            round_number += 1

    except KeyboardInterrupt:
        logger.info("Interview interrupted by user")
        session.status = SessionStatus.INTERRUPTED
    except Exception as e:
        logger.error(f"Interview error: {e}")
        session.status = SessionStatus.ERROR
        raise
    else:
        session.status = SessionStatus.COMPLETED

    # Finalize session
    session.end_time = datetime.now(timezone.utc)

    # Display summary
    display_interview_summary(session, len(messages_list))

    return session, messages_list, synth


if __name__ == "__main__":
    """Validation with mock data."""
    import sys

    print("=== Interview Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Load synth function
    total_tests += 1
    try:
        # This will fail if no synths exist, which is expected in test
        synth = load_synth("nonexistent")
        if synth is None:
            print("✓ Load synth returns None for non-existent ID")
        else:
            all_validation_failures.append("Load synth: Should return None for non-existent ID")
    except Exception as e:
        all_validation_failures.append(f"Load synth: {e}")

    # Test 2: Validate synth exists
    total_tests += 1
    try:
        exists = validate_synth_exists("nonexistent")
        if not exists:
            print("✓ Validate synth exists returns False for non-existent ID")
        else:
            all_validation_failures.append("Validate synth: Should return False")
    except Exception as e:
        all_validation_failures.append(f"Validate synth: {e}")

    # Test 3: Display functions don't crash
    total_tests += 1
    try:
        test_synth = {
            "nome": "Test",
            "arquetipo": "Test Archetype",
            "demografia": {
                "idade": 30,
                "localizacao": {"cidade": "Test City", "estado": "TC"},
            },
        }
        display_interview_header(test_synth)
        print("✓ Display interview header works")
    except Exception as e:
        all_validation_failures.append(f"Display header: {e}")

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
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Interview module is validated and ready for use")
        sys.exit(0)
