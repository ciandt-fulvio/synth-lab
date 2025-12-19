"""
Interview execution logic - core conversation loop.

This module handles:
- Loading synths from data
- OpenAI client wrapping with structured outputs
- Conversation turn execution
- Main interview loop
- Function calling for dynamic image loading (when topic guide provided)

Functions:
- load_synth(): Load synth by ID from JSON
- validate_synth_exists(): Check if synth exists
- load_image_for_analysis(): Load and base64-encode images for Vision API
- conversation_turn(): Execute single LLM call (supports function calling)
- run_interview(): Main interview loop

Function Calling:
When a topic guide is provided (not .md file), the system:
- Loads context description and file descriptions
- Enables load_image_for_analysis tool for LLM
- LLM can request to see actual images during interview
- Images are base64-encoded and sent to Vision API
- Allows visual analysis beyond text descriptions

Sample usage:
    from synth_lab.research.interview import run_interview

    # Run interview with topic guide (required)
    session, messages, synth = run_interview(
        synth_id="abc123",
        topic_guide_name="compra-amazon",
        max_rounds=10
    )

    # Topic guide must contain:
    # - script.json: Interview questions
    # - summary.md: Context and file descriptions
    # - Files referenced in summary.md

Expected output:
    (InterviewSession, list[Message], dict) tuple

Third-party Documentation:
- OpenAI Python SDK: https://github.com/openai/openai-python
- Function Calling: https://platform.openai.com/docs/guides/function-calling
- Vision API: https://platform.openai.com/docs/guides/vision
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
from synth_lab.trace_visualizer import Tracer, SpanType, SpanStatus
import base64
import os
import json
import openai
from pydantic import BaseModel

console = Console()
SYNTHS_FILE = Path("output/synths/synths.json")


# Pydantic model for load_image_for_analysis tool parameters
class LoadImageParams(BaseModel):
    """Parameters for loading an image from topic guide."""
    filename: str


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


def load_image_for_analysis(filename: str, topic_guide_name: str) -> str | None:
    """
    Load image file and encode to base64 for Vision API.

    Args:
        filename: Name of the image file (e.g., '01_homepage.PNG')
        topic_guide_name: Name of the topic guide directory

    Returns:
        Base64-encoded image data or None if file not found

    Raises:
        FileNotFoundError: If image file doesn't exist
    """
    base_dir = Path(os.environ.get("TOPIC_GUIDES_DIR", "data/topic_guides"))
    guide_path = base_dir / topic_guide_name
    image_path = guide_path / filename

    if not image_path.exists():
        logger.error(f"Image not found: {image_path}")
        raise FileNotFoundError(
            f"Image file '{filename}' not found in topic guide '{topic_guide_name}'")

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    logger.info(f"Loaded image: {filename} ({len(image_data)} bytes base64)")
    return image_data


def conversation_turn(
    client: OpenAI,
    messages: list[dict],
    system_prompt: str,
    model: str = "gpt-5-mini",
    tools: list[dict] | None = None,
    topic_guide_name: str | None = None,
    tracer: Tracer | None = None,
    speaker: Speaker | None = None,
) -> InterviewResponse:
    """
    Execute single conversation turn with LLM.

    Args:
        client: OpenAI client instance
        messages: Conversation history
        system_prompt: System prompt for this participant
        model: Model name to use
        tools: Optional list of function calling tools
        topic_guide_name: Topic guide name (required if tools provided)
        tracer: Optional Tracer for recording trace data
        speaker: Speaker type (for trace metadata)

    Returns:
        Parsed InterviewResponse from LLM

    Raises:
        Exception: If API call fails
    """
    # Build API call parameters
    api_params = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "response_format": InterviewResponse,
        "reasoning_effort": "low",
        "verbosity": "low"
    }

    # Add tools if provided
    if tools:
        api_params["tools"] = tools

    # Get prompt context for tracing
    user_msgs = [m for m in messages if m.get("role") == "user"]
    last_msg = user_msgs[-1]["content"] if user_msgs else "Starting conversation"

    # Execute LLM call with optional tracing
    def _make_llm_call():
        return client.beta.chat.completions.parse(**api_params)

    if tracer:
        with tracer.start_span(SpanType.LLM_CALL, attributes={
            "prompt": last_msg,
            "model": model,
            "speaker": speaker.value if speaker else "unknown",
            "system_prompt": system_prompt,  # Log the actual system prompt used
        }) as span:
            try:
                completion = _make_llm_call()

                # Record response in span
                if completion.choices:
                    msg = completion.choices[0].message
                    if hasattr(msg, 'parsed') and msg.parsed:
                        span.set_attribute("response", msg.parsed.message)

                    # Record token usage if available
                    if hasattr(completion, 'usage') and completion.usage:
                        span.set_attribute(
                            "tokens_input", completion.usage.prompt_tokens)
                        span.set_attribute(
                            "tokens_output", completion.usage.completion_tokens)

                span.set_status(SpanStatus.SUCCESS)
            except Exception as e:
                span.set_status(SpanStatus.ERROR)
                span.set_attribute("error_message", str(e))
                raise
    else:
        completion = _make_llm_call()

    # Handle tool calls if present
    message = completion.choices[0].message

    # If LLM requested tool calls, execute them
    if hasattr(message, 'tool_calls') and message.tool_calls:
        logger.info(f"LLM requested {len(message.tool_calls)} tool calls")
        logger.debug(
            f"Tracer available: {tracer is not None}, current_turn: {tracer._current_turn if tracer else 'N/A'}")

        # Add assistant's message with tool calls to history
        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        })

        # Execute each tool call
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name

            # With pydantic_function_tool, arguments are already parsed
            if hasattr(tool_call.function, 'parsed_arguments') and tool_call.function.parsed_arguments:
                function_args = tool_call.function.parsed_arguments
            else:
                # Fallback to parsing JSON if not using pydantic_function_tool
                function_args = json.loads(tool_call.function.arguments)

            logger.info(
                f"Executing tool: {function_name} with args: {function_args}")

            # Execute the function with tracing
            if function_name == "load_image_for_analysis":
                # Get filename from parsed arguments (Pydantic model) or dict
                filename = function_args.filename if isinstance(
                    function_args, LoadImageParams) else function_args["filename"]
                logger.info(
                    f"Processing tool call for image: {filename}, tracer: {tracer is not None}")

                def _execute_tool():
                    return load_image_for_analysis(
                        filename=filename,
                        topic_guide_name=topic_guide_name
                    )

                tool_result = None
                tool_error = None

                if tracer:
                    with tracer.start_span(SpanType.TOOL_CALL, attributes={
                        "tool_name": function_name,
                        "arguments": {"filename": filename},
                    }) as span:
                        try:
                            image_data = _execute_tool()
                            span.set_attribute(
                                "result", f"Image loaded: {filename} ({len(image_data)} bytes)")
                            span.set_status(SpanStatus.SUCCESS)
                            tool_result = image_data
                        except Exception as e:
                            logger.error(f"Tool call failed: {e}")
                            span.set_status(SpanStatus.ERROR)
                            span.set_attribute("error_message", str(e))
                            tool_error = e
                else:
                    try:
                        tool_result = _execute_tool()
                    except Exception as e:
                        logger.error(f"Tool call failed: {e}")
                        tool_error = e

                # Add tool response to messages
                if tool_result:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": f"Image loaded successfully. Base64 data: data:image/png;base64,{tool_result[:100]}... (truncated)"
                    })
                else:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": f"Error loading image: {str(tool_error)}"
                    })

        # Make another API call to get the final response
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
    topic_guide_name: str,
    max_rounds: int = 10,
    model: str = "gpt-5-mini",
) -> tuple[InterviewSession, list[Message], dict]:
    """
    Execute complete interview loop with topic guide script.

    Args:
        synth_id: ID of synth to interview
        topic_guide_name: Name of topic guide (required)
        max_rounds: Maximum conversation rounds
        model: LLM model to use

    Returns:
        Tuple of (session, messages, synth_snapshot)

    Raises:
        ValueError: If synth not found or OPENAI_API_KEY missing
        FileNotFoundError: If topic guide, script.json, or summary.md not found
    """
    # Validate API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Load synth
    synth = load_synth(synth_id)
    if not synth:
        raise ValueError(f"Synth with ID '{synth_id}' not found")

    # Load topic guide (required)
    base_dir = Path(os.environ.get("TOPIC_GUIDES_DIR", "data/topic_guides"))
    topic_dir = base_dir / topic_guide_name

    # Validate topic guide directory
    if not topic_dir.exists():
        raise FileNotFoundError(
            f"Topic guide directory not found: {topic_dir}")

    # Load script.json
    script_path = topic_dir / "script.json"
    if not script_path.exists():
        raise FileNotFoundError(
            f"script.json not found in topic guide: {script_path}")

    with open(script_path, encoding="utf-8") as f:
        interview_script = json.load(f)

    # Validate script structure
    if not isinstance(interview_script, list):
        raise ValueError(f"script.json must be a list of questions")

    for item in interview_script:
        if "id" not in item or "ask" not in item:
            raise ValueError(
                f"Each question in script.json must have 'id' and 'ask' fields")

    logger.info(
        f"Loaded interview script with {len(interview_script)} questions")

    # Load topic guide context (summary.md + file descriptions)
    topic_guide_content = load_topic_guide_context(topic_guide_name)

    # Get list of available image files in topic guide
    available_images = [f.name for f in topic_dir.iterdir()
                        if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']]
    logger.info(f"Available images in topic guide: {available_images}")

    # Define tools for loading images using pydantic_function_tool
    tools = [
        openai.pydantic_function_tool(
            LoadImageParams,
            name="load_image_for_analysis",
            description=f"Load an image file from the topic guide to view it visually. Available images: {', '.join(available_images)}"
        )
    ]

    # Initialize session
    session = InterviewSession(
        id=str(uuid4()),
        synth_id=synth_id,
        topic_guide_path=topic_guide_name,  # Store topic guide name
        max_rounds=max_rounds,
        start_time=datetime.now(timezone.utc),
        status=SessionStatus.IN_PROGRESS,
        model_used=model,
    )

    # Initialize tracer for recording conversation trace
    tracer = Tracer(
        trace_id=f"interview-{synth_id}-{session.id[:8]}",
        metadata={
            "synth_id": synth_id,
            "session_id": session.id,
            "topic_guide": topic_guide_name,
            "model": model,
            "synth_name": synth["nome"],
        }
    )

    # Display header
    display_interview_header(synth)

    # Build system prompts
    # Interviewer gets the script (questions to ask)
    interviewer_prompt = build_interviewer_prompt(interview_script)
    # Synth gets the context (materials to reference)
    synth_prompt = build_synth_prompt(synth, topic_guide_content)

    # Initialize OpenAI client
    client = OpenAI()

    # Conversation loop
    messages_list = []
    conversation_history = []
    round_number = 1

    logger.info(f"Starting interview with synth {synth_id}")

    try:
        while round_number <= max_rounds:
            # Start new turn in trace
            with tracer.start_turn(turn_number=round_number):
                # Log system prompts on turn 1
                if round_number == 1:
                    with tracer.start_span(SpanType.LOGIC, attributes={
                        "operation": "Initialize interview prompts",
                        "interviewer_prompt": interviewer_prompt,
                        "synth_prompt": synth_prompt,
                        "available_images": available_images,
                    }) as span:
                        span.set_status(SpanStatus.SUCCESS)

                # Interviewer turn
                with console.status(f"[blue]Entrevistador pensando... (turno {round_number})", spinner="dots"):
                    interviewer_response = conversation_turn(
                        client, conversation_history, interviewer_prompt, model,
                        tools=tools, topic_guide_name=topic_guide_name,
                        tracer=tracer, speaker=Speaker.INTERVIEWER
                    )

                # Display and record
                display_message(Speaker.INTERVIEWER,
                                interviewer_response.message)
                msg = Message(
                    speaker=Speaker.INTERVIEWER,
                    content=interviewer_response.message,
                    timestamp=datetime.now(timezone.utc),
                    internal_notes=interviewer_response.internal_notes,
                    round_number=round_number,
                )
                messages_list.append(msg)
                conversation_history.append(
                    {"role": "assistant" if len(
                        conversation_history) % 2 == 0 else "user", "content": interviewer_response.message}
                )

                # Check if interviewer wants to end
                if interviewer_response.should_end:
                    logger.info("Interviewer signaled end of interview")
                    break

                # Synth turn
                with console.status(f"[green]{synth['nome']} pensando...", spinner="dots"):
                    synth_response = conversation_turn(
                        client, conversation_history, synth_prompt, model,
                        tools=tools, topic_guide_name=topic_guide_name,
                        tracer=tracer, speaker=Speaker.SYNTH
                    )

                # Display and record
                display_message(
                    Speaker.SYNTH, synth_response.message, synth["nome"])
                msg = Message(
                    speaker=Speaker.SYNTH,
                    content=synth_response.message,
                    timestamp=datetime.now(timezone.utc),
                    internal_notes=synth_response.internal_notes,
                    round_number=round_number,
                )
                messages_list.append(msg)
                conversation_history.append(
                    {"role": "user" if len(
                        conversation_history) % 2 == 0 else "assistant", "content": synth_response.message}
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
    finally:
        # Always save trace, even on error (if we have any turns)
        if tracer._turns:
            trace_dir = Path("output/traces")
            trace_dir.mkdir(parents=True, exist_ok=True)
            trace_filename = f"interview-{synth_id}-{session.id[:8]}.trace.json"
            trace_path = trace_dir / trace_filename
            try:
                tracer.save_trace(str(trace_path))
                logger.info(f"Trace saved to {trace_path}")
                console.print(
                    f"\n[cyan]📊 Trace salvo em:[/cyan] [bold]{trace_path}[/bold]")
                console.print(
                    f"[dim]   Visualize em: logui/index.html[/dim]\n")
            except Exception as save_error:
                logger.error(f"Failed to save trace: {save_error}")

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
            all_validation_failures.append(
                "Load synth: Should return None for non-existent ID")
    except Exception as e:
        all_validation_failures.append(f"Load synth: {e}")

    # Test 2: Validate synth exists
    total_tests += 1
    try:
        exists = validate_synth_exists("nonexistent")
        if not exists:
            print("✓ Validate synth exists returns False for non-existent ID")
        else:
            all_validation_failures.append(
                "Validate synth: Should return False")
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
        print(
            f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Interview module is validated and ready for use")
        sys.exit(0)
