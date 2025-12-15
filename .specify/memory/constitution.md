<!--
Sync Impact Report
==================
Version: 0.0.0 → 1.0.0 (MAJOR - Initial constitution ratification)
Ratification Date: 2025-12-12
Last Amended: 2025-12-12

Modified Principles:
- N/A (initial version)

Added Sections:
- I. Test-First Development (TDD/BDD) - NON-NEGOTIABLE
- II. Fast Test Battery on Every Commit
- III. Complete Test Battery Before Pull Requests
- IV. Frequent Version Control Commits
- V. Simplicity and Code Quality
- Development Workflow section
- Quality Gates section
- Governance section

Removed Sections:
- N/A (initial version)

Templates Requiring Updates:
✅ plan-template.md - Constitution Check section updated with specific principle verification
✅ tasks-template.md - Test-first workflow emphasized, constitution compliance notes added
✅ spec-template.md - User scenarios and acceptance criteria already aligned with BDD
✅ checklist-template.md - No changes required (generic template)
✅ agent-file-template.md - No changes required (generic template)

Follow-up TODOs:
- None
-->

# Nexus Planner Constitution

## Core Principles

### I. Test-First Development (TDD/BDD) - NON-NEGOTIABLE

**TDD (Test-Driven Development)** and **BDD (Behavior-Driven Development)** are mandatory for all feature development. This principle is non-negotiable under any circumstances.

**Rules:**
- Tests MUST be written BEFORE implementation code
- Tests MUST fail initially (Red phase of Red-Green-Refactor)
- Implementation code is written ONLY to make tests pass (Green phase)
- Code is refactored ONLY after tests pass (Refactor phase)
- BDD acceptance criteria MUST be defined in user story format (Given-When-Then)
- Test coverage MUST address all acceptance criteria before code is written

**Rationale:** Test-first development ensures that requirements are understood before implementation begins, prevents over-engineering, provides immediate feedback on design decisions, and creates a safety net for refactoring. BDD ensures that tests align with user value and business requirements.

**Enforcement:** No code commits are accepted without corresponding tests. Tests must be committed and shown to fail before implementation commits are made.

### II. Fast Test Battery on Every Commit

A fast test battery MUST run on every commit to provide immediate feedback during development.

**Rules:**
- Fast tests (unit and critical integration tests) battery MUST complete in under 5 seconds (each test in less than 0.5 second)
- Fast test battery MUST run automatically before each commit
- Fast tests MUST cover core functionality and prevent obvious regressions
- If fast test battery exceeds 5 seconds, tests must be optimized or moved to slow battery
- Commits that fail fast tests MUST NOT be pushed to remote repository

**Rationale:** Rapid feedback loops are essential for productive development. Developers need immediate confirmation that changes haven't broken core functionality. A 5-second limit ensures tests remain a helpful tool rather than a productivity impediment.

**Enforcement:** Configure pre-commit hooks or CI/CD pipelines to enforce fast test execution. Fast test failures block commits.

### III. Complete Test Battery Before Pull Requests

The complete test suite (including slower integration and end-to-end tests) MUST pass before any pull request is opened.

**Rules:**
- All tests (fast + slow) MUST pass before opening a PR
- Test results MUST be verified and documented in PR description
- PRs with failing tests MUST NOT be submitted for review
- Test coverage MUST meet project minimum thresholds (defined per feature)
- Acceptance criteria from user stories MUST be validated by passing tests

**Enforcement:** CI/CD pipeline runs complete test battery on PR creation. PRs with test failures are automatically blocked from merge.

### IV. Frequent Version Control Commits

Commits MUST be made frequently to capture incremental progress and maintain clear development history.

**Rules:**
- Commit MUST be made at each task phase completion
- Commit MUST be made when any small, logical objective is achieved
- Commit messages MUST clearly describe what was accomplished
- Commits MUST be atomic (single logical change per commit)
- Each commit MUST represent working code (tests passing at commit time)

**Rationale:** Frequent commits provide detailed development history, enable easier debugging through git bisect, facilitate code review by showing incremental changes, and reduce risk of work loss. Atomic commits make it easier to revert problematic changes without losing valuable work.

**Enforcement:** Task completion requires corresponding commit. Code reviews verify appropriate commit granularity.

### V. Simplicity and Code Quality

Code MUST prioritize simplicity, readability, and maintainability over cleverness or premature optimization.

**Rules:**
- Functions MUST be focused and single-purpose (prefer < 30 lines)
- Files MUST remain under 500 lines of code (except for HTML, TSX files that may be up to 1000 lines)
- Complex logic MUST be justified and documented
- Dependencies MUST be minimized and well-researched
- Code MUST follow project style guidelines (enforced via linters)

**Rationale:** Simple code is easier to understand, test, and modify. Clear code reduces onboarding time, decreases bug introduction, and improves long-term maintainability. Size limits prevent files from becoming unmaintainable monoliths.

**Enforcement:** Code reviews reject unnecessary complexity. Linting tools enforce style standards. Files exceeding size limits trigger refactoring requirements.

### VI. Language
- The code names os Classes, Variables, and Functions must be written in English.
- The documentation must be written in Portuguese.
- System must be i18n ready, with all user-facing strings externalized for localization and, initially, provided in English and Portuguese.

**Enforcement:** Code reviews will check for adherence to language requirements in code and documentation.

## Development Workflow

### Commit and Branch Strategy

**Branch Naming:**
- Feature branches: `###-feature-name` (e.g., `001-backend-api`)
- Branches are created from main and merged via pull request

**Commit Process:**
1. Write tests (commit with message: "test: add tests for [feature]")
2. Verify tests fail (document in commit or local notes)
3. Implement feature incrementally, committing at each logical step
4. Refactor if needed (commit with message: "refactor: improve [aspect]")
5. Run fast test battery before each commit
6. Push commits to feature branch regularly

**Pull Request Process:**
1. Run complete test battery locally
2. Verify all tests pass
3. Create PR with:
   - Summary of changes
   - Test results confirmation
   - Links to related issues/specs
4. CI/CD automatically runs complete test battery
5. Address review feedback with new commits
6. Merge only when tests pass and reviews approve

### Documentation Requirements

**Every Feature Must Include:**
- Feature specification (spec.md) with user stories and acceptance criteria
- Implementation plan (plan.md) with technical approach
- Task list (tasks.md) organized by user story
- Quickstart guide (quickstart.md) for using the feature
- Data model documentation (data-model.md) if applicable

**Every Code File Must Include:**
- Clear documentation header describing purpose
- Links to relevant third-party package documentation
- Type hints for functions (using Python typing library)
- Docstrings for public functions and classes

## Quality Gates

### Test Coverage Requirements

**Test Types:**
- **Unit Tests**: Test individual functions/classes in isolation
- **Integration Tests**: Test interactions between components
- **Contract Tests**: Validate API contracts and interfaces
- **End-to-End Tests**: Validate complete user journeys

**Coverage Thresholds:**
- Fast battery includes unit tests and critical integration tests (< 5s total)
- Complete battery includes all test types
- Minimum coverage thresholds defined per feature in plan.md
- All user story acceptance criteria MUST have corresponding tests

### Validation Requirements

**Before Commits:**
- Fast test battery passes (< 5s)
- Code follows project style guidelines
- Commit message clearly describes change

**Before Pull Requests:**
- Complete test battery passes (all tests)
- Test coverage meets minimum thresholds
- All acceptance criteria validated
- Documentation updated
- Linting and type checking pass

**Before Deployment:**
- All PR reviews approved
- CI/CD pipeline passes completely
- Quickstart guide validated
- Breaking changes documented

## Governance

### Amendment Process

This constitution can be amended when necessary, but amendments require:
1. Clear documentation of the reason for amendment
2. Approval from project maintainers
3. Migration plan for existing code if amendment affects current practices
4. Version bump following semantic versioning rules:
   - **MAJOR**: Backward-incompatible governance changes, principle removals/redefinitions
   - **MINOR**: New principles added, materially expanded guidance
   - **PATCH**: Clarifications, wording improvements, non-semantic refinements

### Compliance and Reviews

**Constitution Compliance:**
- All PRs and code reviews MUST verify compliance with constitution principles
- Violations of non-negotiable principles are grounds for immediate PR rejection
- Complexity that violates Principle V MUST be justified in plan.md Complexity Tracking section

**Review Checkpoints:**
- Constitution is reviewed during feature planning (plan.md creation)
- Constitution compliance checked during task definition (tasks.md creation)
- Constitution principles validated during code review
- Constitution amendments tracked in this file's version history

### Runtime Development Guidance

For day-to-day development instructions and tooling setup, refer to:
- Project README.md for setup and running instructions
- Global CLAUDE.md for AI agent development standards
- Template files in `.specify/templates/` for feature development workflow

**Version**: 1.0.0 | **Ratified**: 2025-12-12 | **Last Amended**: 2025-12-12
