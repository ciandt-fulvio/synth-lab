"""
UX Research Interviews Module - Simulate UX research interviews with synths.

This module enables researchers to conduct simulated interviews with synthetic personas
using two LLMs in conversation (interviewer and synth).

Main Components:
- models: Pydantic models for data validation
- interview: Core interview execution logic
- prompts: System prompt generation
- transcript: Transcript persistence
- cli: CLI command interface

Sample usage:
    # Via CLI
    synthlab research <synth_id> --topic-guide <path> --max-rounds <int>

    # Programmatic usage
    from synth_lab.research import run_interview, save_transcript

    session, messages, synth = run_interview(
        synth_id="abc123",
        topic_guide_path="data/topic_guides/ecommerce-mobile.md",
        max_rounds=10
    )

    transcript_path = save_transcript(session, messages, synth)

Expected output:
    - Real-time interview display in terminal
    - JSON transcript saved to data/transcripts/

Third-party Documentation:
- OpenAI Python SDK: https://github.com/openai/openai-python
- Pydantic: https://docs.pydantic.dev/
- Typer: https://typer.tiangolo.com/
- Rich: https://rich.readthedocs.io/
"""

from synth_lab.research.interview import run_interview, validate_synth_exists
from synth_lab.research.models import (
    InterviewResponse,
    InterviewSession,
    Message,
    SessionStatus,
    Speaker,
    Transcript,
)
from synth_lab.research.prompts import (
    build_interviewer_prompt,
    build_synth_prompt,
    load_topic_guide,
)
from synth_lab.research.transcript import (
    create_transcript,
    load_transcript,
    save_transcript,
)

__version__ = "1.0.0"

__all__ = [
    # Core interview execution
    "run_interview",
    "validate_synth_exists",
    # Data models
    "InterviewResponse",
    "InterviewSession",
    "Message",
    "SessionStatus",
    "Speaker",
    "Transcript",
    # Prompt generation
    "build_interviewer_prompt",
    "build_synth_prompt",
    "load_topic_guide",
    # Transcript management
    "create_transcript",
    "load_transcript",
    "save_transcript",
]
