"""
Agent definitions linking agents to their instructions and tools.

This module provides factory functions to create configured agents for the
interview system. Each agent has specific instructions and optional tools.

References:
- OpenAI Agents SDK: https://openai.github.io/openai-agents-python/agents/
- MCP Integration: https://openai.github.io/openai-agents-python/mcp/

Sample usage:
```python
from synth_lab.research_agentic.agent_definitions import create_interviewer

interviewer = create_interviewer(
    topic_guide="...",
    conversation_history="...",
    mcp_servers=[filesystem_server]
)
```
"""

from typing import Any

from agents import Agent, ModelSettings
from openai.types.shared import Reasoning

from .instructions import (
    format_interviewee_instructions,
    format_interviewee_reviewer_instructions,
    format_interviewer_instructions,
    format_interviewer_reviewer_instructions,
    format_orchestrator_instructions,
)


def _get_model_settings(reasoning_effort: str = "low") -> ModelSettings:
    """Get model settings with reasoning effort configured."""
    return ModelSettings(reasoning=Reasoning(effort=reasoning_effort))  # type: ignore


def create_interviewer(
    topic_guide: str,
    conversation_history: str,
    mcp_servers: list[Any] | None = None,
    model: str = "gpt-5-mini",
    reasoning_effort: str = "low",
) -> Agent:
    """
    Create an interviewer agent.

    The interviewer conducts the UX research interview, asking questions
    based on the topic guide and adapting to the conversation flow.

    Args:
        topic_guide: Research topic guide with questions and objectives
        conversation_history: Formatted conversation history
        mcp_servers: Optional MCP servers for tool access (filesystem, browser)
        model: LLM model to use
        reasoning_effort: Reasoning effort level ("low", "medium", "high")

    Returns:
        Configured Agent instance
    """
    instructions = format_interviewer_instructions(
        topic_guide, conversation_history)

    return Agent(
        name="Interviewer",
        instructions=instructions,
        mcp_servers=mcp_servers or [],
        model=model,
        model_settings=_get_model_settings(reasoning_effort),
    )


def create_interviewee(
    synth: dict[str, Any],
    conversation_history: str,
    mcp_servers: list[Any] | None = None,
    model: str = "gpt-5-mini",
    reasoning_effort: str = "low",
) -> Agent:
    """
    Create an interviewee agent.

    The interviewee is a synthetic persona that responds to interview
    questions based on their demographic and psychographic profile.

    Args:
        synth: Complete synth data dictionary from database
        conversation_history: Formatted conversation history
        mcp_servers: Optional MCP servers for tool access
        model: LLM model to use
        reasoning_effort: Reasoning effort level ("low", "medium", "high")

    Returns:
        Configured Agent instance
    """
    instructions = format_interviewee_instructions(synth, conversation_history)
    synth_name = synth.get("nome", "Participante")

    return Agent(
        name=f"Interviewee ({synth_name})",
        instructions=instructions,
        mcp_servers=mcp_servers or [],
        model=model,
        model_settings=_get_model_settings(reasoning_effort),
    )


def create_interviewer_reviewer(
    raw_response: str,
    model: str = "gpt-5-mini",
    reasoning_effort: str = "low",
) -> Agent:
    """
    Create an interviewer reviewer agent.

    Reviews and adapts the interviewer's responses to ensure professional
    tone and clear communication.

    Args:
        raw_response: The interviewer's raw response to review
        model: LLM model to use
        reasoning_effort: Reasoning effort level ("low", "medium", "high")

    Returns:
        Configured Agent instance
    """
    instructions = format_interviewer_reviewer_instructions(raw_response)

    return Agent(
        name="InterviewerReviewer",
        instructions=instructions,
        model=model,
        model_settings=_get_model_settings(reasoning_effort),
    )


def create_interviewee_reviewer(
    synth: dict[str, Any],
    raw_response: str,
    model: str = "gpt-5-mini",
    reasoning_effort: str = "low",
) -> Agent:
    """
    Create an interviewee reviewer agent.

    Reviews and adapts the interviewee's responses to ensure authenticity
    with the persona profile and natural language.

    Args:
        synth: Complete synth data dictionary from database
        raw_response: The interviewee's raw response to review
        model: LLM model to use
        reasoning_effort: Reasoning effort level ("low", "medium", "high")

    Returns:
        Configured Agent instance
    """
    instructions = format_interviewee_reviewer_instructions(
        synth, raw_response)
    synth_name = synth.get("nome", "Participante")

    return Agent(
        name=f"IntervieweeReviewer ({synth_name})",
        instructions=instructions,
        model=model,
        model_settings=_get_model_settings(reasoning_effort),
    )


def create_orchestrator(
    conversation_history: str,
    last_message: str,
    model: str = "gpt-5-mini",
    reasoning_effort: str = "low",
) -> Agent:
    """
    Create an orchestrator agent.

    Decides whose turn it is to speak based on the conversation state.

    Args:
        conversation_history: Formatted conversation history
        last_message: The last message in the conversation
        model: LLM model to use
        reasoning_effort: Reasoning effort level ("low", "medium", "high")

    Returns:
        Configured Agent instance
    """
    instructions = format_orchestrator_instructions(
        conversation_history, last_message)

    return Agent(
        name="Orchestrator",
        instructions=instructions,
        model=model,
        model_settings=_get_model_settings(reasoning_effort),
    )
