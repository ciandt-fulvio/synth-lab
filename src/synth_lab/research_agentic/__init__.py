"""
Agentic UX Research Interview System.

Multi-agent system for conducting simulated UX research interviews using
the OpenAI Agents SDK. Features:
- Interviewer agent with professional UX researcher personality
- Interviewee agent with synthetic persona personality
- Reviewer agents that adapt tone of voice for each speaker
- Orchestrator that manages turn-taking
- Full trace integration for visualization and debugging

References:
- OpenAI Agents SDK: https://openai.github.io/openai-agents-python/
- Trace Visualizer: src/synth_lab/trace_visualizer/

Sample usage:
```python
from synth_lab.research_agentic import run_interview

# Run a simulated interview
result = await run_interview(
    synth_id="abc123",
    topic="compra-amazon",
    max_turns=6,
    trace_path="data/traces/agentic-interview.trace.json"
)
```
"""

from .agent_definitions import (
    create_interviewee,
    create_interviewee_reviewer,
    create_interviewer,
    create_interviewer_reviewer,
    create_orchestrator,
)
from .instructions import (
    INTERVIEWEE_INSTRUCTIONS,
    INTERVIEWEE_REVIEWER_INSTRUCTIONS,
    INTERVIEWER_INSTRUCTIONS,
    INTERVIEWER_REVIEWER_INSTRUCTIONS,
    ORCHESTRATOR_INSTRUCTIONS,
)
from .runner import run_interview

__all__ = [
    # Instructions
    "INTERVIEWER_INSTRUCTIONS",
    "INTERVIEWEE_INSTRUCTIONS",
    "INTERVIEWER_REVIEWER_INSTRUCTIONS",
    "INTERVIEWEE_REVIEWER_INSTRUCTIONS",
    "ORCHESTRATOR_INSTRUCTIONS",
    # Agent factories
    "create_interviewer",
    "create_interviewee",
    "create_interviewer_reviewer",
    "create_interviewee_reviewer",
    "create_orchestrator",
    # Main entry point
    "run_interview",
]
