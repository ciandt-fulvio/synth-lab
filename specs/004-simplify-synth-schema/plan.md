# Implementation Plan: Simplify Synth Schema

**Branch**: `004-simplify-synth-schema` | **Date**: 2025-12-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-simplify-synth-schema/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Simplify the synth data schema by removing 5 redundant psychographic and behavioral fields (hobbies, valores, estilo_vida, uso_tecnologia, comportamento_compra) and establish coherence rules that align cognitive biases with Big Five personality traits to ensure psychological realism. This will reduce schema complexity, improve generation performance by ~10%, and create more credible synthetic personas.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: jsonschema>=4.20.0 (schema validation), faker>=21.0.0 (data generation), rich>=13.0.0 (output), typer>=0.9.0 (CLI)
**Storage**: JSON files (`data/schemas/synth-schema-cleaned.json` for schema definition, `data/synths/synths.json` for generated synths), DuckDB database (`synths.duckdb`)
**Testing**: pytest>=7.0.0, pytest-cov>=4.0.0
**Target Platform**: Python CLI application (Linux/macOS/Windows)
**Project Type**: Single project (CLI tool with library modules)
**Performance Goals**:
  - Schema simplification: reduce generation time by ≥10% (currently ~0.5s per synth)
  - Schema validation: maintain <50ms per synth validation
  - Coherence rule validation: add <20ms overhead per synth generation
**Constraints**:
  - Backward compatibility: must read old schema synths
  - File size: schema JSON must be ≤15KB (currently ~18KB)
  - Memory: schema validation must use <10MB RAM
**Scale/Scope**:
  - Schema: ~40 fields remaining after removal of 5 fields
  - Coherence rules: 10 personality-bias mappings (5 Big Five traits × 2 extremes each)
  - Validation: must validate 7 bias fields against 5 personality traits

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Test-First Development (TDD/BDD)

- [x] **Gate**: User stories with Given-When-Then scenarios defined in spec.md
- [x] **Gate**: Acceptance criteria testable and unambiguous
- [x] **Plan**: Tests will be written BEFORE implementation for:
  - Schema field removal validation tests (verify removed fields absent)
  - Personality-bias coherence rule tests (verify bias ranges for each trait level)
  - Backward compatibility tests (verify old synths readable)
  - Validation error message tests (verify meaningful error messages)

**Status**: ✅ PASS - All acceptance scenarios defined in spec.md User Stories section

### Principle II: Fast Test Battery on Every Commit

- [x] **Gate**: Fast tests identified and will execute in <5 seconds
- [x] **Plan**: Fast battery includes:
  - Unit tests for coherence rule calculations (<0.5s total)
  - Schema validation unit tests (<1s total)
  - Field removal validation tests (<0.5s total)
  - **Estimated total**: ~2-3 seconds

**Status**: ✅ PASS - Schema validation is inherently fast (in-memory operations)

### Principle III: Complete Test Battery Before Pull Requests

- [x] **Gate**: Test coverage plan defined
- [x] **Plan**: Complete battery includes:
  - Fast battery (unit tests) ~3s
  - Integration tests (synth generation with coherence rules) ~5s
  - Contract tests (schema validation against spec) ~2s
  - **Total estimated**: ~10 seconds

**Status**: ✅ PASS - Full test coverage planned for all functional requirements

### Principle IV: Frequent Version Control Commits

- [x] **Gate**: Atomic commit strategy planned
- [x] **Plan**: Commits at each phase:
  1. "test: add schema field removal validation tests"
  2. "feat: remove 5 fields from synth schema"
  3. "test: add personality-bias coherence rule tests"
  4. "feat: implement coherence rule validation logic"
  5. "test: add backward compatibility tests"
  6. "feat: add schema version bump and migration support"
  7. "docs: update schema documentation with coherence rules"

**Status**: ✅ PASS - Clear atomic commit points defined

### Principle V: Simplicity and Code Quality

- [x] **Gate**: No unjustified complexity
- [x] **Analysis**:
  - Schema modification: simple JSON editing (file manipulation)
  - Coherence rules: pure functions mapping personality → bias ranges
  - Validation: conditional logic checking ranges
  - No new dependencies required
  - Estimated files impacted:
    - `data/schemas/synth-schema-cleaned.json` (schema definition)
    - `src/synth_lab/gen_synth/validation.py` (add coherence validation)
    - `src/synth_lab/gen_synth/biases.py` (add coherence rule logic)
    - `tests/unit/test_coherence_rules.py` (new)
    - `tests/integration/test_schema_validation.py` (existing, expand)
  - All files will remain <500 lines

**Status**: ✅ PASS - No complex patterns or abstractions needed

### Principle VI: Language Requirements

- [x] **Gate**: Language standards defined
- [x] **Plan**:
  - Code: English (class names, variables, functions)
  - Documentation: Portuguese (docstrings, comments, README sections)
  - Schema: Portuguese field names (existing convention preserved)
  - User-facing messages: i18n-ready with English and Portuguese

**Status**: ✅ PASS - Follows existing project conventions

### Overall Constitution Compliance

**Pre-Research Status**: ✅ ALL GATES PASSED

**Post-Design Status** (Re-evaluated after Phase 1): ✅ ALL GATES PASSED

**Design Review**:
- ✅ **Principle I**: Test coverage confirmed in data-model.md (unit, integration, contract tests)
- ✅ **Principle II**: Fast test estimates validated (~2-3s total for fast battery)
- ✅ **Principle III**: Complete battery defined (~10s total including integration tests)
- ✅ **Principle IV**: Commit strategy confirmed in quickstart.md examples
- ✅ **Principle V**: Design maintains simplicity (pure functions, no new patterns)
- ✅ **Principle VI**: Language requirements confirmed (English code, Portuguese docs)

**Changes Since Pre-Research**:
- No architectural changes required
- No new dependencies added
- No complexity introduced
- All files remain <500 lines

No violations requiring justification in Complexity Tracking section.

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
├── gen_synth/
│   ├── biases.py              # MODIFY: Add coherence rule logic
│   ├── validation.py          # MODIFY: Add coherence validation
│   ├── psychographics.py      # MODIFY: Remove hobbies, valores, estilo_vida generation
│   ├── behavior.py            # MODIFY: Remove uso_tecnologia, comportamento_compra generation
│   └── synth_builder.py       # MODIFY: Update to skip removed fields
├── query/
│   └── (no changes needed)
└── __main__.py                # (no changes needed)

data/
└── schemas/
    └── synth-schema-cleaned.json  # MODIFY: Remove 5 fields, bump version

tests/
├── unit/
│   ├── test_coherence_rules.py    # NEW: Unit tests for personality-bias mapping
│   ├── test_biases.py             # MODIFY: Add coherence rule tests
│   └── test_validation.py         # MODIFY: Add field removal validation tests
├── integration/
│   └── test_schema_validation.py  # MODIFY: Add end-to-end schema validation tests
└── contract/
    └── test_schema_contract.py    # NEW: Validate schema against spec requirements
```

**Structure Decision**: Single project structure (Python CLI tool). This feature modifies existing schema definition and generation logic without adding new architectural layers. Changes are localized to:
1. Schema JSON file (data model definition)
2. Generation modules (remove field population logic)
3. Validation modules (add coherence checking)
4. Test modules (verify all requirements)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
