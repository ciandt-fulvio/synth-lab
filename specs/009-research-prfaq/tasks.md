# Task List: Research Report to PR/FAQ Generator

**Feature**: `009-research-prfaq`
**Branch**: `009-research-prfaq`
**Created**: 2025-12-19
**Status**: Ready for Implementation

## Overview

Generate professional PR-FAQ documents from research batch reports using Amazon's Working Backwards framework. Feature includes 4 user stories organized by priority (P1-P3), enabling independent development, testing, and deployment of each capability.

### MVP Scope

**Recommended MVP** (Phase 3 only): User Story 1 - Generate PR-FAQ
- Minimum viable feature: Transform research batch report → validated PR-FAQ JSON
- All acceptance criteria met for core generation capability
- Estimated value: 80% of feature utility
- Can be deployed independently before edit/export/history features

### Parallel Execution Opportunities

- **Setup Phase**: All tasks parallelizable (independent file creation)
- **Foundational Phase**: All tasks parallelizable (independent modules)
- **User Story 1 (P1)**: Tests + Models parallelizable; Generator, Validator, Prompts sequential after Models
- **User Story 2 (P2)**: Independent of US1; can run in parallel after Foundational
- **User Story 3 (P2)**: Independent of US1; can run in parallel after Foundational
- **User Story 4 (P3)**: Can run in parallel with US2 & US3 after Foundational

---

## Phase 1: Setup & Project Initialization

Initialize project structure and configure development environment.

### Independent Test Criteria

✅ Project structure matches plan.md layout
✅ All module directories created
✅ Test directories mirroring source structure
✅ Development dependencies installed
✅ Pre-commit hooks configured for fast test battery

### Tasks

- [X] T001 Create `src/synth_lab/research_prfaq/` module directory structure with all 7 module files (`__init__.py`, `models.py`, `generator.py`, `exporter.py`, `validator.py`, `prompts.py`, `cli.py`)
- [X] T002 [P] Create `tests/unit/synth_lab/research_prfaq/` directory with 5 unit test files: `test_models.py`, `test_generator.py`, `test_exporter.py`, `test_validator.py`, `test_cli.py`
- [X] T003 [P] Create `tests/integration/synth_lab/research_prfaq/` directory with 3 integration test files: `test_batch_summary_parsing.py`, `test_prfaq_generation_e2e.py`, `test_export_formats.py`
- [X] T004 [P] Create `tests/contract/synth_lab/research_prfaq/` directory with contract test file `test_json_schema.py`
- [X] T005 [P] Create output directories: `data/outputs/prfaq/` and `data/outputs/prfaq/.versions/`
- [X] T006 Create `specs/009-research-prfaq/contracts/` directory and `prfaq-schema.json` with JSON Schema from plan.md (Section 1.2)
- [ ] T007 [P] Add reportlab or weasyprint dependency to `pyproject.toml` (decision from Phase 0 research.md) [DEFERRED - Export in Phase 5]
- [X] T008 Verify existing dependencies available: openai>=2.8.0, pydantic>=2.0, typer>=0.9.0, loguru
- [ ] T009 Create `.pre-commit-config.yaml` entry to run fast test battery (unit tests with mocked LLM) on every commit [DEFERRED - Phase 7]
- [ ] T010 Create `specs/009-research-prfaq/research.md` placeholder for Phase 0 research findings (few-shot examples, PDF library decision, etc.) [DEFERRED - Documentation in Phase 7]

---

## Phase 2: Foundational Modules & Infrastructure

Implement core data models, validation, and utilities. These tasks are blocking prerequisites for all user stories.

### Independent Test Criteria

✅ All Pydantic models instantiate correctly
✅ JSON Schema validation passes for valid documents
✅ JSON Schema validation rejects invalid documents
✅ Models can be serialized to/from JSON
✅ Batch summary parsing extracts all required sections

### Tasks

- [X] T011 [P] Create Pydantic models in `src/synth_lab/research_prfaq/models.py`: ResearchReport (batch_id, summary_content, sections, generated_at, parsed_insights), PRFAQDocument (id, batch_id, press_release, faqs, metadata, edit_history), Version (id, prfaq_id, timestamp, changes), and supporting classes per plan.md Section 1.1
- [X] T012 [P] Create `src/synth_lab/research_prfaq/validator.py` with JSONSchemaValidator class: validate_prfaq_structure() method that validates against `contracts/prfaq-schema.json`, consistency checks (headline != empty, 8-12 FAQs), and returns validation status + errors
- [X] T013 [P] Create `src/synth_lab/research_prfaq/prompts.py` with: SYSTEM_PROMPT (chain-of-thought instruction focused on "recommendations" + "recurrent_patterns" sections), 2 few-shot examples (high-quality PR-FAQ samples), and helper functions for prompt formatting per plan.md Section 1.2
- [X] T014 Create batch summary parser in `src/synth_lab/research_prfaq/models.py` or utility function: parse_batch_summary(batch_id) → loads `data/transcripts/{batch_id}/batch_summary.json`, parses Markdown sections, extracts pain points/benefits/quotes, returns ResearchReport
- [X] T015 [P] Create `src/synth_lab/research_prfaq/__init__.py` with public API exports: ResearchReport, PRFAQDocument, JSONSchemaValidator, parse_batch_summary, etc.
- [X] T016 [P] Create logging setup in `src/synth_lab/research_prfaq/models.py` or separate utility: configure loguru logger for feature (file output to `logs/research_prfaq.log`)

### Acceptance Criteria

- ✅ All models instantiate with valid data
- ✅ Serialization round-trip (JSON → model → JSON) preserves data
- ✅ Validator accepts valid PR-FAQ documents
- ✅ Validator rejects documents missing required fields or with <8 FAQs
- ✅ Batch summary parser correctly extracts all sections from Markdown
- ✅ Logger outputs to file without errors

---

## Phase 3: User Story 1 - Generate PR-FAQ from Research Report (P1)

Core feature: Transform research batch reports into valid PR-FAQ documents using LLM with chain-of-thought + few-shot prompting.

### Story Goal

User can execute `synthlab research-prfaq generate --batch-id {batch_id}` and receive a complete, valid PR-FAQ document with Press Release and FAQ sections derived from research findings.

### Independent Test Criteria

✅ PR-FAQ generated in <2 minutes for typical reports (SC-001)
✅ Generated document passes JSON Schema validation (SC-002)
✅ Press Release section includes required fields extracted from research (SC-003)
✅ FAQ includes 8-12 questions addressing research pain points/benefits (SC-004)
✅ Customer segment field populated for each FAQ (synth persona linking)
✅ Document persisted to `data/outputs/prfaq/{batch_id}_{timestamp}_prfaq.json`
✅ Confidence score calculated for quality assessment

### Tasks

**Tests (if TDD - write before implementation)**:
- [ ] T017 [US1] Create unit test in `tests/unit/synth_lab/research_prfaq/test_generator.py`: test_generate_prfaq_with_mocked_llm() - validates LLM parsing and output structure with mocked API calls [DEFERRED - Phase 7]
- [ ] T018 [P] [US1] Create unit test in `tests/unit/synth_lab/research_prfaq/test_models.py`: test_prfaq_document_validation() - validates Pydantic model constraints (8-12 FAQs, required fields, types) [DEFERRED - Phase 7]
- [ ] T019 [P] [US1] Create contract test in `tests/contract/synth_lab/research_prfaq/test_json_schema.py`: test_valid_prfaq_passes_schema() and test_invalid_prfaq_fails_schema() using `contracts/prfaq-schema.json` [DEFERRED - Phase 7]
- [ ] T020 [US1] Create integration test in `tests/integration/synth_lab/research_prfaq/test_prfaq_generation_e2e.py`: test_generate_prfaq_e2e() - real batch_summary.json parsing, LLM call (with fixture/mock), file I/O validation [DEFERRED - Phase 7]

**Implementation**:
- [X] T021 [US1] Create `src/synth_lab/research_prfaq/generator.py` with PRFAQGenerator class:
  - __init__(model="gpt-4o", confidence_threshold=0.75)
  - generate(research_report: ResearchReport) → PRFAQDocument
  - Extract pain points from research.sections["recommendations"] + ["recurrent_patterns"]
  - Build chain-of-thought prompt with few-shot examples from prompts.py
  - Call OpenAI API with JSON Schema structured output mode
  - Parse LLM response, calculate confidence_score
  - Handle rate limiting with exponential backoff (3 retries)
  - Return PRFAQDocument with metadata
- [X] T022 [US1] Add LLM error handling to generator: retry logic for rate limits, API errors, malformed responses; fallback behavior if generation fails
- [X] T023 [US1] Create `src/synth_lab/research_prfaq/cli.py` with generate command:
  - @app.command() for "research-prfaq generate"
  - Arguments: --batch-id (required), --output (optional, default: data/outputs/prfaq/), --model (optional)
  - Load batch_summary.json via parse_batch_summary()
  - Call PRFAQGenerator.generate()
  - Validate result with JSONSchemaValidator
  - Persist to JSON file with metadata (generated_at, model_used, validation_status, confidence_score)
  - Output: confirmation message + file path + confidence score
  - Error handling: batch_id not found, validation failure, LLM error
- [X] T024 [US1] Integrate generate command into main synthlab Typer app: add research_prfaq subcommand group under main `synthlab` command (following pattern from research_agentic, query modules)
- [X] T025 [P] [US1] Create file I/O utilities in generator or separate module: save_prfaq_json(prfaq: PRFAQDocument, output_dir) → writes to {batch_id}_{timestamp}_prfaq.json with proper formatting and metadata

### Success Validation

- ✅ `uv run synthlab research-prfaq generate --batch-id test_batch` completes successfully
- ✅ Generated JSON file exists at `data/outputs/prfaq/test_batch_{timestamp}_prfaq.json`
- ✅ File passes JSON Schema validation (`contracts/prfaq-schema.json`)
- ✅ Press Release section has headline, one_liner, problem_statement, solution_overview
- ✅ FAQ array contains 8-12 items, each with question, answer, customer_segment
- ✅ Metadata includes generated_at, model_used, validation_status, confidence_score
- ✅ All unit tests pass (<0.5s each, mocked LLM)
- ✅ Integration E2E test passes (real file I/O, real or mocked LLM)
- ✅ Fast test battery completes in <5 seconds

---

## Phase 4: Manual Editing & Validation (SIMPLIFIED)

**Approach**: Users manually edit JSON files in their preferred editor. CLI provides validation only.

**Rationale**: Simpler than interactive CLI editor. Users prefer familiar tools (VS Code, vim, etc.). JSON files are git-friendly and transparent.

### Story Goal

Users can manually edit `data/outputs/prfaq/{batch_id}_prfaq.json` files and validate them with `synthlab research-prfaq validate {batch_id}`.

### Independent Test Criteria

✅ Users can edit JSON files directly with any text editor
✅ Validate command checks edited files against JSON Schema
✅ Validation reports specific errors (missing fields, invalid FAQ count, etc.)
✅ Re-generation warns if file already exists

### Tasks

- [X] T026-T030 ELIMINATED - No interactive editor needed
- [X] T031 Add regeneration warning to generate command (already implemented with --force flag pattern)
- [ ] T032 [RENAMED TO T026] Create validate command in `src/synth_lab/research_prfaq/cli.py`:
  - @app.command() for "research-prfaq validate"
  - Arguments: batch_id (required)
  - Load JSON file via load_prfaq_json()
  - Validate against JSON Schema using existing validator
  - Display validation results with detailed error messages
  - Output: ✓ Valid / ✗ Errors with field-level details

### Success Validation

- ✅ Users can edit JSON files with any editor
- ✅ `uv run synthlab research-prfaq validate batch_001` validates edited files
- ✅ Validation catches schema violations (missing fields, wrong types, etc.)
- ✅ Generate command warns before overwriting existing files

### Manual Editing Workflow

```bash
# 1. Generate PR-FAQ
synthlab research-prfaq generate batch_001

# 2. Edit JSON file manually
vim data/outputs/prfaq/batch_001_prfaq.json

# 3. Validate edits
synthlab research-prfaq validate batch_001
# Output: ✓ Valid PR-FAQ with 8 FAQ items

# 4. Regenerate (if needed)
synthlab research-prfaq generate batch_001
# Warning: File exists. Use --force to overwrite.
```

---

## Phase 5: User Story 3 - Export PR-FAQ to Multiple Formats (P2)

Enable users to export PR-FAQ documents to PDF, Markdown, and HTML formats for stakeholder sharing.

### Story Goal

User can execute `synthlab research-prfaq export --prfaq-id {id} --format <pdf|md|html>` to generate formatted output files ready for presentations, git repositories, or internal wikis.

### Independent Test Criteria

✅ Export command loads PR-FAQ JSON file
✅ PDF export generates professional 341x341px-ready document with proper formatting
✅ Markdown export creates git-friendly document with proper heading hierarchy
✅ HTML export creates web-ready document with semantic HTML
✅ All exports preserve content structure (Press Release + FAQ sections)
✅ Files written to `data/outputs/prfaq/{batch_id}_exports/`
✅ Export completes in <10 seconds per format (SC-005 & SC-006)

### Tasks

- [ ] T033 [US3] Create unit test in `tests/unit/synth_lab/research_prfaq/test_exporter.py`: test_markdown_formatter() - validates MD heading hierarchy and structure
- [ ] T034 [P] [US3] Create unit test in `tests/unit/synth_lab/research_prfaq/test_exporter.py`: test_pdf_formatter_structure() - validates PDF output structure (mocked reportlab)
- [ ] T035 [P] [US3] Create unit test in `tests/unit/synth_lab/research_prfaq/test_exporter.py`: test_html_formatter_structure() - validates HTML semantic structure
- [ ] T036 [US3] Create integration test in `tests/integration/synth_lab/research_prfaq/test_export_formats.py`: test_export_to_pdf() - real reportlab call, verify file creation
- [ ] T037 [P] [US3] Create integration test in `tests/integration/synth_lab/research_prfaq/test_export_formats.py`: test_export_to_markdown() - real file write, verify content
- [ ] T038 [P] [US3] Create integration test in `tests/integration/synth_lab/research_prfaq/test_export_formats.py`: test_export_to_html() - real file write, verify content
- [ ] T039 [US3] Create `src/synth_lab/research_prfaq/exporter.py` with PRFAQExporter class:
  - __init__(template_dir=None)
  - export_to_pdf(prfaq: PRFAQDocument, output_path) → generates PDF using reportlab with:
    - Title: Press Release headline
    - Subtitle: one_liner
    - Sections: problem_statement, solution_overview, FAQ items
    - Styling: professional formatting, proper font sizing, margins
  - export_to_markdown(prfaq: PRFAQDocument, output_path) → generates Markdown with:
    - H1: Headline, H2: problem_statement, solution_overview, FAQ, Answer structure
    - Git-friendly formatting (proper indentation, code blocks if needed)
  - export_to_html(prfaq: PRFAQDocument, output_path) → generates HTML with:
    - Semantic tags (header, section, article)
    - CSS styling (inline or external)
    - Responsive layout
- [ ] T040 [US3] Create export command in `src/synth_lab/research_prfaq/cli.py`:
  - @app.command() for "research-prfaq export"
  - Arguments: --prfaq-id (required), --format (pdf|md|html), --output (optional)
  - Load PR-FAQ from JSON
  - Call PRFAQExporter.export_to_{format}()
  - Create timestamped exports directory if needed
  - Output: file path + confirmation
  - Error handling: invalid format, file write error
- [ ] T041 [P] [US3] Create jinja2 templates for Markdown and HTML export in `src/synth_lab/research_prfaq/templates/`:
  - `prfaq.md.j2` - Markdown template with variables for headline, problem_statement, faqs list
  - `prfaq.html.j2` - HTML template with semantic structure
- [ ] T042 [P] [US3] Add reportlab/weasyprint dependency import and initialization in exporter.py (verify library choice from Phase 0 research.md)

### Success Validation

- ✅ `uv run synthlab research-prfaq export --prfaq-id {id} --format pdf` generates PDF file
- ✅ `uv run synthlab research-prfaq export --prfaq-id {id} --format markdown` generates Markdown file
- ✅ `uv run synthlab research-prfaq export --prfaq-id {id} --format html` generates HTML file
- ✅ All exports written to `data/outputs/prfaq/{id}_exports/`
- ✅ Files are readable and properly formatted
- ✅ All unit tests pass (mocked)
- ✅ All integration tests pass (real file generation)
- ✅ Fast test battery passes

---

## Phase 6: User Story 4 - View PR-FAQ Generation History (P3)

Enable users to discover, list, and compare PR-FAQ documents with version tracking and generation history.

### Story Goal

Users can execute `synthlab research-prfaq list` and `synthlab research-prfaq history --batch-id {id}` to view all generated PR-FAQs and track evolution over time.

### Independent Test Criteria

✅ List command discovers all PR-FAQ files in `data/outputs/prfaq/`
✅ List displays: ID, Batch ID, Created, Modified, Status (valid/edited/needs_review)
✅ History command shows version timeline with all generated + edited versions
✅ Version diffs display field changes (old_value → new_value)
✅ Batch ID filtering works in list command

### Tasks

- [ ] T043 [US4] Create unit test in `tests/unit/synth_lab/research_prfaq/test_cli.py`: test_list_command_parsing() - validates output formatting
- [ ] T044 [P] [US4] Create unit test in `tests/unit/synth_lab/research_prfaq/test_cli.py`: test_history_command_diff_calculation() - validates version comparison logic
- [ ] T045 [US4] Create history/discovery utilities in `src/synth_lab/research_prfaq/generator.py` or separate module:
  - discover_prfaqs(output_dir="data/outputs/prfaq/") → scans directory, returns list of PRFAQDocument metadata (id, batch_id, created, modified, status)
  - get_prfaq_history(batch_id) → reads all versions from .versions/ directory, returns version timeline with diffs
  - calculate_version_diff(old_prfaq, new_prfaq) → compares versions, returns list of field changes
- [ ] T046 [US4] Create list command in `src/synth_lab/research_prfaq/cli.py`:
  - @app.command() for "research-prfaq list"
  - Optional arguments: --batch-id (filter), --sort (created|modified)
  - Call discover_prfaqs()
  - Format as Rich table: ID | Batch ID | Created | Modified | Status
  - Support pagination (e.g., --page 1 --limit 10)
  - Output: table + summary (total count)
- [ ] T047 [US4] Create history command in `src/synth_lab/research_prfaq/cli.py`:
  - @app.command() for "research-prfaq history"
  - Required argument: --batch-id
  - Call get_prfaq_history()
  - Display version timeline with:
    - Version number, timestamp, generation method (auto/manual-edit)
    - Summary of changes per version
    - Option to show detailed diff: --verbose
  - Output: formatted timeline
- [ ] T048 [P] [US4] Create version diff formatter: display old_value → new_value for each field change
- [ ] T049 [US4] Add version persistence: modify save_prfaq_json() to also write version to `.versions/{batch_id}_{version_number}.json`

### Success Validation

- ✅ `uv run synthlab research-prfaq list` displays all PR-FAQs in table format
- ✅ `uv run synthlab research-prfaq list --batch-id {id}` filters results
- ✅ `uv run synthlab research-prfaq history --batch-id {id}` shows version timeline
- ✅ Version diffs display field changes clearly
- ✅ Unit tests pass
- ✅ Output formatting is clean and readable

---

## Phase 7: Polish & Cross-Cutting Concerns

Complete documentation, integration, performance optimization, and final testing.

### Independent Test Criteria

✅ All commands visible in `synthlab --help`
✅ Quickstart guide (quickstart.md) validated end-to-end
✅ README.md updated with new commands
✅ All fast tests pass in <5 seconds
✅ All integration tests pass
✅ Performance targets met: generation <2 min, export <10s
✅ Error messages are user-friendly and actionable

### Tasks

- [ ] T050 Update `README.md` with new `research-prfaq` commands:
  - Add section: "Research PR-FAQ Generation"
  - List all 5 commands with examples
  - Usage examples for each user story
  - Link to quickstart.md
- [ ] T051 [P] Create `specs/009-research-prfaq/quickstart.md` (from plan.md Section 1.3):
  - Workflow diagram: research-batch → PR-FAQ → export
  - Example commands for each user story
  - Expected outputs and files
  - Troubleshooting section
- [ ] T052 [P] Create `specs/009-research-prfaq/data-model.md` (from plan.md Section 1.1):
  - Entity definitions with all fields, types, relationships
  - State transition diagram (generated → valid → edited → exported)
  - Example JSON for each entity
- [ ] T053 Create final integration test in `tests/integration/synth_lab/research_prfaq/test_prfaq_generation_e2e.py`: test_complete_workflow_e2e() - batch → generate → edit → export (all 4 user stories)
- [ ] T054 [P] Create performance test in `tests/integration/synth_lab/research_prfaq/test_prfaq_generation_e2e.py`: test_generation_performance() - verify <2 min for 5000+ word report (SC-001)
- [ ] T055 [P] Create performance test: test_export_performance() - verify <10s per format (SC-005)
- [ ] T056 Implement comprehensive error handling across all modules:
  - File not found errors with helpful suggestions
  - LLM API errors with retry guidance
  - JSON validation errors with field details
  - User-friendly CLI error messages
- [ ] T057 [P] Add logging to all major operations:
  - generator.generate() → log chain-of-thought steps + confidence score
  - validator.validate() → log validation results
  - exporter.export_*() → log file creation + format-specific details
  - cli commands → log command execution + results
- [ ] T058 Create `src/synth_lab/research_prfaq/constants.py` with:
  - DEFAULT_MODEL = "gpt-4o"
  - CONFIDENCE_THRESHOLD = 0.75
  - FAQ_MIN_COUNT, FAQ_MAX_COUNT = 8, 12
  - OUTPUT_DIR = "data/outputs/prfaq/"
  - Etc.
- [ ] T059 [P] Verify CLI integration: `uv run synthlab research-prfaq --help` shows all 5 subcommands with descriptions
- [ ] T060 Run full test suite: unit + integration + contract tests, confirm all pass
- [ ] T061 [P] Run ruff linter: `ruff check src/synth_lab/research_prfaq/` and fix any style violations (per project code style guide)
- [ ] T062 [P] Run type checking: verify all type hints are correct (Pydantic models, function signatures)
- [ ] T063 Create final commit message documenting feature completion and test results
- [ ] T064 [P] Generate code coverage report for `research_prfaq` module (target: >80% coverage)

### Success Validation

- ✅ All CLI commands accessible from main `synthlab` app
- ✅ Help text clear and complete
- ✅ Quickstart guide walkthrough succeeds end-to-end
- ✅ README updated with new feature
- ✅ All tests pass (unit, integration, contract, E2E)
- ✅ Code style and type checking pass
- ✅ Performance targets validated
- ✅ Error messages tested and user-friendly
- ✅ Code coverage >80%

---

## Dependencies & Execution Order

### Critical Path (Blocking)

1. **Phase 1** (Setup) → Required before any implementation
2. **Phase 2** (Foundational) → Required before User Stories
3. **Phase 3** (US1: Generate) → MVP core feature
4. Phases 4, 5, 6 → Can execute in parallel after Phase 2
5. **Phase 7** (Polish) → Final phase after all features

### Parallel Execution Timeline

```
Phase 1 (Setup): T001-T010 [All parallel after T001]
         ↓
Phase 2 (Foundational): T011-T016 [All parallel]
         ↓
Phase 3 (US1): T017-T025 [Tests parallel; Generator/CLI sequential after Models]
         ├─→ Phase 4 (US2): T026-T032 [All parallel after Phase 2]
         ├─→ Phase 5 (US3): T033-T042 [Tests parallel; Exporter sequential after Models]
         └─→ Phase 6 (US4): T043-T049 [All parallel after Phase 2]
              ↓
         Phase 7 (Polish): T050-T064 [All parallel, runs after all user stories]
```

### Task Dependencies

```
T001 → T002-T010 (Phase 1)
T001-T010 → T011-T016 (Phase 2)
T011-T016 → T017-T025 (Phase 3, US1)
T011-T016 → T026-T032 (Phase 4, US2)
T011-T016 → T033-T042 (Phase 5, US3)
T011-T016 → T043-T049 (Phase 6, US4)
T017-T049 → T050-T064 (Phase 7)
```

---

## Summary Statistics

- **Total Tasks**: 64
- **Setup Phase**: 10 tasks
- **Foundational Phase**: 6 tasks
- **User Story Phases**: 48 tasks
  - US1 (P1 - Generate): 9 tasks
  - US2 (P2 - Edit): 7 tasks
  - US3 (P2 - Export): 10 tasks
  - US4 (P3 - History): 7 tasks
- **Polish Phase**: 15 tasks

- **Parallelizable Tasks**: 38 (marked with [P])
- **Estimated MVP Completion**: Phase 1 + Phase 2 + Phase 3 = ~30 days engineering effort (5 developers = 6 days parallel)
- **Full Feature Completion**: All phases = ~45 days (5 developers = 9 days parallel)

---

## Test Coverage by User Story

| User Story | Unit Tests | Integration Tests | Contract Tests | E2E Tests | Total |
|---|---|---|---|---|---|
| **US1 - Generate** | 2 | 1 | 1 | 1 | 5 |
| **US2 - Edit** | 1 | 1 | - | 1 | 3 |
| **US3 - Export** | 3 | 3 | - | 1 | 7 |
| **US4 - History** | 2 | 1 | - | - | 3 |
| **Foundational** | 3 | 1 | 1 | - | 5 |
| **Polish** | - | 2 | - | 1 | 3 |
| **Total** | 11 | 9 | 2 | 4 | 26 tests |

---

## MVP Recommendation

**Minimum Viable Product Scope**: Phases 1-3 (Setup + Foundational + US1)

**Rationale**:
- User Story 1 (Generate) delivers 80% of feature value
- Core functionality: Transform research → PR-FAQ
- All acceptance criteria met for stakeholder alignment
- Can be deployed independently
- Remaining features (Edit, Export, History) are enhancements

**MVP Timeline**: ~2 weeks (10 working days)
- Phase 1: 1 day
- Phase 2: 1 day
- Phase 3: 3 days (parallel test + implementation)
- Polish (minimal): 1 day

---

## Implementation Strategy

### Red-Green-Refactor Cycle

1. **Red**: Write failing test (T017-T020 for US1)
2. **Green**: Implement minimum code to pass test (T021-T025)
3. **Refactor**: Clean up, optimize, ensure <500 lines per file
4. **Repeat** for each user story and cross-cutting concern

### Commit Strategy

- One commit per test completion (`test: add test for...`)
- One commit per functional unit completion (`feat: implement...`)
- One commit per refactoring (`refactor: improve...`)
- All commits include passing tests

### Code Review Checklist

- [ ] All tests pass (unit + integration + contract)
- [ ] Code follows project style guide (ruff)
- [ ] Type hints correct (Pydantic, function signatures)
- [ ] Functions <30 lines, files <500 lines
- [ ] Documentation updated (docstrings, comments for complex logic)
- [ ] Logging added for debugging
- [ ] Error messages user-friendly
- [ ] Performance targets met (if applicable)

---

**Status**: Ready for implementation
**Next Step**: Execute Phase 1 setup tasks in parallel, then Phase 2 foundational tasks
