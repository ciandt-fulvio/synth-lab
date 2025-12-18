# Implementation Plan: Synth Avatar Generation

**Branch**: `008-synth-avatar-generation` | **Date**: 2025-12-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-synth-avatar-generation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add avatar generation capability to the `gensynth` command. The system will generate diverse, realistic avatar images for synthetic Brazilian personas by calling the OpenAI Image Generation API with batches of 9 synth descriptions, receiving a 1024x1024 image with a 3x3 grid layout, splitting it into individual 341x341 PNG files, and saving each with its corresponding synth ID. Users can control avatar generation with `--avatar` flag and `-b` parameter for block count.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: openai>=2.8.0 (API SDK), Pillow (image processing), rich (CLI output), existing synth-lab modules
**Storage**: File system (`data/synths/avatar/` directory for PNG files)
**Testing**: pytest with real OpenAI API calls (using test mode/mocked responses for fast battery)
**Target Platform**: macOS/Linux command-line environment
**Project Type**: Single project (CLI tool extension)
**Performance Goals**: Generate 9 avatars per API call in under 30 seconds (API-dependent)
**Constraints**: OpenAI API rate limits, API quota costs (~$0.03 per 1024x1024 image with gpt-image-1-mini)
**Scale/Scope**: Support batches of 1-100 synths per command invocation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial Check (Before Phase 0)**: ✅ PASSED
**Post-Design Check (After Phase 1)**: ✅ PASSED - No violations introduced during design phase

### I. Test-First Development (TDD/BDD) - ✅ COMPLIANT

**Plan**:
- Write unit tests for prompt construction BEFORE implementing prompt builder
- Write unit tests for image splitting BEFORE implementing splitter
- Write integration tests for avatar generation flow BEFORE implementing orchestrator
- Use BDD acceptance criteria from spec.md user stories as test scenarios

**Evidence**:
- User stories in spec.md define clear Given-When-Then scenarios
- Tasks.md (Phase 2) will organize tests before implementation for each component

### II. Fast Test Battery on Every Commit - ✅ COMPLIANT

**Plan**:
- Unit tests for prompt construction (< 0.1s each, mocked data)
- Unit tests for image splitting logic (< 0.1s each, test images)
- Fast battery target: < 3 seconds total
- Slow battery includes actual OpenAI API calls (optional, skipped by default)

**Mitigation**: Mock OpenAI API responses for fast tests, use `@pytest.mark.slow` for real API tests

### III. Complete Test Battery Before Pull Requests - ✅ COMPLIANT

**Plan**:
- Fast battery: unit tests with mocks
- Slow battery: integration tests with real API (manual verification before PR)
- Contract tests: validate OpenAI SDK usage patterns
- Coverage target: 90% for new avatar generation code

### IV. Frequent Version Control Commits - ✅ COMPLIANT

**Plan**:
- Commit after each module completion (prompt builder, image splitter, CLI integration)
- Commit message format: "test: add tests for [component]" → "feat: implement [component]"
- Atomic commits for each logical change

### V. Simplicity and Code Quality - ✅ COMPLIANT

**Plan**:
- Create focused modules: `avatar_prompt.py` (< 200 lines), `avatar_image.py` (< 200 lines), `avatar_generator.py` (< 300 lines)
- Functions under 30 lines each
- Minimal dependencies: only add Pillow (already standard for image processing)
- Follow existing synth-lab module patterns (validation block in `if __name__ == "__main__"`)

**Justification**: No complexity violations. Feature fits naturally into existing architecture.

### VI. Language - ✅ COMPLIANT

**Plan**:
- Code (classes, variables, functions): English
- Documentation (docstrings, comments): Portuguese (matching existing synth-lab convention)
- User-facing strings: Portuguese (CLI messages, errors)

## Project Structure

### Documentation (this feature)

```text
specs/008-synth-avatar-generation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── openai-image-api.md  # OpenAI API contract documentation
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/synth_lab/gen_synth/
├── avatar_prompt.py         # NEW: Construct prompts for OpenAI image generation
├── avatar_image.py          # NEW: Split 1024x1024 images into 9 parts
├── avatar_generator.py      # NEW: Orchestrate avatar generation flow
├── gen_synth.py             # MODIFIED: Add --avatar and -b CLI parameters
├── synth_builder.py         # EXISTING: Provides synth data for avatars
└── config.py                # EXISTING: Configuration management

tests/unit/synth_lab/gen_synth/
├── test_avatar_prompt.py    # NEW: Unit tests for prompt construction
├── test_avatar_image.py     # NEW: Unit tests for image splitting
└── test_avatar_generator.py # NEW: Unit tests for generation orchestration

tests/integration/
└── test_avatar_generation.py # NEW: Integration tests with OpenAI API (slow)

data/synths/avatar/          # NEW: Avatar image storage directory
```

**Structure Decision**: Single project structure. Avatar generation extends existing `gen_synth` module with 3 new focused modules. Follows established synth-lab patterns for module organization, validation blocks, and testing structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations to track. Feature implementation follows all constitution principles without requiring exceptions.

## Phase 0: Research & Technical Decisions

*STATUS: ✅ COMPLETE*

Research completed and documented in [research.md](./research.md).

**Key Decisions**:
- **Image API**: OpenAI gpt-image-1-mini 2 (cost-effective at $0.020/block)
- **Image Processing**: Pillow (PIL) for grid splitting
- **Image Format**: PNG (lossless quality)
- **CLI Integration**: Extend existing gensynth command with --avatar flag
- **API Key**: Environment variable (OPENAI_API_KEY)

## Phase 1: Design Artifacts

*STATUS: ✅ COMPLETE*

Generated artifacts:
- ✅ [research.md](./research.md): Technical decisions and best practices
- ✅ [data-model.md](./data-model.md): Avatar entities, file naming, prompt structure
- ✅ [contracts/openai-image-api.md](./contracts/openai-image-api.md): OpenAI API contract documentation
- ✅ [quickstart.md](./quickstart.md): User guide for avatar generation feature

## Phase 2: Task Generation

*STATUS: PENDING - Use /speckit.tasks command after Phase 1*

Task breakdown will be generated by `/speckit.tasks` command, organized by user story priority:
- P1: Core batch avatar generation
- P2: Block count control
- P3: Generation for existing synths
