# Implementation Plan: Topic Guides with Multi-Modal Context

**Branch**: `006-topic-guides` | **Date**: 2025-12-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-topic-guides/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature enables researchers to organize multi-modal contextual materials (images, PDFs, documents) in structured topic guide directories and automatically generate AI-powered descriptions for each file. Synths can then access these materials during UX research interviews to provide contextually-informed responses. The system uses content hashing to track file changes, LLM integration for description generation, and robust error handling for various failure scenarios.

## Technical Context

**Language/Version**: Python 3.13 (matching project requirement)
**Primary Dependencies**:
- `openai>=2.8.0` (LLM API for file descriptions - already in project)
- `typer>=0.9.0` (CLI framework - already in project)
- `loguru>=0.7.0` (logging - already in project)
- `pathlib` (built-in - file operations)
- `hashlib` (built-in - MD5/SHA hashing)
- `PyPDF2` or `pypdf` (NEEDS RESEARCH - PDF text extraction)
- `Pillow` (NEEDS RESEARCH - image metadata/OCR if needed)

**Storage**: File system (directories under `data/topic_guides/`), markdown files (`summary.md`)
**Testing**: pytest (already configured in project)
**Target Platform**: Development environment (macOS/Linux/Windows CLI)
**Project Type**: Single project (CLI tool extension)
**Performance Goals**:
- Create topic guide directory in <10 seconds
- Process 20 files in <2 minutes (6 seconds per file average)
- Hash computation <0.1 seconds per file

**Constraints**:
- LLM API rate limits (OpenAI default: 3 requests/minute for free tier, higher for paid)
- File size limits for LLM vision API (OpenAI: 20MB per image)
- Network dependency for LLM calls

**Scale/Scope**:
- Expected: 10-50 topic guides per researcher
- 10-100 files per topic guide
- File sizes: typically 10KB-10MB

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Test-First Development (TDD/BDD) ✅

**Status**: PASS - Planned approach follows TDD

**Evidence**:
- User stories define clear Given-When-Then acceptance criteria
- Tests will be written before implementation for each user story
- Test structure: unit tests for file operations, integration tests for LLM interaction, contract tests for CLI interface

**Plan**:
1. Write tests for P1 (directory creation) → Implement → Refactor
2. Write tests for P2 (file documentation) → Implement → Refactor
3. Write tests for P3 (synth integration) → Implement → Refactor

### Principle II: Fast Test Battery on Every Commit ✅

**Status**: PASS - Fast test strategy defined

**Fast Battery** (<5 seconds total):
- Unit tests for file hashing (mocked file I/O)
- Unit tests for markdown parsing/generation
- Unit tests for file type detection
- Mocked LLM API calls (no network)

**Slow Battery** (full integration):
- Real LLM API calls (with VCR.py for recording)
- File system operations with temp directories
- End-to-end CLI tests

**Estimated Fast Battery Time**: ~2-3 seconds

### Principle III: Complete Test Battery Before Pull Requests ✅

**Status**: PASS - Comprehensive test coverage planned

**Coverage Requirements**:
- All 3 user stories have acceptance criteria → tests
- Edge cases (5 identified) → tests
- Error handling (LLM failures, file errors) → tests
- Minimum coverage: 85% for new code

### Principle IV: Frequent Version Control Commits ✅

**Status**: PASS - Atomic commit strategy

**Commit Plan**:
1. `test: add tests for topic guide directory creation`
2. `feat: implement directory creation and summary.md initialization`
3. `test: add tests for file scanning and hashing`
4. `feat: implement file scanning with content hash tracking`
5. `test: add tests for LLM integration`
6. `feat: integrate OpenAI API for file descriptions`
7. `test: add tests for error handling`
8. `feat: implement error handling for unsupported files and API failures`
9. `docs: add quickstart guide for topic guides CLI`
10. `refactor: extract file processing logic into separate module`

### Principle V: Simplicity and Code Quality ✅

**Status**: PASS - Simple architecture planned

**Simplicity Measures**:
- Single module: `src/synth_lab/topic_guides/` (~300-400 lines total)
- Function-first approach (no unnecessary classes)
- Use existing project patterns (CLI with Typer, logging with Loguru)
- Minimal dependencies (leverage built-ins: pathlib, hashlib)

**File Organization** (estimated lines):
- `cli.py` (~100 lines) - Typer CLI commands
- `file_processor.py` (~150 lines) - File scanning, hashing, LLM calls
- `summary_manager.py` (~100 lines) - Summary.md parsing/writing
- `models.py` (~50 lines) - Data classes for FileDescription, TopicGuide

### Principle VI: Language Requirements ✅

**Status**: PASS - Language standards followed

**Code**: English (variable names, function names, classes)
**Documentation**: Portuguese (docstrings, comments, quickstart.md)
**User-facing**: i18n-ready (CLI help text, log messages) - English and Portuguese initially

## Project Structure

### Documentation (this feature)

```text
specs/006-topic-guides/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (PENDING)
├── data-model.md        # Phase 1 output (PENDING)
├── quickstart.md        # Phase 1 output (PENDING)
├── contracts/           # Phase 1 output (PENDING)
│   └── cli-interface.md # CLI command contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/synth_lab/
├── topic_guides/        # NEW - This feature
│   ├── __init__.py
│   ├── cli.py           # Typer CLI commands
│   ├── file_processor.py # File scanning, hashing, LLM integration
│   ├── summary_manager.py # Summary.md parsing/writing
│   └── models.py        # Data classes
├── research/            # EXISTING - Integration point for P3
│   ├── interview.py     # Will be modified to load topic guides
│   └── ...
├── gen_synth/           # EXISTING - No changes
└── __main__.py          # EXISTING - Add topic-guides subcommand

tests/
├── topic_guides/        # NEW - This feature
│   ├── unit/
│   │   ├── test_file_processor.py
│   │   ├── test_summary_manager.py
│   │   └── test_models.py
│   ├── integration/
│   │   ├── test_llm_integration.py
│   │   └── test_cli_commands.py
│   └── contract/
│       └── test_cli_interface.py
├── research/            # EXISTING - Integration tests
└── ...

data/
├── topic_guides/        # NEW - User data directory
│   └── .gitkeep         # Keep directory in repo
├── synths/              # EXISTING
└── transcripts/         # EXISTING
```

**Structure Decision**: Single project structure with new `topic_guides` module under `src/synth_lab/`. This aligns with existing project organization (separate modules for `gen_synth`, `research`). The feature integrates with existing `research` module for P3 (synth interview context access).

## Complexity Tracking

> **No violations - Constitution Check passed without justifications needed**

---

# Phase 0: Research & Technical Decisions

## Research Tasks

The following areas require research before implementation:

### 1. PDF Text Extraction Library

**Question**: Which Python library should we use for extracting text from PDFs for LLM analysis?

**Options to Research**:
- `PyPDF2` (popular, pure Python)
- `pypdf` (PyPDF2 fork, actively maintained)
- `pdfplumber` (good for tables, more dependencies)
- `pymupdf` (PyMuPDF - fast, C-based, larger dependency)

**Research Criteria**:
- Ease of installation (prefer pure Python or minimal C deps)
- Text extraction quality for typical UX research documents
- File size handling (need to support up to 100MB)
- Compatibility with Python 3.13
- License compatibility (project is open source)

### 2. Image Processing for LLM Vision API

**Question**: Do we need additional image processing before sending to OpenAI Vision API, or can we send files directly?

**Research Items**:
- OpenAI Vision API input requirements (formats, sizes, resolution)
- Whether to use Pillow for preprocessing (resize, format conversion)
- Handling of large images (>20MB OpenAI limit)
- Image metadata extraction (if needed for descriptions)

**Research Criteria**:
- Minimal processing overhead
- Maximum compatibility with common UX screenshot formats (PNG, JPEG)
- Error handling for corrupted images

### 3. LLM API Best Practices for File Descriptions

**Question**: What's the optimal prompt structure and API configuration for generating 10-50 word file descriptions?

**Research Items**:
- OpenAI API parameters (temperature, max_tokens, model selection)
- Prompt engineering for concise, accurate descriptions
- Cost optimization (which model: gpt-4o-mini vs gpt-4o for vision)
- Rate limiting and retry strategies
- Error handling patterns

**Research Criteria**:
- Cost per file (<$0.01 per file target)
- Description quality and consistency
- API reliability and error recovery

### 4. Content Hash Algorithm Selection

**Question**: Should we use MD5 or SHA-256 for file content hashing?

**Options**:
- **MD5**: Faster, 128-bit, not cryptographically secure (but OK for deduplication)
- **SHA-256**: Slower, 256-bit, cryptographically secure

**Research Criteria**:
- Performance for 1MB-10MB files
- Collision risk for this use case (low risk tolerance - false positives mean missed updates)
- Standard library support and ease of use

**Initial Recommendation**: MD5 (speed priority, no security requirement, collision risk negligible for <1000 files per guide)

### 5. Synth Interview Integration Pattern

**Question**: How should synths access topic guide materials during interviews?

**Research Items**:
- Current `research/interview.py` architecture
- How to pass topic guide context to LLM prompts
- Performance impact of loading summary.md during interviews
- Caching strategies for topic guide data

**Research Criteria**:
- Minimal changes to existing interview code
- No performance degradation for interviews without topic guides
- Clear separation of concerns

---

# Phase 1: Design & Contracts

**Prerequisites**: Phase 0 research complete, all NEEDS CLARIFICATION resolved

## Data Model

See [data-model.md](./data-model.md) - To be generated in Phase 1

**Key Entities** (from spec):
1. **TopicGuide**: Directory-based collection of context files
2. **SummaryFile**: Markdown file with context and file descriptions
3. **ContextFile**: Individual file (image, document) in topic guide
4. **FileDescription**: AI-generated 10-50 word description with hash

## API Contracts

See [contracts/cli-interface.md](./contracts/cli-interface.md) - To be generated in Phase 1

**CLI Commands**:
1. `synthlab topic-guide create --name <topic-name>`
2. `synthlab topic-guide update --name <topic-name>`
3. `synthlab topic-guide list`
4. `synthlab topic-guide show --name <topic-name>`

## Integration Points

### Existing Code Modification

**File**: `src/synth_lab/research/interview.py`

**Changes**: Add topic guide loading in interview initialization
- New parameter: `topic_guide: Optional[str] = None`
- Load `data/topic_guides/<topic_guide>/summary.md` if specified
- Include file descriptions in LLM context

**Estimated Impact**: ~20 lines added, no breaking changes

### CLI Integration

**File**: `src/synth_lab/__main__.py`

**Changes**: Register new subcommand group `topic-guide`
- Import `topic_guides.cli` module
- Add to Typer app as subcommand group

**Estimated Impact**: ~5 lines added

## Testing Strategy

### Test Levels

**Unit Tests** (fast battery, <5s total):
- File hashing logic (mocked file I/O)
- Summary.md parsing/writing
- File type detection
- CLI argument validation
- Error handling logic

**Integration Tests** (slow battery):
- Real file system operations (temp directories)
- LLM API calls (VCR.py for recording/replay)
- End-to-end CLI workflows

**Contract Tests**:
- CLI interface stability (command structure, arguments, output format)

### Test Data

**Fixtures**:
- Sample images (PNG, JPEG - 100KB each)
- Sample PDFs (2-3 pages, <1MB)
- Sample markdown and text files
- Pre-recorded LLM API responses (VCR.py cassettes)

**Test Topic Guides**:
- `test-amazon` (5 files: 3 PNG, 1 PDF, 1 MD)
- `test-empty` (no files)
- `test-large` (20+ files for performance testing)

### Coverage Goals

- **Line Coverage**: 85% minimum
- **Branch Coverage**: 80% minimum
- **Critical Paths**: 100% (directory creation, file hashing, LLM calls, error handling)

---

# Phase 2: Task Decomposition

**Note**: Phase 2 is executed by `/speckit.tasks` command (NOT `/speckit.plan`)

The task list will be generated from this plan and organized by user story priority (P1 → P2 → P3).

---

# Success Criteria Validation

## From Spec (mapped to implementation)

- **SC-001**: Users can create topic guide in <10s
  - **Implementation**: Simple directory creation + file write = <1s actual
  - **Validation**: Performance test in integration suite

- **SC-002**: Document 20 files in <2 minutes
  - **Implementation**: LLM API calls are bottleneck (~5s each)
  - **Risk**: API rate limits may extend time
  - **Mitigation**: Implement exponential backoff, consider batching

- **SC-003**: 95% description accuracy
  - **Implementation**: Depends on LLM model quality
  - **Validation**: Manual review of test outputs, user acceptance testing

- **SC-004**: Synths can access materials in interviews
  - **Implementation**: Load summary.md into interview context
  - **Validation**: Integration test with mock interview

- **SC-005**: 100% accuracy in identifying new/modified files
  - **Implementation**: Content hash comparison (MD5/SHA)
  - **Validation**: Unit tests with various file modification scenarios

- **SC-006**: Handle all supported file types without errors
  - **Implementation**: Type detection + robust error handling
  - **Validation**: Test suite with all supported formats + edge cases

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| LLM API rate limits slow processing | Medium | Medium | Implement retry with backoff, document expected times |
| Large PDF extraction fails | Low | Low | Set file size limits, graceful failure with placeholder |
| Hash collision causes missed update | Very Low | Medium | Use SHA-256 if MD5 shows issues, document in research |
| Integration breaks existing interview code | Low | High | Comprehensive integration tests, feature flag for P3 |
| Cost of LLM API calls exceeds budget | Medium | Low | Use gpt-4o-mini, document costs, implement batch processing |

---

# Next Steps

1. **Execute Phase 0**: Run research tasks (see Research Tasks section above)
2. **Generate Phase 1 Artifacts**:
   - `research.md` (consolidate research findings)
   - `data-model.md` (detailed entity definitions)
   - `contracts/cli-interface.md` (CLI command specifications)
   - `quickstart.md` (user guide for topic guides feature)
3. **Update Agent Context**: Run `.specify/scripts/bash/update-agent-context.sh claude`
4. **Validate Constitution Check**: Re-run after Phase 1 design complete
5. **Proceed to Phase 2**: Run `/speckit.tasks` to generate task list
