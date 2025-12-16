# Research: UX Research Interviews with Synths

**Feature Branch**: `005-ux-research-interviews`
**Created**: 2025-12-16

## Technology Decisions

### 1. LLM Provider and SDK

**Decision**: OpenAI Python SDK v2.8.0+ with `chat.completions.parse()` for structured outputs

**Rationale**:
- User explicitly specified OpenAI SDK and gpt-5.1 model
- `chat.completions.parse()` provides native Pydantic integration for structured responses
- Eliminates manual JSON parsing and validation - SDK handles type coercion automatically
- Supports both sync and async clients

**Alternatives Considered**:
- **Anthropic Claude SDK**: Strong alternative but user specified OpenAI
- **LiteLLM**: Good for multi-provider support but adds complexity for single-provider use
- **Manual JSON extraction**: More fragile, requires regex/string parsing

**Implementation Pattern**:
```python
from pydantic import BaseModel
from openai import OpenAI

class InterviewResponse(BaseModel):
    message: str
    should_end: bool
    internal_notes: str | None = None

client = OpenAI()  # Uses OPENAI_API_KEY env var
completion = client.chat.completions.parse(
    model="gpt-4.1",
    messages=[...],
    response_format=InterviewResponse,
)
response = completion.choices[0].message.parsed
```

### 2. Model Selection

**Decision**: gpt-4.1 (as specified by user)

**Rationale**:
- User explicitly specified gpt-5.1 model
- Assumed to be available via OpenAI API (latest model naming)
- High capability for nuanced persona roleplay and interview technique

**Fallback Strategy**:
- If model not available, fall back to gpt-4o or gpt-4o-mini
- Model name configurable via CLI parameter or environment variable

### 3. Structured Output Format

**Decision**: Pydantic models with OpenAI native `response_format` parameter

**Rationale**:
- Native SDK support via `chat.completions.parse()`
- Automatic validation and type coercion
- Clear contract definition in code
- IDE autocomplete and type checking support

**Response Model**:
```python
class InterviewResponse(BaseModel):
    """Response format for both interviewer and synth LLMs."""
    message: str  # The spoken text
    should_end: bool = False  # Only interviewer sets True
    internal_notes: str | None = None  # Optional annotations
```

### 4. CLI Framework

**Decision**: Typer (already in project dependencies)

**Rationale**:
- Consistent with existing `synthlab` CLI commands
- Already used by `query/cli.py`
- Rich integration for beautiful terminal output
- Type-hint-based argument definition

**Command Structure**:
```bash
synthlab research <synth_id> --topic-guide <path> --max-rounds <int>
```

### 5. Terminal Output

**Decision**: Rich library for formatted real-time display

**Rationale**:
- Already in project dependencies
- Supports live updates, panels, colors
- Consistent with existing CLI output style
- Cross-platform terminal support

**Display Pattern**:
- Interviewer messages: Blue panel with "Entrevistador" header
- Synth messages: Green panel with synth name as header
- Progress indicator during LLM calls

### 6. Transcript Storage

**Decision**: JSON files in `data/transcripts/` directory

**Rationale**:
- Consistent with existing data storage pattern (`data/synths/`)
- Human-readable format for manual review
- Easy to parse for downstream analysis tools
- Filename format: `{synth_id}_{timestamp}.json`

**Transcript Schema**:
```json
{
  "session": {
    "id": "uuid",
    "synth_id": "abc123",
    "topic_guide_path": "path/to/guide.md",
    "max_rounds": 10,
    "start_time": "ISO8601",
    "end_time": "ISO8601",
    "status": "completed|interrupted|error"
  },
  "synth_snapshot": { /* full synth data at interview time */ },
  "messages": [
    {
      "speaker": "interviewer|synth",
      "content": "message text",
      "timestamp": "ISO8601",
      "internal_notes": "optional notes"
    }
  ]
}
```

### 7. Synth Loading

**Decision**: Load from existing `data/synths/synths.json` using simple JSON read

**Rationale**:
- Synths already stored in this file by gen_synth module
- Simple dict lookup by ID
- No need for database query for single synth retrieval

**Implementation**:
```python
def load_synth(synth_id: str) -> dict | None:
    with open(SYNTHS_FILE) as f:
        synths = json.load(f)
    return next((s for s in synths if s["id"] == synth_id), None)
```

### 8. Topic Guide Format

**Decision**: Plain text or Markdown files

**Rationale**:
- Simple to create and edit
- User specified file path as input parameter
- No complex parsing needed - full content passed to interviewer prompt

**Example Structure**:
```markdown
# Topic Guide: E-commerce Mobile App

## Objectives
- Understand shopping habits
- Identify pain points in checkout flow
- Explore payment preferences

## Key Questions
1. How often do you shop online using your phone?
2. What frustrates you most about mobile checkout?
3. How do you typically pay for online purchases?

## Follow-up Areas
- Security concerns
- Price comparison behavior
- Return/refund experiences
```

### 9. Error Handling Strategy

**Decision**: Graceful degradation with partial transcript saving

**Rationale**:
- API errors shouldn't lose completed interview progress
- User should see clear error messages
- Transcript saved even if interview interrupted

**Error Categories**:
1. **Pre-interview errors**: Synth not found, topic guide not found → Exit with error message
2. **API errors mid-interview**: Save partial transcript, display error, offer retry
3. **Context limit reached**: End interview gracefully, save transcript with truncation note

### 10. Conversation Context Management

**Decision**: Full conversation history passed to both LLMs each turn

**Rationale**:
- Maintains coherent conversation flow
- Both participants aware of full context
- Simple implementation without sliding window complexity

**Context Limit Handling**:
- Monitor token count per message
- If approaching limit (configurable threshold), signal interviewer to wrap up
- Max rounds parameter provides hard limit protection

## Resolved Clarifications

| Item | Resolution |
|------|------------|
| LLM Provider | OpenAI (user specified) |
| Model | gpt-4.1 (user specified) |
| Structured Output Method | `chat.completions.parse()` with Pydantic |
| Transcript Format | JSON with session metadata + messages |
| Topic Guide Format | Plain text/Markdown |

## Dependencies to Add

```toml
# pyproject.toml additions
dependencies = [
    # ... existing deps ...
    "openai>=2.8.0",
]
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| OPENAI_API_KEY | Yes | OpenAI API authentication key |
| OPENAI_MODEL | No | Override default model (default: gpt-4.1) |
