"""
Runner for orchestrated agentic interviews.

This module provides the main execution loop for multi-agent interviews,
coordinating the orchestrator, interviewer, interviewee, and reviewer agents.

References:
- OpenAI Agents SDK Runner: https://openai.github.io/openai-agents-python/running_agents/
- MCP Integration: https://openai.github.io/openai-agents-python/mcp/

Sample usage:
```python
from synth_lab.research_agentic.runner import run_interview

result = await run_interview(
    synth_id="abc123",
    topic_guide_name="compra-amazon",
    max_turns=6,
    trace_path="output/traces/interview.trace.json"
)
```
"""

from .agent_definitions import (
    create_interviewee,
    create_interviewee_reviewer,
    create_interviewer,
    create_orchestrator,
)
from .tools import create_image_loader_tool, get_available_images
from .tracing_bridge import TraceVisualizerProcessor
import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents import Runner, add_trace_processor, trace
from agents.mcp import MCPServerStdio
from loguru import logger
from rich.console import Console

from synth_lab.trace_visualizer import SpanStatus, SpanType, Tracer

# Console for colored output
_console = Console()


def _print_speaker(speaker: str, message: str) -> None:
    """Print message with colored speaker tag."""
    if speaker == "Interviewer":
        _console.print(f"\n[blue][{speaker}][/blue]")
    else:
        _console.print(f"\n[green][{speaker}][/green]")
    _console.print(message)


@dataclass
class ConversationMessage:
    """A single message in the conversation."""

    speaker: str  # "Interviewer" or "Interviewee"
    text: str  # The visible message (extracted from JSON "message" field)
    raw_text: str | None = None  # Full raw response before parsing
    # Internal notes (not shown to other agents)
    internal_notes: str | None = None
    should_end: bool = False  # Whether agent wants to end the interview


def parse_agent_response(response: str) -> tuple[str, str | None, bool]:
    """
    Parse an agent's JSON response and extract the message.

    Agents return JSON with format:
    {
        "message": "visible message",
        "should_end": false,
        "internal_notes": "private thoughts"
    }

    Args:
        response: Raw response string from agent

    Returns:
        Tuple of (message, internal_notes, should_end)
        If parsing fails, returns (original response, None, False)
    """
    try:
        # Try to parse as JSON
        data = json.loads(response)
        message = data.get("message", response)
        internal_notes = data.get("internal_notes")
        should_end = data.get("should_end", False)
        return message, internal_notes, should_end
    except json.JSONDecodeError:
        # If not valid JSON, return the raw response
        return response, None, False


@dataclass
class SharedMemory:
    """Shared memory between all agents."""

    conversation: list[ConversationMessage] = field(default_factory=list)
    topic_guide: str = ""
    synth: dict[str, Any] = field(default_factory=dict)

    @property
    def synth_name(self) -> str:
        """Get the synth name from the synth dict."""
        return self.synth.get("nome", "Participante")

    def format_history(self) -> str:
        """Format conversation history for agent prompts."""
        if not self.conversation:
            return "(nenhuma mensagem ainda)"

        lines = []
        for msg in self.conversation:
            lines.append(f"[{msg.speaker}]: {msg.text}")
        return "\n\n".join(lines)

    def last_message(self) -> str:
        """Get the last message in the conversation."""
        if not self.conversation:
            return ""
        return f"[{self.conversation[-1].speaker}]: {self.conversation[-1].text}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "conversation": [
                {"speaker": msg.speaker, "text": msg.text}
                for msg in self.conversation
            ],
            "topic_guide": (
                self.topic_guide[:200] + "..."
                if len(self.topic_guide) > 200
                else self.topic_guide
            ),
            "synth_name": self.synth_name,
            "synth_id": self.synth.get("id", ""),
        }


@dataclass
class InterviewResult:
    """Result of a completed interview."""

    messages: list[ConversationMessage]
    synth_id: str
    synth_name: str
    topic_guide_name: str
    trace_path: str | None
    total_turns: int


def load_synth(synth_id: str) -> dict[str, Any]:
    """
    Load a synth by ID from the data file.

    Args:
        synth_id: The synth identifier

    Returns:
        Synth data dictionary

    Raises:
        ValueError: If synth not found
    """
    synths_path = Path("output/synths/synths.json")
    if not synths_path.exists():
        raise FileNotFoundError(f"Synths file not found: {synths_path}")

    with open(synths_path, encoding="utf-8") as f:
        synths = json.load(f)

    for synth in synths:
        if synth.get("id") == synth_id:
            return synth

    raise ValueError(f"Synth not found: {synth_id}")


def load_topic_guide(topic_guide_name: str) -> str:
    """
    Load a topic guide by name.

    Args:
        topic_guide_name: Name of the topic guide directory

    Returns:
        Formatted topic guide content

    Raises:
        FileNotFoundError: If topic guide not found
    """
    topic_guide_path = Path(f"data/topic_guides/{topic_guide_name}")
    if not topic_guide_path.exists():
        raise FileNotFoundError(f"Topic guide not found: {topic_guide_path}")

    # Load script.json if it exists
    script_path = topic_guide_path / "script.json"
    if script_path.exists():
        with open(script_path, encoding="utf-8") as f:
            script = json.load(f)
        return json.dumps(script, indent=2, ensure_ascii=False)

    # Fallback to summary.md
    summary_path = topic_guide_path / "summary.md"
    if summary_path.exists():
        with open(summary_path, encoding="utf-8") as f:
            return f.read()

    raise FileNotFoundError(
        f"No script.json or summary.md in {topic_guide_path}")


def format_synth_profile(synth: dict[str, Any]) -> str:
    """
    Format synth data into a profile string for agent prompts.

    Args:
        synth: Synth data dictionary

    Returns:
        Formatted profile string
    """
    lines = []

    # Demographics
    if "nome" in synth:
        lines.append(f"Nome: {synth['nome']}")
    if "idade" in synth:
        lines.append(f"Idade: {synth['idade']} anos")
    if "genero" in synth:
        lines.append(f"Gênero: {synth['genero']}")
    if "cidade" in synth:
        lines.append(f"Cidade: {synth['cidade']}")
    if "estado" in synth:
        lines.append(f"Estado: {synth['estado']}")

    # Socioeconomic
    if "classe_social" in synth:
        lines.append(f"Classe Social: {synth['classe_social']}")
    if "renda_familiar" in synth:
        lines.append(f"Renda Familiar: {synth['renda_familiar']}")
    if "escolaridade" in synth:
        lines.append(f"Escolaridade: {synth['escolaridade']}")
    if "profissao" in synth:
        lines.append(f"Profissão: {synth['profissao']}")

    # Psychographic
    if "personalidade" in synth:
        lines.append(f"Personalidade: {synth['personalidade']}")
    if "interesses" in synth:
        interests = synth["interesses"]
        if isinstance(interests, list):
            lines.append(f"Interesses: {', '.join(interests)}")
        else:
            lines.append(f"Interesses: {interests}")

    return "\n".join(lines)


async def run_interview(
    synth_id: str,
    topic_guide_name: str,
    max_turns: int = 6,
    trace_path: str | None = None,
    model: str = "gpt-5-mini",
    use_mcp: bool = False,
    mcp_directory: str | None = None,
    verbose: bool = True,
) -> InterviewResult:
    """
    Run an agentic interview with orchestrated turn-taking.

    This function coordinates multiple agents:
    1. Orchestrator: Decides whose turn it is
    2. Interviewer: Asks questions based on topic guide
    3. Interviewee: Responds as synthetic persona
    4. Reviewers: Adapt tone for each speaker

    Args:
        synth_id: ID of the synthetic persona to interview
        topic_guide_name: Name of the topic guide directory
        max_turns: Maximum number of conversation turns
        trace_path: Path to save trace file (optional)
        model: LLM model to use for all agents
        use_mcp: Whether to enable MCP tools (filesystem access)
        mcp_directory: Directory for MCP filesystem server
        verbose: Whether to print conversation to console

    Returns:
        InterviewResult with conversation and metadata

    Sample usage:
    ```python
    result = await run_interview(
        synth_id="abc123",
        topic_guide_name="compra-amazon",
        max_turns=6
    )
    print(f"Completed {result.total_turns} turns")
    for msg in result.messages:
        print(f"[{msg.speaker}]: {msg.text}")
    ```
    """
    # Load data
    synth = load_synth(synth_id)
    topic_guide = load_topic_guide(topic_guide_name)
    synth_name = synth.get("nome", "Participante")

    # Load available images and create image tool for interviewee
    available_images = get_available_images(topic_guide_name)
    image_tool = None
    if available_images:
        image_tool = create_image_loader_tool(
            topic_guide_name, available_images)
        logger.info(
            f"Created image tool with {len(available_images)} images: {available_images}"
        )

    # Initialize shared memory
    shared_memory = SharedMemory(
        topic_guide=topic_guide,
        synth=synth,
    )

    # Initialize tracer for visualization
    trace_id = f"agentic-interview-{synth_id}"
    tracer = Tracer(
        trace_id=trace_id,
        metadata={
            "synth_id": synth_id,
            "synth_name": synth_name,
            "topic_guide": topic_guide_name,
            "model": model,
            "max_turns": str(max_turns),
        },
    )

    # Add custom trace processor to capture SDK traces
    # Note: processor verbose is False to avoid debug spam; conversation verbose is separate
    processor = TraceVisualizerProcessor(tracer, verbose=False)
    add_trace_processor(processor)

    # Setup MCP servers if enabled
    mcp_servers: list[Any] = []

    try:
        if use_mcp and mcp_directory:
            # TODO: MCP servers need async context management
            # For now, we create and add to list for future implementation
            _ = MCPServerStdio(
                name="Filesystem Server",
                params={
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", mcp_directory],
                },
            )
            # mcp_servers.append(mcp_server)  # Enable when async context is implemented

        # Main interview loop
        turns = 0

        with trace(f"Interview with {synth_name}"):
            while turns < max_turns:
                with tracer.start_turn(turn_number=turns + 1):
                    # Log turn start
                    with tracer.start_span(SpanType.LOGIC, {
                        "operation": "determine_speaker",
                        "turn_number": turns + 1,
                    }) as span:
                        # Determine who speaks next
                        orchestrator = create_orchestrator(
                            conversation_history=shared_memory.format_history(),
                            last_message=shared_memory.last_message(),
                            model=model,
                        )

                        decision_result = await Runner.run(
                            orchestrator,
                            input=f"Turn {turns + 1}: Who speaks next?"
                        )
                        decision = decision_result.final_output.strip()
                        span.set_attribute("decision", decision)
                        span.set_status(SpanStatus.SUCCESS)

                    if "Interviewer" in decision:
                        # Interviewer's turn
                        with tracer.start_span(SpanType.LLM_CALL, {
                            "speaker": "interviewer",
                            "turn_number": turns + 1,
                        }) as span:
                            interviewer = create_interviewer(
                                topic_guide=topic_guide,
                                conversation_history=shared_memory.format_history(),
                                mcp_servers=mcp_servers,
                                model=model,
                            )

                            raw_result = await Runner.run(
                                interviewer,
                                input="Faça sua próxima pergunta ou comentário."
                            )
                            final_response = raw_result.final_output
                            span.set_attribute("response", final_response)
                            span.set_status(SpanStatus.SUCCESS)

                        speaker = "Interviewer"

                    else:
                        # Interviewee's turn
                        with tracer.start_span(SpanType.LLM_CALL, {
                            "speaker": "interviewee",
                            "turn_number": turns + 1,
                        }) as span:
                            # Prepare tools for interviewee (image access)
                            interviewee_tools = [
                                image_tool] if image_tool else []

                            interviewee = create_interviewee(
                                synth=shared_memory.synth,
                                conversation_history=shared_memory.format_history(),
                                mcp_servers=mcp_servers,
                                tools=interviewee_tools,
                                available_images=available_images,
                                model=model,
                            )

                            raw_result = await Runner.run(
                                interviewee,
                                input="Responda à última pergunta."
                            )
                            raw_response = raw_result.final_output
                            span.set_attribute("raw_response", raw_response)

                        # Review interviewee response
                        with tracer.start_span(SpanType.LLM_CALL, {
                            "speaker": "interviewee_reviewer",
                            "turn_number": turns + 1,
                        }) as span:
                            reviewer = create_interviewee_reviewer(
                                synth=shared_memory.synth,
                                raw_response=raw_response,
                                model=model,
                            )

                            review_result = await Runner.run(
                                reviewer,
                                input="Revise esta resposta para maior autenticidade."
                            )
                            final_response = review_result.final_output
                            span.set_attribute(
                                "final_response", final_response)
                            span.set_status(SpanStatus.SUCCESS)

                        speaker = "Interviewee"

                    # Parse JSON response to extract only the message
                    visible_message, internal_notes, should_end = parse_agent_response(
                        final_response
                    )

                    # Add to shared memory (only visible message goes to history)
                    message = ConversationMessage(
                        speaker=speaker,
                        text=visible_message,
                        raw_text=final_response,
                        internal_notes=internal_notes,
                        should_end=should_end,
                    )
                    shared_memory.conversation.append(message)

                    # Log to console
                    if verbose:
                        _print_speaker(speaker, visible_message)

                turns += 1

    finally:
        # Save trace
        if trace_path and tracer._turns:
            Path(trace_path).parent.mkdir(parents=True, exist_ok=True)
            tracer.save_trace(trace_path)
            if verbose:
                logger.info(f"Trace saved to: {trace_path}")

        # Cleanup processor
        processor.shutdown()

    return InterviewResult(
        messages=shared_memory.conversation,
        synth_id=synth_id,
        synth_name=synth_name,
        topic_guide_name=topic_guide_name,
        trace_path=trace_path,
        total_turns=turns,
    )


async def run_interview_simple(
    topic: str,
    synth_id: str | None = None,
    persona_description: str | None = None,
    max_turns: int = 4,
    model: str = "gpt-5-mini",
    verbose: bool = True,
) -> list[ConversationMessage]:
    """
    Run a simple interview, optionally loading synth from database.

    Useful for quick testing or when full topic guide isn't needed.

    Args:
        topic: Topic to discuss in the interview
        synth_id: Optional synth ID to load from database
        persona_description: Optional description if not using synth_id (deprecated)
        max_turns: Maximum conversation turns
        model: LLM model to use
        verbose: Whether to print to console

    Returns:
        List of conversation messages

    Note:
        Either synth_id or persona_description must be provided.
        If synth_id is provided, it takes precedence.
    """
    # Load synth from database or build minimal synth dict
    if synth_id:
        synth = load_synth(synth_id)
    elif persona_description:
        # Build minimal synth dict from description (for backwards compatibility)
        synth = {
            "nome": "Participante",
            "descricao": persona_description,
            "demografia": {},
            "psicografia": {"interesses": []},
        }
    else:
        raise ValueError(
            "Either synth_id or persona_description must be provided")

    shared_memory = SharedMemory(
        topic_guide=f"Tema da entrevista: {topic}",
        synth=synth,
    )

    messages: list[ConversationMessage] = []
    turns = 0

    while turns < max_turns:
        # Determine speaker
        orchestrator = create_orchestrator(
            conversation_history=shared_memory.format_history(),
            last_message=shared_memory.last_message(),
            model=model,
        )

        decision_result = await Runner.run(orchestrator, input="Who speaks next?")
        decision = decision_result.final_output.strip()

        if "Interviewer" in decision:
            # Interviewer speaks
            interviewer = create_interviewer(
                topic_guide=shared_memory.topic_guide,
                conversation_history=shared_memory.format_history(),
                model=model,
            )

            result = await Runner.run(interviewer, input="Ask your question.")
            response = result.final_output
            speaker = "Interviewer"

        else:
            # Interviewee speaks
            interviewee = create_interviewee(
                synth=shared_memory.synth,
                conversation_history=shared_memory.format_history(),
                model=model,
            )

            result = await Runner.run(interviewee, input="Answer the question.")
            response = result.final_output
            speaker = "Interviewee"

        # Parse JSON response to extract only the message
        visible_message, internal_notes, should_end = parse_agent_response(
            response)

        message = ConversationMessage(
            speaker=speaker,
            text=visible_message,
            raw_text=response,
            internal_notes=internal_notes,
            should_end=should_end,
        )
        messages.append(message)
        shared_memory.conversation.append(message)

        if verbose:
            _print_speaker(speaker, visible_message)

        turns += 1

    return messages


# Convenience function for sync usage
def run_interview_sync(
    synth_id: str,
    topic_guide_name: str,
    max_turns: int = 6,
    trace_path: str | None = None,
    model: str = "gpt-5-mini",
    verbose: bool = True,
) -> InterviewResult:
    """
    Synchronous wrapper for run_interview.

    Args:
        synth_id: ID of the synthetic persona
        topic_guide_name: Name of the topic guide
        max_turns: Maximum conversation turns
        trace_path: Path to save trace file
        model: LLM model to use
        verbose: Whether to print to console

    Returns:
        InterviewResult with conversation and metadata
    """
    return asyncio.run(
        run_interview(
            synth_id=synth_id,
            topic_guide_name=topic_guide_name,
            max_turns=max_turns,
            trace_path=trace_path,
            model=model,
            verbose=verbose,
        )
    )


if __name__ == "__main__":
    # Simple test
    async def test_simple():
        messages = await run_interview_simple(
            topic="Experiência de compras online",
            persona_description=(
                "Mulher, 35 anos, classe média, mora em São Paulo, "
                "trabalha como professora"
            ),
            max_turns=4,
            verbose=True,
        )
        print(f"\n\nTotal messages: {len(messages)}")

    asyncio.run(test_simple())
