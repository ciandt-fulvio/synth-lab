# Implementation Plan: Gerar Synths Realistas

**Branch**: `001-generate-synths` | **Date**: 2025-12-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-generate-synths/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a command-line Python script (`scripts/gen_synth.py`) that generates realistic Brazilian synthetic personas (Synths) with comprehensive demographic, psychographic, behavioral, and cognitive attributes. The script accepts a count parameter to generate multiple Synths, validates them against a JSON Schema, and stores each Synth as an individual JSON file in `data/synths/{id}.json`. The generation process uses IBGE statistical distributions to ensure demographic realism representative of the Brazilian population.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**:
- `jsonschema` (JSON Schema validation)
- `faker` with pt-BR locale (Brazilian name generation)
- Standard library: `string`, `random`, `datetime`, `json`, `pathlib`, `argparse`

**Storage**: Filesystem - JSON files in `data/synths/` directory (one file per Synth named `{id}.json`)
**Testing**: Validation functions in `if __name__ == "__main__":` blocks per constitution (formal pytest optional)
**Target Platform**: macOS/Linux/Windows - cross-platform Python script
**Project Type**: Single Python script project (simple CLI tool)
**Performance Goals**:
- Single Synth generation: <5 seconds (SC-001)
- Batch of 100 Synths: <2 minutes (SC-003)
- Support up to 10,000 Synths per execution (SC-010)

**Constraints**:
- 100% JSON Schema validation compliance (SC-002)
- No duplicate IDs in 10,000 generations (SC-005)
- Demographic distribution within 10% of IBGE data (SC-004)
- All fields must be non-null (SC-009)
- 60%+ psychographic variation within same demographics (SC-007)

**Scale/Scope**:
- Generate 1-10,000 Synths per execution
- ~150-200 attributes per Synth across 7 categories
- JSON Schema with ~50 field definitions
- Single script file following ≤25 line function limit

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Pre-Research)

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **I. Notebook-First Development** | Jupyter notebooks as primary deliverable for exploratory work | ✅ PASS | Script-only approach is appropriate - this is a CLI tool for data generation, not exploratory analysis. User explicitly requested script implementation. |
| **II. Python Environment Management** | Virtual environment at project root with Python 3.13 | ✅ PASS | Will use existing venv/ with Python 3.13. Dependencies managed via pyproject.toml per CLAUDE.md standards. |
| **III. Simple Script Architecture** | Functions ≤25 lines, NO classes except dataclasses, NO frameworks | ✅ PASS | Plan uses simple functions, no OOP. May use dataclasses for Synth data structure only if needed. |
| **IV. Frequent Version Control Commits** | Commit at meaningful checkpoints | ✅ PASS | Will commit after: (1) schema creation, (2) generator functions, (3) validation logic, (4) CLI interface, (5) testing. |
| **V. Simplicity and Code Quality** | Functions ≤25 lines, minimize dependencies, PEP 8 | ✅ PASS | Only essential dependencies (jsonschema, faker). Functions kept small and focused. |
| **VI. Language** | Code in English, docs in Portuguese | ✅ PASS | Code/variables in English, docstrings and markdown in Portuguese. |

**Constitution Compliance**: ✅ **APPROVED** - All principles satisfied

**Rationale for Script-First Approach**:
- User explicitly requested script implementation: `scripts/gen_synth.py`
- CLI tool for data generation, not exploratory analysis
- Deterministic output (JSON files), not interactive exploration
- Aligns with constitution allowance for scripts when "user explicitly requests"

### Post-Design Check (After Phase 1)

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **I. Notebook-First Development** | Jupyter notebooks as primary deliverable | ✅ PASS | Still appropriate - script design is complete, future analysis can use notebooks (examples/analyze_synths.ipynb planned) |
| **II. Python Environment Management** | Virtual environment with Python 3.13 | ✅ PASS | Confirmed - dependencies added to pyproject.toml (faker, jsonschema) |
| **III. Simple Script Architecture** | Functions ≤25 lines, NO classes | ✅ PASS | Design uses focused functions only. No classes planned except potential dataclass for config loading (acceptable per constitution). |
| **IV. Frequent Commits** | Commit at checkpoints | ✅ PASS | Plan includes 5+ commit points during implementation |
| **V. Simplicity** | Minimize dependencies, PEP 8 | ✅ PASS | Only 2 external deps (faker, jsonschema). All functions will follow ≤25 line limit. |
| **VI. Language** | Code English, docs Portuguese | ✅ PASS | Maintained throughout design artifacts |

**Final Constitution Compliance**: ✅ **APPROVED** - All principles still satisfied after design

**Design Artifacts Created**:
1. ✅ `research.md` - Technical decisions and IBGE data sources
2. ✅ `data-model.md` - Complete Synth entity structure (7 categories, ~150 fields)
3. ✅ `contracts/synth-schema.json` - JSON Schema Draft 2020-12 (formal validation)
4. ✅ `quickstart.md` - Usage examples and CLI documentation

**No Complexity Violations** - Design maintains simplicity:
- Single script file (`scripts/gen_synth.py`)
- Simple functions (each ≤25 lines, single purpose)
- No OOP complexity (no classes beyond optional dataclass for config)
- Minimal dependencies (2 external: faker, jsonschema)
- Standard library for everything else (string, random, json, pathlib, argparse)

## Project Structure

### Documentation (this feature)

```text
specs/001-generate-synths/
├── spec.md              # Feature specification (already created)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - IBGE data sources & library choices
├── data-model.md        # Phase 1 output - Synth entity structure
├── quickstart.md        # Phase 1 output - Usage examples
├── contracts/           # Phase 1 output - JSON Schema files
│   └── synth-schema.json
├── checklists/          # Quality validation
│   └── requirements.md  # Already created - spec validation
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
synth-lab/                    # Project root
├── pyproject.toml            # Python dependencies (uv-managed)
├── uv.lock                   # Dependency lock file
├── .gitignore                # Git ignore (venv/, data/synths/, .ipynb_checkpoints/)
├── README.md                 # Project overview and setup
│
├── scripts/                  # Executable scripts
│   └── gen_synth.py          # Main Synth generator CLI (THIS FEATURE)
│
├── data/                     # Data files (gitignored except structure)
│   ├── synths/               # Generated Synth JSON files (one per synth)
│   │   └── {id}.json         # Individual Synth files
│   ├── config/               # Configuration data
│   │   ├── ibge_distributions.json    # IBGE demographic distributions
│   │   ├── brazilian_names.json       # Brazilian first/last names by region
│   │   ├── occupations.json           # CBO occupations list
│   │   └── interests_hobbies.json     # Curated lists for psychographics
│   └── schemas/              # JSON Schema definitions
│       └── synth-schema.json # Synth validation schema (symlink from specs/001-.../contracts/)
│
├── docs/                     # Additional documentation
│   └── synth_attributes.md   # Detailed attribute documentation (P4 user story)
│
└── examples/                 # Usage examples
    └── analyze_synths.ipynb  # Notebook for analyzing generated Synths (future)
```

**Structure Decision**:

This is a **single-project CLI tool** following the constitution's script architecture principles. The structure prioritizes:

1. **Simple Script Organization**: Single `scripts/gen_synth.py` file containing all generator logic in focused functions (≤25 lines each)
2. **Data Separation**: Configuration data (`data/config/`) separated from generated output (`data/synths/`)
3. **Schema Co-location**: JSON Schema stored both in feature spec (`specs/001-.../contracts/`) and runtime location (`data/schemas/`) via symlink
4. **Documentation**: Comprehensive docs for attributes (P4 user story) in `docs/`
5. **Future Extensibility**: `examples/` directory for future Jupyter notebooks analyzing generated Synths (constitution-compliant exploration)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations** - Constitution fully satisfied. No complexity tracking needed.
