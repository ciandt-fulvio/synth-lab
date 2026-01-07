# Implementation Plan: Synth Material Integration

**Branch**: `029-synth-material-integration` | **Date**: 2026-01-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/029-synth-material-integration/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enable Synths to view and reference experiment materials (images, PDFs, videos) during interviews, scenario exploration, and documentation generation. Materials will be injected into LLM contexts via structured prompt sections and accessible through function calling tools. Generated PR-FAQs and summaries will automatically include material references with timestamps and visual element citations.

**Technical Approach**: Extend existing prompt builders (`research_agentic/instructions.py`, `research_prfaq/prompts.py`, `exploration/`) to include materials sections. Create a shared `materials_context.py` module for formatting materials metadata. Implement LLM function tool for on-demand material retrieval using existing `ExperimentMaterial` ORM model and S3 storage. Leverage OpenAI Agents SDK function tools pattern (similar to `create_image_loader_tool`).

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic, OpenAI SDK, OpenAI Agents SDK, boto3 (S3), Arize Phoenix (tracing)
**Storage**: PostgreSQL 14+ (metadata via `experiment_materials` table), S3-compatible storage (file content)
**Testing**: pytest (unit, integration, contract tests)
**Target Platform**: Linux/macOS server (backend API), modern browsers (frontend consumption)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Material retrieval <5s (images/PDFs), <10s (videos <50MB); PR-FAQ generation time increase <30% vs non-material experiments
**Constraints**: Material metadata in prompts <2000 tokens; individual file size ≤50MB; supported formats: PNG, JPEG, GIF, WebP, PDF, MP4, WebM
**Scale/Scope**: ~10-50 materials per experiment typical; support for 100+ concurrent experiments with materials

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Test-First Development (TDD/BDD)
✅ **PASS** - All new modules will have tests written first:
- `materials_context.py`: Unit tests for formatting functions
- `materials_tool.py`: Integration tests with S3 mock
- Prompt builder extensions: Contract tests verifying materials sections

### Principle II: Fast Test Battery (<5s)
✅ **PASS** - Fast tests will use:
- Mocked S3 operations (no network calls)
- In-memory material metadata fixtures
- Prompt formatting tests (pure functions)

### Principle III: Complete Test Battery Before PR
✅ **PASS** - Slow tests will include:
- S3 integration tests with LocalStack
- End-to-end interview with real materials
- PR-FAQ generation with material references

### Principle IV: Frequent Commits
✅ **PASS** - Atomic commits planned:
- One commit per module (materials_context, materials_tool, each prompt builder update)
- Separate commits for tests, implementation, documentation

### Principle V: Simplicity and Code Quality
✅ **PASS**
- Functions <30 lines (formatting logic, tool definitions)
- No new files >500 lines
- Reuses existing `ExperimentMaterial` ORM, S3 client, LLM client patterns
- No new dependencies (all tools already in project)

### Principle VI: Language
✅ **PASS**
- Code: English (function names, variables, docstrings)
- Documentation: Portuguese (user-facing, inline comments)
- User-facing strings: Portuguese (material type labels, error messages)

### Principle VII: Architecture
✅ **PASS** - Follows established patterns:
- **Service Layer**: New logic in `services/materials_context.py` (shared utility)
- **Repository Layer**: Reuses existing `ExperimentMaterialRepository`
- **Infrastructure**: Reuses existing S3 client from `material_service.py`
- **LLM Tools**: Follows `create_image_loader_tool()` pattern
- **Phoenix Tracing**: All LLM calls wrapped with `_tracer.start_as_current_span()`
- **No Router Changes**: Only service/prompt layer modifications

**Additional Principles:**
- ✅ Phoenix tracing: Material retrieval tool calls traced
- ✅ DRY: Shared `materials_context.py` avoids duplication across prompts
- ✅ Alembic: No migrations needed (reuses `experiment_materials` table)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/synth_lab/
├── services/
│   ├── materials_context.py          # NEW: Shared materials formatting for prompts
│   ├── research_agentic/
│   │   ├── instructions.py           # MODIFIED: Add materials to interviewer/interviewee prompts
│   │   └── tools.py                  # MODIFIED: Add materials retrieval tool
│   ├── research_prfaq/
│   │   └── prompts.py                # MODIFIED: Add materials to PR-FAQ system prompt
│   └── exploration/
│       ├── action_proposal_service.py  # MODIFIED: Add materials to scenario prompts
│       └── exploration_summary_generator_service.py  # MODIFIED: Add materials to summary prompts
│
├── repositories/
│   └── experiment_material_repository.py  # EXISTING: Reuse for fetching materials
│
├── infrastructure/
│   └── (no changes - reuse existing S3 client)
│
└── models/
    └── orm/
        └── material.py               # EXISTING: ExperimentMaterial model

tests/
├── unit/
│   └── services/
│       └── test_materials_context.py  # NEW: Materials formatting tests
├── integration/
│   └── services/
│       ├── test_materials_tool.py     # NEW: Materials retrieval tool tests
│       └── test_interview_with_materials.py  # NEW: End-to-end interview test
└── contract/
    └── test_prompts_with_materials.py  # NEW: Prompt structure validation
```

**Structure Decision**: Web application structure with backend modifications only. This feature is backend-focused, extending LLM prompt construction and tool availability. Frontend already has materials display capability (from feature 001-experiment-materials), so no UI changes needed - materials will automatically appear in generated PR-FAQs and summaries viewed through existing frontend.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - all gates passed.
