# Phase 0: Research - Architecture Refactoring Patterns

**Feature**: Remove CLI Commands & Fix Architecture
**Date**: 2025-12-20
**Status**: Complete

## Overview

This research phase investigates best practices for:
1. **Removing CLI commands** while preserving functionality in REST API
2. **Fixing architectural layering violations** (services importing from feature modules)
3. **Consolidating scattered models** to proper locations
4. **Moving business logic** from CLI to services following clean architecture

All research focused on Python-specific patterns using existing dependencies (FastAPI, Typer, Pydantic).

---

## Research Task 1: CLI Command Removal Strategy

### Decision: Graceful Deprecation with Clear Error Messages

**Chosen Approach**:
- Delete CLI command files completely
- Remove command registrations from master CLI dispatcher (`__main__.py`)
- Update help text to show only available commands
- No "deprecation warnings" phase - direct removal since API already exists

**Rationale**:
1. **API Already Available**: All 17 endpoints already provide the functionality
2. **Clear Migration Path**: Users can immediately switch to API
3. **Simplicity**: No complex deprecation infrastructure needed
4. **Typer Framework**: Command removal is straightforward (just don't register the command)

**Alternatives Considered**:
1. **Deprecation Warnings**: Keep commands but show warnings
   - **Rejected**: Adds complexity, delays cleanup, users already have API
2. **Redirect to API**: Have CLI commands call API internally
   - **Rejected**: Still maintain CLI code, doesn't fix architecture issues
3. **Stub Commands**: Keep commands but return "use API" message
   - **Rejected**: Still need to maintain command infrastructure

**Implementation Pattern**:
```python
# Before (in __main__.py):
from synth_lab.query import cli as query_cli
from synth_lab.research_agentic import cli as research_cli

app.add_typer(query_cli.app, name="listsynth")
app.add_typer(research_cli.app, name="research")

# After:
# Remove imports and registrations completely
# Only keep gensynth command
```

### CLI Error Handling

**Decision**: Natural Typer Behavior (Command Not Found)

When user tries removed commands, Typer automatically shows:
```
Error: No such command 'listsynth'.

Try 'synthlab --help' for help.
```

Updated help text naturally guides users to available commands and API documentation.

---

## Research Task 2: Architectural Layering Best Practices

### Decision: Clean Architecture with Service Layer

**Chosen Architecture**:
```
┌──────────────────┐
│  API Routers     │  (FastAPI routers)
│  CLI Commands    │  (Typer commands - only gensynth)
└────────┬─────────┘
         │ calls
┌────────▼─────────┐
│   Services       │  (Business logic, orchestration)
│  (stateless)     │
└────────┬─────────┘
         │ calls
┌────────▼─────────┐
│  Repositories    │  (Data access, DB queries)
│  (stateless)     │
└────────┬─────────┘
         │ queries
┌────────▼─────────┐
│   Database       │  (PostgreSQL, DuckDB)
└──────────────────┘
```

**Key Principles**:
1. **Services NEVER import from feature-specific modules** (current violation)
2. **Feature modules live UNDER services/** (not as peers)
3. **Models in models/ are API/DB contracts** (shared across layers)
4. **Feature-specific models live WITH feature code** (under services/feature/)

**Rationale**:
1. **Dependency Inversion**: Services depend on abstractions, not implementations
2. **Single Responsibility**: Each layer has clear purpose
3. **Testability**: Layers can be tested independently
4. **Maintainability**: Changes in one layer don't cascade

**Alternatives Considered**:
1. **Flat Structure** (all modules as peers):
   - **Rejected**: No clear boundaries, import cycles, coupling
2. **Feature Slices** (vertical slices per feature):
   - **Rejected**: Doesn't fit current API-driven architecture
3. **Hexagonal Architecture** (ports & adapters):
   - **Rejected**: Over-engineering for this codebase size

**References**:
- Clean Architecture (Robert C. Martin) - Dependency Rule
- FastAPI Best Practices: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- Python Application Layouts: https://realpython.com/python-application-layouts/

---

## Research Task 3: Service Dependencies Refactoring

### Problem Analysis

**Current Violations**:

1. **services/prfaq_service.py** (line 114):
   ```python
   from synth_lab.research_prfaq.generator import generate_prfaq_markdown, save_prfaq_markdown
   ```
   Service importing from feature module breaks layering.

2. **services/research_service.py** (line 224):
   ```python
   from synth_lab.research_agentic.batch_runner import run_batch_interviews
   ```
   Service importing orchestration logic from feature module.

### Decision: Move Feature Modules Under Services

**Chosen Approach**:
```python
# Current (WRONG):
src/synth_lab/
├── services/
│   └── prfaq_service.py  → imports from research_prfaq/
├── research_prfaq/       ← peer to services (wrong level)
    └── generator.py

# Target (CORRECT):
src/synth_lab/
├── services/
│   ├── prfaq_service.py  → imports from .research_prfaq
│   └── research_prfaq/   ← under services (correct level)
       └── generator.py
```

**Implementation Steps**:
1. Move `research_agentic/` → `services/research_agentic/`
2. Move `research_prfaq/` → `services/research_prfaq/`
3. Move `topic_guides/` → `services/topic_guides/`
4. Update imports in services to use relative imports
5. Update imports in API routers (still absolute, but new paths)

**Rationale**:
1. **Proper Nesting**: Feature logic belongs UNDER the layer that uses it
2. **Clear Ownership**: Services own their feature implementations
3. **No Circular Dependencies**: Parent can import child, not vice versa
4. **Discoverable**: Looking at services/ shows all business logic

**Alternatives Considered**:
1. **Keep separate, use dependency injection**:
   - **Rejected**: Adds complexity without solving layering issue
2. **Create separate `features/` directory**:
   - **Rejected**: Introduces new top-level concept, unclear boundaries
3. **Merge into single service files**:
   - **Rejected**: Files would exceed 500-line limit

**Migration Pattern**:
```python
# Before:
from synth_lab.research_prfaq.generator import generate_prfaq_markdown

# After (in prfaq_service.py):
from synth_lab.services.research_prfaq.generator import generate_prfaq_markdown
# Or using relative import:
from .research_prfaq.generator import generate_prfaq_markdown
```

---

## Research Task 4: Model Consolidation Strategy

### Problem Analysis

**Scattered Models** (7 files):
1. ✅ `models/synth.py` - API/DB models for Synth domain
2. ✅ `models/research.py` - API/DB models for Research domain
3. ✅ `models/prfaq.py` - API/DB models for PR-FAQ domain
4. ✅ `models/topic.py` - API/DB models for Topic domain
5. ✅ `models/pagination.py` - Shared pagination models
6. ❌ `research_prfaq/models.py` - Generation pipeline models (conflicts with #3)
7. ❌ `topic_guides/models.py` - Internal dataclasses (conflicts with #4)

**Conflict**: Same name (`models.py`) but different purposes:
- `models/prfaq.py`: API request/response models (PRFAQGenerateRequest, PRFAQSummary)
- `research_prfaq/models.py`: Generation pipeline models (PRFAQDocument, PRFAQSection)

### Decision: Rename Feature-Specific Models

**Chosen Approach**:
```python
# Current:
research_prfaq/models.py          # 488 lines - generation models
topic_guides/models.py            # 337 lines - internal models

# Target:
services/research_prfaq/generation_models.py  # Renamed + moved
services/topic_guides/internal_models.py      # Renamed + moved
```

**Naming Convention**:
- `models/` (top-level): **API/DB models** - shared across layers, Pydantic BaseModel
- `services/feature/generation_models.py`: **Pipeline/workflow models** - feature-specific
- `services/feature/internal_models.py`: **Internal dataclasses** - feature-specific

**Rationale**:
1. **Clear Intent**: Name indicates purpose (generation vs API vs internal)
2. **No Conflicts**: Different names prevent import confusion
3. **Colocated**: Feature models live with feature code (under services/)
4. **Discoverable**: Clear what each model file contains

**Alternatives Considered**:
1. **Merge all models into models/**:
   - **Rejected**: Files would exceed 500 lines, mixes concerns
2. **Use subdirectories** (`models/api/`, `models/internal/`):
   - **Rejected**: Doesn't solve feature-specific vs shared distinction
3. **Prefix with feature name** (`prfaq_models.py`):
   - **Rejected**: Less clear than descriptive suffix (`generation_models.py`)

**Import Updates**:
```python
# Before:
from synth_lab.research_prfaq.models import PRFAQDocument

# After:
from synth_lab.services.research_prfaq.generation_models import PRFAQDocument
```

---

## Research Task 5: Business Logic Extraction from CLI

### Problem Analysis

**Business Logic Currently in CLI Files**:

1. **research_agentic/cli.py** (lines 69-86):
   ```python
   def validate_synth_exists(synth_id: str, db: DatabaseManager) -> Dict:
       """Validate synth exists in database."""
       # 15 lines of business logic
   ```
   - **Issue**: Validation is business logic, belongs in service
   - **Used by**: Only CLI command (will be deleted)
   - **Action**: Extract to `synth_service.validate_exists()`

2. **topic_guides/cli.py** (lines 78-100+):
   ```python
   def create_topic_guide(...):
       """Create topic guide from files."""
       # 20+ lines of business logic
   ```
   - **Issue**: Creation logic belongs in service
   - **Used by**: Only CLI command (will be deleted)
   - **Action**: Extract to `topic_service.create_topic_guide()`

3. **query/cli.py** (direct database access):
   ```python
   @app.command()
   def listsynth(...):
       db = Database(db_path)  # Direct DB access
       results = db.query_synths(...)
   ```
   - **Issue**: No service layer, repository pattern bypassed
   - **Used by**: Only CLI command (will be deleted)
   - **Action**: Delete (API already uses synth_service properly)

### Decision: Extract to Services Before CLI Deletion

**Chosen Approach**:

**Step 1**: Extract business logic to services (if not already in API)
- `validate_synth_exists()` → `synth_service.validate_exists()`
- `create_topic_guide()` → Already exists in API via `topic_service`

**Step 2**: Verify API uses service methods

**Step 3**: Delete CLI files (business logic preserved in services)

**Rationale**:
1. **Preserve Logic**: Don't lose working code even if CLI-specific
2. **Reusable**: Services can be called from any interface (API, CLI, scripts)
3. **Testable**: Service methods easier to unit test than CLI commands

**Alternatives Considered**:
1. **Just delete CLI, logic lost**:
   - **Rejected**: Lose potentially useful validation/creation logic
2. **Keep logic in feature modules**:
   - **Rejected**: Defeats purpose of service layer
3. **Create separate utility modules**:
   - **Rejected**: Services are the right place for business logic

**Implementation Pattern**:
```python
# services/synth_service.py
class SynthService:
    def validate_exists(self, synth_id: str) -> SynthDetail:
        """Validate synth exists and return details."""
        synth = self.synth_repo.get_by_id(synth_id)
        if not synth:
            raise SynthNotFoundError(synth_id)
        return synth
```

---

## Research Task 6: Testing Strategy for Refactoring

### Decision: Test-Driven Refactoring (TDR)

**Chosen Approach**:

**Phase 1: Establish Baseline**
```bash
# Run ALL tests before ANY changes
pytest tests/
# Record results: X tests, Y passed, Z coverage
```

**Phase 2: Refactor with Test Safety**
```bash
# After each atomic change:
pytest tests/  # Fast battery (< 5s)

# Before each commit:
pytest tests/ --cov  # Full battery with coverage
```

**Phase 3: Verify No Regression**
```bash
# Final verification:
pytest tests/  # Must have same pass rate as baseline
curl http://localhost:8000/docs  # API still works
uv run synthlab --help  # CLI shows only gensynth
```

**Test Types**:
1. **Unit Tests** (services, repositories):
   - Verify services still work with new imports
   - Check model renames don't break serialization

2. **Integration Tests** (API endpoints):
   - All 17 endpoints return expected responses
   - No 500 errors from import issues

3. **Contract Tests** (API schemas):
   - Response schemas match OpenAPI spec
   - No breaking changes to API contracts

4. **Manual Verification**:
   - `uv run synthlab --help` shows only `gensynth`
   - Removed commands return "command not found"
   - API documentation still accessible

**Rationale**:
1. **Safety Net**: Tests catch breaking changes immediately
2. **Confidence**: Can refactor aggressively with test protection
3. **Regression Prevention**: Ensure API behavior unchanged
4. **Documentation**: Tests show what should still work

**Alternatives Considered**:
1. **Write new tests for refactoring**:
   - **Rejected**: Existing tests already cover functionality
2. **Manual testing only**:
   - **Rejected**: Too slow, error-prone, no repeatability
3. **Snapshot testing**:
   - **Rejected**: Doesn't exist in current codebase, adds complexity

---

## Summary of Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **CLI Removal** | Direct deletion, no deprecation | API already available, simplicity |
| **Architecture** | Clean layering: API → Service → Repository → DB | Industry standard, testable, maintainable |
| **Service Dependencies** | Move feature modules under services/ | Proper nesting, clear ownership, no circular deps |
| **Model Consolidation** | Rename to generation_models.py, internal_models.py | Clear intent, no conflicts, colocated |
| **Business Logic** | Extract to services before CLI deletion | Preserve logic, reusable, testable |
| **Testing** | Test-driven refactoring with baseline | Safety, confidence, regression prevention |

## Implementation Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking API contracts | Low | High | Run full test suite, verify API docs, check response schemas |
| Import errors after moves | Medium | Medium | Update all imports systematically, test each change |
| Lost business logic | Low | High | Extract to services BEFORE deleting CLI files |
| Incomplete model updates | Medium | Medium | Search codebase for all imports of renamed models |
| Test failures | Medium | High | Establish baseline, fix each failure before proceeding |

## Next Steps (Phase 1)

1. ✅ Generate `data-model.md` - Map current → target model locations
2. ✅ Generate `quickstart.md` - Migration guide for users (CLI → API)
3. ✅ Update agent context with new architecture
4. → Proceed to Phase 2: Task generation (`/speckit.tasks`)

---

**Research Complete**: All architectural decisions documented with rationale and patterns.
