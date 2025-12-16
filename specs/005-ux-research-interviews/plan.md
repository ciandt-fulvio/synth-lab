# Implementation Plan: UX Research Interviews with Synths

**Branch**: `005-ux-research-interviews` | **Date**: 2025-12-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-ux-research-interviews/spec.md`

## Summary

Implement simulated UX research interviews using two LLMs in conversation: an interviewer following UX research best practices and a synth responding based on their complete persona (Big Five personality, demographics, biases, behaviors). The system provides a CLI command (`synthlab research`) that executes the interview loop, displays messages in real-time, and saves transcripts to JSON files.

## Technical Context

**Language/Version**: Python 3.13+ (aligning with existing project)
**Primary Dependencies**:
- openai>=2.8.0 (using `chat.completions.parse()` for structured outputs)
- pydantic>=2.0.0 (for response models)
- typer>=0.9.0 (CLI framework, already in project)
- rich>=13.0.0 (terminal output, already in project)
- loguru>=0.7.0 (logging, already in project)

**Storage**: JSON files for transcripts (`data/transcripts/`), synths loaded from `data/synths/synths.json`
**Testing**: pytest (existing project standard)
**Target Platform**: CLI (Linux, macOS, Windows)
**Project Type**: Single project extending existing CLI
**Performance Goals**:
- Interview completion in <5 minutes for 10 rounds
- <1 second delay between LLM response and terminal display
**Constraints**:
- Requires OPENAI_API_KEY environment variable
- Context window limits for very long interviews
**Scale/Scope**: Single-user CLI tool, interview sessions with 1-20 rounds

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development (TDD/BDD) | PASS | Tasks will be structured with tests before implementation |
| II. Fast Test Battery (<5s) | PASS | Unit tests will mock LLM calls for speed |
| III. Complete Test Battery Before PR | PASS | Integration tests with real API in slow battery |
| IV. Frequent Version Control Commits | PASS | Atomic commits per module |
| V. Simplicity and Code Quality | PASS | <500 lines per file, single-purpose functions |
| VI. Language | PASS | Code in English, docs in Portuguese, i18n strings externalized |

## Project Structure

### Documentation (this feature)

```text
specs/005-ux-research-interviews/
├── plan.md              # This file
├── research.md          # Phase 0 output - technology decisions
├── data-model.md        # Phase 1 output - entities and relationships
├── quickstart.md        # Phase 1 output - usage guide
├── contracts/           # Phase 1 output - API contracts
│   └── interview-response.json  # JSON Schema for LLM responses
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/synth_lab/research/
├── __init__.py          # Module exports and constants
├── cli.py               # Typer CLI command 'research'
├── interview.py         # Interview execution loop
├── prompts.py           # System prompts for interviewer/synth
├── models.py            # Pydantic models for responses
└── transcript.py        # Transcript saving/loading

tests/
├── unit/
│   └── synth_lab/
│       └── research/
│           ├── test_models.py
│           ├── test_prompts.py
│           ├── test_interview.py
│           └── test_transcript.py
├── integration/
│   └── synth_lab/
│       └── research/
│           └── test_cli_integration.py
└── contract/
    └── synth_lab/
        └── research/
            └── test_llm_response_contract.py

data/
├── synths/
│   └── synths.json      # Existing synth data
├── transcripts/         # NEW: Interview transcript storage
│   └── .gitkeep
└── topic_guides/        # NEW: Sample topic guides
    └── interview-guide.md
```

**Structure Decision**: Single project extension following existing `src/synth_lab/{feature}/` pattern used by `gen_synth/` and `query/` modules.

## Complexity Tracking

> No violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
