<!--
Sync Impact Report
==================
Version: 1.1.0 → 1.2.0 (MINOR - Simplification and consolidation)
Ratification Date: 2025-12-12
Last Amended: 2026-01-02

Modified Principles:
- "Test-First Development" - Simplified, removed redundant enforcement text
- "Fast Test Battery" - Consolidated timing requirements
- "Complete Test Battery" - Simplified
- "Frequent Commits" - Simplified
- "Simplicity and Code Quality" - Simplified
- "Architecture" - Now references CLAUDE.md directly for rules (DRY)
- "Other Principles" - Consolidated into Architecture section

Removed Sections:
- Redundant enforcement text in each principle
- Development Workflow (duplicated from CLAUDE.md)
- Quality Gates detailed section (covered by principles)
- Runtime Development Guidance (now in CLAUDE.md)

Added Sections:
- None (simplification release)

Templates Requiring Updates:
✅ plan-template.md - No changes needed (already references constitution)
✅ tasks-template.md - No changes needed
✅ spec-template.md - No changes needed

Follow-up TODOs:
- None
-->

# synth-lab Constitution

## Core Principles

### I. Test-First Development (TDD/BDD) - NON-NEGOTIABLE

Tests MUST be written and runned BEFORE implementation code.

**Rules:**
- Tests MUST fail initially (Red), implementation makes them pass (Green), then refactor
- BDD acceptance criteria in Given-When-Then format
- No code commits accepted without corresponding tests

### II. Fast Test Battery on Every Commit

Fast tests MUST run before each commit and complete in under 5 seconds.

**Rules:**
- Unit tests and critical integration tests only
- Tests exceeding time limit MUST be moved to slow battery
- Commits failing fast tests MUST NOT be pushed

### III. Complete Test Battery Before Pull Requests

All tests (fast + slow) MUST pass before opening a PR.

**Rules:**
- Test results documented in PR description
- Coverage MUST meet project thresholds
- CI/CD blocks PRs with failing tests

### IV. Frequent Version Control Commits

Commits MUST be atomic and made at each logical milestone.

**Rules:**
- One logical change per commit
- Clear commit messages describing what was accomplished
- Each commit represents working code (tests passing)

### V. Simplicity and Code Quality

Code MUST prioritize simplicity and maintainability.

**Rules:**
- Functions < 30 lines, single-purpose
- Files < 500 lines (TSX/HTML may be up to 1000)
- Dependencies minimized and researched
- Linters enforce style standards

### VI. Language

- Code (classes, variables, functions) MUST be in English
- Documentation MUST be in Portuguese
- User-facing strings MUST be i18n-ready (English + Portuguese)

### VII. Architecture - NON-NEGOTIABLE

Architecture rules are defined in:
- **Backend**: [`docs/arquitetura.md`](../../docs/arquitetura.md)
- **Frontend**: [`docs/arquitetura_front.md`](../../docs/arquitetura_front.md)
- **Quick Reference**: [`CLAUDE.md`](../../CLAUDE.md)

**Backend Rules:**
- Router: `request → service.method() → response` (NADA mais)
- Lógica de negócio: SEMPRE em services
- Acesso a dados: SEMPRE em repositories
- LLM calls: DEVEM usar Phoenix tracing
- SQL: DEVE ser parametrizado

**Frontend Rules:**
- Pages: Compõem componentes + usam hooks
- Components: Puros (props → JSX), SEM fetch
- Hooks: Encapsulam React Query
- Services: Funções com `fetchAPI`

**Additional Principles:**
- Phoenix tracing for all LLM calls (first-class observability)
- DRY, SOLID, KISS, YAGNI principles
- Alembic for database migrations

## Documentation Requirements

**Every Feature:**
- `spec.md` - User stories and acceptance criteria
- `plan.md` - Technical approach
- `tasks.md` - Implementation tasks

**Every Code File:**
- Documentation header describing purpose
- Type hints for functions
- Docstrings for public interfaces

## Governance

**Commit Process:**
1. Write tests → verify they fail
2. Implement → commit at each logical step
3. Run fast tests before commit
4. Run complete tests before PR

**PR Process:**
1. All tests pass locally
2. Create PR with summary + test confirmation
3. CI/CD validates automatically
4. Merge when tests pass and reviews approve

**Constitution Amendments:**
- Versioning: MAJOR (breaking), MINOR (additions), PATCH (clarifications)
- Amendments tracked in this file's Sync Impact Report
- Non-negotiable principles require team consensus to modify

**Version**: 1.2.0 | **Ratified**: 2025-12-12 | **Last Amended**: 2026-01-02
