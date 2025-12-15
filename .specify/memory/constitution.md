<!--
  Sync Impact Report:
  - Version change: [TEMPLATE] → 1.0.0 (initial ratification)
  - Modified principles: N/A (first version)
  - Added sections: All core principles established
  - Removed sections: N/A
  - Templates requiring updates:
    ✅ plan-template.md: Constitution Check section aligns with principles
    ✅ spec-template.md: User stories and requirements align with TDD-first approach
    ✅ tasks-template.md: Task structure supports TDD workflow and modular architecture
  - Follow-up TODOs: None
-->

# NexusFlow Insight AI Constitution

## Core Principles

### I. DRY (Don't Repeat Yourself) - NON-NEGOTIABLE
**Rule**: Code duplication is strictly prohibited. Any repeated logic MUST be refactored into reusable functions, classes, or modules.

It's not just about lines of code; duplication of logic, algorithms, or data structures is equally forbidden. This includes copy-pasting code blocks, re-implementing similar functions, or duplicating configuration settings.

### II. Test-Driven Development (TDD) - NON-NEGOTIABLE

**Rule**: Tests MUST be written BEFORE implementation code. The Red-Green-Refactor cycle is strictly enforced:
1. Write the smallest test that captures desired behavior
2. Run test - it MUST fail (Red)
3. Write minimal code to make test pass (Green)
4. Refactor without changing behavior
5. Repeat

**Enforcement**:
- No production code without corresponding tests written first
- Tests MUST fail before implementation begins
- One test = one behavior (keep tests focused)
- Tests MUST be fast (<1s each)
- Minimum 80% code coverage required
- Use pytest markers: `@pytest.mark.unit` for isolated tests, `@pytest.mark.integration` for database tests

### III. Type Safety and Explicit Contracts

**Rule**: All functions MUST have complete type hints. Use mypy in strict mode. Avoid `typing.Any` unless absolutely necessary with explicit justification.

**Rationale**: Type hints improve code understanding, enable better tooling support, catch errors at development time, and serve as inline documentation. Strict typing prevents ambiguity.

**Enforcement**:
- Type hints required for all function parameters and return values
- Use native Python 3.11+ types: `list[str]` not `typing.List[str]`
- mypy strict mode MUST pass without errors
- Document type hint exceptions with comments explaining necessity

### IV. Module Size and Organization

**Rule**: Files MUST NOT exceed 500 lines of code (hard limit). When approaching limit, refactor immediately. Prefer simple functions over classes unless managing state.

**Enforcement**:
- Monitor file sizes during development
- Refactor before hitting 500-line limit
- Use functions as default
- Classes only for: state management, data validation models (Pydantic), established design patterns
- Each file MUST have module docstring explaining purpose

### V. Real Data Validation

**Rule**: Every module MUST include a `if __name__ == "__main__":` block that validates functionality with REAL data. NO mocking of core functionality. NO fake/synthetic test data for validation.

**Enforcement**:
- Every module MUST have validation block
- Validation MUST use real data (actual repositories, real commits, real metrics)
- Validation MUST compare actual results against expected results
- Success messages ONLY if validation explicitly passes
- Exit with code 1 on ANY validation failure
- MagicMock is FORBIDDEN for core functionality testing
- External APIs (GitHub) may be mocked in tests

### VI. Repository Pattern for Data Access

**Rule**: All database CRUD operations MUST go through Repository classes. Direct SQLAlchemy session usage outside repositories is prohibited.

**Rationale**: Repository pattern abstracts data access, enables easier database migration (SQLite → PostgreSQL), centralizes queries, and simplifies testing.

**Enforcement**:
- All models MUST have corresponding repository class in `db/repositories.py`
- API and Workers MUST use repositories, not direct session calls
- Repositories MUST follow consistent interface pattern
- Migration to different database requires only repository changes

### VII. Observability and Debugging

**Rule**: All significant operations MUST be logged using loguru. NO `print()` statements in production code. Structured logging required for tracking operations.

**Rationale**: Proper logging enables debugging production issues, tracking user actions, monitoring system health, and auditing data changes.

**Enforcement**:
- Use `from loguru import logger` for all logging
- Log levels: DEBUG (development details), INFO (significant operations), ERROR (failures)
- NO `print()` statements (use logger instead)
- Log structured data (include repository names, commit counts, metric values)

## Technical Standards

### Python Best Practices

**Requirements**:
- Python 3.11+ features preferred: use `list[str]` over `typing.List[str]`
- Use `pathlib.Path` not `os.path` for file operations
- Async code: NEVER use `asyncio.run()` inside functions (only in main blocks)
- NO conditional imports (try/except) for required packages
- Imports ordered: stdlib → third-party → local (enforced by ruff isort)

### Code Style

**Formatting**:
- `ruff format` (Black-compatible, 100 char line length)
- Google-style docstrings for modules, classes, public functions
- Naming: snake_case (functions/variables), PascalCase (classes), UPPER_SNAKE_CASE (constants)

**Structure**:
- Maximum 500 lines per file
- Each file needs module docstring
- Imports organized: stdlib → third-party → local

### Testing Standards

**Framework**: pytest with markers and fixtures
- Unit tests: `@pytest.mark.unit` - fast, isolated, no database
- Integration tests: `@pytest.mark.integration` - real database, real data flow
- Minimum 80% coverage required (enforced in pyproject.toml)

**Test Organization**:
```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Database + worker tests
├── fixtures/       # Test data (JSON, YAML)
└── conftest.py     # Shared fixtures
```

## Development Workflow

### Git Workflow

**Branch Strategy**:
- `main`: stable, production-ready code
- `feature/*`: new features (base: main)
- `hotfix/*`: urgent fixes (base: main)

**Commit Standards**:
- Frequent, focused commits with clear messages. Create  a commit for each logical change or each phase completed.
- Run tests + linting before committing
- Conventional commits format: `type(scope): description`
- Examples: `feat(metrics): add cognitive load calculation`, `fix(api): resolve ownership query bug`

**Pull Request Requirements**:
- Clear description of changes
- Link related issues
- All tests must pass
- Code review required for main merges
- Squash commits on merge to keep clean history
- Delete feature/hotfix branches after merge

### External Research Rule

**Three-Strike Research Rule**: If a validation function fails 3 consecutive times with different approaches, the developer MUST use external research tools (web search, documentation) to find current best practices, package updates, or solutions. Document research findings in code comments.

## Governance

### Constitutional Authority

This constitution supersedes all other development practices and guidelines. When conflicts arise between this constitution and other documentation, the constitution takes precedence.

### Amendment Process

**Requirements for Amendments**:
1. Document proposed change with clear rationale
2. Assess impact on existing code and processes
3. Update affected templates and documentation
4. Obtain approval from project maintainers
5. Create migration plan if needed

### Version Semantics

Version follows MAJOR.MINOR.PATCH:

### Compliance Review

**All changes MUST verify**:
1. Workers + API separation maintained
2. TDD cycle followed (test before code)
3. Type hints complete and mypy passes
4. File size under 500 lines
5. Real data validation included
6. Repository pattern used for database access
7. Proper logging (no print statements)
8. Tests pass with >80% coverage

**Runtime Development Guidance**: For detailed development instructions, coding patterns, and operational procedures, refer to `CLAUDE.md` which provides agent-specific implementation guidance while adhering to these constitutional principles.

---

**Version**: 1.0.0 | **Ratified**: 2025-12-10 | **Last Amended**: 2025-12-10
