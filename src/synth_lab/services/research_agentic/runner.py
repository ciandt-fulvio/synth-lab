"""
Runner for orchestrated agentic interviews.

This module provides the main execution loop for multi-agent interviews,
coordinating the orchestrator, interviewer, interviewee, and reviewer agents.

References:
- OpenAI Agents SDK Runner: https://openai.github.io/openai-agents-python/running_agents/
- MCP Integration: https://openai.github.io/openai-agents-python/mcp/

Sample usage:
```python
from .runner import run_interview

result = await run_interview(
    synth_id="abc123",
    topic_guide_name="compra-amazon",
    max_turns=6,
    trace_path="output/traces/interview.trace.json"
)
```
"""

import asyncio
import json
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents import Runner, add_trace_processor, trace
from agents.mcp import MCPServerStdio
from loguru import logger
from rich.console import Console

from synth_lab.trace_visualizer import SpanStatus, SpanType, Tracer

from .agent_definitions import (
    create_interviewee,
    create_interviewee_reviewer,
    create_interviewer,
)
from .tools import create_image_loader_tool, get_available_images
from .tracing_bridge import TraceVisualizerProcessor

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
    sentiment: int | None = None  # 1-5 sentiment score (only set by Interviewer)


def parse_agent_response(response: str) -> tuple[str, str | None, bool, int | None]:
    """
    Parse an agent's JSON response and extract the message.

    Agents return JSON with format:
    {
        "message": "visible message",
        "should_end": false,
        "internal_notes": "private thoughts",
        "sentiment": 3
    }

    Args:
        response: Raw response string from agent

    Returns:
        Tuple of (message, internal_notes, should_end, sentiment)
        If parsing fails, returns (original response, None, False, None)
    """
    try:
        # Try to parse as JSON
        data = json.loads(response)
        message = data.get("message", response)
        internal_notes = data.get("internal_notes")
        should_end = data.get("should_end", False)
        sentiment = data.get("sentiment")
        # Validate sentiment is in range 1-5
        if sentiment is not None:
            sentiment = max(1, min(5, int(sentiment)))
        return message, internal_notes, should_end, sentiment
    except json.JSONDecodeError:
        # If not valid JSON, return the raw response
        return response, None, False, None


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
    Load a synth by ID from the database.

    Args:
        synth_id: The synth identifier

    Returns:
        Synth data dictionary

    Raises:
        ValueError: If synth not found
    """
    from synth_lab.gen_synth.storage import get_synth_by_id

    synth = get_synth_by_id(synth_id)
    if synth is None:
        raise ValueError(f"Synth not found: {synth_id}")

    return synth


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
    from synth_lab.infrastructure.config import resolve_topic_guide_path

    topic_guide_path = resolve_topic_guide_path(topic_guide_name)
    if topic_guide_path is None:
        raise FileNotFoundError(f"Topic guide not found: {topic_guide_name}")

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


def load_context_definition(topic_guide_name: str) -> str | None:
    """
    Load context definition from the topic guide script.json.

    Args:
        topic_guide_name: Name of the topic guide directory

    Returns:
        Context definition string or None if not found
    """
    from synth_lab.infrastructure.config import resolve_topic_guide_path

    topic_guide_path = resolve_topic_guide_path(topic_guide_name)
    if topic_guide_path is None:
        return None

    script_path = topic_guide_path / "script.json"
    if not script_path.exists():
        return None

    with open(script_path, encoding="utf-8") as f:
        script = json.load(f)

    # Get context_definition from first item in script
    if script and isinstance(script, list) and len(script) > 0:
        return script[0].get("context_definition")

    return None


def load_context_examples(topic_guide_name: str) -> dict[str, str] | None:
    """
    Load context examples from the topic guide script.json.

    Args:
        topic_guide_name: Name of the topic guide directory

    Returns:
        Dictionary with 'positive', 'negative', 'neutral' examples or None
    """
    from synth_lab.infrastructure.config import resolve_topic_guide_path

    topic_guide_path = resolve_topic_guide_path(topic_guide_name)
    if topic_guide_path is None:
        return None

    script_path = topic_guide_path / "script.json"
    if not script_path.exists():
        return None

    with open(script_path, encoding="utf-8") as f:
        script = json.load(f)

    # Get context_examples from first item in script
    if script and isinstance(script, list) and len(script) > 0:
        return script[0].get("context_examples")

    return None


async def generate_initial_context(
    synth: dict[str, Any],
    context_examples: dict[str, str],
    topic_guide: str,
    model: str = "gpt-4.1-mini",
    context_definition: str | None = None,
    additional_context: str | None = None,
) -> str:
    """
    Generate initial context for the interviewee based on examples.

    Randomly selects positive, negative, or neutral sentiment and generates
    a personalized context using the synth's profile.

    Args:
        synth: Synth data dictionary
        context_examples: Dict with 'positive', 'negative', 'neutral' examples
        topic_guide: Topic guide content for context
        model: LLM model to use
        context_definition: Optional definition/purpose of the context
        additional_context: Optional additional context to complement the scenario

    Returns:
        Generated initial context string
    """
    from agents import Agent
    from agents import Runner as AgentRunner

    # Randomly choose sentiment
    sentiment = random.choice(["positive", "negative", "neutral"])
    example = context_examples.get(sentiment, "")

    if not example:
        return ""

    # Build synth profile summary
    nome = synth.get("nome", "Participante")
    demo = synth.get("demografia", {})
    idade = demo.get("idade", "desconhecida")
    ocupacao = demo.get("ocupacao", "não informada")
    cidade = demo.get("localizacao", {}).get("cidade", "não informada")

    # Build context definition section
    context_def_section = ""
    if context_definition:
        context_def_section = f"""
CONTEXTO:
{context_definition}
"""

    # Build additional context section
    additional_context_section = ""
    if additional_context:
        additional_context_section = f"""
CONTEXTO ADICIONAL:
{additional_context}
"""

    prompt = f"""Você deve gerar uma experiência pessoal para {nome}, {idade} anos, {ocupacao}, de {cidade}.

RELATIVO A:
{context_def_section}
{additional_context_section}

TIPO DE EXPERIÊNCIA: {sentiment.upper()}

EXEMPLO DE REFERÊNCIA (adapte para o perfil da pessoa):
{example}

REGRAS:
- Gere uma experiência {sentiment} única e personalizada para esta pessoa
- Use linguagem natural e coloquial adequada ao perfil
- Inclua detalhes concretos (datas, situações, emoções)
- Máximo 3-4 frases
- NÃO copie o exemplo literalmente, apenas use como inspiração

Responda APENAS com a experiência gerada, sem explicações adicionais."""

    context_agent = Agent(
        name="Context Generator",
        instructions="Você é um gerador de contextos para personas sintéticas. Gere experiências realistas e personalizadas.",
        model=model,
    )

    result = await AgentRunner.run(context_agent, input=prompt)
    generated_context = result.final_output.strip()

    logger.info(
        f"Generated {sentiment} context for {nome}: {generated_context[:100]}...")

    return f"[EXPERIÊNCIA PRÉVIA - {sentiment.upper()}]: {generated_context}"


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
    model: str = "gpt-4.1-mini",
    use_mcp: bool = False,
    mcp_directory: str | None = None,
    verbose: bool = True,
    exec_id: str | None = None,
    message_callback: Callable[[
        str, str, int, ConversationMessage], Awaitable[None]] | None = None,
    skip_interviewee_review: bool = True,
    additional_context: str | None = None,
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
        exec_id: Execution ID for SSE streaming (optional)
        message_callback: Async callback for real-time message streaming (optional)
            Signature: (exec_id, synth_id, turn_number, message) -> None
        skip_interviewee_review: Whether to skip the interviewee response reviewer.
            If True, uses raw interviewee response without humanization review.
        additional_context: Optional additional context to complement the research scenario

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

    context_definition = load_context_definition(topic_guide_name)

    # Load context examples for generating initial context
    context_examples = load_context_examples(topic_guide_name)

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

    # Initial context will be generated in parallel with first interviewer turn
    initial_context: str = ""

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
        # Each "turn" is a complete exchange: interviewer question + interviewee answer
        turns = 0

        with trace(f"Interview with {synth_name}"):
            while turns < max_turns:
                with tracer.start_turn(turn_number=turns + 1):
                    # === PART 1: Interviewer asks a question ===
                    interviewer_input = "Faça sua próxima pergunta ou comentário."
                    with tracer.start_span(SpanType.LLM_CALL, {
                        "speaker": "interviewer",
                        "turn_number": turns + 1,
                    }) as span:
                        interviewer = create_interviewer(
                            topic_guide=topic_guide,
                            conversation_history=shared_memory.format_history(),
                            max_turns=max_turns,
                            mcp_servers=mcp_servers,
                            model=model,
                            additional_context=additional_context,
                        )

                        # Log request (system prompt + input)
                        span.set_attribute(
                            "request", f"[System Prompt]\n{interviewer.instructions}\n\n[Input]\n{interviewer_input}")

                        # On first turn, generate context in parallel with interviewer
                        if turns == 0 and context_examples:
                            # Run both in parallel
                            interviewer_task = Runner.run(
                                interviewer,
                                input=interviewer_input
                            )
                            context_task = generate_initial_context(
                                synth=synth,
                                context_examples=context_examples,
                                topic_guide=topic_guide,
                                model=model,
                                context_definition=context_definition,
                                additional_context=additional_context,
                            )
                            raw_result, initial_context = await asyncio.gather(
                                interviewer_task, context_task
                            )
                            logger.info(
                                f"Generated initial context: {initial_context[:80]}...")
                        else:
                            raw_result = await Runner.run(
                                interviewer,
                                input=interviewer_input
                            )

                        interviewer_response = raw_result.final_output
                        span.set_attribute("response", interviewer_response)
                        span.set_status(SpanStatus.SUCCESS)

                    # Parse and add interviewer message
                    visible_message, internal_notes, should_end, sentiment = parse_agent_response(
                        interviewer_response
                    )
                    interviewer_msg = ConversationMessage(
                        speaker="Interviewer",
                        text=visible_message,
                        raw_text=interviewer_response,
                        internal_notes=internal_notes,
                        should_end=should_end,
                        sentiment=sentiment,
                    )
                    shared_memory.conversation.append(interviewer_msg)

                    # Publish interviewer message in real-time
                    if message_callback and exec_id:
                        await message_callback(exec_id, synth_id, turns + 1, interviewer_msg)

                    if verbose:
                        _print_speaker("Interviewer", visible_message)

                    # === PART 2: Interviewee responds ===
                    interviewee_input = "Responda à última pergunta."
                    with tracer.start_span(SpanType.LLM_CALL, {
                        "speaker": "interviewee",
                        "turn_number": turns + 1,
                    }) as span:
                        # Prepare tools for interviewee (image access)
                        interviewee_tools = [image_tool] if image_tool else []

                        interviewee = create_interviewee(
                            synth=shared_memory.synth,
                            conversation_history=shared_memory.format_history(),
                            mcp_servers=mcp_servers,
                            tools=interviewee_tools,
                            available_images=available_images,
                            initial_context=initial_context,
                            model=model,
                        )

                        # Log request (system prompt + input)
                        span.set_attribute(
                            "request", f"[System Prompt]\n{interviewee.instructions}\n\n[Input]\n{interviewee_input}")

                        raw_result = await Runner.run(
                            interviewee,
                            input=interviewee_input
                        )
                        raw_response = raw_result.final_output
                        span.set_attribute("response", raw_response)
                        span.set_status(SpanStatus.SUCCESS)

                    # Review interviewee response (optional)
                    if skip_interviewee_review:
                        interviewee_response = raw_response
                        logger.debug("Skipping interviewee reviewer")
                    else:
                        reviewer_input = "Revise esta resposta para maior autenticidade."
                        with tracer.start_span(SpanType.LLM_CALL, {
                            "speaker": "interviewee_reviewer",
                            "turn_number": turns + 1,
                        }) as span:
                            reviewer = create_interviewee_reviewer(
                                synth=shared_memory.synth,
                                raw_response=raw_response,
                                model=model,
                            )

                            span.set_attribute(
                                "request", f"[System Prompt]\n{reviewer.instructions}\n\n[Input]\n{reviewer_input}")

                            review_result = await Runner.run(
                                reviewer,
                                input=reviewer_input
                            )
                            interviewee_response = review_result.final_output
                            span.set_attribute(
                                "response", interviewee_response)
                            span.set_status(SpanStatus.SUCCESS)

                    # Parse and add interviewee message (sentiment not used for interviewee)
                    visible_message, internal_notes, should_end, _ = parse_agent_response(
                        interviewee_response
                    )
                    interviewee_msg = ConversationMessage(
                        speaker="Interviewee",
                        text=visible_message,
                        raw_text=interviewee_response,
                        internal_notes=internal_notes,
                        should_end=should_end,
                    )
                    shared_memory.conversation.append(interviewee_msg)

                    # Publish interviewee message in real-time
                    if message_callback and exec_id:
                        await message_callback(exec_id, synth_id, turns + 1, interviewee_msg)

                    if verbose:
                        _print_speaker("Interviewee", visible_message)

                # Turn complete (1 turn = 1 question + 1 answer)
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
    model: str = "gpt-4.1-mini",
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

    # Each turn = 1 question + 1 answer
    while turns < max_turns:
        # === PART 1: Interviewer asks ===
        interviewer = create_interviewer(
            topic_guide=shared_memory.topic_guide,
            conversation_history=shared_memory.format_history(),
            max_turns=max_turns,
            model=model,
        )

        result = await Runner.run(interviewer, input="Ask your question.")
        response = result.final_output

        visible_message, internal_notes, should_end, sentiment = parse_agent_response(
            response)
        interviewer_msg = ConversationMessage(
            speaker="Interviewer",
            text=visible_message,
            raw_text=response,
            internal_notes=internal_notes,
            should_end=should_end,
            sentiment=sentiment,
        )
        messages.append(interviewer_msg)
        shared_memory.conversation.append(interviewer_msg)

        if verbose:
            _print_speaker("Interviewer", visible_message)

        # === PART 2: Interviewee responds ===
        interviewee = create_interviewee(
            synth=shared_memory.synth,
            conversation_history=shared_memory.format_history(),
            model=model,
        )

        result = await Runner.run(interviewee, input="Answer the question.")
        response = result.final_output

        visible_message, internal_notes, should_end, _ = parse_agent_response(
            response)
        interviewee_msg = ConversationMessage(
            speaker="Interviewee",
            text=visible_message,
            raw_text=response,
            internal_notes=internal_notes,
            should_end=should_end,
        )
        messages.append(interviewee_msg)
        shared_memory.conversation.append(interviewee_msg)

        if verbose:
            _print_speaker("Interviewee", visible_message)

        # Turn complete (1 turn = 1 question + 1 answer)
        turns += 1

    return messages


# Convenience function for sync usage
def run_interview_sync(
    synth_id: str,
    topic_guide_name: str,
    max_turns: int = 6,
    trace_path: str | None = None,
    model: str = "gpt-4.1-mini",
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
