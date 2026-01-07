"""
Runner for orchestrated agentic interviews.

This module provides the main execution loop for multi-agent interviews,
coordinating the orchestrator, interviewer, interviewee, and reviewer agents.

References:
- OpenAI Agents SDK Runner: https://openai.github.io/openai-agents-python/running_agents/

Sample usage:
```python
from .runner import run_interview

result = await run_interview(
    synth_id="abc123",
    context_definition="Contexto da pesquisa...",
    questions="Q1: Pergunta 1?\nQ2: Pergunta 2?",
    max_turns=6)
```
"""

import asyncio
import json
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from synth_lab.domain.entities.synth_outcome import SynthOutcome

from agents import Runner, add_trace_processor, trace
from loguru import logger
from rich.console import Console

from synth_lab.trace_visualizer import SpanStatus, SpanType, Tracer

from .agent_definitions import (
    create_interviewee,
    create_interviewee_reviewer,
    create_interviewer)
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
                {"speaker": msg.speaker, "text": msg.text} for msg in self.conversation
            ],
            "topic_guide": (
                self.topic_guide[:200] + "..." if len(self.topic_guide) > 200 else self.topic_guide
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
    topic_guide_name: str  # Kept for backward compatibility (can be experiment_id)
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


@dataclass
class InterviewGuideData:
    """Data from interview_guide table."""

    context_definition: str | None = None
    questions: str | None = None
    context_examples: str | None = None

    def get_context_examples_dict(self) -> dict[str, str] | None:
        """Parse context_examples string into dict with positive/negative/neutral."""
        if not self.context_examples:
            return None

        # If it's already structured, return as a dict with a single "example" key
        # The context_examples is free text, so we'll use it as a neutral example
        return {
            "positive": self.context_examples,
            "negative": self.context_examples,
            "neutral": self.context_examples,
        }


def build_topic_guide_from_interview_guide(guide: InterviewGuideData) -> str:
    """
    Build a topic guide string from interview_guide data.

    Args:
        guide: InterviewGuideData with context, questions, examples

    Returns:
        Formatted topic guide string for the interviewer agent
    """
    parts = []

    if guide.context_definition:
        parts.append(f"CONTEXTO DA PESQUISA:\n{guide.context_definition}")

    if guide.questions:
        parts.append(f"PERGUNTAS DO GUIA:\n{guide.questions}")

    if guide.context_examples:
        parts.append(f"EXEMPLOS DE CONTEXTO:\n{guide.context_examples}")

    return "\n\n".join(parts) if parts else "Conduza uma entrevista exploratória."


async def generate_initial_context(
    synth: dict[str, Any],
    context_examples: dict[str, str],
    topic_guide: str,
    model: str = "gpt-4o-mini",
    context_definition: str | None = None,
    additional_context: str | None = None,
    synth_outcome: "SynthOutcome | None" = None,
    avg_success_rate: float | None = None) -> str:
    """
    Generate initial context for the interviewee based on examples.

    When simulation data is provided, uses it to determine appropriate sentiment.
    Otherwise falls back to random selection.

    Args:
        synth: Synth data dictionary
        context_examples: Dict with 'positive', 'negative', 'neutral' examples
        topic_guide: Topic guide content for context
        model: LLM model to use
        context_definition: Optional definition/purpose of the context
        additional_context: Optional additional context to complement the scenario
        synth_outcome: Optional simulation outcome for data-driven sentiment selection
        avg_success_rate: Optional average success rate for comparison

    Returns:
        Generated initial context string
    """
    from agents import Agent
    from agents import Runner as AgentRunner

    from synth_lab.services.research_agentic.context_formatter import (
        ExperienceClassification,
        classify_experience)

    # Determine sentiment based on simulation data or randomly
    classification: ExperienceClassification | None = None
    if synth_outcome is not None and avg_success_rate is not None:
        classification = classify_experience(synth_outcome, avg_success_rate)
        sentiment = classification.sentiment
        logger.info(
            f"Classified experience for synth {synth_outcome.synth_id}: "
            f"{sentiment} ({classification.reason})"
        )
    else:
        # Fallback: random selection when no simulation data
        sentiment = random.choice(["positive", "negative", "neutral"])
        logger.debug(f"No simulation data, using random sentiment: {sentiment}")

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

    # Build simulation data section (when available)
    simulation_data_section = ""
    behavior_section = ""
    simulation_rules = ""

    if classification is not None and synth_outcome is not None:
        success_pct = int(synth_outcome.success_rate * 100)
        avg_pct = int(avg_success_rate * 100) if avg_success_rate else 0
        attempt_pct = int((1 - synth_outcome.did_not_try_rate) * 100)

        # Determine position relative to average
        if classification.sentiment == "positive":
            position = "ACIMA DA MÉDIA - experiência predominantemente positiva"
        elif classification.sentiment == "negative":
            position = "ABAIXO DA MÉDIA - experiência predominantemente negativa"
        else:
            position = "NA MÉDIA - experiência mista"

        simulation_data_section = f"""
DADOS DA SIMULAÇÃO:
- Taxa de sucesso: {success_pct}% (média do experimento: {avg_pct}%)
- Taxa de tentativa: {attempt_pct}% (tentou usar)
- Classificação: {position}
"""

        # Add behavior context for non-attempt patterns
        if classification.non_attempt_reason:
            behavior_section = f"""
COMPORTAMENTO DE USO:
Esta pessoa tentou usar a funcionalidade apenas {attempt_pct}% das vezes.
Possível motivo: {classification.non_attempt_reason}
"""

        # Add simulation-aware rules
        outcome_desc = "SUCESSO frequente" if success_pct > 50 else "DIFICULDADES"
        simulation_rules = (
            f"\n- A experiência deve refletir alguém que teve {outcome_desc} ({success_pct}%)"
        )

    # Build additional context section
    additional_context_section = ""
    if additional_context:
        additional_context_section = f"""
CONTEXTO ADICIONAL:
{additional_context}
"""

    # Build prompt header
    header = (
        f"Você deve gerar uma experiência pessoal para {nome}, "
        f"{idade} anos, {ocupacao}, de {cidade}."
    )

    prompt = f"""{header}

RELATIVO A:
{context_def_section}{simulation_data_section}{behavior_section}{additional_context_section}

TIPO DE EXPERIÊNCIA: {sentiment.upper()}

EXEMPLO DE REFERÊNCIA (adapte para o perfil da pessoa):
{example}

REGRAS:
- Gere uma experiência {sentiment} única e personalizada para esta pessoa
- Use linguagem natural e coloquial adequada ao perfil
- Inclua detalhes concretos (datas, situações, emoções)
- Máximo 3-4 frases
- NÃO copie o exemplo literalmente, apenas use como inspiração{simulation_rules}

Responda APENAS com a experiência gerada, sem explicações adicionais."""

    context_agent = Agent(
        name="Context Generator",
        instructions=(
            "Você é um gerador de contextos para personas sintéticas. "
            "Gere experiências realistas e personalizadas."
        ),
        model=model)

    result = await AgentRunner.run(context_agent, input=prompt)
    generated_context = result.final_output.strip()

    logger.info(f"Generated {sentiment} context for {nome}: {generated_context[:100]}...")

    return f"[EXPERIÊNCIA PRÉVIA - {sentiment.upper()}]: {generated_context}"


def _get_simulation_context_for_synth(synth_id: str, analysis_id: str) -> str:
    """
    Fetch simulation results and format as context for interview.

    Args:
        synth_id: The synth ID
        analysis_id: The analysis ID to fetch results from

    Returns:
        Formatted simulation context string, or empty string if not found
    """
    from synth_lab.repositories.synth_outcome_repository import SynthOutcomeRepository
    from synth_lab.services.research_agentic.context_formatter import (
        create_simulation_context_from_outcome,
        format_simulation_context)

    try:
        repo = SynthOutcomeRepository()
        outcome = repo.get_by_synth_and_analysis(synth_id, analysis_id)

        if outcome is None:
            logger.debug(f"No simulation results for synth {synth_id} in analysis {analysis_id}")
            return ""

        context = create_simulation_context_from_outcome(outcome)
        return format_simulation_context(context)

    except Exception as e:
        logger.warning(f"Failed to fetch simulation context: {e}")
        return ""


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
    interview_guide: InterviewGuideData,
    max_turns: int = 6,
    trace_path: str | None = None,
    model: str = "gpt-4o-mini",
    verbose: bool = True,
    exec_id: str | None = None,
    message_callback: Callable[[str, str, int, ConversationMessage], Awaitable[None]] | None = None,
    skip_interviewee_review: bool = True,
    additional_context: str | None = None,
    guide_name: str = "interview",
    analysis_id: str | None = None,
    materials: list | None = None) -> InterviewResult:
    """
    Run an agentic interview with orchestrated turn-taking.

    This function coordinates multiple agents:
    1. Interviewer: Asks questions based on interview guide
    2. Interviewee: Responds as synthetic persona
    3. Reviewer (optional): Adapts tone for interviewee

    Args:
        synth_id: ID of the synthetic persona to interview
        interview_guide: InterviewGuideData with context_definition, questions, examples
        max_turns: Maximum number of conversation turns
        trace_path: Path to save trace file (optional)
        model: LLM model to use for all agents
        verbose: Whether to print conversation to console
        exec_id: Execution ID for SSE streaming (optional)
        message_callback: Async callback for real-time message streaming (optional)
            Signature: (exec_id, synth_id, turn_number, message) -> None
        skip_interviewee_review: Whether to skip the interviewee response reviewer.
            If True, uses raw interviewee response without humanization review.
        additional_context: Optional additional context to complement the research scenario
        guide_name: Name identifier for the guide (for logging/tracing)
        analysis_id: Optional analysis ID to fetch simulation results for context.
            When provided, synth's simulation performance is included in the
            interviewee prompt for coherent behavior.
        materials: Optional list of ExperimentMaterial objects to include in prompts.
            When provided, materials are accessible to both interviewer and interviewee.

    Returns:
        InterviewResult with conversation and metadata

    Sample usage:
    ```python
    guide = InterviewGuideData(
        context_definition="Pesquisa sobre checkout 1-clique",
        questions="Q1: Como você se sente...?",
        context_examples="Exemplo de experiência positiva...")
    result = await run_interview(
        synth_id="abc123",
        interview_guide=guide,
        max_turns=6,
        analysis_id="ana_12345678",  # Include simulation context
    )
    ```
    """
    # Load synth data
    synth = load_synth(synth_id)
    synth_name = synth.get("nome", "Participante")

    # Build topic guide from interview_guide data
    topic_guide = build_topic_guide_from_interview_guide(interview_guide)

    # Get context examples for generating initial context
    context_examples = interview_guide.get_context_examples_dict()

    # Fetch simulation data if analysis_id provided
    simulation_context_text: str = ""
    synth_outcome: "SynthOutcome | None" = None
    avg_success_rate: float | None = None

    if analysis_id:
        from synth_lab.domain.entities.synth_outcome import SynthOutcome
        from synth_lab.repositories.synth_outcome_repository import SynthOutcomeRepository

        outcome_repo = SynthOutcomeRepository()

        # Get synth's simulation outcome
        synth_outcome = outcome_repo.get_by_synth_and_analysis(synth_id, analysis_id)

        # Get analysis statistics for comparison
        stats = outcome_repo.get_analysis_statistics(analysis_id)
        if stats:
            avg_success_rate = stats["avg_success_rate"]

        # Get formatted simulation context for interviewee prompt
        simulation_context_text = _get_simulation_context_for_synth(synth_id, analysis_id)
        if simulation_context_text:
            logger.info(f"Using simulation context for {synth_name} from {analysis_id}")
        if synth_outcome and avg_success_rate is not None:
            logger.info(
                f"Simulation data: success={synth_outcome.success_rate:.0%}, "
                f"avg={avg_success_rate:.0%}"
            )

    # Initialize shared memory
    shared_memory = SharedMemory(
        topic_guide=topic_guide,
        synth=synth)

    # Initial context will be generated in parallel with first interviewer turn
    # If we have simulation context, prepend it
    initial_context: str = simulation_context_text

    # Initialize tracer for visualization
    trace_id = f"agentic-interview-{synth_id}"
    tracer = Tracer(
        trace_id=trace_id,
        metadata={
            "synth_id": synth_id,
            "synth_name": synth_name,
            "guide_name": guide_name,
            "model": model,
            "max_turns": str(max_turns),
        })

    # Add custom trace processor to capture SDK traces
    processor = TraceVisualizerProcessor(tracer, verbose=False)
    add_trace_processor(processor)

    try:
        # Main interview loop
        # Each "turn" is a complete exchange: interviewer question + interviewee answer
        turns = 0

        with trace(f"Interview with {synth_name}"):
            while turns < max_turns:
                with tracer.start_turn(turn_number=turns + 1):
                    # === PART 1: Interviewer asks a question ===
                    interviewer_input = "Faça sua próxima pergunta ou comentário."
                    with tracer.start_span(
                        SpanType.LLM_CALL,
                        {
                            "speaker": "interviewer",
                            "turn_number": turns + 1,
                        }) as span:
                        interviewer = create_interviewer(
                            topic_guide=topic_guide,
                            conversation_history=shared_memory.format_history(),
                            max_turns=max_turns,
                            model=model,
                            additional_context=additional_context,
                            materials=materials)

                        # Log request
                        span.set_attribute(
                            "request",
                            f"[System Prompt]\n{interviewer.instructions}\n\n[Input]\n{interviewer_input}")

                        # On first turn, generate context in parallel with interviewer
                        if turns == 0 and context_examples:
                            # Run both in parallel
                            interviewer_task = Runner.run(interviewer, input=interviewer_input)
                            context_task = generate_initial_context(
                                synth=synth,
                                context_examples=context_examples,
                                topic_guide=topic_guide,
                                model=model,
                                context_definition=interview_guide.context_definition,
                                additional_context=additional_context,
                                synth_outcome=synth_outcome,
                                avg_success_rate=avg_success_rate)
                            raw_result, generated_context = await asyncio.gather(
                                interviewer_task, context_task
                            )
                            # Combine simulation context with generated context
                            if initial_context and generated_context:
                                initial_context = f"{initial_context}\n\n{generated_context}"
                            elif generated_context:
                                initial_context = generated_context
                            logger.info(f"Generated initial context: {initial_context[:80]}...")
                        else:
                            raw_result = await Runner.run(interviewer, input=interviewer_input)

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
                        sentiment=sentiment)
                    shared_memory.conversation.append(interviewer_msg)

                    # Publish interviewer message in real-time
                    if message_callback and exec_id:
                        await message_callback(exec_id, synth_id, turns + 1, interviewer_msg)

                    if verbose:
                        _print_speaker("Interviewer", visible_message)

                    # === PART 2: Interviewee responds ===
                    interviewee_input = "Responda à última pergunta."
                    with tracer.start_span(
                        SpanType.LLM_CALL,
                        {
                            "speaker": "interviewee",
                            "turn_number": turns + 1,
                        }) as span:
                        interviewee = create_interviewee(
                            synth=shared_memory.synth,
                            conversation_history=shared_memory.format_history(),
                            initial_context=initial_context,
                            model=model,
                            materials=materials)

                        # Log request
                        span.set_attribute(
                            "request",
                            f"[System Prompt]\n{interviewee.instructions}\n\n[Input]\n{interviewee_input}")

                        raw_result = await Runner.run(interviewee, input=interviewee_input)
                        raw_response = raw_result.final_output
                        span.set_attribute("response", raw_response)
                        span.set_status(SpanStatus.SUCCESS)

                    # Review interviewee response (optional)
                    if skip_interviewee_review:
                        interviewee_response = raw_response
                        logger.debug("Skipping interviewee reviewer")
                    else:
                        reviewer_input = "Revise esta resposta para maior autenticidade."
                        with tracer.start_span(
                            SpanType.LLM_CALL,
                            {
                                "speaker": "interviewee_reviewer",
                                "turn_number": turns + 1,
                            }) as span:
                            reviewer = create_interviewee_reviewer(
                                synth=shared_memory.synth,
                                raw_response=raw_response,
                                model=model)

                            span.set_attribute(
                                "request",
                                f"[System Prompt]\n{reviewer.instructions}\n\n[Input]\n{reviewer_input}")

                            review_result = await Runner.run(reviewer, input=reviewer_input)
                            interviewee_response = review_result.final_output
                            span.set_attribute("response", interviewee_response)
                            span.set_status(SpanStatus.SUCCESS)

                    # Parse and add interviewee message
                    visible_message, internal_notes, should_end, _ = parse_agent_response(
                        interviewee_response
                    )
                    interviewee_msg = ConversationMessage(
                        speaker="Interviewee",
                        text=visible_message,
                        raw_text=interviewee_response,
                        internal_notes=internal_notes,
                        should_end=should_end)
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
        topic_guide_name=guide_name,
        trace_path=trace_path,
        total_turns=turns)


async def run_interview_simple(
    topic: str,
    synth_id: str | None = None,
    persona_description: str | None = None,
    max_turns: int = 4,
    model: str = "gpt-4o-mini",
    verbose: bool = True,
    materials: list | None = None) -> list[ConversationMessage]:
    """
    Run a simple interview, optionally loading synth from database.

    Useful for quick testing or when full interview guide isn't needed.

    Args:
        topic: Topic to discuss in the interview
        synth_id: Optional synth ID to load from database
        persona_description: Optional description if not using synth_id
        max_turns: Maximum conversation turns
        model: LLM model to use
        verbose: Whether to print to console
        materials: Optional list of ExperimentMaterial objects to include in prompts

    Returns:
        List of conversation messages

    Note:
        Either synth_id or persona_description must be provided.
    """
    # Load synth from database or build minimal synth dict
    if synth_id:
        synth = load_synth(synth_id)
    elif persona_description:
        synth = {
            "nome": "Participante",
            "descricao": persona_description,
            "demografia": {},
            "psicografia": {"interesses": []},
        }
    else:
        raise ValueError("Either synth_id or persona_description must be provided")

    shared_memory = SharedMemory(
        topic_guide=f"Tema da entrevista: {topic}",
        synth=synth)

    messages: list[ConversationMessage] = []
    turns = 0

    while turns < max_turns:
        # === PART 1: Interviewer asks ===
        interviewer = create_interviewer(
            topic_guide=shared_memory.topic_guide,
            conversation_history=shared_memory.format_history(),
            max_turns=max_turns,
            model=model,
            materials=materials)

        result = await Runner.run(interviewer, input="Ask your question.")
        response = result.final_output

        visible_message, internal_notes, should_end, sentiment = parse_agent_response(response)
        interviewer_msg = ConversationMessage(
            speaker="Interviewer",
            text=visible_message,
            raw_text=response,
            internal_notes=internal_notes,
            should_end=should_end,
            sentiment=sentiment)
        messages.append(interviewer_msg)
        shared_memory.conversation.append(interviewer_msg)

        if verbose:
            _print_speaker("Interviewer", visible_message)

        # === PART 2: Interviewee responds ===
        interviewee = create_interviewee(
            synth=shared_memory.synth,
            conversation_history=shared_memory.format_history(),
            model=model,
            materials=materials)

        result = await Runner.run(interviewee, input="Answer the question.")
        response = result.final_output

        visible_message, internal_notes, should_end, _ = parse_agent_response(response)
        interviewee_msg = ConversationMessage(
            speaker="Interviewee",
            text=visible_message,
            raw_text=response,
            internal_notes=internal_notes,
            should_end=should_end)
        messages.append(interviewee_msg)
        shared_memory.conversation.append(interviewee_msg)

        if verbose:
            _print_speaker("Interviewee", visible_message)

        turns += 1

    return messages


# Convenience function for sync usage
def run_interview_sync(
    synth_id: str,
    interview_guide: InterviewGuideData,
    max_turns: int = 6,
    trace_path: str | None = None,
    model: str = "gpt-4o-mini",
    verbose: bool = True) -> InterviewResult:
    """
    Synchronous wrapper for run_interview.

    Args:
        synth_id: ID of the synthetic persona
        interview_guide: InterviewGuideData with context, questions, examples
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
            interview_guide=interview_guide,
            max_turns=max_turns,
            trace_path=trace_path,
            model=model,
            verbose=verbose)
    )


if __name__ == "__main__":
    # Simple test
    async def test_simple():
        messages = await run_interview_simple(
            topic="Experiência de compras online",
            persona_description=(
                "Mulher, 35 anos, classe média, mora em São Paulo, trabalha como professora"
            ),
            max_turns=4,
            verbose=True)
        print(f"\n\nTotal messages: {len(messages)}")

    asyncio.run(test_simple())
