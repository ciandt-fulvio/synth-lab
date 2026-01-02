"""
Agent definitions linking agents to their instructions and tools.

This module provides factory functions to create configured agents for the
interview system. Each agent has specific instructions and optional tools.

References:
- OpenAI Agents SDK: https://openai.github.io/openai-agents-python/agents/
- MCP Integration: https://openai.github.io/openai-agents-python/mcp/

Sample usage:
```python
from .agent_definitions import create_interviewer

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

from synth_lab.infrastructure.llm_client import supports_reasoning_effort

from .instructions import (
    format_interviewee_instructions,
    format_interviewee_reviewer_instructions,
    format_interviewer_instructions,
    format_interviewer_reviewer_instructions,
    format_orchestrator_instructions)


def _get_model_settings(model: str, reasoning_effort: str = "low") -> ModelSettings | None:
    """
    Get model settings with reasoning effort configured.

    Args:
        model: Model name to check for reasoning_effort support.
        reasoning_effort: Reasoning effort level ("low", "medium", "high").

    Returns:
        ModelSettings with reasoning configured if supported, None otherwise.
    """
    if supports_reasoning_effort(model):
        return ModelSettings(reasoning=Reasoning(effort=reasoning_effort))  # type: ignore
    # Model doesn't support reasoning_effort, return None (no special settings)
    return None


def create_interviewer(
    topic_guide: str,
    conversation_history: str,
    max_turns: int = 6,
    mcp_servers: list[Any] | None = None,
    model: str = "gpt-4o-mini",
    reasoning_effort: str = "low",
    additional_context: str | None = None) -> Agent:
    """
    Create an interviewer agent.

    The interviewer conducts the UX research interview, asking questions
    based on the topic guide and adapting to the conversation flow.

    Args:
        topic_guide: Research topic guide with questions and objectives
        conversation_history: Formatted conversation history
        max_turns: Maximum number of question-answer turns allowed
        mcp_servers: Optional MCP servers for tool access (filesystem, browser)
        model: LLM model to use
        reasoning_effort: Reasoning effort level ("low", "medium", "high")
        additional_context: Optional additional context to complement the research scenario

    Returns:
        Configured Agent instance
    """
    instructions = format_interviewer_instructions(
        topic_guide=topic_guide,
        conversation_history=conversation_history,
        max_turns=max_turns,
        additional_context=additional_context)

    # Build agent kwargs - only include model_settings if model supports it
    agent_kwargs = {
        "name": "Interviewer",
        "instructions": instructions,
        "mcp_servers": mcp_servers or [],
        "model": model,
    }
    model_settings = _get_model_settings(model, reasoning_effort)
    if model_settings is not None:
        agent_kwargs["model_settings"] = model_settings

    return Agent(**agent_kwargs)


def create_interviewee(
    synth: dict[str, Any],
    conversation_history: str,
    mcp_servers: list[Any] | None = None,
    tools: list[Any] | None = None,
    available_images: list[str] | None = None,
    initial_context: str = "",
    model: str = "gpt-4o-mini",
    reasoning_effort: str = "low") -> Agent:
    """
    Create an interviewee agent.

    The interviewee is a synthetic persona that responds to interview
    questions based on their demographic and psychographic profile.

    Args:
        synth: Complete synth data dictionary from database
        conversation_history: Formatted conversation history
        mcp_servers: Optional MCP servers for tool access
        tools: Optional list of function tools (e.g., image loader)
        available_images: Optional list of available image filenames from topic guide
        initial_context: Pre-generated context about prior experience (positive/negative/neutral)
        model: LLM model to use
        reasoning_effort: Reasoning effort level ("low", "medium", "high")

    Returns:
        Configured Agent instance
    """
    instructions = format_interviewee_instructions(
        synth, conversation_history, available_images, initial_context
    )
    synth_name = synth.get("nome", "Participante")

    # Build agent kwargs - only include model_settings if model supports it
    agent_kwargs = {
        "name": f"Interviewee ({synth_name})",
        "instructions": instructions,
        "mcp_servers": mcp_servers or [],
        "tools": tools or [],
        "model": model,
    }
    model_settings = _get_model_settings(model, reasoning_effort)
    if model_settings is not None:
        agent_kwargs["model_settings"] = model_settings

    return Agent(**agent_kwargs)


def create_interviewer_reviewer(
    raw_response: str,
    model: str = "gpt-4o-mini",
    reasoning_effort: str = "low") -> Agent:
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

    # Build agent kwargs - only include model_settings if model supports it
    agent_kwargs = {
        "name": "InterviewerReviewer",
        "instructions": instructions,
        "model": model,
    }
    model_settings = _get_model_settings(model, reasoning_effort)
    if model_settings is not None:
        agent_kwargs["model_settings"] = model_settings

    return Agent(**agent_kwargs)


def create_interviewee_reviewer(
    synth: dict[str, Any],
    raw_response: str,
    model: str = "gpt-4o-mini",
    reasoning_effort: str = "low") -> Agent:
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
    instructions = format_interviewee_reviewer_instructions(synth, raw_response)
    synth_name = synth.get("nome", "Participante")

    # Build agent kwargs - only include model_settings if model supports it
    agent_kwargs = {
        "name": f"IntervieweeReviewer ({synth_name})",
        "instructions": instructions,
        "model": model,
    }
    model_settings = _get_model_settings(model, reasoning_effort)
    if model_settings is not None:
        agent_kwargs["model_settings"] = model_settings

    return Agent(**agent_kwargs)


def create_orchestrator(
    conversation_history: str,
    last_message: str,
    model: str = "gpt-4o-mini",
    reasoning_effort: str = "low") -> Agent:
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
    instructions = format_orchestrator_instructions(conversation_history, last_message)

    # Build agent kwargs - only include model_settings if model supports it
    agent_kwargs = {
        "name": "Orchestrator",
        "instructions": instructions,
        "model": model,
    }
    model_settings = _get_model_settings(model, reasoning_effort)
    if model_settings is not None:
        agent_kwargs["model_settings"] = model_settings

    return Agent(**agent_kwargs)
