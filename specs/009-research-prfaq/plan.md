# Implementation Plan: Research Report to PR/FAQ Generator

**Branch**: `009-research-prfaq` | **Date**: 2025-12-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-research-prfaq/spec.md`

## Summary

Generate professional PR-FAQ documents from research batch reports using Amazon's Working Backwards framework. The feature transforms qualitative research insights (markdown text from summarizer agent) into structured, customer-focused documents with Press Release and FAQ sections. Implementation uses hybrid LLM strategy: few-shot prompting + JSON Schema validation + chain-of-thought instruction to extract pain points/benefits from research "recommendations" and "recurrent_patterns" sections. FAQ answers link to synth persona archetypes for rastreability and customer segment context.

## Technical Context

**Language/Version**: Python 3.13+ (project standard)
**Primary Dependencies**:
  - OpenAI Python SDK (existing, used for LLM integration)
  - Pydantic v2 (existing, for data validation)
  - typer (existing, for CLI)
  - reportlab or weasyprint (for PDF export)
  - loguru (existing, for logging)

**Storage**: File-based JSON (local data directory `data/outputs/prfaq/`)
**Testing**: pytest (project standard)
**Target Platform**: CLI (command-line interface)
**Project Type**: Single project (extends existing synth-lab Python monolith)
**Performance Goals**:
  - Generate complete PR-FAQ in <2 minutes (including LLM processing)
  - Handle 5,000+ word research reports without degradation
  - Export to all formats in <10 seconds each

**Constraints**:
  - PR-FAQ generation sequential (not batch)
  - OpenAI API rate limits apply (with retry/backoff)
  - Local file I/O only, no external sync

**Scale/Scope**:
  - Single batch report per execution
  - 8-12 FAQ Q&A pairs per PR-FAQ
  - Support ~10-50 concurrent users in typical research workflows

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Test-First Development (TDD/BDD) - NON-NEGOTIABLE
✅ **PASS** - Feature spec includes 4 prioritized user stories with BDD acceptance scenarios (Given-When-Then format). Implementation will follow Red-Green-Refactor with tests written before code.

**Test Strategy:**
- Unit tests for: PR-FAQ generation logic, LLM prompt validation, data parsing, export formatting
- Integration tests for: batch_summary.json loading, LLM integration, file I/O
- Contract tests for: JSON Schema validation, API responses
- E2E tests for: complete workflows (batch → PR-FAQ → export)

**Fast Test Battery (<5s)**: Unit tests + critical integration tests
**Complete Battery**: All test types covering acceptance criteria

### Principle II: Fast Test Battery on Every Commit
✅ **PASS** - Will configure unit tests to run on pre-commit. Mock LLM calls to keep tests <0.5s each.

### Principle III: Complete Test Battery Before PRs
✅ **PASS** - All tests (fast + slow) including LLM integration tests will pass before PR submission.

### Principle IV: Frequent Version Control Commits
✅ **PASS** - Implementation will commit at each task phase: test definition → implementation → refactoring → export features.

### Principle V: Simplicity and Code Quality
✅ **PASS** - Architecture targets:
- Functions <30 lines (LLM integration, parsing, validation separate)
- Files <500 lines (separate modules: generator, exporter, models, cli)
- No premature optimization
- Minimal dependencies (using existing OpenAI, Pydantic, typer)

### Principle VI: Language Requirements
✅ **PASS** - Code in English (classes, functions, variables), documentation in Portuguese. I18n-ready for user-facing strings.

## Project Structure

### Documentation (this feature)

```text
specs/009-research-prfaq/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification with user stories & requirements
├── checklists/requirements.md  # Quality validation checklist
├── research.md          # Phase 0 output: technology decisions & rationale
├── data-model.md        # Phase 1 output: entities, relationships, state transitions
├── quickstart.md        # Phase 1 output: usage examples & workflows
├── contracts/           # Phase 1 output: API contracts & JSON schemas
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/synth_lab/research_prfaq/          # New feature module
├── __init__.py                        # Public API exports
├── models.py                          # Pydantic models: ResearchReport, PRFAQDocument, Version
├── generator.py                       # Core LLM-based PR-FAQ generation with chain-of-thought
├── exporter.py                        # PDF/Markdown/HTML export formatters
├── prompts.py                         # LLM system prompts + few-shot examples (2 examples)
├── validator.py                       # JSON Schema validation for PR-FAQ structure
└── cli.py                            # Typer CLI integration (research-prfaq commands)

tests/unit/synth_lab/research_prfaq/
├── test_models.py                    # Unit: Pydantic model validation
├── test_generator.py                 # Unit: PR-FAQ generation logic (mocked LLM)
├── test_exporter.py                  # Unit: export formatting (PDF, MD, HTML)
├── test_validator.py                 # Unit: JSON Schema validation
└── test_cli.py                       # Unit: CLI argument parsing & command routing

tests/integration/synth_lab/research_prfaq/
├── test_batch_summary_parsing.py     # Integration: load & parse batch_summary.json
├── test_prfaq_generation_e2e.py      # E2E: batch → generation → persistence
└── test_export_formats.py            # Integration: export to all formats

tests/contract/synth_lab/research_prfaq/
└── test_json_schema.py               # Contract: PR-FAQ JSON Schema validation

data/outputs/prfaq/                   # Output directory for generated PR-FAQs
├── {batch_id}_{timestamp}_prfaq.json # Generated PR-FAQ document
├── {batch_id}_{timestamp}_exports/   # Export formats directory
│   ├── prfaq.pdf
│   ├── prfaq.md
│   └── prfaq.html
└── .versions/                        # Version history for diffs
```

**Structure Decision**: Single project extension to existing synth-lab Python monolith. New `research_prfaq` module mirrors existing feature structure (research_agentic, gen_synth, query, etc.). CLI integrated into main `synthlab` Typer app via new `research_prfaq` subcommand group. Tests mirror source structure per project conventions.

## Complexity Tracking

✅ **No Constitution Violations** - All principles are satisfied by the plan. Architecture is simple and aligned with project standards.

---

## Phase 0: Research & Technical Validation

**Objective**: Resolve any unknowns and validate technology choices. No unknowns identified in Technical Context (all items are known/existing tech).

**Research Tasks** (Parallel):
1. ✅ LLM Few-shot Prompt Examples: Identify 1-2 high-quality PR-FAQ examples from Amazon/public sources to include in prompts
2. ✅ JSON Schema Validation: Validate Pydantic + JSON Schema approach for PR-FAQ structure validation
3. ✅ PDF Export Strategy: Evaluate reportlab vs weasyprint for PDF generation performance/quality
4. ✅ Batch Summary Parsing: Confirm markdown-to-JSON parsing approach for batch_summary.json sections

**Deliverable**: `research.md` with findings, rationale, and technology decisions confirmed.

---

## Phase 1: Design & Data Modeling

**Prerequisites**: research.md complete

### 1.1 Data Model (data-model.md)

**Entities**:

**Research Report**
- batch_id: string (unique identifier)
- summary_content: string (markdown text from summarizer)
- sections: dict with keys: executive_summary, recurrent_patterns, relevant_divergences, identified_tensions, notable_absences, key_quotes, recommendations
- generated_at: ISO-8601 timestamp
- parsed_insights: dict (pain_points, benefits, quotes extracted)

**PR-FAQ Document**
- id: string (batch_id + timestamp)
- batch_id: string (reference to source research)
- press_release: object
  - headline: string (extracted from research insights)
  - one_liner: string (value proposition)
  - problem_statement: string (from pain points)
  - solution_overview: string (from benefits/recommendations)
- faqs: list[object] (8-12 Q&A pairs)
  - question: string
  - answer: string
  - customer_segment: string (synth persona archetype: e.g., "Jovem Urbano", "Profissional Conservador")
- metadata: object
  - generated_at: ISO-8601 timestamp
  - model_used: string (e.g., "gpt-4o")
  - prompt_version: string
  - validation_status: enum (valid, invalid, needs_review)
  - confidence_score: float (0-1, quality metric)
- edit_history: list[object]
  - timestamp: ISO-8601
  - field_modified: string
  - old_value, new_value: string
  - modified_by: string

**State Transitions**:
- generated → valid (after JSON Schema validation passes)
- generated → needs_review (if confidence_score < 0.75)
- valid → edited (after user modifications via edit command)
- valid/edited → exported (after export to PDF/MD/HTML)

### 1.2 API Contracts (contracts/)

**CLI Commands** (Typer interface):

```
synthlab research-prfaq generate --batch-id <batch_id> [--output <path>] [--model <model>]
  Input: Reads data/transcripts/{batch_id}/batch_summary.json
  Output: PR-FAQ JSON + confirmation message + file path
  Error: Invalid batch_id, missing batch_summary.json, LLM API error

synthlab research-prfaq edit --prfaq-id <id>
  Input: Reads PR-FAQ from data/outputs/prfaq/{id}.json
  Output: Interactive editor (opens temp file for manual editing)
  Updates: Press Release fields, FAQ questions/answers
  Note: Auto-saves edits with version tracking

synthlab research-prfaq export --prfaq-id <id> --format <pdf|md|html> [--output <path>]
  Input: PR-FAQ document ID
  Output: Exports to specified format in data/outputs/prfaq/{id}_exports/
  Returns: File path + confirmation

synthlab research-prfaq list [--batch-id <id>]
  Output: Table with columns: ID, Batch ID, Created, Modified, Status
  Filters: By batch_id if provided

synthlab research-prfaq history --batch-id <batch_id>
  Output: Version timeline showing all versions + timestamps + edit diffs
```

**JSON Schema** (`contracts/prfaq-schema.json`):
```json
{
  "$schema": "http://json-schema.org/draft-2020-12/schema#",
  "title": "PR-FAQ Document",
  "type": "object",
  "required": ["batch_id", "press_release", "faqs", "metadata"],
  "properties": {
    "press_release": {
      "required": ["headline", "one_liner", "problem_statement", "solution_overview"],
      "minLength": 10
    },
    "faqs": {
      "type": "array",
      "minItems": 8,
      "maxItems": 12,
      "items": {
        "required": ["question", "answer"],
        "properties": {
          "customer_segment": {"type": "string"}
        }
      }
    }
  }
}
```

### 1.3 Quick Start Guide (quickstart.md)

**Workflow**:
1. Generate batch research summary (via existing research-batch feature)
2. Generate PR-FAQ: `synthlab research-prfaq generate --batch-id <batch_id>`
3. Review generated document in JSON
4. Optionally edit: `synthlab research-prfaq edit --prfaq-id <id>`
5. Export: `synthlab research-prfaq export --prfaq-id <id> --format pdf`

**Example**:
```bash
# Generate PR-FAQ from research report
uv run synthlab research-prfaq generate --batch-id abc123

# Export to PDF and Markdown
uv run synthlab research-prfaq export --prfaq-id abc123_20251219120000 --format pdf
uv run synthlab research-prfaq export --prfaq-id abc123_20251219120000 --format markdown

# View version history
uv run synthlab research-prfaq history --batch-id abc123

# List all PR-FAQs
uv run synthlab research-prfaq list
```

### 1.4 Agent Context Update

Will run `.specify/scripts/bash/update-agent-context.sh claude` to add:
- New module: `src/synth_lab/research_prfaq/` with module structure
- New dependencies: reportlab (or weasyprint) for PDF export
- Test structure expectations for unit/integration/contract tests
- LLM integration patterns: few-shot prompting, JSON Schema validation, chain-of-thought
- File I/O patterns for batch_summary.json and PR-FAQ persistence

---

## Phase 2: Task Generation

**Note**: Task generation happens in `/speckit.tasks` command (NOT in this plan).

**User Stories → Tasks Mapping**:
- **P1 - Generate PR-FAQ**:
  - Models (ResearchReport, PRFAQDocument)
  - LLM generator with few-shot + chain-of-thought
  - Parser for batch_summary.json
  - Validator for JSON Schema
  - Tests (unit + integration)

- **P2 - Edit PR-FAQ**:
  - Edit CLI command
  - Version tracking + edit history
  - File I/O (load/save PR-FAQ JSON)
  - Tests

- **P2 - Export**:
  - Exporter module (PDF, MD, HTML formatters)
  - Export CLI command
  - Tests (format-specific)

- **P3 - History**:
  - List + history CLI commands
  - Version diff calculation
  - Tests

---

## Implementation Architecture

### High-Level Flow

```
batch_summary.json (Markdown from summarizer agent)
    ↓
[Parse & Validate] → Research Report (extract sections, pain points, benefits)
    ↓
[LLM Generation] → Chain-of-thought prompt with few-shot examples
                   (focuses on "recommendations" + "recurrent_patterns")
    ↓
[LLM Output] → JSON with Press Release + FAQ (each with customer_segment)
    ↓
[Validate] → JSON Schema validation + consistency checks + confidence scoring
    ↓
[Persist] → PR-FAQ JSON + metadata to data/outputs/prfaq/{id}.json
    ↓
[Export] → PDF/MD/HTML formatters generate output files
```

### Module Responsibilities

| Module | Responsibility | Test Type | Dependencies |
|--------|---|---|---|
| models.py | Pydantic models: ResearchReport, PRFAQDocument, Version | Unit | pydantic |
| generator.py | LLM calls + parsing with few-shot + chain-of-thought + confidence scoring | Unit (mocked), Integration (real LLM) | openai, models, prompts, validator |
| prompts.py | System prompts + 2 few-shot PR-FAQ examples | Unit | (strings only) |
| validator.py | JSON Schema validation + consistency checks | Unit, Contract | jsonschema, models |
| exporter.py | Format converters: JSON→PDF, JSON→MD, JSON→HTML | Unit, Integration | reportlab/weasyprint, models |
| cli.py | Typer commands + file I/O + CLI routing | Unit (arg parsing) | typer, generator, exporter, models |
| __init__.py | Public API exports | N/A | (module imports) |

### Key Design Decisions

1. **LLM Strategy**: Hybrid chain-of-thought + structured output + few-shot
   - Few-shot examples in `prompts.py` (2 high-quality examples) ensure output quality
   - JSON Schema in validator.py enforces structure compliance
   - Chain-of-thought instruction explicitly focuses on extracting pain points/benefits from "recommendations" + "recurrent_patterns" sections
   - Confidence score metric enables quality assessment

2. **Synth Persona Integration**: FAQ customer_segment field links to persona archetypes
   - Enables rastreability and context during review
   - Uses simple string matching on persona names (e.g., "Jovem Urbano", "Profissional Conservador")
   - Fuzzy matching can be added later if needed

3. **File-Based Persistence**: JSON to `data/outputs/prfaq/` directory
   - Simple, no database required (aligns with project simplicity principle)
   - Enables git-friendly version tracking via .versions/ subdirectory
   - Supports future migration to database if scale requires

4. **Export Flexibility**: Separate exporter module for each format
   - PDF: reportlab (lighter dependency) or weasyprint (if needed for complex layouts)
   - Markdown: jinja2 templates for git/documentation
   - HTML: jinja2 templates for web/wikis

5. **CLI Integration**: New subcommand group in main synthlab Typer app
   - Follows existing pattern from research, query, topic-guide commands
   - Single entry point: `synthlab research-prfaq <subcommand>`

---

## Testing Strategy

### Test Coverage by User Story

| User Story | Unit | Integration | Contract | E2E |
|---|---|---|---|---|
| P1 - Generate | generator logic (mocked LLM), models, parser | batch_summary parsing, real LLM, file I/O | JSON Schema | batch→PR-FAQ→file |
| P2 - Edit | CLI arg parsing, field updates, models | file load/save, version tracking | - | edit workflow |
| P2 - Export | formatter logic (PDF/MD/HTML) | export to all formats | - | format-specific E2E |
| P3 - History | version list, diff logic | file scanning, version diffs | - | history timeline |

**Fast Test Battery** (<5s total):
- Unit: models, generator (mocked LLM), validator, CLI parsing, exporter templates
- Integration (fast): batch_summary parsing with real file I/O

**Complete Battery** (all tests):
- All unit + fast integration
- Real LLM integration tests (with test API key + mocked API responses)
- Export format validation (real PDF/HTML generation)
- E2E workflows (complete batch→PR-FAQ→export)
- All acceptance criteria from spec validated

### Constitution Compliance

✅ **TDD**: Tests written before implementation code (Red-Green-Refactor)
✅ **Fast Tests**: Unit tests mock LLM; keep each test <0.5s
✅ **Complete Battery**: All tests pass before PR submission
✅ **Frequent Commits**: Commit at each task phase with passing tests
✅ **Code Quality**: Functions <30 lines, files <500 lines, minimal dependencies

---

## Success Validation

**Upon Completion**:
1. ✅ All Constitution principles validated (TDD, fast tests, code quality, docs)
2. ✅ PR-FAQ generation <2 minutes for typical reports (SC-001)
3. ✅ 100% PR-FAQ structure validation (SC-002)
4. ✅ User testing: ≥85% acceptance of generated content (SC-003)
5. ✅ ≥80% FAQs directly address research findings (SC-004)
6. ✅ 100% export success across all formats (SC-005)
7. ✅ Performance: 5,000+ word reports in <3 minutes (SC-006)
8. ✅ Integration with existing research infrastructure (batch reports, synth personas)

---

## Known Risks & Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| LLM output quality varies | Medium | Few-shot examples + chain-of-thought + confidence_score + validation |
| Batch summary inconsistency | Medium | Validate required sections (executive_summary, recommendations) before processing |
| PDF export library choice | Low | Research reportlab vs weasyprint in Phase 0; default to reportlab |
| Synth persona archetype matching | Low | Simple string matching initially; add fuzzy matching in future if needed |
| Rate limiting on LLM calls | Low | Implement exponential backoff in generator.py |

---

## Timeline (Not Estimated)

**Execution Order**:
1. Phase 0: Research & validation (parallel tasks)
2. Phase 1: Data model + contracts + quickstart documentation
3. Agent context update
4. /speckit.tasks command for Phase 2 implementation (test-first task generation)
